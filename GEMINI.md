# Kalyan Prediction System - Scientific Refactor (v2.0)

The project has been fully refactored into a modular, scientifically robust, and production-ready system as per the user's latest requirements.

**Refactor Summary:**

*   **Modular Architecture:**
    *   Separated concerns into a strict directory structure: `data`, `models`, `analytics`, `backtest`, `reporting`, and `utils`.
    *   Simplified the codebase by removing redundant and experimental models (Gap, Mirror, DigitMomentum, Ensemble).
    *   Implemented a clean `DataLoader` with automatic dummy data generation and column normalization.

*   **Scientific Prediction Engines:**
    *   **`HeatModel` Implementation:** Strictly follows the weighted formula: `(recent_frequency * 0.7) + (absence_score * 0.2) + (long_term_frequency * 0.1)`.
    *   **`MomentumModel` Implementation:** Focuses on short-term streaks and recent repeat cycles.
    *   Both models are interchangeable and share a consistent `predict()` interface.

*   **Robust Backtesting:**
    *   Implemented a `RollingBacktester` that evaluates models against historical data without data leakage.
    *   Calculates Top 5 and Top 10 hit rates used as the primary "Confidence Score" for the day's picks.

*   **Lean Orchestration (`main.py`):**
    *   `main.py` acts as a pure orchestrator managing the workflow: Data Loading -> Model Selection -> Backtesting -> Prediction -> Reporting -> Notification.
    *   Added a **Duplicate Execution Check** to prevent multiple runs for the same date (skips if PDF report already exists).
    *   Centralized all parameters in `config.py`.

*   **Production Delivery:**
    *   **Console Reports:** Clean summaries with Top 5, Top 10, and hit-rate derived confidence.
    *   **PDF Reports:** Professional Unicode PDFs with detailed score breakdowns.
    *   **Telegram Integration:** HTML notifications for automated delivery.

**New Directory Structure:**

```
project_root/
├── main.py             # Pure Orchestrator
├── config.py           # Centralized Configuration (v2.0)
├── src/
│   ├── data/           # loader.py (Robust loading)
│   ├── models/         # heat_model.py, momentum_model.py
│   ├── analytics/      # digit_analysis.py, trend_analysis.py (v2.0)
│   ├── backtest/       # rolling_backtester.py (No data leakage)
│   ├── reporting/      # report_generator.py, telegram_sender.py
│   └── utils/          # logger.py
├── data/               # kalyan.csv (Historical Data)
├── fonts/              # Unicode Fonts
├── logs/               # Application Logs
└── reports/            # Daily Generated Reports
```

**Status:** The refactor is complete, verified, and production-ready.
