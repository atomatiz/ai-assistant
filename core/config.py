import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    GEMINI_API_KEY: str
    OPENAI_MODEL: str
    GEMINI_MODEL: str
    REDIS_HOST: str
    REDIS_PORT: int
    ALLOWED_HOST_1: str
    ALLOWED_HOST_2: str
    PORT: int

    class Config:
       env_file = ".env.production" if os.getenv("ENV") == "production" else ".env"

settings = Settings()