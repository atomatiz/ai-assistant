from enum import Enum

DOMAIN = "base"
LOCALEDIR = "./locales"


class TRANSLATION_KEYS(str, Enum):
    RATE_LIMIT = "rate_limit"
    UNAVAILABLE_MODEL = "unavailable_model"
    AI_ACTIVATED_1 = "ai_activated_1"
    AI_ACTIVATED_2 = "ai_activated_2"
    AI_GREETING = "ai_greeting"
