from enum import Enum
from core.setting import settings

GPT_DEFAULT_CONTENT = "You are a helpful assistant."


class AI_MODELS(str, Enum):
    CHATGPT = "ChatGPT"
    GEMINI = "Gemini"


class AI_MODEL_NAMES(str, Enum):
    CHATGPT = "GPT-3.5 Turbo"
    GEMINI = "Gemini 1.5 Pro"


class AI_QUERY_MODELS(str, Enum):
    OPENAI = settings.OPENAI_MODEL
    GEMINI = settings.GEMINI_MODEL


class AI_API_KEYS(str, Enum):
    OPENAI = settings.OPENAI_API_KEY
    GEMINI = settings.GEMINI_API_KEY


class GPT_ROLES(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class GPT_CONTEXT_MESSAGE_KEYS(str, Enum):
    ROLE = "role"
    CONTENT = "content"


class GEMINI_ROLES(str, Enum):
    USER = "user"
    MODEL = "model"


class GEMINI_CONTEXT_MESSAGE_KEYS(str, Enum):
    ROLE = "role"
    PARTS = "parts"
