"""
Kalyan Prediction System Orchestrator v2.0
Scientific Refactor for Production Readiness
"""
import sys
import argparse
from datetime import datetime
from pathlib import Path
from src.utils.logger import setup_logger

# Import internal modules
import config
from src.data.loader import DataLoader
from src.models.heat_model import HeatModel
from src.models.momentum_model import MomentumModel
from src.backtest.rolling_backtester import RollingBacktester
from src.reporting.report_generator import ReportGenerator
from src.reporting.telegram_sender import TelegramSender

def main():
    # Setup Logger
    logger = setup_logger(log_file=config.LOG_FILE)
    logger.info("="*40)
    logger.info("Initializing Kalyan Prediction System v2.0")

    # Command Line Arguments
    parser = argparse.ArgumentParser(description="Kalyan Market Scientific Prediction System")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"), help="Analysis date (YYYY-MM-DD)")
    parser.add_argument("--model", choices=['heat', 'momentum'], default='heat', help="Prediction model to use")
    parser.add_argument("--skip-backtest", action="store_true", default=config.SKIP_BACKTEST, help="Skip the backtest phase")
    parser.add_argument("--skip-telegram", action="store_true", default=config.SKIP_TELEGRAM, help="Skip Telegram notification")
    parser.add_argument("--force", action="store_true", help="Force run even if report already exists")
    args = parser.parse_args()

    # 0. Check for Duplicate Run (Point 5 in requirements)
    if config.CHECK_DUPLICATE_RUN and not args.force:
        report_path = config.REPORTS_DIR / f"kalyan_analysis_{args.date}.pdf"
        if report_path.exists():
            logger.info(f"Report for {args.date} already exists. Skipping run. Use --force to override.")
            return

    # 1. Load Data
    loader = DataLoader(config.DATA_PATH)
    df = loader.load_data()
    logger.info(f"Loaded {len(df)} records from {config.DATA_PATH}")

    # 2. Initialize Selected Model (Point 7 in requirements)
    if args.model == 'heat':
        model = HeatModel()
    else:
        model = MomentumModel()
    logger.info(f"Using prediction model: {model.__class__.__name__}")

    # 3. Rolling Backtest (Point 3 & 4 in requirements)
    # Calculate historical confidence from the SAME model code
    metrics = {'hit_rate_top5': 0.0, 'hit_rate_top10': 0.0}
    if not args.skip_backtest:
        logger.info(f"Running rolling backtest for {model.__class__.__name__}...")
        backtester = RollingBacktester(model)
        backtest_results = backtester.run(df)
        if backtest_results:
            metrics['hit_rate_top5'] = backtest_results['hit_rate_top5']
            metrics['hit_rate_top10'] = backtest_results['hit_rate_top10']
        else:
            logger.warning("Insufficient data for backtesting.")

    # 4. Generate Predictions for the target date (Point 1 in requirements)
    analysis_date = datetime.strptime(args.date, "%Y-%m-%d")
    # Only use data strictly BEFORE the analysis date to prevent leakage
    df_for_prediction = df[df['date'] < analysis_date]
    
    if df_for_prediction.empty:
        logger.warning(f"No historical data before {args.date}. Using latest available records.")
        df_for_prediction = df
    
    predictions = model.predict(df_for_prediction)
    logger.info("Generated predictions successfully.")

    # 5. Reporting (Point 7 & 9 in requirements)
    reporter = ReportGenerator(reports_dir=config.REPORTS_DIR, fonts_dir=config.FONTS_DIR)
    reporter.generate_console_report(predictions, metrics)
    pdf_path = reporter.generate_pdf_report(predictions, metrics)

    # 6. Telegram Notification
    if not args.skip_telegram:
        telegram = TelegramSender()
        telegram.send_prediction_update(predictions, metrics)

    logger.info(f"Kalyan prediction workflow for {args.date} completed successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)
