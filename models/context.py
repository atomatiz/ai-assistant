from pydantic import BaseModel
from typing import List
from .message import Message


class Context(BaseModel):
    id: str
    messages: List[Message]
