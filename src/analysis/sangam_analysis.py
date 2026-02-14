# -*- coding: utf-8 -*-
"""
src/analysis/sangam_analysis.py

Module for advanced Sangam analysis, including hot, cold, and due Sangams.
"""

from typing import Dict, List

import pandas as pd


class SangamAnalyzer:
    """
    Analyzes Sangam patterns, including identifying hot, cold, and due Sangams.
    """
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        # Ensure 'open_sangam' and 'close_sangam' columns exist
        if 'open_sangam' not in self.df.columns or 'close_sangam' not in self.df.columns:
            raise ValueError("DataFrame must contain 'open_sangam' and 'close_sangam' columns for Sangam analysis.")
        
        # Ensure sangam columns are string type
        self.df['open_sangam'] = self.df['open_sangam'].astype(str)
        self.df['close_sangam'] = self.df['close_sangam'].astype(str)

    def get_hot_sangams(self, lookback_days: int = 30, top_n: int = 5) -> Dict[str, List[str]]:
        """
        Identifies 'hot' open and close Sangams based on their frequency in recent days.
        """
        latest_date = self.df['date'].max()
        recent_df = self.df[self.df['date'] >= (latest_date - pd.Timedelta(days=lookback_days))]

        hot_open_sangams = recent_df['open_sangam'].value_counts().head(top_n).index.tolist()
        hot_close_sangams = recent_df['close_sangam'].value_counts().head(top_n).index.tolist()

        return {
            "hot_open_sangams": hot_open_sangams,
            "hot_close_sangams": hot_close_sangams
        }

    def get_due_sangams(self, lookback_days: int = 60, top_n: int = 5) -> Dict[str, List[str]]:
        """
        Identifies 'due' open and close Sangams based on their absence in recent days.
        """
        latest_date = self.df['date'].max()
        recent_df = self.df[self.df['date'] >= (latest_date - pd.Timedelta(days=lookback_days))]

        all_open_sangams = self.df['open_sangam'].unique()
        all_close_sangams = self.df['close_sangam'].unique()

        due_open_sangams = []
        for sangam in all_open_sangams:
            if sangam not in recent_df['open_sangam'].values:
                due_open_sangams.append(sangam)
        
        due_close_sangams = []
        for sangam in all_close_sangams:
            if sangam not in recent_df['close_sangam'].values:
                due_close_sangams.append(sangam)
        
        # For simplicity, just returning all due ones found.
        # A more sophisticated approach would involve sorting by last appearance date.
        return {
            "due_open_sangams": due_open_sangams[:top_n],
            "due_close_sangams": due_close_sangams[:top_n]
        }

    # Placeholder for other advanced Sangam analysis methods
    def get_sangam_cycle_streaks(self) -> Dict:
        """
        Identifies streaks or cycles in Sangam appearances. (Placeholder)
        """
        return {"open_sangam_streaks": [], "close_sangam_streaks": []}

    def get_sangam_digit_dominance(self) -> Dict:
        """
        Analyzes the dominance of individual digits within Sangams. (Placeholder)
        """
        return {"open_sangam_digit_dominance": {}, "close_sangam_digit_dominance": {}}
