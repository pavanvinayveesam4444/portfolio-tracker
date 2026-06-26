"""
Main entry point for Portfolio Tracker.
Demonstrates all features working end to end.
"""

import logging
from services.database import create_tables, get_session, close_session
from services.portfolio_service import (
    create_user,
    get_user,
    create_portfolio,
    get_user_portfolios,
    add_holding,
    sell_holding,
    get_holdings,
    get_portfolio_value,
    get_asset_allocation,
    get_transaction_history
)
from services.stock_service import get_stock_price, get_stock_info

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)-5s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def main():
    """
    Main function — runs the complete portfolio tracker demo.
    Shows all features working end to end.
    """

    print("\n" + "=" * 60)
    print("   PORTFOLIO TRACKER — COMPLETE DEMO")
    print("=" * 60)

    # =============================================
    # STEP 1: Create database tables
    # =============================================
    print("\n📦 STEP 1: Setting up database...")
    create_tables()
    print("✅ All tables created in PostgreSQL")

    # =============================================
    # STEP 2: Create a session
    # =============================================
    session = get_session()
    print("✅ Database session opened")

    try:
        # =============================================
        # STEP 3: Create a user
        # =============================================
        print("\n👤 STEP 2: Creating user...")

        # Check if user already exists
        from services.portfolio_service import get_user_by_username
        existing_user = get_user_by_username(session, "pavan")

        if existing_user:
            user = existing_user
            print(f"✅ User already exists: {user.username}")
        else:
            user = create_user(
                session,
                username="pavan",
                email="pavan@email.com"
            )
            print(f"✅ Created user: {user.username} (id={user.id})")

        # =============================================
        # STEP 4: Create a portfolio
        # =============================================
        print("\n💼 STEP 3: Creating portfolio...")

        portfolios = get_user_portfolios(session, user.id)

        if portfolios:
            portfolio = portfolios[0]
            print(f"✅ Portfolio already exists: {portfolio.name}")
        else:
            portfolio = create_portfolio(
                session,
                user_id=user.id,
                name="Tech Stocks",
                description="My technology stock portfolio"
            )
            print(f"✅ Created portfolio: {portfolio.name} (id={portfolio.id})")

        # =============================================
        # STEP 5: Buy some stocks
        # =============================================
        print("\n📈 STEP 4: Buying stocks...")

        holdings = get_holdings(session, portfolio.id)
        existing_tickers = [h.ticker for h in holdings]

        if "AAPL" not in existing_tickers:
            aapl = add_holding(
                session,
                portfolio_id=portfolio.id,
                ticker="AAPL",
                shares=10.0,
                purchase_price=180.50
            )
            print(f"✅ Bought AAPL: {aapl.shares} shares at ${aapl.average_price}")
        else:
            print("✅ AAPL already in portfolio")

        if "TSLA" not in existing_tickers:
            tsla = add_holding(
                session,
                portfolio_id=portfolio.id,
                ticker="TSLA",
                shares=5.0,
                purchase_price=250.00
            )
            print(f"✅ Bought TSLA: {tsla.shares} shares at ${tsla.average_price}")
        else:
            print("✅ TSLA already in portfolio")

        if "JPM" not in existing_tickers:
            jpm = add_holding(
                session,
                portfolio_id=portfolio.id,
                ticker="JPM",
                shares=20.0,
                purchase_price=145.00
            )
            print(f"✅ Bought JPM: {jpm.shares} shares at ${jpm.average_price}")
        else:
            print("✅ JPM already in portfolio")

        # =============================================
        # STEP 6: Get current stock prices
        # =============================================
        print("\n💰 STEP 5: Fetching current stock prices...")

        for ticker in ["AAPL", "TSLA", "JPM"]:
            price = get_stock_price(ticker)
            if price:
                print(f"✅ {ticker}: ${price:.2f}")
            else:
                print(f"❌ Could not fetch {ticker} price")

        # =============================================
        # STEP 7: Get portfolio value
        # =============================================
        print("\n📊 STEP 6: Calculating portfolio value...")

        portfolio_value = get_portfolio_value(session, portfolio.id)

        print(f"\n{'─' * 50}")
        print(f"  PORTFOLIO PERFORMANCE REPORT")
        print(f"{'─' * 50}")
        print(f"  Total Value:    ${portfolio_value['total_value']:,.2f}")
        print(f"  Total Cost:     ${portfolio_value['total_cost']:,.2f}")
        print(f"  Profit/Loss:    ${portfolio_value['profit_loss']:,.2f}")
        print(f"  Return:         {portfolio_value['profit_loss_pct']:.2f}%")
        print(f"{'─' * 50}")

        print(f"\n  HOLDINGS BREAKDOWN:")
        for h in portfolio_value["holdings_breakdown"]:
            print(f"\n  {h['ticker']}:")
            print(f"    Shares:         {h['shares']}")
            print(f"    Avg Buy Price:  ${h['average_price']:.2f}")
            print(f"    Current Price:  ${h['current_price']:.2f}")
            print(f"    Current Value:  ${h['current_value']:,.2f}")
            print(f"    Profit/Loss:    ${h['profit_loss']:,.2f} ({h['profit_loss_pct']:.2f}%)")

        # =============================================
        # STEP 8: Get asset allocation
        # =============================================
        print(f"\n{'─' * 50}")
        print(f"  ASSET ALLOCATION")
        print(f"{'─' * 50}")

        allocation = get_asset_allocation(session, portfolio.id)
        for item in allocation:
            bar = "█" * int(item["percentage"] / 2)
            print(f"  {item['ticker']:6} {bar} {item['percentage']:.1f}%")

        # =============================================
        # STEP 9: Sell some shares
        # =============================================
        print(f"\n📉 STEP 7: Selling 2 AAPL shares...")

        holdings = get_holdings(session, portfolio.id)
        aapl_holding = next(
            (h for h in holdings if h.ticker == "AAPL"), None
        )

        if aapl_holding and aapl_holding.shares >= 2:
            sell_holding(
                session,
                holding_id=aapl_holding.id,
                shares=2.0,
                sell_price=195.00
            )
            print(f"✅ Sold 2 AAPL shares at $195.00")
            print(f"   Remaining AAPL shares: {aapl_holding.shares}")

        # =============================================
        # STEP 10: Show transaction history
        # =============================================
        print(f"\n📋 STEP 8: Transaction history for AAPL...")

        holdings = get_holdings(session, portfolio.id)
        aapl_holding = next(
            (h for h in holdings if h.ticker == "AAPL"), None
        )

        if aapl_holding:
            transactions = get_transaction_history(
                session, aapl_holding.id
            )
            print(f"\n  AAPL TRANSACTION HISTORY:")
            print(f"  {'Type':<6} {'Shares':<8} {'Price':<10} {'Total':<12} {'Date'}")
            print(f"  {'─'*55}")
            for t in transactions:
                print(
                    f"  {t.transaction_type:<6} "
                    f"{t.shares:<8.1f} "
                    f"${t.price:<9.2f} "
                    f"${t.total_value:<11.2f} "
                    f"{t.transaction_date.strftime('%Y-%m-%d %H:%M')}"
                )

        # =============================================
        # STEP 11: Get detailed stock info
        # =============================================
        print(f"\n🔍 STEP 9: Getting Apple stock details...")

        info = get_stock_info("AAPL")
        if info:
            print(f"\n  APPLE INC. STOCK INFO:")
            print(f"  Company:      {info['name']}")
            print(f"  Sector:       {info['sector']}")
            print(f"  Price:        ${info['current_price']:.2f}")
            print(f"  Market Cap:   ${info['market_cap']:,.0f}")
            print(f"  P/E Ratio:    {info['pe_ratio']:.2f}")
            print(f"  52W High:     ${info['52_week_high']:.2f}")
            print(f"  52W Low:      ${info['52_week_low']:.2f}")

        print("\n" + "=" * 60)
        print("   DEMO COMPLETE — ALL FEATURES WORKING!")
        print("=" * 60 + "\n")

    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

    finally:
        close_session(session)
        print("✅ Database session closed")


if __name__ == "__main__":
    main()