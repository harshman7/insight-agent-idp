"""
Tests for SQL tools and safety guards.
"""
import pytest
from datetime import datetime
from app.services.sql_tools import SQLTools
from app.models import Transaction
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base


@pytest.fixture
def test_db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    # Add sample data
    transactions = [
        Transaction(
            date=datetime(2024, 1, 15),
            amount=1500.00,
            vendor="Acme Corp",
            category="Rent",
            description="Monthly rent"
        ),
        Transaction(
            date=datetime(2024, 2, 10),
            amount=1500.00,
            vendor="Acme Corp",
            category="Rent",
            description="Monthly rent"
        ),
        Transaction(
            date=datetime(2024, 1, 20),
            amount=250.50,
            vendor="Tech Supplies",
            category="Office",
            description="Supplies"
        ),
    ]
    for txn in transactions:
        session.add(txn)
    session.commit()
    
    yield session
    session.close()


def test_sql_tools_execute_safe_select(test_db_session, monkeypatch):
    """Test that SQL tools can execute safe SELECT queries."""
    # Mock the SessionLocal to return our test session
    monkeypatch.setattr("app.db.SessionLocal", lambda: test_db_session)
    
    result = SQLTools.execute_query("SELECT * FROM transactions LIMIT 2")
    
    assert len(result) == 2
    assert "amount" in result[0]
    assert "vendor" in result[0]


def test_sql_tools_rejects_dangerous_queries(monkeypatch):
    """Test that SQL tools reject dangerous operations."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.db import Base
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    monkeypatch.setattr("app.db.SessionLocal", lambda: session)
    
    # Test DROP
    with pytest.raises(ValueError, match="dangerous keyword"):
        SQLTools.execute_query("DROP TABLE transactions")
    
    # Test DELETE
    with pytest.raises(ValueError, match="dangerous keyword"):
        SQLTools.execute_query("DELETE FROM transactions")
    
    # Test INSERT
    with pytest.raises(ValueError, match="dangerous keyword"):
        SQLTools.execute_query("INSERT INTO transactions VALUES (1, 100)")
    
    # Test UPDATE
    with pytest.raises(ValueError, match="dangerous keyword"):
        SQLTools.execute_query("UPDATE transactions SET amount = 0")


def test_sql_tools_rejects_non_select(monkeypatch):
    """Test that SQL tools reject non-SELECT queries."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.db import Base
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    monkeypatch.setattr("app.db.SessionLocal", lambda: session)
    
    with pytest.raises(ValueError, match="Only SELECT queries"):
        SQLTools.execute_query("SHOW TABLES")


def test_sql_tools_adds_limit(test_db_session, monkeypatch):
    """Test that SQL tools automatically add LIMIT if missing."""
    monkeypatch.setattr("app.db.SessionLocal", lambda: test_db_session)
    
    result = SQLTools.execute_query("SELECT * FROM transactions", limit=1)
    
    assert len(result) == 1


def test_sql_tools_get_sample_data(test_db_session, monkeypatch):
    """Test getting sample data from a table."""
    monkeypatch.setattr("app.db.SessionLocal", lambda: test_db_session)
    
    result = SQLTools.get_sample_data("transactions", limit=2)
    
    assert len(result) <= 2
    assert isinstance(result, list)
    assert len(result) > 0

