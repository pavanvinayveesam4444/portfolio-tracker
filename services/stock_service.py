"""
Stock service.
Fetches stock prices from Yahoo Finance.
Checks Redis cache first before hitting the API.
"""

import yfinance as yf
import logging
from services.cache import set_cache, get_cache

logger = logging.getLogger(__name__)

# Cache key pattern
PRICE_CACHE_KEY = "stock_price:{ticker}"
INFO_CACHE_KEY = "stock_info:{ticker}"


def get_stock_price(ticker: str) -> float | None:
    """
    Get current stock price.
    Checks Redis cache first.
    If not cached → fetches from Yahoo Finance.
    Caches result for 5 minutes.

    Args:
        ticker: stock symbol like "AAPL", "TSLA"

    Returns:
        current price as float
        None if failed
    """

    cache_key = PRICE_CACHE_KEY.format(ticker=ticker)

    # Step 1: Check Redis cache first
    cached = get_cache(cache_key)
    if cached:
        logger.info(f"Cache HIT: {ticker} price = ${cached['price']}")
        return cached["price"]

    # Step 2: Not in cache → fetch from Yahoo Finance
    try:
        logger.info(f"Cache MISS: fetching {ticker} from Yahoo Finance...")
        stock = yf.Ticker(ticker)
        price = stock.fast_info["lastPrice"]

        if price is None:
            logger.error(f"Could not get price for {ticker}")
            return None

        # Step 3: Store in Redis for 5 minutes
        set_cache(cache_key, {"price": price, "ticker": ticker})
        logger.info(f"Fetched and cached: {ticker} = ${price:.2f}")
        return price

    except Exception as e:
        logger.error(f"Failed to fetch price for {ticker}: {e}")
        return None


def get_stock_info(ticker: str) -> dict | None:
    """
    Get detailed stock information.
    Company name, sector, market cap etc.
    Cached for 5 minutes.

    Args:
        ticker: stock symbol like "AAPL"

    Returns:
        dictionary with stock information
        None if failed
    """

    cache_key = INFO_CACHE_KEY.format(ticker=ticker)

    # Check cache first
    cached = get_cache(cache_key)
    if cached:
        logger.info(f"Cache HIT: {ticker} info")
        return cached

    # Fetch from Yahoo Finance
    try:
        logger.info(f"Fetching {ticker} info from Yahoo Finance...")
        stock = yf.Ticker(ticker)
        info = stock.info

        stock_info = {
            "ticker": ticker,
            "name": info.get("longName", ticker),
            "sector": info.get("sector", "Unknown"),
            "current_price": info.get("currentPrice", 0),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", 0),
            "52_week_high": info.get("fiftyTwoWeekHigh", 0),
            "52_week_low": info.get("fiftyTwoWeekLow", 0),
        }

        # Cache for 5 minutes
        set_cache(cache_key, stock_info)
        logger.info(f"Fetched and cached info for {ticker}")
        return stock_info

    except Exception as e:
        logger.error(f"Failed to fetch info for {ticker}: {e}")
        return None


def get_multiple_prices(tickers: list[str]) -> dict[str, float]:
    """
    Get current prices for multiple stocks.
    Checks cache for each stock individually.

    Args:
        tickers: list of stock symbols
                 ["AAPL", "TSLA", "JPM"]

    Returns:
        dictionary of ticker → price
        {"AAPL": 180.50, "TSLA": 250.00}
    """

    prices = {}

    for ticker in tickers:
        price = get_stock_price(ticker)
        if price is not None:
            prices[ticker] = price
        else:
            logger.warning(f"Could not get price for {ticker}")

    logger.info(f"Fetched prices for {len(prices)}/{len(tickers)} stocks")
    return prices