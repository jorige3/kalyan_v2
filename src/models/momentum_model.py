import pandas as pd
from typing import List, Dict, Any
from src.utils.logger import setup_logger
import config

class MomentumModel:
    """
    Predicts based on short-term momentum (streaks) and recurring patterns.
    Analyzes the "Wait Cycle" - how often a jodi repeats after its last appearance.
    """
    
    def __init__(self, momentum_window: int = config.MOMENTUM_WINDOW):
        self.momentum_window = momentum_window
        self.logger = setup_logger()

    def predict(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Generates momentum-based predictions.
        Higher score for jodis that appeared recently or are 'hot' in the momentum window.
        """
        if df.empty: return []
        
        all_jodis = [f"{i:02d}" for i in range(100)]
        
        # Analyze the momentum window
        recent_jodis = df['jodi'].tail(self.momentum_window).tolist()
        jodi_counts = pd.Series(recent_jodis).value_counts().to_dict()
        
        # Streak detection: how many times it appeared in the last X days
        max_streak = max(jodi_counts.values()) if jodi_counts else 1.0
        
        predictions = []
        for jodi in all_jodis:
            count = jodi_counts.get(jodi, 0)
            
            # Simple momentum score: normalized frequency in short window
            momentum_score = count / max_streak if max_streak > 0 else 0
            
            # Bonus: if it was the VERY last result (potential for repeat)
            last_result_bonus = 0.5 if not df.empty and str(df['jodi'].iloc[-1]).zfill(2) == jodi else 0.0
            
            final_score = (momentum_score * 0.7) + (last_result_bonus * 0.3)
            
            predictions.append({
                'value': jodi,
                'score': float(final_score),
                'metrics': {
                    'momentum_count': count,
                    'is_last_result': last_result_bonus > 0,
                    'recent_freq': 0.0, # Not primary metric for momentum
                    'long_term_freq': 0.0,
                    'absence_score': 0.0
                }
            })
            
        predictions.sort(key=lambda x: x['score'], reverse=True)
        return predictions
