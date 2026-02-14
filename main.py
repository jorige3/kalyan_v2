import argparse
import logging
import os
import json
import hashlib
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List

from fpdf import FPDF, XPos, YPos
from dotenv import load_dotenv # Import load_dotenv

import config
from src.engine.kalyan_engine import KalyanEngine
from src.analysis.hot_cold import HotColdAnalyzer
from src.analysis.trend_window import TrendWindowAnalyzer
from src.analysis.sangam_analysis import SangamAnalyzer
from src.analysis.explainability import explain_pick
from src.ux.text_templates import ReportText
from src.telegram_notifier import send_telegram_message, escape_html_chars # Import Telegram notifier and escape utility
from src.analysis.backtester import Backtester # Import Backtester
from src.analysis.core_logic import generate_daily_summary_and_confidence # Import generate_daily_summary_and_confidence
from src.tracking.manual_tracker import load_manual_predictions, save_manual_predictions, track_hits, get_tracking_summary # Import manual tracking functions

# Load environment variables from .env file
load_dotenv()

# -------------------------------------------------------------------
# Paths & Logging
# -------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO, # Reset to INFO
    format="%(asctime)s - %(levelname)s - %(message)s",
    force=True # Ensure reconfiguration
)

# -------------------------------------------------------------------
# Utilities
# -------------------------------------------------------------------

def format_list(items, limit=15):
    if not items:
        return "N/A"
    items = list(map(str, items))
    if len(items) > limit:
        return ", ".join(items[:limit]) + f" ... (+{len(items)-limit} more)"
    return ", ".join(items)


def hash_file(path: str) -> str:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
    except FileNotFoundError:
        return "FILE_NOT_FOUND"
    return h.hexdigest()


def write_analysis_snapshot(
    output_path: Path,
    analysis_date: datetime,
    summary: Dict,
    ranked_picks: List[Dict],
    df_record_count: int,
    csv_path: Path,
):
    snapshot = {
        "analysis_date": analysis_date.strftime("%Y-%m-%d"),
        "engine_version": ReportText.VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data": {
            "source_file": str(csv_path),
            "record_count": df_record_count,
            "sha256": hash_file(str(csv_path)),
        },
        "daily_summary": summary,
        "ranked_picks": ranked_picks,
    }

    with open(output_path, "w") as f:
        json.dump(snapshot, f, indent=2)

    logging.info(f"📊 Analysis snapshot saved to {output_path}")

# -------------------------------------------------------------------
# PDF Report
# -------------------------------------------------------------------

class PDFReport(FPDF):
    def __init__(self):
        super().__init__()
        fonts = BASE_DIR / "fonts"
        self.add_font("DejaVu", "", str(fonts / "DejaVuSans.ttf"))
        self.add_font("DejaVu", "B", str(fonts / "DejaVuSansCondensed-Bold.ttf"))
        self.set_font("DejaVu", "", 12)

    def header(self):
        self.set_font("DejaVu", "B", 14)
        title = f"{ReportText.PDF_HEADER_TITLE} - {datetime.now().strftime(ReportText.DATE_FORMAT)}"
        self.cell(0, 10, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def chapter_title(self, title):
        self.set_font("DejaVu", "B", 12)
        self.cell(0, 8, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def summary_body(self, body: str):
        self.set_font("DejaVu", "", 10)
        parts = body.split("**")
        for i, part in enumerate(parts):
            if i % 2:
                self.set_font("DejaVu", "B", 10)
                self.write(5, part)
                self.set_font("DejaVu", "", 10)
            else:
                self.write(5, part)
        self.ln(8)

    def add_picks_table(self, picks):
        self.chapter_title("Top 5 Analytical Picks")

        widths = [20, 30, 20, 110]
        headers = ["Pick", "Confidence", "Score", "Explanation"]

        self.set_font("DejaVu", "B", 10)
        for h, w in zip(headers, widths):
            self.cell(w, 7, h, 1, align="C")
        self.ln()

        self.set_font("DejaVu", "", 9)
        for p in picks:
            reasons = " • ".join(p.get("reasons", []))
            self.cell(widths[0], 7, str(p["value"]), 1)
            self.cell(widths[1], 7, p["confidence"], 1)
            self.cell(widths[2], 7, f'{p["score"]:.2f}', 1)
            self.multi_cell(widths[3], 7, reasons, 1)



# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=ReportText.PROJECT_TITLE)
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--csv", default="data/kalyan.csv")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    analysis_date = datetime.strptime(args.date, "%Y-%m-%d")
    logging.info(f"Starting Kalyan analysis for {analysis_date.date()}")

    engine = KalyanEngine(args.csv)
    df = engine.get_historical_data()

    if df.empty:
        logging.error("No data available.")
        return

    analysis_results = {
        "hot_digits": HotColdAnalyzer(df).get_hot_digits(),
        "hot_jodis": HotColdAnalyzer(df).get_hot_jodis(),
        "due_jodis": HotColdAnalyzer(df).get_due_cycles()["due_jodis"],
        "exhausted_jodis": HotColdAnalyzer(df).get_exhausted_numbers()["exhausted_jodis"],
        "trend_due_jodis": TrendWindowAnalyzer(df).get_due_cycles_by_last_appearance()["due_jodis"],
        "hot_open_sangams": SangamAnalyzer(df).get_hot_sangams()["hot_open_sangams"],
        "hot_close_sangams": SangamAnalyzer(df).get_hot_sangams()["hot_close_sangams"],
        "due_open_sangams": SangamAnalyzer(df).get_due_sangams()["due_open_sangams"],
        "due_close_sangams": SangamAnalyzer(df).get_due_sangams()["due_close_sangams"],
    }

    summary = generate_daily_summary_and_confidence(analysis_results)

    json_path = REPORTS_DIR / f"kalyan_analysis_{analysis_date:%Y-%m-%d}.json"
    write_analysis_snapshot(
        json_path,
        analysis_date,
        summary,
        summary["top_picks_with_confidence"],
        len(df),
        Path(args.csv)
    )

    console_output_parts = [
        "=" * 60,
        f"{ReportText.CONSOLE_HEADER_TITLE} | {analysis_date:%d-%b-%Y}",
        "=" * 60,
        f"Market Mood           : {summary['market_mood']}",
        f"Analytical Confidence : {summary['analytical_confidence_score']}/10",
        "-" * 60
    ]

    for p in summary["top_picks_with_confidence"]:
        console_output_parts.append(f"{p['value']} ({p['confidence']})")
        for r in p["reasons"]:
            console_output_parts.append(f"  • {r}")
        console_output_parts.append("") # Add an empty line for spacing
    
    print("\n".join(console_output_parts))


    pdf_path = REPORTS_DIR / f"kalyan_analysis_{analysis_date:%Y-%m-%d}.pdf"
    if not pdf_path.exists():
        pdf = PDFReport()
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.summary_body(
            f"**Market Mood:** {summary['market_mood']}\n"
            f"**Confidence:** {summary['analytical_confidence_score']}/10"
        )
        pdf.add_picks_table(summary["top_picks_with_confidence"])
        pdf.output(pdf_path)
        logging.info(f"📄 PDF saved to {pdf_path}")

    # --- Telegram Notification ---
    hit_rate = 0.0
    try:
        backtester_instance = Backtester(df)

        if not df.empty and len(df) > backtester_instance.warmup:
            backtest_results = backtester_instance.run()
            if not backtest_results.empty:
                hit_rate = backtest_results['top5_hit'].mean() * 100
                logging.info(f"Calculated hit rate for Telegram: {hit_rate:.2f}%")
            else:
                logging.warning("Backtester returned empty results for Telegram.")
        else:
            logging.warning("Not enough historical data for backtesting for Telegram.")
    except Exception as e:
        logging.error(f"Error calculating backtest hit rate for Telegram: {e}")

    latest_actual_jodi = "N/A"
    try:
        df_current_data = pd.read_csv(Path(args.csv))
        if not df_current_data.empty:
            latest_actual_jodi = str(df_current_data['jodi'].iloc[-1])
    except FileNotFoundError:
        logging.warning(f"Data file {Path(args.csv)} not found for Telegram.")
    except Exception as e:
        logging.error(f"Error reading latest actual Jodi for Telegram: {e}")

    telegram_message_parts = [
        f"<b>{escape_html_chars(ReportText.CONSOLE_HEADER_TITLE)}</b> - {datetime.now().strftime('%d-%b-%Y')}",
        f"Market Mood: <code>{escape_html_chars(summary['market_mood'])}</code>",
        f"Analytical Confidence: <code>{summary['analytical_confidence_score']}/10</code>",
        f"Overall Backtest Hit Rate (Top 5): <code>{hit_rate:.2f}%</code>",
        f"Latest Result (Jodi): <code>{escape_html_chars(latest_actual_jodi)}</code>",
        "", # Empty line for spacing, which HTML generally ignores unless <br> or <p> is used.
        "<b>Top Analytical Picks:</b>"
    ]

    if summary["top_picks_with_confidence"]:
        for p in summary["top_picks_with_confidence"][:5]: # Limit to top 5 picks
            value = str(p.get('value', 'N/A')) # Already passed through escape_html_chars in the `code` tag.
            confidence = escape_html_chars(p.get('confidence', 'N/A'))
            telegram_message_parts.append(f"• <code>{value}</code> <b>({confidence})</b>")
            reasons = p.get("reasons", [])
            if reasons:
                for r in reasons:
                    telegram_message_parts.append(f"  - <i>{escape_html_chars(r)}</i>")
    else:
        telegram_message_parts.append("No top picks available.")

    full_message = "\n".join(telegram_message_parts)
    send_telegram_message(full_message)

    # --- Manual Prediction Tracking ---
    analysis_date_str = analysis_date.strftime("%Y-%m-%d")
    
    # Get actual results for the analysis_date
    actual_open = "N/A"
    actual_close = "N/A"
    actual_jodi = "N/A"
    
    current_day_data = df[df['date'] == analysis_date_str]
    if not current_day_data.empty:
        # Assuming 'open_panel', 'close_panel', 'jodi' are available in df
        actual_open = str(current_day_data['open'].iloc[-1])
        actual_close = str(current_day_data['close'].iloc[-1])
        actual_jodi = str(current_day_data['jodi'].iloc[-1])
    else:
        logging.warning(f"No actual data found for {analysis_date_str} in CSV. Cannot track manual predictions.")

    logging.debug(f"DEBUG: Tracking for date: {analysis_date_str}")
    logging.debug(f"DEBUG: Actual Open: {actual_open}, Actual Close: {actual_close}, Actual Jodi: {actual_jodi}")

    manual_preds_data = load_manual_predictions()
    if analysis_date_str in manual_preds_data: # Only track if there are predictions for today
        manual_preds_data = track_hits(
            analysis_date_str, 
            actual_open, 
            actual_close, 
            actual_jodi, 
            manual_preds_data
        )
        save_manual_predictions(manual_preds_data)
        tracking_summary = get_tracking_summary(manual_preds_data)
        logging.info(f"Manual prediction tracking summary: {tracking_summary}")

        # Enhance Telegram message with tracking summary
        telegram_message_parts.append("\n<b>Manual Prediction Tracking:</b>")
        telegram_message_parts.append(f"Total Predictions: {tracking_summary['total_predictions']}")
        telegram_message_parts.append(f"Total Hits: {tracking_summary['total_hits']}")
        telegram_message_parts.append(f"Overall Hit Rate: {tracking_summary['overall_hit_rate']:.2f}%")
        
        # Add daily breakdown if applicable
        if analysis_date_str in tracking_summary['daily_breakdown']:
            daily_summary = tracking_summary['daily_breakdown'][analysis_date_str]
            telegram_message_parts.append(f"<u>Today ({analysis_date_str}):</u>")
            telegram_message_parts.append(f"  Hits: {daily_summary['hits']}")
            telegram_message_parts.append(f"  Misses: {daily_summary['misses']}")
            telegram_message_parts.append(f"  Pending: {daily_summary['pending']}")
        
        # Re-send the message with updated content
        full_message = "\n".join(telegram_message_parts) # No HTML replace here, just join
        send_telegram_message(full_message)

    # --- End Manual Prediction Tracking ---




if __name__ == "__main__":
    main()
