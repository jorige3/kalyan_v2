from typing import Any, Dict, List

import pandas as pd

from src.utils.logger import setup_logger


class DigitMomentumModel:
    """
    Scores jodi pairs based on the strength of their individual digits.
    Based on digit frequency for the last 30 days.
    """
    
    def __init__(self, window: int = 30):
        self.window = window
        self.logger = setup_logger()

    def get_digit_scores(self, df: pd.DataFrame) -> Dict[int, float]:
        """Returns normalized scores for digits 0-9 based on combined Open/Close frequency."""
        if df.empty: return {i: 0.0 for i in range(10)}
        
        recent_df = df.tail(self.window)
        jodis = recent_df['jodi'].astype(str).str.zfill(2)
        
        # Combined frequency of digits in both positions
        all_digits = pd.concat([jodis.str[0], jodis.str[1]])
        counts = all_digits.value_counts(normalize=True).to_dict()
        
        # Max observed frequency to normalize
        max_freq = max(counts.values()) if counts else 1.0
        
        scores = {}
        for i in range(10):
            d = str(i)
            # Normalize relative to max observed
            scores[i] = float(counts.get(d, 0.0) / max_freq) if max_freq > 0 else 0.0
            
        return scores

    def predict(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Generates digit-based predictions.
        Score = (OpenDigitFreq + CloseDigitFreq) / 2
        """
        if df.empty: return []
        
        recent_df = df.tail(self.window)
        # Ensure jodi strings are zfilled
        jodis = recent_df['jodi'].astype(str).str.zfill(2)
        
        open_digits = jodis.str[0]
        close_digits = jodis.str[1]
        
        # Calculate raw frequencies for digits 0-9
        open_counts = open_digits.value_counts(normalize=True).to_dict()
        close_counts = close_digits.value_counts(normalize=True).to_dict()
        
        # Ensure all digits are covered
        for d in "0123456789":
            open_counts.setdefault(d, 0.0)
            close_counts.setdefault(d, 0.0)
            
        all_jodis = [f"{i:02d}" for i in range(100)]
        predictions = []
        for jodi in all_jodis:
            o_digit = jodi[0]
            c_digit = jodi[1]
            
            # Simple average of digit strengths
            o_freq = open_counts[o_digit]
            c_freq = close_counts[c_digit]
            
            # Normalize: max possible score for a digit is 1.0 (if it appeared every time)
            # but usually it's around 0.1-0.3. Let's normalize relative to max observed.
            max_o = max(open_counts.values()) if open_counts else 1.0
            max_c = max(close_counts.values()) if close_counts else 1.0
            
            score = ( (o_freq / max_o) + (c_freq / max_c) ) / 2
            
            predictions.append({
                'value': jodi,
                'score': float(score),
                'metrics': {
                    'open_freq': float(o_freq),
                    'close_freq': float(c_freq)
                }
            })
            
        predictions.sort(key=lambda x: x['score'], reverse=True)
        return predictions
