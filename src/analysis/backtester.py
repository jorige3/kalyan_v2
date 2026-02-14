# src/analysis/backtester.py

import pandas as pd
from src.engine.kalyan_engine import KalyanEngine
from src.analysis.hot_cold import HotColdAnalyzer
from src.analysis.trend_window import TrendWindowAnalyzer
from src.analysis.sangam_analysis import SangamAnalyzer
from src.analysis.core_logic import generate_daily_summary_and_confidence # Import from core_logic.py



class Backtester:
    def __init__(self, df: pd.DataFrame, warmup: int = 50):
        self.df = df.sort_values("date").reset_index(drop=True)
        self.warmup = warmup

    def run(self) -> pd.DataFrame:
        results = []

        for i in range(self.warmup, len(self.df)):
            train_df = self.df.iloc[:i]
            test_row = self.df.iloc[i]

            # Instantiate analyzers with the training data
            hot_cold_analyzer = HotColdAnalyzer(train_df)
            trend_analyzer = TrendWindowAnalyzer(train_df)
            sangam_analyzer = SangamAnalyzer(train_df)

            # Perform analysis to get signals
            analysis_results = {
                "hot_digits": hot_cold_analyzer.get_hot_digits(),
                "hot_jodis": hot_cold_analyzer.get_hot_jodis(),
                "due_jodis": hot_cold_analyzer.get_due_cycles()['due_jodis'],
                "exhausted_jodis": hot_cold_analyzer.get_exhausted_numbers()['exhausted_jodis'],
                "trend_due_jodis": trend_analyzer.get_due_cycles_by_last_appearance()['due_jodis'],
                "trend_exhausted_jodis": trend_analyzer.get_exhausted_numbers_by_streak()['exhausted_jodis'],
                "hot_open_sangams": sangam_analyzer.get_hot_sangams()['hot_open_sangams'],
                "hot_close_sangams": sangam_analyzer.get_hot_sangams()['hot_close_sangams'],
                "due_open_sangams": sangam_analyzer.get_due_sangams()['due_open_sangams'],
                "due_close_sangams": sangam_analyzer.get_due_sangams()['due_close_sangams'],
            }

            # Generate daily summary and confidence to get top picks
            summary_data = generate_daily_summary_and_confidence(analysis_results)
            picks = summary_data.get('top_picks_with_confidence', [])

            assert isinstance(picks, list), "top_picks_with_confidence is not a list"
            # Each pick in the list should be a dictionary with at least 'value' and 'confidence'
            if picks:
                assert isinstance(picks[0], dict), "Each pick should be a dictionary"
                assert "value" in picks[0], "Pick dictionary missing 'value' key"
                assert "confidence" in picks[0], "Pick dictionary missing 'confidence' key"

            actual = str(test_row["jodi"])

            row = {
                "date": test_row["date"],
                "actual": actual,
                "top1_hit": False,
                "top3_hit": False,
                "top5_hit": False,
                "confidence": "Miss"
            }

            if picks:
                # Check for top 1 hit
                if str(picks[0]["value"]) == actual:
                    row["top1_hit"] = True
                    row["confidence"] = picks[0]["confidence"]

                # Check for top 3 hit
                if any(str(p["value"]) == actual for p in picks[:3]):
                    row["top3_hit"] = True
                    if row["confidence"] == "Miss": # Only update if not already a top1 hit
                        row["confidence"] = next(
                            (p["confidence"] for p in picks[:3] if str(p["value"]) == actual),
                            "Miss"
                        )

                # Check for top 5 hit
                if any(str(p["value"]) == actual for p in picks[:5]):
                    row["top5_hit"] = True
                    if row["confidence"] == "Miss": # Only update if not already a top1 or top3 hit
                        row["confidence"] = next(
                            (p["confidence"] for p in picks[:5] if str(p["value"]) == actual),
                            "Miss"
                        )
            results.append(row)

        return pd.DataFrame(results)
