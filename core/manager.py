from typing import Dict, Any, List
from models.api import MessageItem

# In-memory store: sessionId -> Dict
sessions: Dict[str, Any] = {}

class SessionManager:
    @staticmethod
    def get_session(session_id: str) -> Dict[str, Any]:
        if session_id not in sessions:
            sessions[session_id] = {
                "history": [],
                "scam_detected": False,
                "metadata": {}
            }
        return sessions[session_id]

    @staticmethod
    def add_message(session_id: str, message: MessageItem):
        session = SessionManager.get_session(session_id)
        session["history"].append(message)

    @staticmethod
    def set_scam_detected(session_id: str, status: bool):
        session = SessionManager.get_session(session_id)
        session["scam_detected"] = status
        
    @staticmethod
    def get_history(session_id: str) -> List[MessageItem]:
        return SessionManager.get_session(session_id)["history"]
