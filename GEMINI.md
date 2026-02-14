The project has been transformed into a "strong output" powerhouse as requested.

**Summary of Changes:**

*   **STEP 1: Project Ingestion & Analysis:**
    *   Completed a thorough analysis of the existing codebase, identifying strengths, weaknesses, and key data structures.
    *   Formulated an upgrade plan to enhance modularity, robustness, and output quality.

*   **STEP 2: File Rewrites:**
    *   **`src/engine/kalyan_engine.py`**: Rewritten to handle data loading, preprocessing, and dummy data generation with improved error handling and type consistency (ensuring 'jodi' is always a string).
    *   **`src/analysis/hot_cold.py`**: Rewritten to perform hot/cold digit and jodi analysis, including frequency calculations and identification of due cycles and exhausted numbers.
    *   **`src/analysis/trend_window.py`**: Rewritten to analyze trends and cycles using a sliding window approach, also including due cycle and exhausted number identification.
    *   **`main.py`**: Rewritten to orchestrate the analysis, integrate `KalyanEngine`, `HotColdAnalyzer`, and `TrendWindowAnalyzer`. It now includes:
        *   `argparse` for CLI inputs (`--date`, `--csv`, `--verbose`).
        *   Basic PDF report generation using `fpdf2`, with Unicode font support (`DejaVuSans.ttf` and `DejaVuSansCondensed-Bold.ttf`) to display emojis and special characters.
        *   A placeholder for Monte Carlo simulations to assess prediction confidence.
        *   Improved error handling and logging.
    *   **`config.py`**: Updated with new configuration parameters for analysis.
    *   **`requirements.txt`**: Updated to include `fpdf2` and other necessary dependencies.

*   **STEP 3: Integration & Run Script:**
    *   All dependencies were installed successfully.
    *   The `main.py` script runs without critical errors, producing console output and a PDF report (`reports/kalyan_analysis_YYYY-MM-DD.pdf`).
    *   Dummy data is generated if `data/kalyan.csv` is not found or is malformed.

**Recent Enhancements & Fixes:**

*   **Telegram Notification Integration:**
    *   Telegram notification functionality has been fully integrated into `main.py`, consolidating analysis, reporting, and alerts into a single execution flow.
    *   **HTML Parse Mode Implementation:** Switched Telegram notifications from MarkdownV2 to HTML parse mode to resolve persistent parsing issues, particularly with complex formatting and special characters like parentheses and line breaks.
    *   **Robust HTML Escaping:** Implemented `escape_html_chars` for reliable HTML escaping of message content.
    *   **Circular Import Resolution:** Refactored `generate_daily_summary_and_confidence` into `src/analysis/core_logic.py` to eliminate circular dependencies, ensuring smoother module imports.
    *   **Removed Redundant Script:** `scripts/send_report.py` has been removed as its functionality is now absorbed by `main.py`.
    *   **Logging Refinement:** Adjusted Telegram notifier logging for production readiness.
*   **Manual Prediction Tracking System:**
    *   **Implemented `src/tracking/manual_tracker.py`**: A new module for managing and tracking manual predictions.
    *   **`config/manual_predictions.json`**: Introduced a JSON file for storing user-defined predictions (single digits, jodis) with tracking status (pending, hit, miss).
    *   **Integrated into `main.py`**: `main.py` now loads manual predictions, compares them against actual market results, updates their status, saves the changes, and includes a comprehensive tracking summary in the Telegram notification.
    *   **Robust Comparison Logic**: Implemented value normalization in `manual_tracker.py` to ensure accurate hit/miss detection despite data type variations (e.g., "6" vs "6.0").

**Current Status:**

The system now provides:
*   Robust data loading with dummy data fallback.
*   Modular analysis for hot/cold numbers, due cycles, and exhausted numbers.
*   CLI-driven execution.
*   A PDF report with basic formatting, including Unicode support.
*   Automated Telegram notifications with HTML formatting for enhanced reliability.
*   A comprehensive manual prediction tracking system integrated with analysis and reporting.
*   A placeholder for Monte Carlo simulations.

The project is now in a much stronger state, fulfilling the core requirements of the prompt. I am ready for your next instruction.