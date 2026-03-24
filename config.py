"""
Centralized Configuration for Kalyan Prediction System v2.2 (Decision Engine Upgrade)
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables (from .env if present)
load_dotenv()

# --- Project Paths ---
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "kalyan.csv"
REPORTS_DIR = BASE_DIR / "reports"
FONTS_DIR = BASE_DIR / "fonts"
LOG_FILE = BASE_DIR / "logs" / "app.log"

# Create directories if they don't exist
REPORTS_DIR.mkdir(exist_ok=True)
BASE_DIR.joinpath("logs").mkdir(exist_ok=True)

# --- Model Parameters ---

# 1. Heat Model settings
RECENT_WINDOW = 30
LONG_TERM_WINDOW = 90
HEAT_MODEL_WEIGHTS = {
    'recent_freq': 0.7,
    'absence': 0.2,
    'long_term_freq': 0.1
}

# 2. Digit Momentum Model settings
DIGIT_WINDOW = 30

# 3. Gap Cluster Model settings
GAP_MIN = 25
GAP_MAX = 40

# 4. Mirror Pair Model settings
MIRROR_WINDOW = 15

# 5. Streak Momentum Model settings
MOMENTUM_WINDOW = 7

# --- Ensemble Configuration ---
ENSEMBLE_WEIGHTS = {
    "heat": 0.3,
    "digit": 0.2,
    "gap": 0.3,
    "momentum": 0.1,
    "mirror": 0.1
}
# --- Smart Ranker Configuration ---
SMART_RANKER_WEIGHTS = {
    "base_score": 0.5,
    "recency": 0.2,
    "delay": 0.15,
    "digit_score": 0.1,
    "penalty": -0.2
}

# Top 5 Filter Settings
FILTER_MIN_DIGIT_SCORE = 0.35
FILTER_MAX_ABSENCE = 120
FILTER_MIN_RECENT = 0.01
FILTER_MIN_DELAY = 5

# --- Backtest Configuration ---
BACKTEST_WARMUP = 60 # Min days of data before starting backtest
BACKTEST_TOP_N = [5, 10] # Track hit rate for top 5 and top 10

# --- Telegram Configuration ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- System Settings ---
SKIP_BACKTEST = False
SKIP_TELEGRAM = False
CHECK_DUPLICATE_RUN = True # Prevent running multiple times for same date
