import httpx
import logging

logger = logging.getLogger("scambaiter")

CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

async def send_final_report(session_id: str, scam_detected: bool, message_count: int, intelligence: dict):
    """
    Sends the final extracted intelligence to the evaluation endpoint.
    """
    payload = {
        "sessionId": session_id,
        "scamDetected": scam_detected,
        "totalMessagesExchanged": message_count,
        "extractedIntelligence": intelligence,
        "agentNotes": intelligence.get("agentNotes", "No notes")
    }
    
    import json
    print(f"\n[Callback] Sending Final Report | Session: {session_id} | ScamDetected: {scam_detected}")
    print(f"--- Extracted Intelligence ---")
    print(json.dumps(intelligence, indent=2))
    print(f"------------------------------")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(CALLBACK_URL, json=payload, timeout=10.0)
            response.raise_for_status()
            logger.info(f"Report sent successfully! Status: {response.status_code}")
            return True
    except Exception as e:
        logger.error(f"Failed to send report: {e}")
        return False
