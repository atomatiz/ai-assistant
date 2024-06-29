from pydantic import BaseModel
from typing import List, Optional
from .message import Message


class Context(BaseModel):
    id: str
    messages: List[Message]
    current_model: Optional[str] = None
