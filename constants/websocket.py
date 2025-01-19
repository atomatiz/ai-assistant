from enum import Enum

ACTIVE_TYPES = "send_message", "switch_model"


class WS_KEYS(str, Enum):
    ACTION = "action"
    CONTEXT = "context"


class AI_WS_SEND_KEYS(str, Enum):
    TYPE = "type"
    DATA = "data"
    MODEL = "model"
    MESSAGES = "messages"
    ID = "id"
    PROMPT = "prompt"


class AI_WS_ACTION_TYPE(str, Enum):
    SEND_MESSAGE = "send_message"
    SWITCH_MODEL = "switch_model"
    NEW_CONTEXT = "new_context"
    SET_CURRENT_MODEL = "set_current_model"
    CURRENT_MODEL = "current_model"


class AI_WS_MESSAGE_TYPE(str, Enum):
    SYSTEM_MESSAGE = "system_message"
    AI_MESSAGE = "ai_message"
    CLIENT_MESSAGE = "client_message"
    SWITCH_MODEL = "switch_model"
    CONTEXT = "context"
    PARTIAL_MESSAGE = "partial_message"
    CURRENT_MODEL = "current_model"
