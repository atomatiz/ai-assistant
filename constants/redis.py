from enum import Enum
from core.setting import settings

CONTEXT_EXPIRE_TIME = 86400  # 24hrs by seconds


class REDIS_CONNECTION_PARAMETERS(str, Enum):
    HOST = settings.REDIS_HOST
    PORT = settings.REDIS_PORT
    USERNAME = settings.REDIS_USER
    PASSWORD = settings.REDIS_PASS
    DECODE_RESPONSE = True


class AI_REDIS_DATA_KEYS(str, Enum):
    MODEL = "model"
    PROMT = "prompt"
