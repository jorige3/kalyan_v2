import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import config

logger = logging.getLogger(__name__)

MANUAL_PREDICTIONS_FILE = Path(config.MANUAL_PREDICTIONS_CONFIG["FILE_PATH"])

def _normalize_value(value: str) -> str:
    """
    Normalizes a value (digit or jodi) to a consistent string format for comparison.
    Handles "6.0" to "6", and ensures strings are comparable.
    """
    try:
        if isinstance(value, str) and value.lower() == 'n/a': # Handle "N/A"
            return value
        # Try to convert to float then int to handle "6.0" -> 6
        # Then convert back to string
        return str(int(float(value)))
    except (ValueError, TypeError):
        # If not a number, return as is (e.g., "N/A" or "06" if jodi can have leading zeros)
        # Assuming current data won't have "06" but "6", and "6.0" -> "6" is the main issue.
        return str(value)

def load_manual_predictions() -> Dict[str, List[Dict[str, Any]]]:
    """
    Loads manual predictions from the configuration file.
    Returns a dictionary where keys are dates (YYYY-MM-DD) and values are lists of predictions.
    """
    if not MANUAL_PREDICTIONS_FILE.exists():
        logger.info(f"Manual predictions file not found at {MANUAL_PREDICTIONS_FILE}. Returning empty structure.")
        return {"manual_predictions": {}}
    
    try:
        with open(MANUAL_PREDICTIONS_FILE, 'r') as f:
            data = json.load(f)
            return data.get("manual_predictions", {})
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {MANUAL_PREDICTIONS_FILE}: {e}")
        return {"manual_predictions": {}}
    except Exception as e:
        logger.error(f"An unexpected error occurred loading manual predictions: {e}")
        return {"manual_predictions": {}}

def save_manual_predictions(predictions: Dict[str, List[Dict[str, Any]]]):
    """
    Saves manual predictions to the configuration file.
    """
    try:
        with open(MANUAL_PREDICTIONS_FILE, 'w') as f:
            json.dump({"manual_predictions": predictions}, f, indent=2)
        logger.info(f"Manual predictions saved to {MANUAL_PREDICTIONS_FILE}.")
    except Exception as e:
        logger.error(f"Error saving manual predictions to {MANUAL_PREDICTIONS_FILE}: {e}")

def track_hits(
    prediction_date: str, 
    actual_open: str, 
    actual_close: str, 
    actual_jodi: str,
    predictions_data: Dict[str, List[Dict[str, Any]]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Tracks hits/misses for manual predictions for a given date.
    Updates the status of predictions for the specified date.
    
    Args:
        prediction_date (str): Date in YYYY-MM-DD format.
        actual_open (str): The actual open panel result.
        actual_close (str): The actual close panel result.
        actual_jodi (str): The actual jodi result.
        predictions_data (Dict): The full manual predictions data.
        
    Returns:
        Dict: The updated manual predictions data.
    """
    if prediction_date not in predictions_data:
        logger.info(f"No manual predictions found for {prediction_date}.")
        return predictions_data

    daily_predictions = predictions_data[prediction_date]
    updated_predictions = []

    normalized_actual_open = _normalize_value(actual_open)
    normalized_actual_close = _normalize_value(actual_close)
    normalized_actual_jodi = _normalize_value(actual_jodi) # For jodi "06" vs "6" needs care, but for now assuming direct int-like comparison

    for pred in daily_predictions:
        if pred['status'] in ["hit", "miss"]: # Skip already tracked predictions
            updated_predictions.append(pred)
            continue
            
        predicted_value = _normalize_value(str(pred['value'])) # Normalize predicted value
        is_hit = False

        if pred['type'] == 'single':
            if pred['panel'] == 'open' and predicted_value == normalized_actual_open:
                is_hit = True
            elif pred['panel'] == 'close' and predicted_value == normalized_actual_close:
                is_hit = True
        elif pred['type'] == 'jodi' and predicted_value == normalized_actual_jodi:
            is_hit = True
        
        pred['status'] = "hit" if is_hit else "miss"
        updated_predictions.append(pred)

    predictions_data[prediction_date] = updated_predictions
    return predictions_data


def get_tracking_summary(predictions_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Generates a summary of hit/miss rates for manual predictions.
    """
    total_predictions = 0
    total_hits = 0
    
    daily_summaries = {}

    for date, daily_preds in predictions_data.items():
        daily_total = len(daily_preds)
        daily_hits = sum(1 for p in daily_preds if p['status'] == 'hit')
        daily_misses = sum(1 for p in daily_preds if p['status'] == 'miss')
        daily_pending = sum(1 for p in daily_preds if p['status'] == 'pending')

        daily_summaries[date] = {
            "total": daily_total,
            "hits": daily_hits,
            "misses": daily_misses,
            "pending": daily_pending
        }
        
        total_predictions += daily_total
        total_hits += daily_hits

    hit_rate = (total_hits / total_predictions * 100) if total_predictions > 0 else 0.0

    return {
        "total_predictions": total_predictions,
        "total_hits": total_hits,
        "overall_hit_rate": hit_rate,
        "daily_breakdown": daily_summaries
    }
