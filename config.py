# Configuration for analysis
CYCLE_GAP_MAX_DAYS = 7 # Days a number hasn't appeared to be considered 'due'
DUE_THRESHOLD = 30 # Lookback days for due cycles
DUE_TOP_N = 5 # Not directly used in current due cycle logic, but kept for future expansion

HOT_LOOKBACK_DAYS = 30 # Days to look back for hot numbers
HOT_TOP_N = 3 # Top N hot digits/jodis

EXHAUSTED_LOOKBACK_DAYS = 30 # Days to look back for exhausted numbers
EXHAUSTED_GAP_THRESHOLD = 3 # Number of consecutive hits to consider exhausted (e.g., 3+ hits)
EXHAUSTED_BOTTOM_N = 3 # Not directly used in current exhausted logic, but kept for future expansion

TOP_PICKS_COUNT = 3 # Number of top picks to generate

# Monte Carlo Simulation
MONTE_CARLO_SIMULATIONS = 1000

# --- Scoring Weights ---
# Weights for different analytical signals to calculate confidence scores.
# Higher values give more importance to that signal.
SCORING_WEIGHTS = {
    "HIGH_FREQUENCY_JODI": 1.5,          # From HotColdAnalyzer
    "TREND_ALIGNED_JODI": 1.5,           # From TrendWindowAnalyzer
    "EXTENDED_ABSENCE_JODI": 0.75,       # From HotColdAnalyzer (due_cycles)
    
    "HIGH_FREQUENCY_OPEN_SANGAM": 1.2,
    "HIGH_FREQUENCY_CLOSE_SANGAM": 1.2,
    "EXTENDED_ABSENCE_OPEN_SANGAM": 0.6,
    "EXTENDED_ABSENCE_CLOSE_SANGAM": 0.6,
    
    "EXHAUSTED_PATTERN_PENALTY": -2.5    # Penalty for being in the exhausted list
}

# --- Confidence Thresholds ---
# Score thresholds for classifying a pick's confidence level.
CONFIDENCE_THRESHOLDS = {
    "HIGH": 2.5,
    "MEDIUM": 1.0,
}

# --- Manual Predictions Configuration ---
MANUAL_PREDICTIONS_CONFIG = {
    "FILE_PATH": "config/manual_predictions.json"
}