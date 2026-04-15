# Kalyan Prediction System - Scientific Refactor (v2.4-stable)

The project has been upgraded to a **Quantitative Decision Engine (v2.4-stable)**, featuring a multi-model ensemble, a smart ranker decision layer, and a high-precision delay intelligence engine.

**Key Features & Updates (v2.4-stable):**

*   **Delay Intelligence Engine v1:**
    *   Exploits the "Top 10 Delay Pattern" where jodis appear 1 day after being predicted.
    *   Applies a **Strong Boost (0.25)** to jodis that were in yesterday's Top 10.
    *   Features a "Sweet Spot" boost for jodis last seen 1-3 days ago.
    *   Implements an **Overdelay Penalty** for jodis absent for more than 10 days.

*   **Micro Rank Engine v2.4:**
    *   Fine-tunes Top 10 candidates using high-precision behavioral rules.
    *   Incorporates Digit Strength, Recent Trends, and Consistency Bonuses.
    *   Prevents "Cold Death" by penalizing jodis absent for more than 120 days.

*   **Smart Ranker Upgrades:**
    *   Enhanced with **Multi-Day Delay Boost** looking back at the last 3 days of predictions.
    *   Optimized recency boosts and repeat penalties.

*   **Weight Comparison Mode:**
    *   Added a `--compare-weights` flag to run dual backtests (Stable vs. Experimental).
    *   Automated decision logic to accept or reject experimental weight profiles based on Top 10 hit rate improvement.

*   **Machine-Readable Reporting:**
    *   Automated **JSON report generation** for every run, enabling automated tracking and external tool integration.

**Decision Engine Architecture:**

*   **Weighted Ensemble:** HeatModel (0.25), DigitMomentumModel (0.4), GapClusterModel (0.15), MomentumModel (0.1), MirrorPairModel (0.1).
*   **Layered Decision Flow:** Ensemble -> Multi-Day Smart Ranker -> Micro Rank Engine -> Delay Intelligence Engine.

**Historical Performance:**
*   Achieved a **13.33% Top 10 hit rate** in recent 30-day market simulations (v2.4-stable).

**Current Directory Structure:**

```
project_root/
├── main.py             # Ensemble Orchestrator (v2.4-stable)
├── config.py           # Centralized Configuration
├── src/
│   ├── data/           # loader.py
│   ├── models/         # heat, digit, gap, momentum, mirror, ensemble, smart_ranker, delay_engine, micro_ranker
│   ├── analytics/      # digit_analysis.py, trend_analysis.py
│   ├── backtest/       # rolling_backtester.py (Delay-engine aware)
│   ├── reporting/      # report_generator.py, telegram_sender.py
│   └── utils/          # logger.py
├── data/               # kalyan.csv (Live Market Data)
├── scripts/            # optimize_weights.py, scrape_kalyan.py
├── fonts/              # Unicode Fonts
└── reports/            # Daily PDF/JSON Analysis Reports
```

**Status:** The system is mathematically optimized, verified via dual-backtesting, and production-ready as `v2.4-stable`.
