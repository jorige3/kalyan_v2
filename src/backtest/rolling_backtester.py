import logging
from typing import Any, Dict

import pandas as pd

import config
from src.models.smart_ranker import SmartRanker


class RollingBacktester:
    """
    Performs a rolling backtest of a prediction model.
    Evaluates historical performance without data leakage.
    Integrated with SmartRanker for decision-layer evaluation.
    """
    
    def __init__(self, model: Any, warmup: int = config.BACKTEST_WARMUP):
        self.model = model
        self.warmup = warmup
        self.logger = logging.getLogger(self.__class__.__name__)
        # Initialize SmartRanker with config weights
        self.smart_ranker = SmartRanker(weights=config.SMART_RANKER_WEIGHTS)

    def run(self, df: pd.DataFrame, max_days: int = None) -> Dict[str, Any]:
        """Runs the backtest on the provided DataFrame."""
        if len(df) <= self.warmup:
            self.logger.warning(f"Data size {len(df)} is less than warmup {self.warmup}.")
            return {}

        start_idx = self.warmup
        if max_days and len(df) - self.warmup > max_days:
            start_idx = len(df) - max_days

        results = []
        self.logger.info(f"Starting backtest from index {start_idx} to {len(df)-1}...")
        
        # Track yesterday's top 10 for SmartRanker delay boost
        # To be accurate, we need to get the top 10 for start_idx - 1
        yesterday_top10 = []
        if start_idx > 0:
            self.logger.debug(f"Pre-calculating yesterday_top10 for index {start_idx}...")
            yesterday_train = df.iloc[:start_idx-1]
            if not yesterday_train.empty:
                prev_raw = self.model.predict(yesterday_train)
                yesterday_top10 = [p['value'] for p in prev_raw[:10]]
        
        for i in range(start_idx, len(df)):
            # "Train" only on data BEFORE the current index (No Data Leakage)
            train_df = df.iloc[:i]
            actual_row = df.iloc[i]
            actual_jodi = str(actual_row['jodi']).zfill(2)
            
            # 1. Base Ensemble Prediction
            raw_predictions = self.model.predict(train_df)
            
            # 2. Get digit scores from the digit model (if available in ensemble)
            digit_scores = {}
            if hasattr(self.model, 'models') and 'digit' in self.model.models:
                digit_scores = self.model.models['digit'].get_digit_scores(train_df)
            
            # 3. Apply Smart Reranking
            final_predictions = self.smart_ranker.rerank(
                raw_predictions,
                train_df,
                digit_scores,
                yesterday_top10
            )
            
            # Use Micro Rank Engine v2.4 (Rerank Top 10)
            from src.models.micro_ranker import rerank_top10
            top_10_candidates = [p['value'] for p in final_predictions[:10]]
            top_10_reranked = rerank_top10(top_10_candidates, train_df, digit_scores)
            
            top_5 = top_10_reranked[:5]
            top_10 = top_10_reranked # Still top 10 candidates, just reranked
            
            # Update yesterday_top10 for NEXT iteration (tomorrow)
            yesterday_top10 = [p['value'] for p in final_predictions[:10]]
            
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
        
        # Yearly Breakdown
        results_df['year'] = results_df['date'].dt.year
        yearly_breakdown = results_df.groupby('year')[['hit_top5', 'hit_top10']].mean()
        
        # Recent 30-day Performance
        recent_30 = results_df.tail(30)
        recent_top5 = recent_30['hit_top5'].mean()
        recent_top10 = recent_30['hit_top10'].mean()
        
        self.logger.info("-" * 40)
        self.logger.info(f"Backtest Overall (Top 5): {hit_rate_top5*100:.2f}%")
        self.logger.info(f"Backtest Overall (Top 10): {hit_rate_top10*100:.2f}%")
        self.logger.info("-" * 40)
        self.logger.info(f"Recent 30 Days (Top 5): {recent_top5*100:.2f}%")
        self.logger.info(f"Recent 30 Days (Top 10): {recent_top10*100:.2f}%")
        self.logger.info("-" * 40)
        self.logger.info("Yearly Breakdown:")
        for year, row in yearly_breakdown.iterrows():
            self.logger.info(f"  {year}: Top 5={row['hit_top5']*100:.1f}%, Top 10={row['hit_top10']*100:.1f}%")
            
        return {
            'results_df': results_df,
            'hit_rate_top5': float(hit_rate_top5),
            'hit_rate_top10': float(hit_rate_top10),
            'recent_top5': float(recent_top5),
            'recent_top10': float(recent_top10),
            'yearly_breakdown': yearly_breakdown.to_dict(),
            'total_days': len(results_df)
        }
