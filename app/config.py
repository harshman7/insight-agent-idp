"""
Application configuration loaded from environment variables.
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "insight_agent"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    USE_SQLITE: bool = False  # Set to True to use SQLite instead of PostgreSQL
    
    @property
    def DATABASE_URL(self) -> str:
        if self.USE_SQLITE:
            return "sqlite:///./insight_agent.db"
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # LLM (Ollama)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"  # or mistral, codellama, etc.
    
    # Vector Store
    FAISS_INDEX_PATH: str = "data/embeddings/faiss.index"
    FAISS_DOCUMENTS_PATH: str = "data/embeddings/documents.pkl"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Data paths
    RAW_DOCS_PATH: str = "data/raw_docs"
    PROCESSED_PATH: str = "data/processed"
    
    # Application
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

