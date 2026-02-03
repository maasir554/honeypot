import os
import logging
from fastapi import FastAPI, Header, HTTPException, BackgroundTasks, Depends
from dotenv import load_dotenv

# Load env before imports that use it
load_dotenv()

from models.api import IncomingRequest, AgentResponse, SenderType, MessageItem
from core.detector import ScamDetector
from core.agent import HoneyPotAgent
from core.extractor import IntelligenceExtractor
from core.manager import SessionManager
from utils.callback import send_final_report

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("scambaiter-main")
# Add file handler for conversation logging
file_handler = logging.FileHandler("conversation.log")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Intelligence Logger
intel_logger = logging.getLogger("scambaiter-intel")
intel_handler = logging.FileHandler("extracted_intelligence.log")
intel_handler.setLevel(logging.INFO)
intel_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
intel_logger.addHandler(intel_handler)

app = FastAPI(title="Agentic Honey-Pot API")

# Initialize modules
# We initialize them globally for now. In production, might want dependency injection.
try:
    detector = ScamDetector()
    agent = HoneyPotAgent()
    extractor = IntelligenceExtractor()
    logger.info("Core modules initialized successfully.")
except ValueError as e:
    logger.error(f"Initialization failed: {e}")
    # We don't crash the app, but endpoints might fail.

async def verify_api_key(x_api_key: str = Header(...)):
    # Simple check. In real world, check against a DB or env.
    # For now, we accept any key or a specific one if set in env.
    expected_key = os.getenv("API_KEY") 
    if expected_key and x_api_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return x_api_key

@app.post("/api/chat", response_model=AgentResponse)
async def chat_endpoint(request: IncomingRequest, background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)):
    """
    Main entry point for the Honey-Pot.
    """
    session_id = request.sessionId
    incoming_msg = request.message
    
    SessionManager.add_message(session_id, incoming_msg)
    
    session_data = SessionManager.get_session(session_id)
    is_scam = session_data.get("scam_detected", False)
    
    if not is_scam:
        full_history = request.conversationHistory + [incoming_msg]
        is_scam = detector.detect(incoming_msg.text, request.conversationHistory)
        
        if is_scam:
            logger.info(f"Scam detected for session {session_id}!")
            SessionManager.set_scam_detected(session_id, True)
            logger.info(f"[CONVO] Session: {session_id} | SCAM DETECTED | Trigger: {incoming_msg.text}")
        else:
            logger.info(f"[CONVO] Session: {session_id} | Message seems safe")
            
    logger.info(f"[CONVO] Session: {session_id} | SCAMMER: {incoming_msg.text}")

    history_for_agent = request.conversationHistory + [incoming_msg]
    reply_text = agent.generate_reply(history_for_agent, incoming_msg.text)
    
    logger.info(f"[CONVO] Session: {session_id} | AGENT: {reply_text}")
    
    agent_msg = MessageItem(sender=SenderType.USER, text=reply_text, timestamp=incoming_msg.timestamp + 1000) # Fake ts
    SessionManager.add_message(session_id, agent_msg)
    
    if is_scam:
        background_tasks.add_task(process_intelligence, session_id, history_for_agent + [agent_msg], is_scam)
    
    return AgentResponse(status="success", reply=reply_text)

async def process_intelligence(session_id: str, history: list, is_scam: bool):
    try:
        data = extractor.extract(history)
        message_count = len(history)
        
        # Log to file
        intel_logger.info(f"Session: {session_id} | Extracted: {data}")
        
        await send_final_report(session_id, is_scam, message_count, data)
        
    except Exception as e:
        logger.error(f"Background processing failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
