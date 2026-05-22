"""
Configuration settings for Portfolio Tracker.
Reads settings from .env file.
"""

import os
from dotenv import load_dotenv

# Load settings from .env file
load_dotenv()

# Database settings
DATABASE_URL = os.getenv("DATABASE_URL", 
               "postgresql://localhost:5432/portfolio_tracker")

# Redis settings
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_TTL = int(os.getenv("REDIS_TTL", 300))