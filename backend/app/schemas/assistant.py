from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class AssistantRequest(BaseModel):
    message: str
    persona: str = "CEO"
    context: Optional[Dict[str, Any]] = None

class AssistantResponse(BaseModel):
    response: str
    sources: List[str] = []
    confidence: Optional[float] = None
    follow_up_suggestions: List[str] = []
