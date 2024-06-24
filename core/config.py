import os
from dotenv import find_dotenv, load_dotenv
from pydantic_settings import BaseSettings

ENV = os.getenv("ENV", "")

def load_dotenv_fallback(env_files):
    for env_file in env_files:
        dotenv_path = find_dotenv(env_file)
        if dotenv_path:
            load_dotenv(dotenv_path)
            return dotenv_path
    return None

ENV_FILES = {
    "env": [".env.production", ".env.development", ".env"],
}

dotenv_path = load_dotenv_fallback(ENV_FILES.get(ENV, ENV_FILES["env"]))
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
       env_file = dotenv_path

settings = Settings()