import logging
from typing import Any, Dict, List

import pandas as pd


class SmartRanker:
    """
    Smart Rank Engine v2 - Decision Layer
    Adjusts ensemble ranking using real-world behavior patterns.
    """
    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or {
            "base_score": 0.5,
            "recency": 0.2,
            "delay": 0.15,
            "digit_score": 0.1,
            "penalty": -0.2
        }
        self.logger = logging.getLogger(self.__class__.__name__)

    def rerank(
        self, 
        predictions: List[Dict[str, Any]], 
        df: pd.DataFrame, 
        digit_scores: Dict[int, float], 
        recent_top10s: List[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Reranks predictions based on:
        1. Base Ensemble Score
        2. Recency Boost (Trend continues)
        3. Multi-Day Delay Boost (Last 3 days Top 10)
        4. Digit Strength (Combined digit intelligence)
        5. Repeat Penalty (Avoid overfitting)
        """
        if not predictions or df.empty:
            return predictions

        final = []
        last_date = df["date"].max()
        
        # Calculate last seen for each jodi in the dataset
        df_copy = df.copy()
        df_copy['jodi_str'] = df_copy['jodi'].astype(str).str.zfill(2)
        last_seen = df_copy.groupby("jodi_str")["date"].max()
        yesterday_jodi = df_copy.iloc[-1]["jodi_str"]

        delay_boost_count = 0
        recent_top10s = recent_top10s or []
        
        for p in predictions:
            jodi = str(p["value"]).zfill(2)
            base_score = p["score"]

            # 1. Days absent (Recency)
            last_seen_date = last_seen.get(jodi)
            if last_seen_date:
                days_absent = (last_date - last_seen_date).days
            else:
                days_absent = 365
            
            recency_boost = max(0.0, 1.0 - (days_absent / 30.0))

            # 2. Multi-Day Delay boost (Last 3 days Top 10)
            # Weights: Day-1 (1.0), Day-2 (0.6), Day-3 (0.3)
            delay_boost = 0.0
            day_weights = [1.0, 0.6, 0.3]
            
            for i, top10 in enumerate(recent_top10s):
                if i >= len(day_weights): break
                if jodi in top10:
                    rank = top10.index(jodi)
                    # Rank weight: 1.0 for top 1, 0.8 for top 2-5, 0.5 for top 6-10
                    rank_weight = 1.0 if rank == 0 else (0.8 if rank < 5 else 0.5)
                    boost = rank_weight * day_weights[i]
                    delay_boost = max(delay_boost, boost)
                    if i == 0: delay_boost_count += 1

            # 3. Digit strength
            d1, d2 = int(jodi[0]), int(jodi[1])
            digit_score = digit_scores.get(d1, 0.0) + digit_scores.get(d2, 0.0)

            # 4. Repeat penalty
            penalty = 1.0 if jodi == yesterday_jodi else 0.0

            # Combined Formula
            final_score = (
                base_score * self.weights.get("base_score", 0.5) +
                recency_boost * self.weights.get("recency", 0.2) +
                delay_boost * self.weights.get("delay", 0.15) +
                digit_score * self.weights.get("digit_score", 0.1) +
                (penalty * self.weights.get("penalty", -0.2))
            )

            metrics = p.get('metrics', {}).copy()
            metrics.update({
                'base_score': base_score,
                'recency_boost': recency_boost,
                'delay_boost': delay_boost,
                'digit_strength': digit_score,
                'repeat_penalty': penalty
            })

            final.append({
                "value": jodi,
                "score": float(final_score),
                "metrics": metrics
            })

        self.logger.debug(f"SmartRanker: Applied delay boost to {delay_boost_count} jodis.")
        return sorted(final, key=lambda x: x["score"], reverse=True)
