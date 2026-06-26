"""
Tests for database models.
Verifies that models create correct tables
and relationships work correctly.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Portfolio, Holding, Transaction


# =============================================
# TEST DATABASE SETUP
# =============================================

# Use in-memory SQLite for testing
# Fast, no setup needed, deleted after tests
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def engine():
    """Create test database engine."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def session(engine):
    """Create test database session."""
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


# =============================================
# USER MODEL TESTS
# =============================================

def test_create_user(session):
    """Test creating a user."""
    user = User(username="pavan", email="pavan@email.com")
    session.add(user)
    session.commit()

    assert user.id is not None
    assert user.username == "pavan"
    assert user.email == "pavan@email.com"
    assert user.created_at is not None


def test_user_unique_username(session):
    """Test that two users cannot have same username."""
    user1 = User(username="pavan", email="pavan@email.com")
    user2 = User(username="pavan", email="other@email.com")

    session.add(user1)
    session.commit()

    session.add(user2)
    with pytest.raises(Exception):
        session.commit()


def test_user_unique_email(session):
    """Test that two users cannot have same email."""
    user1 = User(username="pavan", email="pavan@email.com")
    user2 = User(username="rahul", email="pavan@email.com")

    session.add(user1)
    session.commit()

    session.add(user2)
    with pytest.raises(Exception):
        session.commit()


def test_user_repr(session):
    """Test user string representation."""
    user = User(username="pavan", email="pavan@email.com")
    session.add(user)
    session.commit()

    assert "pavan" in repr(user)


# =============================================
# PORTFOLIO MODEL TESTS
# =============================================

def test_create_portfolio(session):
    """Test creating a portfolio linked to a user."""
    user = User(username="pavan", email="pavan@email.com")
    session.add(user)
    session.commit()

    portfolio = Portfolio(
        user_id=user.id,
        name="Tech Stocks",
        description="My tech investments"
    )
    session.add(portfolio)
    session.commit()

    assert portfolio.id is not None
    assert portfolio.name == "Tech Stocks"
    assert portfolio.user_id == user.id
    assert portfolio.created_at is not None


def test_portfolio_belongs_to_user(session):
    """Test that portfolio links back to its user."""
    user = User(username="pavan", email="pavan@email.com")
    session.add(user)
    session.commit()

    portfolio = Portfolio(user_id=user.id, name="Tech Stocks")
    session.add(portfolio)
    session.commit()

    assert portfolio.user_id == user.id


def test_user_has_multiple_portfolios(session):
    """Test one user can have many portfolios."""
    user = User(username="pavan", email="pavan@email.com")
    session.add(user)
    session.commit()

    portfolio1 = Portfolio(user_id=user.id, name="Tech Stocks")
    portfolio2 = Portfolio(user_id=user.id, name="Retirement")
    portfolio3 = Portfolio(user_id=user.id, name="Growth")

    session.add_all([portfolio1, portfolio2, portfolio3])
    session.commit()

    session.refresh(user)
    assert len(user.portfolios) == 3


def test_delete_user_deletes_portfolios(session):
    """Test deleting user also deletes their portfolios."""
    user = User(username="pavan", email="pavan@email.com")
    session.add(user)
    session.commit()

    portfolio = Portfolio(user_id=user.id, name="Tech Stocks")
    session.add(portfolio)
    session.commit()

    portfolio_id = portfolio.id

    session.delete(user)
    session.commit()

    deleted = session.query(Portfolio).filter(
        Portfolio.id == portfolio_id
    ).first()
    assert deleted is None


# =============================================
# HOLDING MODEL TESTS
# =============================================

def test_create_holding(session):
    """Test creating a holding in a portfolio."""
    user = User(username="pavan", email="pavan@email.com")
    session.add(user)
    session.commit()

    portfolio = Portfolio(user_id=user.id, name="Tech Stocks")
    session.add(portfolio)
    session.commit()

    holding = Holding(
        portfolio_id=portfolio.id,
        ticker="AAPL",
        shares=10.0,
        average_price=180.50
    )
    session.add(holding)
    session.commit()

    assert holding.id is not None
    assert holding.ticker == "AAPL"
    assert holding.shares == 10.0
    assert holding.average_price == 180.50
    assert holding.portfolio_id == portfolio.id


def test_portfolio_has_multiple_holdings(session):
    """Test one portfolio can have many holdings."""
    user = User(username="pavan", email="pavan@email.com")
    session.add(user)
    session.commit()

    portfolio = Portfolio(user_id=user.id, name="Tech Stocks")
    session.add(portfolio)
    session.commit()

    holding1 = Holding(
        portfolio_id=portfolio.id,
        ticker="AAPL",
        shares=10.0,
        average_price=180.50
    )
    holding2 = Holding(
        portfolio_id=portfolio.id,
        ticker="TSLA",
        shares=5.0,
        average_price=250.00
    )
    holding3 = Holding(
        portfolio_id=portfolio.id,
        ticker="JPM",
        shares=20.0,
        average_price=145.00
    )

    session.add_all([holding1, holding2, holding3])
    session.commit()

    session.refresh(portfolio)
    assert len(portfolio.holdings) == 3


def test_delete_portfolio_deletes_holdings(session):
    """Test deleting portfolio also deletes its holdings."""
    user = User(username="pavan", email="pavan@email.com")
    session.add(user)
    session.commit()

    portfolio = Portfolio(user_id=user.id, name="Tech Stocks")
    session.add(portfolio)
    session.commit()

    holding = Holding(
        portfolio_id=portfolio.id,
        ticker="AAPL",
        shares=10.0,
        average_price=180.50
    )
    session.add(holding)
    session.commit()

    holding_id = holding.id

    session.delete(portfolio)
    session.commit()

    deleted = session.query(Holding).filter(
        Holding.id == holding_id
    ).first()
    assert deleted is None


def test_holding_repr(session):
    """Test holding string representation."""
    user = User(username="pavan", email="pavan@email.com")
    session.add(user)
    session.commit()

    portfolio = Portfolio(user_id=user.id, name="Tech Stocks")
    session.add(portfolio)
    session.commit()

    holding = Holding(
        portfolio_id=portfolio.id,
        ticker="AAPL",
        shares=10.0,
        average_price=180.50
    )
    session.add(holding)
    session.commit()

    assert "AAPL" in repr(holding)
    assert "10.0" in repr(holding)


# =============================================
# TRANSACTION MODEL TESTS
# =============================================

def test_create_buy_transaction(session):
    """Test creating a BUY transaction."""
    user = User(username="pavan", email="pavan@email.com")
    session.add(user)
    session.commit()

    portfolio = Portfolio(user_id=user.id, name="Tech Stocks")
    session.add(portfolio)
    session.commit()

    holding = Holding(
        portfolio_id=portfolio.id,
        ticker="AAPL",
        shares=10.0,
        average_price=180.50
    )
    session.add(holding)
    session.commit()

    transaction = Transaction(
        holding_id=holding.id,
        transaction_type="BUY",
        shares=10.0,
        price=180.50,
        total_value=1805.00
    )
    session.add(transaction)
    session.commit()

    assert transaction.id is not None
    assert transaction.transaction_type == "BUY"
    assert transaction.shares == 10.0
    assert transaction.price == 180.50
    assert transaction.total_value == 1805.00


def test_create_sell_transaction(session):
    """Test creating a SELL transaction."""
    user = User(username="pavan", email="pavan@email.com")
    session.add(user)
    session.commit()

    portfolio = Portfolio(user_id=user.id, name="Tech Stocks")
    session.add(portfolio)
    session.commit()

    holding = Holding(
        portfolio_id=portfolio.id,
        ticker="AAPL",
        shares=10.0,
        average_price=180.50
    )
    session.add(holding)
    session.commit()

    transaction = Transaction(
        holding_id=holding.id,
        transaction_type="SELL",
        shares=5.0,
        price=195.00,
        total_value=975.00
    )
    session.add(transaction)
    session.commit()

    assert transaction.transaction_type == "SELL"
    assert transaction.shares == 5.0
    assert transaction.price == 195.00
    assert transaction.total_value == 975.00


def test_holding_has_multiple_transactions(session):
    """Test one holding can have many transactions."""
    user = User(username="pavan", email="pavan@email.com")
    session.add(user)
    session.commit()

    portfolio = Portfolio(user_id=user.id, name="Tech Stocks")
    session.add(portfolio)
    session.commit()

    holding = Holding(
        portfolio_id=portfolio.id,
        ticker="AAPL",
        shares=10.0,
        average_price=180.50
    )
    session.add(holding)
    session.commit()

    transaction1 = Transaction(
        holding_id=holding.id,
        transaction_type="BUY",
        shares=5.0,
        price=180.00,
        total_value=900.00
    )
    transaction2 = Transaction(
        holding_id=holding.id,
        transaction_type="BUY",
        shares=5.0,
        price=181.00,
        total_value=905.00
    )
    transaction3 = Transaction(
        holding_id=holding.id,
        transaction_type="SELL",
        shares=2.0,
        price=195.00,
        total_value=390.00
    )

    session.add_all([transaction1, transaction2, transaction3])
    session.commit()

    session.refresh(holding)
    assert len(holding.transactions) == 3


def test_delete_holding_deletes_transactions(session):
    """Test deleting holding also deletes its transactions."""
    user = User(username="pavan", email="pavan@email.com")
    session.add(user)
    session.commit()

    portfolio = Portfolio(user_id=user.id, name="Tech Stocks")
    session.add(portfolio)
    session.commit()

    holding = Holding(
        portfolio_id=portfolio.id,
        ticker="AAPL",
        shares=10.0,
        average_price=180.50
    )
    session.add(holding)
    session.commit()

    transaction = Transaction(
        holding_id=holding.id,
        transaction_type="BUY",
        shares=10.0,
        price=180.50,
        total_value=1805.00
    )
    session.add(transaction)
    session.commit()

    transaction_id = transaction.id

    session.delete(holding)
    session.commit()

    deleted = session.query(Transaction).filter(
        Transaction.id == transaction_id
    ).first()
    assert deleted is None


def test_transaction_repr(session):
    """Test transaction string representation."""
    user = User(username="pavan", email="pavan@email.com")
    session.add(user)
    session.commit()

    portfolio = Portfolio(user_id=user.id, name="Tech Stocks")
    session.add(portfolio)
    session.commit()

    holding = Holding(
        portfolio_id=portfolio.id,
        ticker="AAPL",
        shares=10.0,
        average_price=180.50
    )
    session.add(holding)
    session.commit()

    transaction = Transaction(
        holding_id=holding.id,
        transaction_type="BUY",
        shares=10.0,
        price=180.50,
        total_value=1805.00
    )
    session.add(transaction)
    session.commit()

    assert "BUY" in repr(transaction)
    assert "10.0" in repr(transaction)