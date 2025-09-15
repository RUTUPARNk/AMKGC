import os
from typing import Optional
from pydantic_settings import BaseSettings

class Neo4jSettings(BaseSettings):
    """Neo4j database configuration settings"""
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global instance
neo4j_settings = Neo4jSettings()
