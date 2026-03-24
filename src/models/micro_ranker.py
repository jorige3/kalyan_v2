import pandas as pd
from typing import List, Dict, Tuple

class MicroRanker:
    """
    Micro Ranking Engine v2.4 (Optimized)
    Fine-tunes Top 10 candidates using high-precision behavioral rules.
    Refined to avoid conflict with Macro/Ensemble models.
    """
    
    def __init__(self):
        # Weights for micro-factors
        self.weights = {
            'digit_strength': 0.40,
            'recent_trend': 0.30,
            'consistency_bonus': 0.20,
            'penalty_overdue': -0.30
        }

    def rerank(self, top10_values: List[str], df: pd.DataFrame, digit_scores: Dict[int, float]) -> List[str]:
        """
        Reranks the top 10 candidates based on micro-patterns.
        """
        if not top10_values or df.empty:
            return top10_values

        last_date = df["date"].max()
        
        # Optimize: Pre-calculate last seen dates for ALL candidates
        relevant_mask = df['jodi'].astype(str).str.zfill(2).isin(top10_values)
        history_df = df[relevant_mask].copy()
        history_df['jodi_str'] = history_df['jodi'].astype(str).str.zfill(2)
        
        last_seen_map = history_df.groupby('jodi_str')['date'].max().to_dict()
        
        # Calculate recent frequency (last 30 days) for all candidates
        recent_cutoff = last_date - pd.Timedelta(days=30)
        recent_counts = history_df[history_df['date'] >= recent_cutoff]['jodi_str'].value_counts().to_dict()

        scored_candidates = []
        
        for jodi in top10_values:
            score = self._calculate_micro_score(jodi, last_date, last_seen_map, recent_counts, digit_scores)
            scored_candidates.append((jodi, score))
        
        # Sort by score descending
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        return [item[0] for item in scored_candidates]

    def _calculate_micro_score(self, jodi: str, current_date, last_seen_map, recent_counts, digit_scores) -> float:
        j = str(jodi).zfill(2)
        d1, d2 = int(j[0]), int(j[1])
        
        score = 0.0
        
        # 1. Digit Strength (Average of digits)
        # Using average avoids "double counting" high digits compared to other factors
        ds = (digit_scores.get(d1, 0.0) + digit_scores.get(d2, 0.0)) / 2.0
        score += ds * self.weights['digit_strength']
        
        # 2. Recent Trend (Hot Jodis stay hot)
        # Normalized: 1 appearance = 0.33, 3 = 1.0 (capped)
        freq = recent_counts.get(j, 0)
        if freq > 0:
            trend_score = min(freq / 3.0, 1.0)
            score += trend_score * self.weights['recent_trend']
            
        # 3. Overdue Penalty (The "Cold Death" Zone)
        last_seen = last_seen_map.get(j)
        days_absent = (current_date - last_seen).days if last_seen else 999
        
        if days_absent > 120:
            score += self.weights['penalty_overdue']
            
        # 4. Consistency Bonus (Implied)
        # If digit strength is high AND it's trending, give extra boost
        if ds > 0.6 and freq > 0:
            score += self.weights['consistency_bonus']
            
        return score

# Singleton instance for easy import
micro_ranker = MicroRanker()

def rerank_top10(top10_values: List[str], df: pd.DataFrame, digit_scores: Dict[int, float]) -> List[str]:
    """Wrapper function for backward compatibility."""
    return micro_ranker.rerank(top10_values, df, digit_scores)
