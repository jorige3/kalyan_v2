"""
Kalyan Prediction System Ensemble Orchestrator v2.1
Scientific Refactor for Production Readiness
"""
import argparse
import sys
from datetime import datetime

# Import internal modules
import config
from src.backtest.rolling_backtester import RollingBacktester
from src.data.loader import DataLoader
from src.models.digit_model import DigitMomentumModel
from src.models.ensemble_model import EnsembleModel
from src.models.gap_model import GapClusterModel
from src.models.heat_model import HeatModel
from src.models.mirror_model import MirrorPairModel
from src.models.momentum_model import MomentumModel
from src.reporting.report_generator import ReportGenerator
from src.reporting.telegram_sender import TelegramSender
from src.utils.logger import setup_logger


def main():
    # Setup Logger
    logger = setup_logger(log_file=config.LOG_FILE)
    logger.info("="*40)
    logger.info("Initializing Kalyan Ensemble Prediction System v2.1")

    # Command Line Arguments
    parser = argparse.ArgumentParser(description="Kalyan Market Scientific Ensemble System")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"), help="Analysis date (YYYY-MM-DD)")
    parser.add_argument("--skip-backtest", action="store_true", default=config.SKIP_BACKTEST, help="Skip backtest")
    parser.add_argument("--skip-telegram", action="store_true", default=config.SKIP_TELEGRAM, help="Skip Telegram")
    parser.add_argument("--force", action="store_true", help="Force run override")
    args = parser.parse_args()

    # 0. Check for Duplicate Run
    if config.CHECK_DUPLICATE_RUN and not args.force:
        report_path = config.REPORTS_DIR / f"kalyan_analysis_{args.date}.pdf"
        if report_path.exists():
            logger.info(f"Report for {args.date} already exists. Skipping run. Use --force to override.")
            return

    # 1. Load Data
    loader = DataLoader(config.DATA_PATH)
    df = loader.load_data()
    logger.info(f"Loaded {len(df)} records.")

    # 2. Initialize Ensemble Model
    sub_models = {
        'heat': HeatModel(),
        'digit': DigitMomentumModel(window=config.DIGIT_WINDOW),
        'gap': GapClusterModel(min_gap=config.GAP_MIN, max_gap=config.GAP_MAX),
        'momentum': MomentumModel(momentum_window=config.MOMENTUM_WINDOW),
        'mirror': MirrorPairModel(window=config.MIRROR_WINDOW)
    }
    
    ensemble_model = EnsembleModel(models=sub_models, weights=config.ENSEMBLE_WEIGHTS)
    logger.info(f"Using Ensemble Model with weights: {config.ENSEMBLE_WEIGHTS}")

    # 3. Rolling Backtest (to get confidence score for the ENSEMBLE)
    metrics = {'hit_rate_top5': 0.0, 'hit_rate_top10': 0.0}
    if not args.skip_backtest:
        logger.info("Running rolling backtest for Ensemble model (last 30 days)...")
        backtester = RollingBacktester(ensemble_model)
        backtest_results = backtester.run(df, max_days=30)
        if backtest_results:
            metrics['hit_rate_top5'] = backtest_results['hit_rate_top5']
            metrics['hit_rate_top10'] = backtest_results['hit_rate_top10']
        else:
            logger.warning("Insufficient data for backtesting.")

    # 4. Generate Predictions for the target date
    analysis_date = datetime.strptime(args.date, "%Y-%m-%d")
    df_for_prediction = df[df['date'] < analysis_date]
    
    if df_for_prediction.empty:
        logger.warning(f"No historical data before {args.date}. Using latest records.")
        df_for_prediction = df
    
    # 4.1 Base Ensemble Predictions
    raw_predictions = ensemble_model.predict(df_for_prediction)
    
    # 4.2 Get Yesterday's Top 10 for Delay Boost
    # Yesterday's top 10 are the predictions made FOR yesterday using data before yesterday
    yesterday_df = df_for_prediction.iloc[:-1] if len(df_for_prediction) > 1 else df_for_prediction
    yesterday_raw_predictions = ensemble_model.predict(yesterday_df)
    yesterday_top10 = [p['value'] for p in yesterday_raw_predictions[:10]]
    
    # 4.3 Get Digit Scores
    digit_scores = sub_models['digit'].get_digit_scores(df_for_prediction)
    
    # 4.4 Apply Smart Ranker
    from src.models.smart_ranker import SmartRanker
    smart_ranker = SmartRanker(weights=config.SMART_RANKER_WEIGHTS)
    
    predictions = smart_ranker.rerank(
        raw_predictions, 
        df_for_prediction, 
        digit_scores, 
        yesterday_top10
    )
    
    logger.info("Generated smart ensemble predictions successfully.")

    # 5. Reporting
    reporter = ReportGenerator(reports_dir=config.REPORTS_DIR, fonts_dir=config.FONTS_DIR)
    reporter.generate_console_report(predictions, metrics)
    reporter.generate_pdf_report(predictions, metrics)

    # 6. Telegram Notification
    if not args.skip_telegram:
        telegram = TelegramSender()
        telegram.send_prediction_update(predictions, metrics)

    logger.info(f"Kalyan Ensemble workflow for {args.date} completed successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)
