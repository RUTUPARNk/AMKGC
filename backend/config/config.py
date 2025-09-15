import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator, field_validator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/node_llm_system"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    
    # LLM Configuration
    LLM_PROVIDER: str = "ollama"  # Can be "ollama" or "qwen"
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:latest"
    QWEN_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001"]
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # Rate Limiting
    RATE_LIMIT_LOGIN: int = 5  # attempts per minute
    RATE_LIMIT_REGISTER: int = 3  # attempts per minute
    RATE_LIMIT_API: int = 100  # requests per minute
    
    # Token Management
    MAX_TOKENS: int = 4096
    TOKEN_SPLIT_THRESHOLD: float = 0.8  # 80% of max tokens
    
    # Monitoring
    ENABLE_MONITORING: bool = True
    PROMETHEUS_PORT: int = 9090
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Cache TTL (in seconds)
    CACHE_TTL_NODE: int = 3600  # 1 hour
    CACHE_TTL_GRAPH: int = 1800  # 30 minutes
    CACHE_TTL_SEARCH: int = 900  # 15 minutes
    CACHE_TTL_SESSION: int = 86400  # 24 hours
    
    @field_validator('CORS_ORIGINS', mode='before')
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()

# Database engine and session
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=StaticPool,
    pool_pre_ping=True,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database health check
def check_database_connection() -> bool:
    """Check if database connection is working"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

# Redis health check
def check_redis_connection() -> bool:
    """Check if Redis connection is working"""
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        return True
    except Exception as e:
        print(f"Redis connection failed: {e}")
        return False

# Environment validation
def validate_environment() -> List[str]:
    """Validate environment configuration and return list of issues"""
    issues = []
    
    # Check required environment variables
    if not settings.SECRET_KEY or settings.SECRET_KEY == "your-secret-key-change-in-production":
        issues.append("SECRET_KEY should be set to a secure value")
    
    if not settings.OPENAI_API_KEY:
        issues.append("OPENAI_API_KEY is not set (fallback will not work)")
    
    # Check database connection
    if not check_database_connection():
        issues.append("Database connection failed")
    
    # Check Redis connection
    if not check_redis_connection():
        issues.append("Redis connection failed")
    
    return issues

# Configuration helpers
def get_cache_ttl(cache_type: str) -> int:
    """Get TTL for specific cache type"""
    ttl_map = {
        'node': settings.CACHE_TTL_NODE,
        'graph': settings.CACHE_TTL_GRAPH,
        'search': settings.CACHE_TTL_SEARCH,
        'session': settings.CACHE_TTL_SESSION,
    }
    return ttl_map.get(cache_type, 3600)

def get_rate_limit_config(action: str) -> dict:
    """Get rate limit configuration for specific action"""
    rate_limits = {
        'login': settings.RATE_LIMIT_LOGIN,
        'register': settings.RATE_LIMIT_REGISTER,
        'api': settings.RATE_LIMIT_API,
    }
    return {
        'max_requests': rate_limits.get(action, settings.RATE_LIMIT_API),
        'window': 60  # 1 minute window
    }

# Export settings for use in other modules
__all__ = [
    'settings',
    'engine',
    'SessionLocal',
    'get_db',
    'check_database_connection',
    'check_redis_connection',
    'validate_environment',
    'get_cache_ttl',
    'get_rate_limit_config'
] 