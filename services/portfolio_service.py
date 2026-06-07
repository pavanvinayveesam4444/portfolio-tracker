"""
Portfolio service.
Handles all CRUD operations and calculations
for users, portfolios, holdings and transactions.
"""

import logging
from sqlalchemy.orm import Session
from models import User, Portfolio, Holding, Transaction
from services.stock_service import get_stock_price, get_multiple_prices

logger = logging.getLogger(__name__)


# =============================================
# USER OPERATIONS
# =============================================

def create_user(session: Session, username: str, email: str) -> User:
    """
    Create a new user.

    Args:
        session: database session
        username: unique username
        email: unique email address

    Returns:
        newly created User object
    """
    try:
        user = User(username=username, email=email)
        session.add(user)
        session.commit()
        session.refresh(user)
        logger.info(f"Created user: {username}")
        return user
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to create user {username}: {e}")
        raise


def get_user(session: Session, user_id: int) -> User | None:
    """
    Get a user by their ID.

    Returns:
        User object or None if not found
    """
    user = session.query(User).filter(User.id == user_id).first()
    if user:
        logger.info(f"Found user: {user.username}")
    else:
        logger.warning(f"User {user_id} not found")
    return user


def get_user_by_username(session: Session, username: str) -> User | None:
    """
    Get a user by their username.

    Returns:
        User object or None if not found
    """
    return session.query(User).filter(
        User.username == username
    ).first()


# =============================================
# PORTFOLIO OPERATIONS
# =============================================

def create_portfolio(session: Session, user_id: int,
                     name: str, description: str = None) -> Portfolio:
    """
    Create a new portfolio for a user.

    Args:
        session: database session
        user_id: which user owns this portfolio
        name: portfolio name like "Tech Stocks"
        description: optional description

    Returns:
        newly created Portfolio object
    """
    try:
        portfolio = Portfolio(
            user_id=user_id,
            name=name,
            description=description
        )
        session.add(portfolio)
        session.commit()
        session.refresh(portfolio)
        logger.info(f"Created portfolio: {name} for user {user_id}")
        return portfolio
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to create portfolio {name}: {e}")
        raise


def get_portfolio(session: Session, portfolio_id: int) -> Portfolio | None:
    """
    Get a portfolio by its ID.

    Returns:
        Portfolio object or None if not found
    """
    return session.query(Portfolio).filter(
        Portfolio.id == portfolio_id
    ).first()


def get_user_portfolios(session: Session, user_id: int) -> list[Portfolio]:
    """
    Get ALL portfolios belonging to a user.

    Returns:
        list of Portfolio objects
    """
    portfolios = session.query(Portfolio).filter(
        Portfolio.user_id == user_id
    ).all()
    logger.info(f"Found {len(portfolios)} portfolios for user {user_id}")
    return portfolios


def delete_portfolio(session: Session, portfolio_id: int) -> bool:
    """
    Delete a portfolio and all its holdings and transactions.

    Returns:
        True if deleted, False if not found
    """
    try:
        portfolio = get_portfolio(session, portfolio_id)
        if not portfolio:
            logger.warning(f"Portfolio {portfolio_id} not found")
            return False
        session.delete(portfolio)
        session.commit()
        logger.info(f"Deleted portfolio {portfolio_id}")
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to delete portfolio {portfolio_id}: {e}")
        raise


# =============================================
# HOLDING OPERATIONS
# =============================================

def add_holding(session: Session, portfolio_id: int,
                ticker: str, shares: float,
                purchase_price: float) -> Holding:
    """
    Add a new stock holding to a portfolio.
    Also records a BUY transaction automatically.

    Args:
        session: database session
        portfolio_id: which portfolio
        ticker: stock symbol like "AAPL"
        shares: how many shares bought
        purchase_price: price per share

    Returns:
        newly created or updated Holding object
    """
    try:
        # Check if holding already exists for this ticker
        existing = session.query(Holding).filter(
            Holding.portfolio_id == portfolio_id,
            Holding.ticker == ticker
        ).first()

        if existing:
            # Update existing holding
            # Calculate new average price
            total_shares = existing.shares + shares
            total_cost = (existing.shares * existing.average_price) + \
                         (shares * purchase_price)
            existing.average_price = total_cost / total_shares
            existing.shares = total_shares
            holding = existing
            logger.info(
                f"Updated holding: {ticker} now {total_shares} shares"
            )
        else:
            # Create brand new holding
            holding = Holding(
                portfolio_id=portfolio_id,
                ticker=ticker,
                shares=shares,
                average_price=purchase_price
            )
            session.add(holding)
            session.flush()
            logger.info(f"Created new holding: {ticker} {shares} shares")

        # Record the BUY transaction automatically
        transaction = Transaction(
            holding_id=holding.id,
            transaction_type="BUY",
            shares=shares,
            price=purchase_price,
            total_value=shares * purchase_price
        )
        session.add(transaction)
        session.commit()
        session.refresh(holding)
        return holding

    except Exception as e:
        session.rollback()
        logger.error(f"Failed to add holding {ticker}: {e}")
        raise


def sell_holding(session: Session, holding_id: int,
                 shares: float, sell_price: float) -> Transaction:
    """
    Sell shares from a holding.
    Records a SELL transaction automatically.

    Args:
        session: database session
        holding_id: which holding to sell from
        shares: how many shares to sell
        sell_price: price per share at sale

    Returns:
        Transaction object
    """
    try:
        holding = session.query(Holding).filter(
            Holding.id == holding_id
        ).first()

        if not holding:
            raise ValueError(f"Holding {holding_id} not found")

        if shares > holding.shares:
            raise ValueError(
                f"Cannot sell {shares} shares."
                f"Only {holding.shares} available."
            )

        # Reduce shares
        holding.shares -= shares

        # Record SELL transaction automatically
        transaction = Transaction(
            holding_id=holding_id,
            transaction_type="SELL",
            shares=shares,
            price=sell_price,
            total_value=shares * sell_price
        )
        session.add(transaction)
        session.commit()

        logger.info(
            f"Sold {shares} shares of {holding.ticker} at ${sell_price}"
        )
        return transaction

    except Exception as e:
        session.rollback()
        logger.error(f"Failed to sell holding {holding_id}: {e}")
        raise


def get_holdings(session: Session, portfolio_id: int) -> list[Holding]:
    """
    Get all holdings in a portfolio.

    Returns:
        list of Holding objects
    """
    return session.query(Holding).filter(
        Holding.portfolio_id == portfolio_id
    ).all()


def delete_holding(session: Session, holding_id: int) -> bool:
    """
    Delete a holding and all its transactions.

    Returns:
        True if deleted, False if not found
    """
    try:
        holding = session.query(Holding).filter(
            Holding.id == holding_id
        ).first()
        if not holding:
            return False
        session.delete(holding)
        session.commit()
        logger.info(f"Deleted holding {holding_id}")
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to delete holding {holding_id}: {e}")
        raise


# =============================================
# PORTFOLIO CALCULATIONS
# =============================================

def get_portfolio_value(session: Session, portfolio_id: int) -> dict:
    """
    Calculate total current value of a portfolio.

    Returns dictionary with:
        total_value:      current market value
        total_cost:       what you originally paid
        profit_loss:      how much you made or lost
        profit_loss_pct:  percentage gain or loss
        holdings_breakdown: value breakdown per stock
    """

    holdings = get_holdings(session, portfolio_id)

    if not holdings:
        return {
            "total_value": 0,
            "total_cost": 0,
            "profit_loss": 0,
            "profit_loss_pct": 0,
            "holdings_breakdown": []
        }

    # Get current prices for all stocks at once
    tickers = [h.ticker for h in holdings]
    current_prices = get_multiple_prices(tickers)

    total_value = 0
    total_cost = 0
    holdings_breakdown = []

    for holding in holdings:
        current_price = current_prices.get(holding.ticker, 0)
        current_value = holding.shares * current_price
        cost_basis = holding.shares * holding.average_price
        profit_loss = current_value - cost_basis

        if cost_basis > 0:
            profit_loss_pct = (profit_loss / cost_basis) * 100
        else:
            profit_loss_pct = 0

        total_value += current_value
        total_cost += cost_basis

        holdings_breakdown.append({
            "ticker": holding.ticker,
            "shares": holding.shares,
            "average_price": holding.average_price,
            "current_price": current_price,
            "current_value": round(current_value, 2),
            "cost_basis": round(cost_basis, 2),
            "profit_loss": round(profit_loss, 2),
            "profit_loss_pct": round(profit_loss_pct, 2)
        })

    total_profit_loss = total_value - total_cost
    total_profit_loss_pct = (
        (total_profit_loss / total_cost) * 100
        if total_cost > 0 else 0
    )

    logger.info(f"Portfolio {portfolio_id} value: ${total_value:.2f}")

    return {
        "total_value": round(total_value, 2),
        "total_cost": round(total_cost, 2),
        "profit_loss": round(total_profit_loss, 2),
        "profit_loss_pct": round(total_profit_loss_pct, 2),
        "holdings_breakdown": holdings_breakdown
    }


def get_asset_allocation(session: Session,
                          portfolio_id: int) -> list[dict]:
    """
    Calculate what percentage of portfolio
    each stock represents.

    Example:
        AAPL: 65% of portfolio
        TSLA: 35% of portfolio

    Returns:
        list of dicts with ticker and percentage
        sorted by highest percentage first
    """

    holdings = get_holdings(session, portfolio_id)

    if not holdings:
        return []

    tickers = [h.ticker for h in holdings]
    current_prices = get_multiple_prices(tickers)

    total_value = sum(
        h.shares * current_prices.get(h.ticker, 0)
        for h in holdings
    )

    if total_value == 0:
        return []

    allocation = []
    for holding in holdings:
        current_price = current_prices.get(holding.ticker, 0)
        holding_value = holding.shares * current_price
        percentage = (holding_value / total_value) * 100

        allocation.append({
            "ticker": holding.ticker,
            "value": round(holding_value, 2),
            "percentage": round(percentage, 2)
        })

    # Sort by percentage — highest first
    allocation.sort(key=lambda x: x["percentage"], reverse=True)

    logger.info(
        f"Calculated allocation for portfolio {portfolio_id}"
    )
    return allocation


def get_transaction_history(session: Session,
                             holding_id: int) -> list[Transaction]:
    """
    Get all buy/sell transactions for a holding.
    Ordered by most recent first.

    Returns:
        list of Transaction objects
    """
    transactions = session.query(Transaction).filter(
        Transaction.holding_id == holding_id
    ).order_by(Transaction.transaction_date.desc()).all()

    logger.info(
        f"Found {len(transactions)} transactions "
        f"for holding {holding_id}"
    )
    return transactions