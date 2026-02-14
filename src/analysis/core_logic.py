from typing import Dict, List
from datetime import datetime, timezone

import config
from src.analysis.explainability import explain_pick
from src.ux.text_templates import ReportText

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
