"""
Tests for service layer.
Uses mocking to avoid needing real Redis, PostgreSQL, or Yahoo Finance.
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Portfolio, Holding, Transaction

TEST_DATABASE_URL = "sqlite:///:memory:"


# =============================================
# TEST DATABASE SETUP
# =============================================

@pytest.fixture
def engine():
    """Create in-memory SQLite engine for tests."""
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


@pytest.fixture
def user(session):
    """Create a test user."""
    u = User(username="pavan", email="pavan@email.com")
    session.add(u)
    session.commit()
    session.refresh(u)
    return u


@pytest.fixture
def portfolio(session, user):
    """Create a test portfolio."""
    p = Portfolio(user_id=user.id, name="Tech Stocks", description="Test")
    session.add(p)
    session.commit()
    session.refresh(p)
    return p


@pytest.fixture
def holding(session, portfolio):
    """Create a test holding."""
    h = Holding(
        portfolio_id=portfolio.id,
        ticker="AAPL",
        shares=10.0,
        average_price=150.0
    )
    session.add(h)
    session.flush()
    t = Transaction(
        holding_id=h.id,
        transaction_type="BUY",
        shares=10.0,
        price=150.0,
        total_value=1500.0
    )
    session.add(t)
    session.commit()
    session.refresh(h)
    return h


# =============================================
# USER SERVICE TESTS
# =============================================

def test_create_user(session):
    """create_user returns a persisted User with correct fields."""
    from services.portfolio_service import create_user

    user = create_user(session, "pavan", "pavan@email.com")

    assert user.id is not None
    assert user.username == "pavan"
    assert user.email == "pavan@email.com"


def test_get_user_found(session, user):
    """get_user returns the User when it exists."""
    from services.portfolio_service import get_user

    result = get_user(session, user.id)

    assert result is not None
    assert result.id == user.id
    assert result.username == "pavan"


def test_get_user_not_found(session):
    """get_user returns None for a non-existent ID."""
    from services.portfolio_service import get_user

    result = get_user(session, 9999)

    assert result is None


def test_get_user_by_username_found(session, user):
    """get_user_by_username returns the correct User."""
    from services.portfolio_service import get_user_by_username

    result = get_user_by_username(session, "pavan")

    assert result is not None
    assert result.username == "pavan"


def test_get_user_by_username_not_found(session):
    """get_user_by_username returns None when username doesn't exist."""
    from services.portfolio_service import get_user_by_username

    result = get_user_by_username(session, "nobody")

    assert result is None


def test_create_user_duplicate_username_raises(session):
    """create_user raises when username is already taken."""
    from services.portfolio_service import create_user

    create_user(session, "pavan", "pavan@email.com")

    with pytest.raises(Exception):
        create_user(session, "pavan", "other@email.com")


# =============================================
# PORTFOLIO SERVICE TESTS
# =============================================

def test_create_portfolio(session, user):
    """create_portfolio returns a Portfolio linked to the user."""
    from services.portfolio_service import create_portfolio

    portfolio = create_portfolio(session, user.id, "Tech Stocks", "My tech picks")

    assert portfolio.id is not None
    assert portfolio.name == "Tech Stocks"
    assert portfolio.description == "My tech picks"
    assert portfolio.user_id == user.id


def test_create_portfolio_no_description(session, user):
    """create_portfolio works without an optional description."""
    from services.portfolio_service import create_portfolio

    portfolio = create_portfolio(session, user.id, "Retirement")

    assert portfolio.id is not None
    assert portfolio.description is None


def test_get_portfolio_found(session, portfolio):
    """get_portfolio returns the Portfolio when it exists."""
    from services.portfolio_service import get_portfolio

    result = get_portfolio(session, portfolio.id)

    assert result is not None
    assert result.id == portfolio.id


def test_get_portfolio_not_found(session):
    """get_portfolio returns None for a non-existent ID."""
    from services.portfolio_service import get_portfolio

    result = get_portfolio(session, 9999)

    assert result is None


def test_get_user_portfolios(session, user):
    """get_user_portfolios returns all portfolios owned by a user."""
    from services.portfolio_service import create_portfolio, get_user_portfolios

    create_portfolio(session, user.id, "Tech Stocks")
    create_portfolio(session, user.id, "Retirement")
    create_portfolio(session, user.id, "Growth")

    portfolios = get_user_portfolios(session, user.id)

    assert len(portfolios) == 3


def test_get_user_portfolios_empty(session, user):
    """get_user_portfolios returns empty list when user has no portfolios."""
    from services.portfolio_service import get_user_portfolios

    result = get_user_portfolios(session, user.id)

    assert result == []


def test_delete_portfolio_returns_true(session, portfolio):
    """delete_portfolio returns True and removes the portfolio."""
    from services.portfolio_service import delete_portfolio, get_portfolio

    result = delete_portfolio(session, portfolio.id)

    assert result is True
    assert get_portfolio(session, portfolio.id) is None


def test_delete_portfolio_not_found_returns_false(session):
    """delete_portfolio returns False when portfolio doesn't exist."""
    from services.portfolio_service import delete_portfolio

    result = delete_portfolio(session, 9999)

    assert result is False


# =============================================
# HOLDING SERVICE TESTS
# =============================================

def test_add_holding_new(session, portfolio):
    """add_holding creates a new Holding and a BUY transaction."""
    from services.portfolio_service import add_holding

    holding = add_holding(session, portfolio.id, "AAPL", 10.0, 150.0)

    assert holding.id is not None
    assert holding.ticker == "AAPL"
    assert holding.shares == 10.0
    assert holding.average_price == 150.0
    assert len(holding.transactions) == 1
    assert holding.transactions[0].transaction_type == "BUY"


def test_add_holding_existing_updates_average_price(session, portfolio):
    """add_holding averages cost when ticker already exists in portfolio."""
    from services.portfolio_service import add_holding

    add_holding(session, portfolio.id, "AAPL", 10.0, 100.0)
    holding = add_holding(session, portfolio.id, "AAPL", 10.0, 200.0)

    assert holding.shares == 20.0
    assert holding.average_price == 150.0


def test_add_holding_existing_records_second_buy_transaction(session, portfolio):
    """add_holding on an existing ticker records a second BUY transaction."""
    from services.portfolio_service import add_holding

    h = add_holding(session, portfolio.id, "AAPL", 5.0, 100.0)
    h = add_holding(session, portfolio.id, "AAPL", 5.0, 200.0)

    assert len(h.transactions) == 2


def test_sell_holding_reduces_shares(session, holding):
    """sell_holding reduces share count and records a SELL transaction."""
    from services.portfolio_service import sell_holding

    transaction = sell_holding(session, holding.id, 4.0, 200.0)

    session.refresh(holding)
    assert holding.shares == 6.0
    assert transaction.transaction_type == "SELL"
    assert transaction.shares == 4.0
    assert transaction.price == 200.0
    assert transaction.total_value == 800.0


def test_sell_holding_too_many_shares_raises(session, holding):
    """sell_holding raises ValueError when selling more shares than owned."""
    from services.portfolio_service import sell_holding

    with pytest.raises(ValueError):
        sell_holding(session, holding.id, 50.0, 200.0)


def test_sell_holding_not_found_raises(session):
    """sell_holding raises ValueError when holding ID doesn't exist."""
    from services.portfolio_service import sell_holding

    with pytest.raises(ValueError):
        sell_holding(session, 9999, 1.0, 100.0)


def test_get_holdings(session, portfolio):
    """get_holdings returns all holdings in a portfolio."""
    from services.portfolio_service import add_holding, get_holdings

    add_holding(session, portfolio.id, "AAPL", 10.0, 150.0)
    add_holding(session, portfolio.id, "TSLA", 5.0, 250.0)

    holdings = get_holdings(session, portfolio.id)

    assert len(holdings) == 2
    tickers = {h.ticker for h in holdings}
    assert tickers == {"AAPL", "TSLA"}


def test_get_holdings_empty(session, portfolio):
    """get_holdings returns empty list when portfolio has no holdings."""
    from services.portfolio_service import get_holdings

    result = get_holdings(session, portfolio.id)

    assert result == []


def test_delete_holding_returns_true(session, holding):
    """delete_holding returns True and removes the holding."""
    from services.portfolio_service import delete_holding

    result = delete_holding(session, holding.id)

    assert result is True
    remaining = session.query(Holding).filter(Holding.id == holding.id).first()
    assert remaining is None


def test_delete_holding_not_found_returns_false(session):
    """delete_holding returns False when holding ID doesn't exist."""
    from services.portfolio_service import delete_holding

    result = delete_holding(session, 9999)

    assert result is False


# =============================================
# PORTFOLIO CALCULATION TESTS
# =============================================

def test_get_portfolio_value_empty_portfolio(session, portfolio):
    """get_portfolio_value returns zeros when portfolio has no holdings."""
    from services.portfolio_service import get_portfolio_value

    result = get_portfolio_value(session, portfolio.id)

    assert result["total_value"] == 0
    assert result["total_cost"] == 0
    assert result["profit_loss"] == 0
    assert result["profit_loss_pct"] == 0
    assert result["holdings_breakdown"] == []


@patch("services.portfolio_service.get_multiple_prices")
def test_get_portfolio_value_with_holdings(mock_prices, session, portfolio):
    """get_portfolio_value correctly calculates gain/loss using mocked prices."""
    from services.portfolio_service import add_holding, get_portfolio_value

    mock_prices.return_value = {"AAPL": 200.0, "TSLA": 300.0}

    add_holding(session, portfolio.id, "AAPL", 10.0, 150.0)
    add_holding(session, portfolio.id, "TSLA", 5.0, 250.0)

    result = get_portfolio_value(session, portfolio.id)

    # AAPL: 10 * 200 = 2000, cost 1500, P/L +500
    # TSLA:  5 * 300 = 1500, cost 1250, P/L +250
    assert result["total_value"] == 3500.0
    assert result["total_cost"] == 2750.0
    assert result["profit_loss"] == 750.0
    assert len(result["holdings_breakdown"]) == 2


@patch("services.portfolio_service.get_multiple_prices")
def test_get_portfolio_value_breakdown_fields(mock_prices, session, portfolio):
    """Each entry in holdings_breakdown has the required keys."""
    from services.portfolio_service import add_holding, get_portfolio_value

    mock_prices.return_value = {"AAPL": 180.0}
    add_holding(session, portfolio.id, "AAPL", 10.0, 150.0)

    result = get_portfolio_value(session, portfolio.id)
    entry = result["holdings_breakdown"][0]

    for key in ("ticker", "shares", "average_price", "current_price",
                "current_value", "cost_basis", "profit_loss", "profit_loss_pct"):
        assert key in entry


@patch("services.portfolio_service.get_multiple_prices")
def test_get_portfolio_value_loss(mock_prices, session, portfolio):
    """get_portfolio_value reports negative profit/loss correctly."""
    from services.portfolio_service import add_holding, get_portfolio_value

    mock_prices.return_value = {"AAPL": 100.0}
    add_holding(session, portfolio.id, "AAPL", 10.0, 150.0)

    result = get_portfolio_value(session, portfolio.id)

    assert result["profit_loss"] == -500.0
    assert result["profit_loss_pct"] < 0


def test_get_asset_allocation_empty_portfolio(session, portfolio):
    """get_asset_allocation returns empty list when portfolio has no holdings."""
    from services.portfolio_service import get_asset_allocation

    result = get_asset_allocation(session, portfolio.id)

    assert result == []


@patch("services.portfolio_service.get_multiple_prices")
def test_get_asset_allocation(mock_prices, session, portfolio):
    """get_asset_allocation returns correct percentages sorted descending."""
    from services.portfolio_service import add_holding, get_asset_allocation

    mock_prices.return_value = {"AAPL": 200.0, "TSLA": 100.0}

    add_holding(session, portfolio.id, "AAPL", 10.0, 150.0)  # value=2000
    add_holding(session, portfolio.id, "TSLA", 10.0, 80.0)   # value=1000

    result = get_asset_allocation(session, portfolio.id)

    assert len(result) == 2
    # AAPL is 66.67%, TSLA is 33.33% — AAPL should be first
    assert result[0]["ticker"] == "AAPL"
    assert result[0]["percentage"] > result[1]["percentage"]
    total_pct = sum(r["percentage"] for r in result)
    assert abs(total_pct - 100.0) < 0.1


@patch("services.portfolio_service.get_multiple_prices")
def test_get_asset_allocation_zero_prices(mock_prices, session, portfolio):
    """get_asset_allocation returns empty list when all prices are zero."""
    from services.portfolio_service import add_holding, get_asset_allocation

    mock_prices.return_value = {"AAPL": 0}
    add_holding(session, portfolio.id, "AAPL", 10.0, 150.0)

    result = get_asset_allocation(session, portfolio.id)

    assert result == []


def test_get_transaction_history(session, holding):
    """get_transaction_history returns all transactions for a holding."""
    from services.portfolio_service import get_transaction_history, sell_holding

    sell_holding(session, holding.id, 3.0, 200.0)

    history = get_transaction_history(session, holding.id)

    assert len(history) == 2
    types = {t.transaction_type for t in history}
    assert types == {"BUY", "SELL"}


def test_get_transaction_history_empty(session, portfolio):
    """get_transaction_history returns empty list for holding with no transactions."""
    from services.portfolio_service import get_transaction_history

    h = Holding(portfolio_id=portfolio.id, ticker="GOOG", shares=5.0, average_price=100.0)
    session.add(h)
    session.commit()

    result = get_transaction_history(session, h.id)

    assert result == []


# =============================================
# STOCK SERVICE TESTS
# =============================================

@patch("services.stock_service.get_cache")
def test_get_stock_price_cache_hit(mock_get_cache):
    """get_stock_price returns cached price without calling Yahoo Finance."""
    from services.stock_service import get_stock_price

    mock_get_cache.return_value = {"price": 180.50, "ticker": "AAPL"}

    price = get_stock_price("AAPL")

    assert price == 180.50
    mock_get_cache.assert_called_once_with("stock_price:AAPL")


@patch("services.stock_service.set_cache")
@patch("services.stock_service.get_cache")
@patch("services.stock_service.yf.Ticker")
def test_get_stock_price_cache_miss_fetches_yfinance(mock_ticker, mock_get_cache, mock_set_cache):
    """get_stock_price fetches from Yahoo Finance on cache miss and stores result."""
    from services.stock_service import get_stock_price

    mock_get_cache.return_value = None
    mock_stock = MagicMock()
    mock_stock.fast_info = {"lastPrice": 195.0}
    mock_ticker.return_value = mock_stock

    price = get_stock_price("AAPL")

    assert price == 195.0
    mock_set_cache.assert_called_once()
    args = mock_set_cache.call_args[0]
    assert args[0] == "stock_price:AAPL"
    assert args[1]["price"] == 195.0


@patch("services.stock_service.get_cache")
@patch("services.stock_service.yf.Ticker")
def test_get_stock_price_yfinance_error_returns_none(mock_ticker, mock_get_cache):
    """get_stock_price returns None when Yahoo Finance raises an exception."""
    from services.stock_service import get_stock_price

    mock_get_cache.return_value = None
    mock_ticker.side_effect = Exception("network error")

    price = get_stock_price("AAPL")

    assert price is None


@patch("services.stock_service.get_cache")
def test_get_stock_info_cache_hit(mock_get_cache):
    """get_stock_info returns cached info without calling Yahoo Finance."""
    from services.stock_service import get_stock_info

    cached_info = {
        "ticker": "AAPL", "name": "Apple Inc.", "sector": "Technology",
        "current_price": 195.0, "market_cap": 3000000000000,
        "pe_ratio": 28.5, "52_week_high": 220.0, "52_week_low": 165.0
    }
    mock_get_cache.return_value = cached_info

    result = get_stock_info("AAPL")

    assert result["ticker"] == "AAPL"
    assert result["name"] == "Apple Inc."


@patch("services.stock_service.set_cache")
@patch("services.stock_service.get_cache")
@patch("services.stock_service.yf.Ticker")
def test_get_stock_info_cache_miss_fetches_yfinance(mock_ticker, mock_get_cache, mock_set_cache):
    """get_stock_info fetches from Yahoo Finance on cache miss."""
    from services.stock_service import get_stock_info

    mock_get_cache.return_value = None
    mock_stock = MagicMock()
    mock_stock.info = {
        "longName": "Apple Inc.",
        "sector": "Technology",
        "currentPrice": 195.0,
        "marketCap": 3000000000000,
        "trailingPE": 28.5,
        "fiftyTwoWeekHigh": 220.0,
        "fiftyTwoWeekLow": 165.0
    }
    mock_ticker.return_value = mock_stock

    result = get_stock_info("AAPL")

    assert result["name"] == "Apple Inc."
    assert result["sector"] == "Technology"
    mock_set_cache.assert_called_once()


@patch("services.stock_service.get_cache")
@patch("services.stock_service.yf.Ticker")
def test_get_stock_info_yfinance_error_returns_none(mock_ticker, mock_get_cache):
    """get_stock_info returns None on Yahoo Finance failure."""
    from services.stock_service import get_stock_info

    mock_get_cache.return_value = None
    mock_ticker.side_effect = Exception("API error")

    result = get_stock_info("AAPL")

    assert result is None


@patch("services.stock_service.get_cache")
@patch("services.stock_service.yf.Ticker")
def test_get_multiple_prices(mock_ticker, mock_get_cache):
    """get_multiple_prices returns a dict of ticker → price for each symbol."""
    from services.stock_service import get_multiple_prices

    def fake_cache(key):
        prices = {
            "stock_price:AAPL": {"price": 180.0, "ticker": "AAPL"},
            "stock_price:TSLA": {"price": 250.0, "ticker": "TSLA"},
        }
        return prices.get(key)

    mock_get_cache.side_effect = fake_cache

    result = get_multiple_prices(["AAPL", "TSLA"])

    assert result == {"AAPL": 180.0, "TSLA": 250.0}


@patch("services.stock_service.get_cache")
@patch("services.stock_service.yf.Ticker")
def test_get_multiple_prices_skips_failed_tickers(mock_ticker, mock_get_cache):
    """get_multiple_prices omits tickers whose price fetch failed."""
    from services.stock_service import get_multiple_prices

    mock_get_cache.return_value = None
    mock_ticker.side_effect = Exception("network error")

    result = get_multiple_prices(["AAPL", "TSLA"])

    assert result == {}


# =============================================
# CACHE SERVICE TESTS
# =============================================

@patch("services.cache.redis_client")
def test_set_cache(mock_redis):
    """set_cache calls redis setex with JSON-serialized value."""
    import json
    from services.cache import set_cache

    set_cache("stock_price:AAPL", {"price": 180.0}, ttl=300)

    mock_redis.setex.assert_called_once_with(
        "stock_price:AAPL", 300, json.dumps({"price": 180.0})
    )


@patch("services.cache.redis_client")
def test_get_cache_hit(mock_redis):
    """get_cache returns parsed dict when key exists in Redis."""
    import json
    from services.cache import get_cache

    mock_redis.get.return_value = json.dumps({"price": 180.0})

    result = get_cache("stock_price:AAPL")

    assert result == {"price": 180.0}


@patch("services.cache.redis_client")
def test_get_cache_miss(mock_redis):
    """get_cache returns None when key is not in Redis."""
    from services.cache import get_cache

    mock_redis.get.return_value = None

    result = get_cache("stock_price:AAPL")

    assert result is None


@patch("services.cache.redis_client")
def test_delete_cache(mock_redis):
    """delete_cache calls redis delete with the given key."""
    from services.cache import delete_cache

    delete_cache("stock_price:AAPL")

    mock_redis.delete.assert_called_once_with("stock_price:AAPL")


@patch("services.cache.redis_client")
def test_clear_all_cache(mock_redis):
    """clear_all_cache calls redis flushdb."""
    from services.cache import clear_all_cache

    clear_all_cache()

    mock_redis.flushdb.assert_called_once()


@patch("services.cache.redis_client")
def test_is_cached_true(mock_redis):
    """is_cached returns True when key exists in Redis."""
    from services.cache import is_cached

    mock_redis.exists.return_value = 1

    assert is_cached("stock_price:AAPL") is True


@patch("services.cache.redis_client")
def test_is_cached_false(mock_redis):
    """is_cached returns False when key does not exist in Redis."""
    from services.cache import is_cached

    mock_redis.exists.return_value = 0

    assert is_cached("stock_price:AAPL") is False


@patch("services.cache.redis_client")
def test_get_cache_ttl(mock_redis):
    """get_cache_ttl returns remaining seconds from Redis."""
    from services.cache import get_cache_ttl

    mock_redis.ttl.return_value = 240

    result = get_cache_ttl("stock_price:AAPL")

    assert result == 240
    mock_redis.ttl.assert_called_once_with("stock_price:AAPL")


@patch("services.cache.redis_client")
def test_get_cache_ttl_key_missing(mock_redis):
    """get_cache_ttl returns -2 when key does not exist."""
    from services.cache import get_cache_ttl

    mock_redis.ttl.return_value = -2

    result = get_cache_ttl("nonexistent_key")

    assert result == -2
