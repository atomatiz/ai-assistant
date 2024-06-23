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
    ALLOW_HOSTS: list
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