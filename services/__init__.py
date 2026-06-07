"""
Services package.
Import all services here.
"""

from services.database import create_tables, get_session, close_session, engine
from services.cache import (
    set_cache,
    get_cache,
    delete_cache,
    clear_all_cache,
    is_cached,
    get_cache_ttl
)
from services.stock_service import (
    get_stock_price,
    get_stock_info,
    get_multiple_prices
)
from services.portfolio_service import (
    create_user,
    get_user,
    get_user_by_username,
    create_portfolio,
    get_portfolio,
    get_user_portfolios,
    delete_portfolio,
    add_holding,
    sell_holding,
    get_holdings,
    delete_holding,
    get_portfolio_value,
    get_asset_allocation,
    get_transaction_history
)

__all__ = [
    # Database
    "create_tables",
    "get_session",
    "close_session",
    "engine",

    # Cache
    "set_cache",
    "get_cache",
    "delete_cache",
    "clear_all_cache",
    "is_cached",
    "get_cache_ttl",

    # Stock
    "get_stock_price",
    "get_stock_info",
    "get_multiple_prices",

    # Portfolio
    "create_user",
    "get_user",
    "get_user_by_username",
    "create_portfolio",
    "get_portfolio",
    "get_user_portfolios",
    "delete_portfolio",
    "add_holding",
    "sell_holding",
    "get_holdings",
    "delete_holding",
    "get_portfolio_value",
    "get_asset_allocation",
    "get_transaction_history"
]