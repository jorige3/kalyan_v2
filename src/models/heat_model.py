import pandas as pd
import numpy as np
from typing import List, Dict, Any
from src.utils.logger import setup_logger
import config

class HeatModel:
    """
    Implements a heat-based scoring model for Jodi predictions.
    
    Formula:
    score = (recent_frequency * 0.7) + (absence_score * 0.2) + (long_term_frequency * 0.1)
    """

    def __init__(self, recent_window: int = config.RECENT_WINDOW, 
                 long_term_window: int = config.LONG_TERM_WINDOW, 
                 weights: Dict[str, float] = config.HEAT_MODEL_WEIGHTS):
        self.recent_window = recent_window
        self.long_term_window = long_term_window
        self.weights = weights
        self.logger = setup_logger()

    def predict(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Generates predictions based on historical data.
        Assumes df is already filtered to only include data prior to the prediction date.
        """
        if df.empty:
            self.logger.warning("Empty dataframe provided to HeatModel.predict()")
            return []

        # All possible jodis from 00 to 99 as strings
        all_jodis = [f"{i:02d}" for i in range(100)]
        
        # Calculate raw frequencies
        recent_df = df.tail(self.recent_window)
        long_term_df = df.tail(self.long_term_window)
        
        recent_counts = recent_df['jodi'].value_counts().to_dict()
        long_term_counts = long_term_df['jodi'].value_counts().to_dict()
        
        # Normalize frequencies relative to the window size to get raw probability
        recent_freqs = {k: v / len(recent_df) for k, v in recent_counts.items()}
        long_term_freqs = {k: v / len(long_term_df) for k, v in long_term_counts.items()}
        
        # Calculate absence scores
        # absence_score = (days_since_last_appearance) / window_size (clamped to 1.0)
        last_appearance = {}
        for jodi in all_jodis:
            # Find the last index of this jodi
            idx = df[df['jodi'] == jodi].index
            if not idx.empty:
                days_since = len(df) - 1 - idx[-1]
                # Scientific normalization: scale absence by recent window
                last_appearance[jodi] = min(days_since / self.recent_window, 1.0)
            else:
                last_appearance[jodi] = 1.0 # Max absence score if never seen

        # --- Scientific Normalization ---
        # Frequency scores can be very small (e.g. 0.033 for 1 appearance in 30 days)
        # We normalize them relative to the MAXIMUM observed frequency to make them more distinct
        max_r_freq = max(recent_freqs.values()) if recent_freqs else 1.0
        max_l_freq = max(long_term_freqs.values()) if long_term_freqs else 1.0

        predictions = []
        for jodi in all_jodis:
            r_freq = recent_freqs.get(jodi, 0)
            l_freq = long_term_freqs.get(jodi, 0)
            a_score = last_appearance.get(jodi, 0)
            
            # Normalize for scoring
            norm_r_freq = r_freq / max_r_freq if max_r_freq > 0 else 0
            norm_l_freq = l_freq / max_l_freq if max_l_freq > 0 else 0
            
            final_score = (
                (norm_r_freq * self.weights['recent_freq']) +
                (a_score * self.weights['absence']) +
                (norm_l_freq * self.weights['long_term_freq'])
            )
            
            predictions.append({
                'value': jodi,
                'score': float(final_score),
                'metrics': {
                    'recent_freq': float(r_freq),
                    'long_term_freq': float(l_freq),
                    'absence_score': float(a_score)
                }
            })

        # Sort by score descending (Scientific Ranking)
        predictions.sort(key=lambda x: x['score'], reverse=True)
        return predictions
