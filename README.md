# Portfolio Tracker with Database Backend

A Python application that tracks stock portfolios
using PostgreSQL, SQLAlchemy ORM, and Redis caching.

## What It Does

- Stores users, portfolios, holdings and transactions
  in PostgreSQL using SQLAlchemy ORM
- Caches stock prices in Redis for 5 minutes
- Fetches real-time stock prices from Yahoo Finance
- Calculates portfolio value, profit/loss, asset allocation
- Records complete buy/sell transaction history

## Tech Stack

- PostgreSQL — production database
- SQLAlchemy ORM — Python to database bridge
- Redis — caching layer (5 minute TTL)
- yfinance — Yahoo Finance API
- pytest — testing

## Project Structure

portfolio-tracker/
├── main.py                    → entry point
├── config.py                  → settings
├── models/
│   ├── user.py                → User table
│   ├── portfolio.py           → Portfolio table
│   ├── holding.py             → Holding table
│   └── transaction.py         → Transaction table
├── services/
│   ├── database.py            → PostgreSQL connection
│   ├── cache.py               → Redis operations
│   ├── stock_service.py       → fetch stock prices
│   └── portfolio_service.py   → CRUD + calculations
└── tests/
    ├── test_models.py         → model tests
    └── test_services.py       → service tests

## How To Run

Install dependencies:
pip install -r requirements.txt

Start services:
brew services start postgresql@15
brew services start redis

Run the app:
python main.py

Run tests:
pytest tests/ -v

## Skills Demonstrated

- PostgreSQL database design
- SQLAlchemy ORM (models, relationships, CRUD)
- Redis caching patterns
- REST API integration (Yahoo Finance)
- Python engineering (error handling, logging)
- Unit testing with pytest
- Git version control
