# backend/core/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "AI Ads Consultant"
    DEBUG: bool = False
    SECRET_KEY: str
    DATABASE_URL: str
    REDIS_URL: str
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str
    PINECONE_INDEX: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    class Config:
        env_file = ".env"

settings = Settings()