import os
import re
import json
import glob
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path

from src.engine.kalyan_engine import KalyanEngine
from src.analysis.backtester import Backtester
from src.telegram_notifier import send_telegram_message, escape_markdown_v2_chars
from src.ux.text_templates import ReportText

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BASE_DIR = Path(__file__).resolve().parent.parent # Adjust to project root
REPORTS_DIR = BASE_DIR / "reports"
DATA_DIR = BASE_DIR / "data"

def send_daily_report():
    try:
        # 1. Load latest analysis snapshot from main.py
        latest_report_json = None
        json_files = sorted(REPORTS_DIR.glob("kalyan_analysis_*.json"), key=os.path.getmtime, reverse=True)
        
        if json_files:
            latest_report_json = json_files[0]
            logging.info(f"Using latest analysis snapshot: {latest_report_json}")
            with open(latest_report_json, 'r') as f:
                snapshot = json.load(f)
            
            summary = snapshot.get("daily_summary", {})
            ranked_picks = snapshot.get("ranked_picks", [])

            market_mood = summary.get("market_mood", "N/A")
            analytical_confidence_score = summary.get("analytical_confidence_score", "N/A")
            
        else:
            logging.warning("No analysis snapshot JSON found. Cannot generate detailed report.")
            return

        # 2. Get hit rate from backtester
        hit_rate = 0.0
        try:
            engine = KalyanEngine(DATA_DIR / "kalyan.csv")
            df_historical = engine.get_historical_data()
            
            # Instantiate Backtester to access its warmup attribute
            backtester_instance = Backtester(df_historical)

            if not df_historical.empty and len(df_historical) > backtester_instance.warmup:
                backtest_results = backtester_instance.run()
                if not backtest_results.empty:
                    # Assuming we are interested in top5_hit for overall hit rate
                    hit_rate = backtest_results['top5_hit'].mean() * 100
                    logging.info(f"Calculated hit rate: {hit_rate:.2f}%")
                else:
                    logging.warning("Backtester returned empty results.")
            else:
                logging.warning("Not enough historical data for backtesting or DataFrame is empty.")
        except Exception as e:
            logging.error(f"Error calculating backtest hit rate: {e}")

        # 3. Get latest actual result from kalyan.csv
        latest_actual_jodi = "N/A"
        try:
            with open(DATA_DIR / "kalyan.csv", 'r') as f:
                lines = f.readlines()
                if len(lines) > 1: # Skip header
                    last_line = lines[-1].strip()
                    # Assuming CSV format where Jodi is in the 'jodi' column
                    # This is a bit fragile, better to use pandas for reading
                    df_current_data = pd.read_csv(DATA_DIR / "kalyan.csv")
                    if not df_current_data.empty:
                        latest_actual_jodi = str(df_current_data['jodi'].iloc[-1])
        except FileNotFoundError:
            logging.warning(f"Data file {DATA_DIR / 'kalyan.csv'} not found.")
        except Exception as e:
            logging.error(f"Error reading latest actual Jodi: {e}")

        # 4. Construct Telegram message
        telegram_message_parts = [
            f"*{escape_markdown_v2_chars(ReportText.CONSOLE_HEADER_TITLE)}* \\- {datetime.now().strftime('%d\\-%b\\-%Y')}",
            f"Market Mood: `{escape_markdown_v2_chars(market_mood)}`",
            f"Analytical Confidence: `{analytical_confidence_score}/10`",
            f"Overall Backtest Hit Rate (Top 5): `{hit_rate:.2f}\\%`",
            f"Latest Result (Jodi): `{escape_markdown_v2_chars(latest_actual_jodi)}`",
            "", # Empty line for spacing
            "*Top Analytical Picks:*"
        ]

        if ranked_picks:
            for p in ranked_picks[:5]: # Limit to top 5 picks
                value = escape_markdown_v2_chars(str(p.get('value', 'N/A')))
                confidence = escape_markdown_v2_chars(p.get('confidence', 'N/A'))
                telegram_message_parts.append(f"• `{value}` \\({confidence}\\)")
                reasons = p.get("reasons", [])
                if reasons:
                    for r in reasons:
                        escaped_reason = escape_markdown_v2_chars(r)
                        telegram_message_parts.append(f"  \\- _{escaped_reason}_")
        else:
            telegram_message_parts.append("No top picks available.")

        # 5. Send via Telegram
        full_message = "\n\n".join(telegram_message_parts)
        send_telegram_message(full_message)

    except Exception as e:
        logging.error(f"❌ Error in send_daily_report: {e}")

if __name__ == "__main__":
    send_daily_report()
