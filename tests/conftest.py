"""
Pytest configuration and fixtures.
"""
import pytest
import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base, get_db
from app.config import Settings
from app.models import Transaction, Document


@pytest.fixture(scope="function")
def test_db():
    """Create a temporary SQLite database for testing."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    # Create engine and session
    engine = create_engine(f"sqlite:///{db_path}")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    yield TestingSessionLocal()
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope="function")
def sample_transactions(test_db):
    """Create sample transaction data for testing."""
    transactions = [
        Transaction(
            date="2024-01-15",
            amount=1500.00,
            vendor="Acme Corp",
            category="Rent",
            description="Monthly rent payment"
        ),
        Transaction(
            date="2024-01-20",
            amount=250.50,
            vendor="Tech Supplies Inc",
            category="Office Supplies",
            description="Office supplies purchase"
        ),
        Transaction(
            date="2024-02-10",
            amount=1500.00,
            vendor="Acme Corp",
            category="Rent",
            description="Monthly rent payment"
        ),
        Transaction(
            date="2024-02-15",
            amount=75.00,
            vendor="Coffee Shop",
            category="Meals",
            description="Team lunch"
        ),
    ]
    
    for txn in transactions:
        test_db.add(txn)
    test_db.commit()
    
    return transactions


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    return Settings(
        USE_SQLITE=True,
        POSTGRES_DB="test_db"
    )

