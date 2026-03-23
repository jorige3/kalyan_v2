from typing import Dict

import pandas as pd

from src.utils.logger import setup_logger


class DigitAnalyzer:
    """
    Performs scientific analysis on single digits (Open/Close).
    Useful for identifying digit-level heat.
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.logger = setup_logger()

    def get_digit_frequencies(self, window: int = 30) -> Dict[str, Dict[str, float]]:
        """Calculates frequency of each digit (0-9) in open and close positions."""
        if self.df.empty:
            return {'open': {}, 'close': {}}
            
        recent_df = self.df.tail(window)
        
        # Ensure jodi is zfilled
        jodis = recent_df['jodi'].astype(str).str.zfill(2)
        
        open_digits = jodis.str[0]
        close_digits = jodis.str[1]
        
        open_freq = open_digits.value_counts(normalize=True).to_dict()
        close_freq = close_digits.value_counts(normalize=True).to_dict()
        
        # Ensure all digits 0-9 are represented
        for d in "0123456789":
            open_freq.setdefault(d, 0.0)
            close_freq.setdefault(d, 0.0)
            
        return {
            'open': open_freq,
            'close': close_freq
        }
