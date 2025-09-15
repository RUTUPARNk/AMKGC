import os
from typing import Optional

class Settings:
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://localhost/node_llm_system")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # LLM Configuration
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # CORS
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # Token Limits
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2000000"))
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    
    @classmethod
    def get_database_url(cls) -> str:
        return cls.DATABASE_URL
    
    @classmethod
    def get_redis_url(cls) -> str:
        return cls.REDIS_URL
    
    @classmethod
    def get_ollama_model(cls) -> str:
        return cls.OLLAMA_MODEL
    
    @classmethod
    def get_openai_api_key(cls) -> Optional[str]:
        return cls.OPENAI_API_KEY

settings = Settings() 