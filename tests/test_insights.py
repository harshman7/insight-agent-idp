"""
Tests for insights service and metrics functions.
"""
import pytest
from datetime import datetime
from app.services.insights import InsightsService
from app.models import Transaction
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base


@pytest.fixture
def test_db_session():
    """Create a test database session with sample data."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    # Add sample transactions
    transactions = [
        Transaction(
            date=datetime(2024, 1, 15),
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
        Transaction(
            date=datetime(2024, 2, 10),
            amount=1500.00,
            vendor="Acme Corp",
            category="Rent",
            description="Monthly rent"
        ),
        Transaction(
            date=datetime(2024, 2, 15),
            amount=75.00,
            vendor="Coffee Shop",
            category="Meals",
            description="Team lunch"
        ),
    ]
    for txn in transactions:
        session.add(txn)
    session.commit()
    
    # Create a mock SessionLocal that returns our test session
    class MockSessionLocal:
        def __init__(self, session):
            self.session = session
        
        def __call__(self):
            # Return a context manager that yields the session
            class SessionCM:
                def __init__(self, s):
                    self.session = s
                
                def __enter__(self):
                    return self.session
                
                def __exit__(self, *args):
                    pass  # Don't close, fixture handles it
            
            return SessionCM(self.session)
    
    yield MockSessionLocal(session)
    session.close()


def test_get_monthly_spend(test_db_session, monkeypatch):
    """Test monthly spend calculation."""
    # Patch SessionLocal in the module where it's used
    monkeypatch.setattr("app.services.insights.SessionLocal", test_db_session)
    
    result = InsightsService.get_monthly_spend(2024, 1)
    
    assert result["year"] == 2024
    assert result["month"] == 1
    assert result["total_spend"] == 1750.50  # 1500 + 250.50
    assert result["transaction_count"] == 2


def test_get_vendor_stats(test_db_session, monkeypatch):
    """Test vendor statistics calculation."""
    monkeypatch.setattr("app.services.insights.SessionLocal", test_db_session)
    
    result = InsightsService.get_vendor_stats(limit=10)
    
    assert isinstance(result, list)
    assert len(result) > 0
    # Acme Corp should be first (highest total spend)
    assert result[0]["vendor"] == "Acme Corp"
    assert result[0]["total_spend"] == 3000.00  # 1500 * 2
    assert result[0]["transaction_count"] == 2


def test_get_category_breakdown(test_db_session, monkeypatch):
    """Test category breakdown calculation."""
    monkeypatch.setattr("app.services.insights.SessionLocal", test_db_session)
    
    result = InsightsService.get_category_breakdown()
    
    assert isinstance(result, list)
    # Rent should be the highest category
    rent_cat = next((cat for cat in result if cat["category"] == "Rent"), None)
    assert rent_cat is not None
    assert rent_cat["total_spend"] == 3000.00
    assert rent_cat["transaction_count"] == 2


def test_get_time_series_data(test_db_session, monkeypatch):
    """Test time series data generation."""
    monkeypatch.setattr("app.services.insights.SessionLocal", test_db_session)
    
    result = InsightsService.get_time_series_data(
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 2, 28)
    )
    
    assert "daily" in result
    assert "monthly" in result
    assert "vendor_trends" in result
    assert isinstance(result["daily"], list)
    assert isinstance(result["monthly"], list)
    assert len(result["monthly"]) >= 2  # At least Jan and Feb


def test_get_time_series_empty(test_db_session, monkeypatch):
    """Test time series with no data."""
    monkeypatch.setattr("app.services.insights.SessionLocal", test_db_session)
    
    # Query for a period with no data
    result = InsightsService.get_time_series_data(
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 31)
    )
    
    assert result["daily"] == []
    assert result["monthly"] == []
    assert result["vendor_trends"] == []


def test_get_spending_forecast_insufficient_data(test_db_session, monkeypatch):
    """Test spending forecast with insufficient data."""
    monkeypatch.setattr("app.services.insights.SessionLocal", test_db_session)
    
    result = InsightsService.get_spending_forecast(months=3)
    
    # With only 2 months of data, might return insufficient_data
    assert "trend" in result
    assert "forecast" in result

