"""
Refinement Script: Kalyan Ensemble Weight Optimization v2.2
Performs a sweep of weight combinations against historical data to maximize hit rates.
"""
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import config
from src.backtest.rolling_backtester import RollingBacktester
from src.data.loader import DataLoader
from src.models.digit_model import DigitMomentumModel
from src.models.ensemble_model import EnsembleModel
from src.models.gap_model import GapClusterModel
from src.models.heat_model import HeatModel
from src.models.mirror_model import MirrorPairModel
from src.models.momentum_model import MomentumModel


def optimize():
    print("\n" + "="*60)
    print("🧪 QUANTITATIVE WEIGHT OPTIMIZATION - STARTING")
    print("="*60)

    # 1. Load Data
    loader = DataLoader(config.DATA_PATH)
    df = loader.load_data()
    print(f"Data Loaded: {len(df)} records for simulation.")

    # 2. Define Sub-models (cached)
    sub_models = {
        'heat': HeatModel(),
        'digit': DigitMomentumModel(window=config.DIGIT_WINDOW),
        'gap': GapClusterModel(min_gap=config.GAP_MIN, max_gap=config.GAP_MAX),
        'momentum': MomentumModel(momentum_window=config.MOMENTUM_WINDOW),
        'mirror': MirrorPairModel(window=config.MIRROR_WINDOW)
    }

    # 3. Define Weight Combinations to Test
    # [heat, digit, gap, momentum, mirror]
    test_weights = [
        {'heat': 0.35, 'digit': 0.25, 'gap': 0.20, 'momentum': 0.10, 'mirror': 0.10}, # Current (Balanced)
        {'heat': 0.50, 'digit': 0.20, 'gap': 0.15, 'momentum': 0.10, 'mirror': 0.05}, # Heat-Heavy
        {'heat': 0.25, 'digit': 0.40, 'gap': 0.15, 'momentum': 0.10, 'mirror': 0.10}, # Digit-Heavy
        {'heat': 0.30, 'digit': 0.20, 'gap': 0.30, 'momentum': 0.10, 'mirror': 0.10}, # Gap-Heavy
        {'heat': 0.40, 'digit': 0.20, 'gap': 0.10, 'momentum': 0.15, 'mirror': 0.15}  # Momentum-Heavy
    ]

    best_hit_rate = 0.0
    best_weights = None
    all_results = []

    # 4. Run Backtests
    for i, weights in enumerate(test_weights, 1):
        print(f"\nSimulation {i}/{len(test_weights)}: Weights = {weights}")
        ensemble_model = EnsembleModel(models=sub_models, weights=weights)
        
        # We use a larger warmup for long-term simulation robustness
        backtester = RollingBacktester(ensemble_model, warmup=100)
        results = backtester.run(df)
        
        if results:
            hit5 = results['hit_rate_top5'] * 100
            hit10 = results['hit_rate_top10'] * 100
            print(f"-> Top 5 Hit Rate: {hit5:.2f}% | Top 10 Hit Rate: {hit10:.2f}%")
            
            all_results.append({
                'id': i,
                'weights': weights,
                'hit5': hit5,
                'hit10': hit10
            })
            
            # Optimization Goal: Maximize Top 10 hit rate
            if hit10 > best_hit_rate:
                best_hit_rate = hit10
                best_weights = weights

    # 5. Report Findings
    print("\n" + "="*60)
    print("🏆 OPTIMIZATION SUMMARY")
    print("="*60)
    print(f"Winning Weights (Max Top 10): {best_weights}")
    print(f"Best Top 10 Performance: {best_hit_rate:.2f}%")
    print("-" * 60)
    
    # Simple recommendation
    print("\nRecommendation: Update config.py with these ENSEMBLE_WEIGHTS for production.")
    print("="*60 + "\n")

if __name__ == "__main__":
    optimize()
