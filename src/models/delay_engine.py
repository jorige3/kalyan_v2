"""
Delay Intelligence Engine v1
Exploits the "Top 10 Delay Pattern" (Jodi appears 1 day AFTER being predicted).
"""
import logging

logger = logging.getLogger(__name__)

def apply_delay_boost(predictions, previous_top10, last_seen_map, delay_weights):
    """
    Applies boosts to predictions based on historical delay patterns.
    
    Args:
        predictions (list): List of dicts [{value: "15", score: 0.52}, ...]
        previous_top10 (list): List of jodis from yesterday's prediction
        last_seen_map (dict): Dict {jodi: last_seen_days}
        delay_weights (dict): Dict with "strong", "medium", "penalty" weights
        
    Returns:
        list: Modified predictions with updated scores, sorted by score descending.
    """
    if not predictions:
        return []

    boosted_jodis = []
    
    strong_boost = delay_weights.get("strong", 0.25)
    medium_boost = delay_weights.get("medium", 0.10)
    penalty = delay_weights.get("penalty", 0.15)

    for pred in predictions:
        jodi = pred['value']
        original_score = pred['score']
        boost_applied = 0
        
        # 1. NEXT-DAY DELAY BOOST (Strongest Signal)
        if previous_top10 and jodi in previous_top10:
            boost_applied += strong_boost
            boosted_jodis.append(jodi)
            
        # 2. SWEET SPOT DELAY (Optional)
        last_seen_days = last_seen_map.get(jodi, 999)
        if 1 <= last_seen_days <= 3:
            boost_applied += medium_boost
            
        # 3. OVERDELAY PENALTY
        if last_seen_days > 10:
            boost_applied -= penalty
            
        pred['score'] = original_score + boost_applied

    # Sort predictions by new score
    predictions.sort(key=lambda x: x['score'], reverse=True)
    
    if boosted_jodis:
        logger.info("Delay Engine Applied")
        logger.debug(f"Boosted jodis: {boosted_jodis}")
        
    return predictions
