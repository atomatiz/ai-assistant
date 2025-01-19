from enum import Enum
from core.setting import settings

HOST = "0.0.0.0"
PORT = settings.PORT
MODULE = "__main__"
PREFIX = "/api"
ORIGINS = [
    settings.ALLOWED_HOST_1,
    settings.ALLOWED_HOST_2,
    settings.ALLOWED_HOST_3,
    settings.ALLOWED_HOST_4,
]
ALLOWED_METHODS = []
ALLOWED_HEADERS = ["*"]
RATE_LIMIT_COUNT = 5
RATE_LIMIT_PERIOD = 10  # seconds


class SYSTEM_ROLES(str, Enum):
    USER = "You"
    AI = "AI"
