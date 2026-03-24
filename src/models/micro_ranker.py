import pandas as pd
from typing import List, Dict, Any

def micro_score(jodi: str, df: pd.DataFrame, digit_scores: Dict[int, float]) -> float:
    """
    Micro Ranking Score v2.4
    Fine-tunes the top 10 candidates using behavioral micro-patterns.
    """
    j = str(jodi).zfill(2)
    d1, d2 = int(j[0]), int(j[1])
    score = 0.0

    # 1. Digit Strength (40% Weighting influence)
    score += (digit_scores.get(d1, 0.0) + digit_scores.get(d2, 0.0)) * 0.4

    # Pre-calculate data for rules
    last_date = df["date"].max()
    jodi_history = df[df["jodi"].astype(str).str.zfill(2) == j]
    
    if jodi_history.empty:
        days_absent = 999
        last_seen = None
    else:
        last_seen = jodi_history["date"].max()
        days_absent = (last_date - last_seen).days

    # 2. Recent Boost (Last 30 days appearance)
    recent_threshold = last_date - pd.Timedelta(days=30)
    if last_seen and last_seen >= recent_threshold:
        score += 0.3

    # 3. Delay Boost (Sweet Spot: 5-25 days)
    if 5 <= days_absent <= 25:
        score += 0.4

    # 4. Overdue Penalty (Cold Zone)
    if days_absent > 120:
        score -= 0.3

    return score

def rerank_top10(top10_values: List[str], df: pd.DataFrame, digit_scores: Dict[int, float]) -> List[str]:
    """
    Applies micro-scoring to rerank the top 10 candidates.
    """
    scored_items = []
    for jodi in top10_values:
        m_score = micro_score(jodi, df, digit_scores)
        scored_items.append((jodi, m_score))
    
    # Sort by micro_score descending
    scored_items.sort(key=lambda x: x[1], reverse=True)
    
    return [item[0] for item in scored_items]
