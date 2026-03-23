from typing import Any, Dict, List

import pandas as pd

from src.utils.logger import setup_logger


class EnsembleModel:
    """
    Combines multiple models into a single weighted score.
    Final Score = 0.35 * Heat + 0.25 * Digit + 0.20 * Gap + 0.20 * Mirror (or Momentum)
    """
    
    def __init__(self, models: Dict[str, Any], weights: Dict[str, float]):
        self.models = models
        self.weights = weights
        self.logger = setup_logger()

    def predict(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Calculates weighted scores from all sub-models.
        Each sub-model must return a list of {value, score}.
        """
        if df.empty: return []

        # Get scores from all sub-models
        model_predictions = {}
        for name, model in self.models.items():
            self.logger.debug(f"Calculating scores for sub-model: {name}")
            preds = model.predict(df)
            # Create a lookup for quick access: { 'XX': score }
            model_predictions[name] = {p['value']: p for p in preds}

        all_jodis = [f"{i:02d}" for i in range(100)]
        ensemble_results = []
        
        for jodi in all_jodis:
            final_score = 0.0
            metrics_summary = {}
            
            # Combine weighted sub-scores
            for name, weight in self.weights.items():
                if name in model_predictions:
                    sub_pred = model_predictions[name].get(jodi)
                    if sub_pred:
                        sub_score = sub_pred['score']
                        final_score += sub_score * weight
                        
                        # Store specific metrics from sub-models for reporting
                        metrics_summary[name] = sub_pred.get('metrics', {})
                        
            ensemble_results.append({
                'value': jodi,
                'score': float(final_score),
                'metrics': metrics_summary
            })

        # Sort by final ensemble score descending
        ensemble_results.sort(key=lambda x: x['score'], reverse=True)
        return ensemble_results
