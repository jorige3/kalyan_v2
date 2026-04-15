"""
Kalyan Prediction System Ensemble Orchestrator v2.4-stable
Scientific Refactor for Production Readiness
"""
import argparse
import json
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
from src.models.delay_engine import apply_delay_boost
from src.reporting.report_generator import ReportGenerator
from src.reporting.telegram_sender import TelegramSender
from src.utils.logger import setup_logger


def load_yesterday_top10(logger):
    """Loads the top 10 jodis from the most recent JSON report."""
    try:
        report_files = sorted(config.REPORTS_DIR.glob("kalyan_analysis_*.json"), reverse=True)
        if not report_files:
            return []
        
        # Latest might be today if we already ran, so we might need the one BEFORE latest
        # But usually we run once per day. 
        # Actually, let's just take the most recent one.
        latest_report = report_files[0]
        with open(latest_report, 'r') as f:
            data = json.load(f)
            picks = data.get('ranked_picks', [])
            return [p['value'] for p in picks[:10]]
    except Exception as e:
        logger.warning(f"Could not load yesterday's predictions: {e}")
        return []


def run_weight_comparison(df, sub_models, backtest_days, logger):
    """Runs a dual backtest to compare stable vs experimental weights."""
    logger.info("="*50)
    logger.info("🚀 STARTING WEIGHT COMPARISON MODE")
    logger.info("="*50)

    # 1. Stable Weights
    logger.info(f"Step 1/2: Running backtest with STABLE weights ({config.ENSEMBLE_WEIGHTS})...")
    ensemble_stable = EnsembleModel(models=sub_models, weights=config.ENSEMBLE_WEIGHTS)
    backtester_stable = RollingBacktester(ensemble_stable)
    result_stable = backtester_stable.run(df, max_days=backtest_days)

    # 2. Experimental Weights
    logger.info(f"Step 2/2: Running backtest with EXPERIMENTAL weights ({config.EXPERIMENTAL_WEIGHTS})...")
    ensemble_experimental = EnsembleModel(models=sub_models, weights=config.EXPERIMENTAL_WEIGHTS)
    backtester_experimental = RollingBacktester(ensemble_experimental)
    result_experimental = backtester_experimental.run(df, max_days=backtest_days)

    if not result_stable or not result_experimental:
        logger.error("Weight comparison failed due to insufficient data for backtesting.")
        return

    stable_t10 = result_stable.get('hit_rate_top10', 0)
    stable_t5 = result_stable.get('hit_rate_top5', 0)
    exp_t10 = result_experimental.get('hit_rate_top10', 0)
    exp_t5 = result_experimental.get('hit_rate_top5', 0)

    # 3. Decision Logic
    # IF experimental_top10 > stable_top10 + 0.2% -> ACCEPT
    # ELSE IF experimental_top10 < stable_top10 -> REJECT
    # ELSE -> INCONCLUSIVE
    
    diff = exp_t10 - stable_t10
    if diff > 0.002: # 0.2% threshold
        decision = "✅ ACCEPT"
    elif diff < 0:
        decision = "❌ REJECT"
    else:
        decision = "⚖️ INCONCLUSIVE"

    # 4. Console Output
    print("\n" + "="*50)
    print("⚔️ WEIGHT COMPARISON REPORT")
    print("="*50)
    print(f"\nStable Weights ({config.ENSEMBLE_WEIGHTS}):")
    print(f"Top 10 Hit Rate: {stable_t10*100:.2f}%")
    print(f"Top 5 Hit Rate : {stable_t5*100:.2f}%")
    print(f"\nExperimental Weights ({config.EXPERIMENTAL_WEIGHTS}):")
    print(f"Top 10 Hit Rate: {exp_t10*100:.2f}%")
    print(f"Top 5 Hit Rate : {exp_t5*100:.2f}%")
    print("\n" + "-"*50)
    print(f"Decision for Experimental Weights: {decision}")
    print("-"*50 + "\n")

    # 5. Save results to JSON
    comparison_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "backtest_days": backtest_days,
        "stable": {
            "weights": config.ENSEMBLE_WEIGHTS,
            "top10_hit_rate": stable_t10,
            "top5_hit_rate": stable_t5
        },
        "experimental": {
            "weights": config.EXPERIMENTAL_WEIGHTS,
            "top10_hit_rate": exp_t10,
            "top5_hit_rate": exp_t5
        },
        "hit_rate_diff": diff,
        "decision": decision
    }
    
    report_file = config.REPORTS_DIR / f"weight_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(report_file, 'w') as f:
            json.dump(comparison_data, f, indent=4)
        logger.info(f"Comparison report saved to: {report_file}")
    except Exception as e:
        logger.error(f"Failed to save comparison report to file: {e}")


def main():
    # Setup Logger
    logger = setup_logger(log_file=config.LOG_FILE)
    logger.info("="*40)
    logger.info("Initializing Kalyan Ensemble Prediction System v2.4-stable")

    # Command Line Arguments
    parser = argparse.ArgumentParser(description="Kalyan Market Scientific Ensemble System")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"), help="Analysis date (YYYY-MM-DD)")
    parser.add_argument("--skip-backtest", action="store_true", default=config.SKIP_BACKTEST, help="Skip backtest")
    parser.add_argument("--skip-telegram", action="store_true", default=config.SKIP_TELEGRAM, help="Skip Telegram")
    parser.add_argument("--force", action="store_true", help="Force run override")
    parser.add_argument("--backtest-days", type=int, default=30, help="Number of days for backtesting")
    parser.add_argument("--compare-weights", action="store_true", help="Run dual backtest comparison")
    args = parser.parse_args()

    # 0. Check for Duplicate Run
    if config.CHECK_DUPLICATE_RUN and not args.force and not args.compare_weights:
        report_path = config.REPORTS_DIR / f"kalyan_analysis_{args.date}.pdf"
        if report_path.exists():
            logger.info(f"Report for {args.date} already exists. Skipping run. Use --force to override.")
            return

    # 1. Load Data
    loader = DataLoader(config.DATA_PATH)
    df = loader.load_data()
    logger.info(f"Loaded {len(df)} records.")

    # 2. Select Weights and Initialize Ensemble Model
    if config.USE_EXPERIMENTAL_MODE:
        weights = config.EXPERIMENTAL_WEIGHTS
    else:
        weights = config.ENSEMBLE_WEIGHTS
    
    logger.info(f"Using weights: {weights} (Experimental Mode: {config.USE_EXPERIMENTAL_MODE})")

    sub_models = {
        'heat': HeatModel(),
        'digit': DigitMomentumModel(window=config.DIGIT_WINDOW),
        'gap': GapClusterModel(min_gap=config.GAP_MIN, max_gap=config.GAP_MAX),
        'momentum': MomentumModel(momentum_window=config.MOMENTUM_WINDOW),
        'mirror': MirrorPairModel(window=config.MIRROR_WINDOW)
    }
    
    ensemble_model = EnsembleModel(models=sub_models, weights=weights)

    # 3. Rolling Backtest (to get confidence score for the ENSEMBLE)
    metrics = {
        'hit_rate_top5': 0.0, 'hit_rate_top10': 0.0, 
        'recent_top5': 0.0, 'recent_top10': 0.0,
        'system_confidence': 0.0
    }
    
    if args.compare_weights:
        run_weight_comparison(df, sub_models, args.backtest_days, logger)
        if not args.force: # Don't proceed to prediction unless forced when comparing
            return

    if not args.skip_backtest:
        logger.info(f"Running rolling backtest for Ensemble model (last {args.backtest_days} days)...")
        backtester = RollingBacktester(ensemble_model)
        backtest_results = backtester.run(df, max_days=args.backtest_days)
        if backtest_results:
            metrics.update(backtest_results)
            
            # Calculate System Confidence (0-10 Scale)
            # Base: Top 10 Hit Rate (Target 12% -> 6.0)
            # Bonus: Recent Trend > Overall
            
            base_score = min(10.0, (metrics['hit_rate_top10'] / 0.12) * 6.0)
            consistency_bonus = 0.0
            if metrics['recent_top10'] > metrics['hit_rate_top10']:
                consistency_bonus = 1.0
            elif metrics['recent_top10'] < metrics['hit_rate_top10'] * 0.8:
                consistency_bonus = -1.0
                
            final_conf = max(0.0, min(10.0, base_score + consistency_bonus))
            metrics['system_confidence'] = final_conf
            logger.info(f"System Confidence Score: {final_conf:.1f}/10")
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
    
    # 4.2 Get Recent Top 10s for Multi-Day Delay Boost
    # We look back at predictions made for the last 3 market days
    recent_top10s = []
    for i in range(1, 4):
        if len(df_for_prediction) >= i:
            hist_df = df_for_prediction.iloc[:-i] if i > 0 else df_for_prediction
            if not hist_df.empty:
                hist_raw = ensemble_model.predict(hist_df)
                recent_top10s.append([p['value'] for p in hist_raw[:10]])
    
    # 4.3 Get Digit Scores
    digit_scores = sub_models['digit'].get_digit_scores(df_for_prediction)
    
    # 4.4 Apply Smart Ranker
    from src.models.smart_ranker import SmartRanker
    smart_ranker = SmartRanker(weights=config.SMART_RANKER_WEIGHTS)
    
    predictions = smart_ranker.rerank(
        raw_predictions, 
        df_for_prediction, 
        digit_scores, 
        recent_top10s
    )
    
    # 4.5 Micro Rank Engine v2.4 (Top 10 Reranking)
    top10_candidates = [p['value'] for p in predictions[:10]]
    from src.models.micro_ranker import rerank_top10
    top10_reranked = rerank_top10(top10_candidates, df_for_prediction, digit_scores)
    
    # Re-map top10 objects to reflect new order for Top 5 reporting
    reranked_objs = []
    for val in top10_reranked:
        for p in predictions[:10]:
            if p['value'] == val:
                reranked_objs.append(p)
                break
    
    # Update predictions list (Reranked Top 10 + original remainder)
    predictions = reranked_objs + predictions[10:]
    
    # 4.6 Delay Intelligence Engine v1
    if config.DELAY_ENGINE_ENABLED:
        # Precompute last_seen_map
        all_jodis = [f"{i:02d}" for i in range(100)]
        last_seen_map = {}
        for jodi in all_jodis:
            # Find the last index of this jodi
            idx = df_for_prediction[df_for_prediction['jodi'] == jodi].index
            if not idx.empty:
                days_since = len(df_for_prediction) - 1 - idx[-1]
                last_seen_map[jodi] = days_since
            else:
                last_seen_map[jodi] = 999

        predictions = apply_delay_boost(
            predictions,
            previous_top10=load_yesterday_top10(logger),
            last_seen_map=last_seen_map,
            delay_weights=config.DELAY_WEIGHTS
        )
        logger.info("Generated smart ensemble predictions successfully with Delay Engine v1.")
    else:
        logger.info("Generated smart ensemble predictions successfully with Micro Rank v2.4.")

    # 5. Reporting
    reporter = ReportGenerator(reports_dir=config.REPORTS_DIR, fonts_dir=config.FONTS_DIR)
    reporter.generate_console_report(predictions, metrics)
    reporter.generate_pdf_report(predictions, metrics)
    reporter.generate_json_report(predictions, metrics)

    # 6. Telegram Notification
    if not args.skip_telegram:
        telegram = TelegramSender()
        telegram.send_prediction_update(predictions, metrics)

    # 7. Daily Performance Tracking
    try:
        actual_row = df[df['date'] == analysis_date]
        actual_jodi = str(actual_row.iloc[0]['jodi']).zfill(2) if not actual_row.empty else "Pending"
        
        top5 = [p['value'] for p in predictions[:5]]
        top10 = [p['value'] for p in predictions[:10]]
        
        hit_status = "Miss"
        if actual_jodi != "Pending":
            if actual_jodi in top5:
                hit_status = "Top5_Hit"
            elif actual_jodi in top10:
                hit_status = "Top10_Hit"
        
        delay_hit = "no_delay"
        for i, top10 in enumerate(recent_top10s):
            if actual_jodi in top10:
                delay_hit = f"delay_hit_d{i+1}"
                break
        
        log_line = f"{analysis_date.strftime('%d-%b')} | {top5} | {top10} | {actual_jodi} | {hit_status} | {delay_hit}\n"
        
        with open(config.PERFORMANCE_LOG, "a") as f:
            f.write(log_line)
        logger.info(f"Performance tracked: {hit_status} | {delay_hit}")
    except Exception as e:
        logger.error(f"Failed to track daily performance: {e}")

    logger.info(f"Kalyan Ensemble workflow for {args.date} completed successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)
