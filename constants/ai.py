from enum import Enum

CONTEXT_EXPIRE_TIME = 86400  # 24hrs by seconds
RATE_LIMIT_COUNT = 3
RATE_LIMIT_PERIOD = 10  # seconds
AI_MODEL = "ChatGPT", "Gemini"
AI_MODEL_NAME = "GPT-3.5 Turbo", "Gemini 1.5 Pro"
LOCALES = "vi", "en"
ACTIVE_TYPES = "send_message", "switch_model"


class AI_WS_ACTION_TYPE(str, Enum):
    SEND_MESSAGE = "send_message"
    SWITCH_MODEL = "switch_model"
    NEW_CONTEXT = "new_context"


class AI_WS_MESSAGE_TYPE(str, Enum):
    SYSTEM_MESSAGE = "system_message"
    AI_MESSAGE = "ai_message"
    CLIENT_MESSAGE = "client_message"
    SWITCH_MODEL = "switch_model"
    CONTEXT = "context"
