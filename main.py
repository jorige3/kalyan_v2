import argparse
import logging
import os
import json
import hashlib
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
from src.telegram_notifier import send_telegram_message, escape_markdown_v2_chars # Import Telegram notifier and escape utility

# Load environment variables from .env file
load_dotenv()

# -------------------------------------------------------------------
# Paths & Logging
# -------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
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
# Core Summary Logic
# -------------------------------------------------------------------

def generate_daily_summary_and_confidence(analysis_results: Dict) -> Dict:
    signals = {
        "high_frequency": analysis_results["hot_jodis"],
        "trend_window": analysis_results["trend_due_jodis"],
        "extended_absence": analysis_results["due_jodis"],
        "exhausted": analysis_results["exhausted_jodis"],
    }

    all_picks = set().union(
        analysis_results["hot_jodis"],
        analysis_results["due_jodis"],
        analysis_results["trend_due_jodis"],
        analysis_results["hot_open_sangams"],
        analysis_results["hot_close_sangams"],
        analysis_results["due_open_sangams"],
        analysis_results["due_close_sangams"],
    )

    scored = []
    for val in all_picks:
        score = 0
        if val in signals["high_frequency"]:
            score += config.SCORING_WEIGHTS["HIGH_FREQUENCY_JODI"]
        if val in signals["trend_window"]:
            score += config.SCORING_WEIGHTS["TREND_ALIGNED_JODI"]
        if val in signals["extended_absence"]:
            score += config.SCORING_WEIGHTS["EXTENDED_ABSENCE_JODI"]
        if val in signals["exhausted"]:
            score += config.SCORING_WEIGHTS["EXHAUSTED_PATTERN_PENALTY"]

        confidence = ReportText.CONFIDENCE_LOW
        if score >= config.CONFIDENCE_THRESHOLDS["HIGH"]:
            confidence = ReportText.CONFIDENCE_HIGH
        elif score >= config.CONFIDENCE_THRESHOLDS["MEDIUM"]:
            confidence = ReportText.CONFIDENCE_MEDIUM

        scored.append({
            "value": val,
            "score": score,
            "confidence": confidence,
            "reasons": explain_pick(val, signals)
        })

    def _pick_sort_key(p):
        try:
            num = int(p["value"])
        except (TypeError, ValueError):
            num = None
        return (-p["score"], num if num is not None else float("inf"), str(p["value"]))

    scored.sort(key=_pick_sort_key)

    return {
        "market_mood": "Active" if scored else "Quiet",
        "analytical_confidence_score": min(10, 6 + len([s for s in scored if s["confidence"] == "High"])),
        "strongest_signals": scored[:3],
        "caution_areas": [],
        "top_picks_with_confidence": scored[:5],
    }

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




if __name__ == "__main__":
    main()
