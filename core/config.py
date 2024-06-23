import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    GEMINI_API_KEY: str
    OPENAI_MODEL: str
    GEMINI_MODEL: str
    REDIS_HOST: str
    REDIS_PORT: int
    ALLOWED_HOST_1: str
    ALLOWED_HOST_2: str
    ENV: str
    PORT: int

    class Config:
       
       env = os.getenv("ENV", "development")
       if env == "production":
            env_file = ".env.production"
       elif env == "development":
            env_file = ".env.development"
       else:
            env_file = ".env"
        
       load_dotenv(env_file)

settings = Settings()