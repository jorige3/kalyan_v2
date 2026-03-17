import pandas as pd
from typing import List, Dict, Any
from src.utils.logger import setup_logger
import config

class GapClusterModel:
    """
    Identifies and boosts jodis that have been absent for a specific "Wait Cycle" range.
    Target range: 25–40 days.
    """
    
    def __init__(self, min_gap: int = 25, max_gap: int = 40):
        self.min_gap = min_gap
        self.max_gap = max_gap
        self.logger = setup_logger()

    def predict(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Scores jodis based on their absence gap.
        Score is 1.0 if the jodi is within the target gap cluster.
        """
        if df.empty: return []
        
        all_jodis = [f"{i:02d}" for i in range(100)]
        predictions = []
        
        # Calculate current gap for each jodi
        for jodi in all_jodis:
            # Find last index
            idx = df[df['jodi'] == jodi].index
            if not idx.empty:
                gap = len(df) - 1 - idx[-1]
            else:
                gap = len(df) # Max gap if never seen
                
            # Score based on cluster: 1.0 if in range, 0.0 otherwise.
            # We use a fuzzy score (peak at center of gap) for scientific robustness
            center = (self.min_gap + self.max_gap) / 2
            width = (self.max_gap - self.min_gap) / 2
            
            # Simple binary score for now, but normalized
            if self.min_gap <= gap <= self.max_gap:
                # Gaussian-like peak at center
                score = 1.0 - (abs(gap - center) / width)
                score = max(score, 0.1) # Min base score if in range
            else:
                score = 0.0
                
            predictions.append({
                'value': jodi,
                'score': float(score),
                'metrics': {
                    'gap': int(gap),
                    'in_cluster': self.min_gap <= gap <= self.max_gap
                }
            })
            
        predictions.sort(key=lambda x: x['score'], reverse=True)
        return predictions
