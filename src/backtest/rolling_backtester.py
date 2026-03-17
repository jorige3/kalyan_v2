import pandas as pd
from typing import Any, List, Dict
import logging
import config

class RollingBacktester:
    """
    Performs a rolling backtest of a prediction model.
    Evaluates historical performance without data leakage.
    """
    
    def __init__(self, model: Any, warmup: int = config.BACKTEST_WARMUP):
        self.model = model
        self.warmup = warmup
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Runs the backtest on the provided DataFrame."""
        if len(df) <= self.warmup:
            self.logger.warning(f"Data size {len(df)} is less than warmup {self.warmup}.")
            return {}

        results = []
        self.logger.info(f"Starting backtest from index {self.warmup} to {len(df)-1}...")
        
        for i in range(self.warmup, len(df)):
            # "Train" only on data BEFORE the current index (No Data Leakage)
            train_df = df.iloc[:i]
            actual_row = df.iloc[i]
            actual_jodi = str(actual_row['jodi']).zfill(2)
            
            # Predict for the next day based only on historical data
            predictions = self.model.predict(train_df)
            top_5 = [p['value'] for p in predictions[:5]]
            top_10 = [p['value'] for p in predictions[:10]]
            
            # Calculate hits
            is_hit_top5 = actual_jodi in top_5
            is_hit_top10 = actual_jodi in top_10
            
            results.append({
                'date': actual_row['date'],
                'actual': actual_jodi,
                'hit_top5': is_hit_top5,
                'hit_top10': is_hit_top10,
                'top_picked': top_5[0] if top_5 else None
            })

        if not results:
            return {}

        results_df = pd.DataFrame(results)
        
        # Aggregate Overall Metrics (Hit Rates)
        hit_rate_top5 = results_df['hit_top5'].mean()
        hit_rate_top10 = results_df['hit_top10'].mean()
        
        self.logger.info(f"Backtest complete. Top 5 Hit Rate: {hit_rate_top5*100:.2f}%")
        
        return {
            'results_df': results_df,
            'hit_rate_top5': float(hit_rate_top5),
            'hit_rate_top10': float(hit_rate_top10),
            'total_days': len(results_df)
        }
