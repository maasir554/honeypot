import os
import logging
from typing import Optional, List
from fastapi import FastAPI, Header, HTTPException, BackgroundTasks, Depends, Query, Body
from dotenv import load_dotenv

# Load env before imports that use it
load_dotenv()

from models.api import IncomingRequest, AgentResponse, SenderType, MessageItem, RequestMetadata
from core.detector import ScamDetector
from core.agent import HoneyPotAgent
from core.extractor import IntelligenceExtractor
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
try:
    detector = ScamDetector()
    agent = HoneyPotAgent()
    extractor = IntelligenceExtractor()
    logger.info("Core modules initialized successfully.")
except ValueError as e:
    logger.error(f"Initialization failed: {e}")

async def verify_api_key(x_api_key: Optional[str] = Header(None), api_key: Optional[str] = Query(None)):
    # Allow passing key via Header OR Query param (for easy GET access via browser/curl)
    key = x_api_key or api_key
    expected_key = os.getenv("API_KEY") 
    if expected_key and key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return key

async def process_request_logic(request_data: IncomingRequest, background_tasks: BackgroundTasks, is_test_mode: bool = False):
    session_id = request_data.sessionId
    incoming_msg = request_data.message
    history = request_data.conversationHistory
    
    # Stateless Scam Detection:
    full_history = history + [incoming_msg]
    is_scam = detector.detect(incoming_msg.text, history)
    
    history_for_agent = history + [incoming_msg]
    reply_text = agent.generate_reply(history_for_agent, incoming_msg.text)
    
    # logger.info(f"[CONVO] Session: {session_id} | AGENT: {reply_text}")
    
    # Extract Intelligence
    # If Test Mode: Run synchronously and return result
    # If Prod Mode: Run background task based on Scam Detection
    
    intelligence_data = None        
    if is_scam:
        # Normal production flow
        agent_msg = MessageItem(sender=SenderType.USER, text=reply_text, timestamp=incoming_msg.timestamp + 1000)
        background_tasks.add_task(process_intelligence, session_id, history_for_agent + [agent_msg], is_scam)
    
    return AgentResponse(status="success", reply=reply_text, intelligence=intelligence_data)

async def process_intelligence(session_id: str, history: list, is_scam: bool):
    if not is_scam:
        return

    try:
        data = extractor.extract(history)
        message_count = len(history)
        
        await send_final_report(session_id, is_scam, message_count, data)
        
    except Exception as e:
        # logger.error(f"Background processing failed: {e}")
        pass

@app.post("/", response_model=AgentResponse)
async def handle_post(
    request: IncomingRequest, 
    background_tasks: BackgroundTasks, 
    key: str = Depends(verify_api_key),
    x_test_mode: bool = Header(False)
):
    """
    Handle POST request with JSON payload.
    """
    return await process_request_logic(request, background_tasks, is_test_mode=x_test_mode)

@app.get("/", response_model=AgentResponse)
async def handle_get(
    request: IncomingRequest,
    background_tasks: BackgroundTasks,
    key: str = Depends(verify_api_key),
    test_mode: bool = Query(False, description="Enable test mode to return extracted intelligence")
):
    """
    Handle GET request with JSON payload (forced).
    """
    return await process_request_logic(request, background_tasks, is_test_mode=test_mode)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
