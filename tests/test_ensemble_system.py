import pandas as pd
import pytest

from src.backtest.rolling_backtester import RollingBacktester
from src.models.digit_model import DigitMomentumModel
from src.models.ensemble_model import EnsembleModel
from src.models.gap_model import GapClusterModel
from src.models.heat_model import HeatModel
from src.models.mirror_model import MirrorPairModel


@pytest.fixture
def sample_data():
    """Generates a small valid dataframe for testing."""
    data = []
    # 50 days of data
    for i in range(50):
        data.append({
            'date': pd.Timestamp('2024-01-01') + pd.Timedelta(days=i),
            'jodi': f"{i%10}{(i+1)%10}", # Cycle jodis
            'open_panel': '123',
            'close_panel': '456',
            'sangam': '123-456'
        })
    return pd.DataFrame(data)

def test_heat_model(sample_data):
    model = HeatModel(recent_window=10, long_term_window=30)
    preds = model.predict(sample_data)
    assert len(preds) == 100
    assert 'value' in preds[0]
    assert 'score' in preds[0]
    # Check sorting
    assert preds[0]['score'] >= preds[-1]['score']

def test_digit_model(sample_data):
    model = DigitMomentumModel(window=10)
    preds = model.predict(sample_data)
    assert len(preds) == 100
    assert preds[0]['score'] >= 0.0

def test_gap_model(sample_data):
    model = GapClusterModel(min_gap=5, max_gap=15)
    preds = model.predict(sample_data)
    # At least one jodi should be in the gap range in this artificial data
    assert any(p['score'] > 0 for p in preds)

def test_mirror_model(sample_data):
    model = MirrorPairModel(window=10)
    preds = model.predict(sample_data)
    assert len(preds) == 100

def test_ensemble_model(sample_data):
    sub_models = {
        'heat': HeatModel(),
        'digit': DigitMomentumModel()
    }
    weights = {'heat': 0.6, 'digit': 0.4}
    ensemble = EnsembleModel(models=sub_models, weights=weights)
    preds = ensemble.predict(sample_data)
    assert len(preds) == 100
    assert 'heat' in preds[0]['metrics']
    assert 'digit' in preds[0]['metrics']

def test_backtester(sample_data):
    model = HeatModel(recent_window=5, long_term_window=10)
    # Use small warmup for test speed
    backtester = RollingBacktester(model, warmup=40)
    results = backtester.run(sample_data)
    assert 'hit_rate_top5' in results
    assert results['total_days'] == 10 # 50 - 40
