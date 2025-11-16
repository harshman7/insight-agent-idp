"""
Tests for configuration settings.
"""
import pytest
from app.config import Settings


def test_settings_defaults():
    """Test that settings have sensible defaults."""
    settings = Settings()
    
    assert settings.POSTGRES_USER == "postgres"
    assert settings.POSTGRES_DB == "insight_agent"
    assert settings.OLLAMA_MODEL == "llama3"
    assert settings.EMBEDDING_MODEL == "all-MiniLM-L6-v2"


def test_database_url_sqlite():
    """Test SQLite database URL generation."""
    settings = Settings(USE_SQLITE=True)
    
    assert "sqlite" in settings.DATABASE_URL.lower()


def test_database_url_postgres():
    """Test PostgreSQL database URL generation."""
    settings = Settings(
        USE_SQLITE=False,
        POSTGRES_USER="testuser",
        POSTGRES_PASSWORD="testpass",
        POSTGRES_HOST="localhost",
        POSTGRES_PORT=5432,
        POSTGRES_DB="testdb"
    )
    
    url = settings.DATABASE_URL
    assert "postgresql" in url.lower()
    assert "testuser" in url
    assert "testdb" in url

