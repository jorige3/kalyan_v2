import os
import pandas as pd
import pytest
from kalyan_v2.src.engine.kalyan_engine import KalyanEngine

# Fixture to create a dummy kalyan.csv for testing
@pytest.fixture
def dummy_kalyan_csv(tmp_path):
    csv_path = tmp_path / "kalyan.csv"
    dummy_data = {
        'date': pd.to_datetime([f'2023-01-{i:02d}' for i in range(1, 31)]), # 30 days
        'open': [str(i % 10) for i in range(30)],
        'close': [str((i + 1) % 10) for i in range(30)],
        'jodi': [f'{i % 10}{(i + 1) % 10}' for i in range(30)],
        'open_panel': [f'{i % 10}{ (i + 2) % 10}{(i + 3) % 10}' for i in range(30)],
        'close_panel': [f'{ (i + 4) % 10}{(i + 5) % 10}{(i + 1) % 10}' for i in range(30)],
        'sangam': [f'{i % 10}{(i + 2) % 10}{(i + 3) % 10}-{(i + 4) % 10}{(i + 5) % 10}{(i + 1) % 10}' for i in range(30)],
    }
    pd.DataFrame(dummy_data).to_csv(csv_path, index=False)
    return str(csv_path)

# Fixture to ensure no kalyan.csv exists
@pytest.fixture
def no_kalyan_csv(tmp_path):
    csv_path = tmp_path / "kalyan.csv"
    # Ensure it doesn't exist before test
    if os.path.exists(csv_path):
        os.remove(csv_path)
    return str(csv_path)

def test_kalyan_engine_loads_existing_data(dummy_kalyan_csv):
    engine = KalyanEngine(dummy_kalyan_csv)
    assert not engine.df.empty
    assert len(engine.df) == 30
    expected_cols = ['date', 'open', 'close', 'jodi', 'open_panel', 'close_panel', 'sangam']
    assert all(col in engine.df.columns for col in expected_cols)
    assert pd.to_datetime(engine.df['date'].iloc[-1]).year >= 2023

def test_kalyan_engine_generates_dummy_data_if_no_csv(no_kalyan_csv):
    engine = KalyanEngine(no_kalyan_csv)
    assert not engine.df.empty
    assert len(engine.df) > 0  # Should generate some dummy data
    expected_cols = ['date', 'open', 'close', 'jodi', 'open_panel', 'close_panel', 'sangam']
    assert all(col in engine.df.columns for col in expected_cols)
    assert pd.to_datetime(engine.df['date'].iloc[-1]).year >= 2023

def test_get_historical_data(dummy_kalyan_csv):
    engine = KalyanEngine(dummy_kalyan_csv)
    df = engine.get_historical_data()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty

def test_get_all_jodis(dummy_kalyan_csv):
    engine = KalyanEngine(dummy_kalyan_csv)
    jodis = engine.get_all_jodis()
    assert isinstance(jodis, list)
    assert len(jodis) == 10
    assert "01" in jodis and "90" in jodis
