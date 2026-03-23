from typing import Any, Dict, List

import pandas as pd

from src.utils.logger import setup_logger


class MirrorPairModel:
    """
    Detects mirror relationships (12 <-> 21, 34 <-> 43, etc.).
    Boosts a jodi if its mirrored pair has appeared recently.
    """
    
    def __init__(self, window: int = 15):
        self.window = window
        self.logger = setup_logger()

    def predict(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Boosts jodis based on the recent appearance of their mirror counterparts.
        """
        if df.empty: return []
        
        recent_jodis = df['jodi'].tail(self.window).astype(str).str.zfill(2).tolist()
        
        all_jodis = [f"{i:02d}" for i in range(100)]
        predictions = []
        
        for jodi in all_jodis:
            # Mirror logic: XY -> YX
            mirror = jodi[1] + jodi[0]
            
            # Count mirror appearances in window
            mirror_count = recent_jodis.count(mirror)
            
            # Simple boost score: 1.0 if mirror appeared at least once
            # 0.5 bonus for each subsequent appearance
            score = 1.0 if mirror_count > 0 else 0.0
            if mirror_count > 1:
                score += (mirror_count - 1) * 0.2
            
            # Max score clamp for ensemble stability
            score = min(score, 1.5)
            
            predictions.append({
                'value': jodi,
                'score': float(score),
                'metrics': {
                    'mirror': mirror,
                    'mirror_hits': int(mirror_count)
                }
            })
            
        predictions.sort(key=lambda x: x['score'], reverse=True)
        return predictions
