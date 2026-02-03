from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum

class SenderType(str, Enum):
    SCAMMER = "scammer"
    USER = "user"

class MessageItem(BaseModel):
    sender: SenderType
    text: str
    timestamp: int

class RequestMetadata(BaseModel):
    channel: Optional[str] = None
    language: Optional[str] = None
    locale: Optional[str] = None

class IncomingRequest(BaseModel):
    sessionId: str
    message: MessageItem
    conversationHistory: List[MessageItem] = []
    metadata: Optional[RequestMetadata] = None

class AgentResponse(BaseModel):
    status: Literal["success", "error"] = "success"
    reply: str
