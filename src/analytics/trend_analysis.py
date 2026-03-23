from typing import Dict

import pandas as pd

from src.utils.logger import setup_logger


class TrendAnalyzer:
    """Analyzes recent trends and streaks in Kalyan market outcomes."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.logger = setup_logger()

    def get_market_sentiment(self, window: int = 15) -> str:
        """Determines if the market is favoring high or low digits based on recent data."""
        if self.df.empty: return "NEUTRAL"
        
        recent_df = self.df.tail(window)
        # Combine open and close digits to analyze overall distribution
        jodis = recent_df['jodi'].astype(str).str.zfill(2)
        all_digits = "".join(jodis.tolist())
        
        digits = [int(d) for d in all_digits]
        avg_digit = sum(digits) / len(digits) if digits else 4.5
        
        if avg_digit > 5.5: return "HIGH_DIGIT_BIAS"
        elif avg_digit < 3.5: return "LOW_DIGIT_BIAS"
        else: return "STABLE"

    def detect_streaks(self, window: int = 10) -> Dict[str, int]:
        """Checks for repeating jodis in the last X days."""
        if self.df.empty: return {}
        
        recent_jodis = self.df['jodi'].tail(window).astype(str).str.zfill(2).tolist()
        jodi_counts = pd.Series(recent_jodis).value_counts().to_dict()
        
        # Only return jodis that have appeared more than once in the window
        return {k: v for k, v in jodi_counts.items() if v > 1}
