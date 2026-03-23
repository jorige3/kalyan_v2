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
        yesterday_top10: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Reranks predictions based on:
        1. Base Ensemble Score
        2. Recency Boost (Trend continues)
        3. Delay Boost (Yesterday's Top 10)
        4. Digit Strength (Combined digit intelligence)
        5. Repeat Penalty (Avoid overfitting)
        """
        if not predictions or df.empty:
            return predictions

        final = []
        last_date = df["date"].max()
        
        # Calculate last seen for each jodi in the dataset
        # Ensure jodi is string and zero-padded
        df_copy = df.copy()
        df_copy['jodi_str'] = df_copy['jodi'].astype(str).str.zfill(2)
        last_seen = df_copy.groupby("jodi_str")["date"].max()
        yesterday_jodi = df_copy.iloc[-1]["jodi_str"]

        delay_boost_count = 0
        
        for p in predictions:
            jodi = str(p["value"]).zfill(2)
            base_score = p["score"]

            # 1. Days absent (Recency)
            last_seen_date = last_seen.get(jodi)
            if last_seen_date:
                days_absent = (last_date - last_seen_date).days + 1
            else:
                days_absent = 365
            
            recency_boost = 1 / days_absent

            # 2. Delay boost (Yesterday's Top 10)
            delay_boost = 1.0 if jodi in yesterday_top10 else 0.0
            if delay_boost > 0:
                delay_boost_count += 1

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

            # Keep original metrics if they exist
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
        # Sort by final score descending
        return sorted(final, key=lambda x: x["score"], reverse=True)
