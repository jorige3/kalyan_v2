from datetime import datetime, timedelta
from unittest.mock import patch

import pandas as pd
import pytest

from kalyan_v2.src.analysis.core_logic import generate_daily_summary_and_confidence
from kalyan_v2.src.analysis.hot_cold import HotColdAnalyzer
from kalyan_v2.src.analysis.sangam_analysis import SangamAnalyzer
from kalyan_v2.src.analysis.trend_window import TrendWindowAnalyzer
from kalyan_v2 import config # Import config from the package root

@pytest.fixture
def dummy_dataframe_for_analysis():
    """
    Provides a dummy DataFrame for testing analysis modules.
    Includes jodis and sangams for comprehensive testing.
    """
    dates = [datetime.now() - timedelta(days=i) for i in range(100, 0, -1)] # 100 days data, ascending date
    data = []
    for i, d in enumerate(dates):
        open_digit = i % 10
        close_digit = (i + 1) % 10
        jodi = f"{open_digit}{close_digit}"
        
        # Simple dummy sangams for testing purposes
        open_sangam = f"{open_digit}{i % 10}{(i + 2) % 10}"
        close_sangam = f"{close_digit}{(i + 3) % 10}{(i + 4) % 10}"

        data.append({
            "date": d,
            "open": open_digit,
            "close": close_digit,
            "jodi": jodi,
            "open_sangam": open_sangam,
            "close_sangam": close_sangam
        })
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    return df

# --- Tests for HotColdAnalyzer ---

def test_hot_cold_analyzer_init(dummy_dataframe_for_analysis):
    analyzer = HotColdAnalyzer(dummy_dataframe_for_analysis)
    assert not analyzer.df.empty

def test_hot_cold_analyzer_get_hot_jodis(dummy_dataframe_for_analysis):
    analyzer = HotColdAnalyzer(dummy_dataframe_for_analysis)
    hot_jodis = analyzer.get_hot_jodis(lookback_days=30, top_n=3)
    assert isinstance(hot_jodis, list)
    assert len(hot_jodis) <= 3
    for jodi in hot_jodis:
        assert isinstance(jodi, str)

def test_hot_cold_analyzer_get_due_cycles(dummy_dataframe_for_analysis):
    # Manipulate data to create a "due" jodi
    test_df = dummy_dataframe_for_analysis.copy()
    # Find a jodi to make due, e.g., '01'
    if not '01' in test_df['jodi'].values: # Ensure '01' exists for manipulation
        test_df.loc[len(test_df)] = {'date': datetime.now() - timedelta(days=100), 'open': 0, 'close': 1, 'jodi': '01', 'open_sangam': '123', 'close_sangam': '456'}
    test_df.loc[test_df['jodi'] == '01', 'date'] = datetime.now() - timedelta(days=50) # Make '01' appear 50 days ago
    analyzer = HotColdAnalyzer(test_df)
    due_cycles = analyzer.get_due_cycles(lookback_days=30, threshold_days=7) # Expecting this to be in a dict
    assert isinstance(due_cycles, dict)
    assert 'due_jodis' in due_cycles
    assert 'due_digits' in due_cycles
    assert isinstance(due_cycles['due_jodis'], list)
    assert isinstance(due_cycles['due_digits'], list)
    # Check if '01' is in due_jodis and its days overdue is correct (or close)
    if '01' in due_cycles['due_jodis']:
        assert due_cycles['due_jodis']['01'] >= 7

def test_hot_cold_analyzer_get_exhausted_numbers(dummy_dataframe_for_analysis):
    # Manipulate data to create an "exhausted" jodi
    test_df = dummy_dataframe_for_analysis.copy()
    # Make '23' appear 5 times in the last few days
    for i in range(5):
        test_df.loc[len(test_df) - 1 - i, 'jodi'] = '23'
    analyzer = HotColdAnalyzer(test_df)
    exhausted = analyzer.get_exhausted_numbers(lookback_days=10, consecutive_hits=3)
    assert isinstance(exhausted, dict)
    assert 'exhausted_jodis' in exhausted
    assert 'exhausted_digits' in exhausted
    assert isinstance(exhausted['exhausted_jodis'], list)
    assert isinstance(exhausted['exhausted_digits'], list)
    if '23' in exhausted['exhausted_jodis']:
        assert '23' in exhausted['exhausted_jodis']

# --- Tests for TrendWindowAnalyzer ---

def test_trend_window_analyzer_init(dummy_dataframe_for_analysis):
    analyzer = TrendWindowAnalyzer(dummy_dataframe_for_analysis)
    assert not analyzer.df.empty

def test_trend_window_analyzer_get_due_cycles_by_last_appearance(dummy_dataframe_for_analysis):
    # Manipulate data to create a "due" jodi for trend window
    test_df = dummy_dataframe_for_analysis.copy()
    # Find a jodi to make due, e.g., '02'
    if not '02' in test_df['jodi'].values: # Ensure '02' exists for manipulation
        test_df.loc[len(test_df)] = {'date': datetime.now() - timedelta(days=100), 'open': 0, 'close': 2, 'jodi': '02', 'open_sangam': '123', 'close_sangam': '456'}
    test_df.loc[test_df['jodi'] == '02', 'date'] = datetime.now() - timedelta(days=15) # Make '02' due
    analyzer = TrendWindowAnalyzer(test_df)
    due_cycles = analyzer.get_due_cycles_by_last_appearance(lookback_days=30, threshold_days=7)
    assert isinstance(due_cycles, dict)
    assert 'due_jodis' in due_cycles
    assert 'due_digits' in due_cycles
    assert isinstance(due_cycles['due_jodis'], list)
    assert isinstance(due_cycles['due_digits'], list)
    if '02' in due_cycles['due_jodis']:
        assert '02' in due_cycles['due_jodis']

def test_trend_window_analyzer_get_exhausted_numbers_by_streak(dummy_dataframe_for_analysis):
    # Manipulate data to create an "exhausted" jodi for trend window
    test_df = dummy_dataframe_for_analysis.copy()
    for i in range(4):
        test_df.loc[len(test_df) - 1 - i, 'jodi'] = '34'
    analyzer = TrendWindowAnalyzer(test_df)
    exhausted = analyzer.get_exhausted_numbers_by_streak(lookback_days=10, consecutive_hits=3)
    assert isinstance(exhausted, dict)
    assert 'exhausted_jodis' in exhausted
    assert 'exhausted_digits' in exhausted
    assert isinstance(exhausted['exhausted_jodis'], list)
    assert isinstance(exhausted['exhausted_digits'], list)
    if '34' in exhausted['exhausted_jodis']:
        assert '34' in exhausted['exhausted_jodis']

# --- Tests for SangamAnalyzer ---

def test_sangam_analyzer_init(dummy_dataframe_for_analysis):
    analyzer = SangamAnalyzer(dummy_dataframe_for_analysis)
    assert not analyzer.df.empty

def test_sangam_analyzer_get_hot_sangams(dummy_dataframe_for_analysis):
    analyzer = SangamAnalyzer(dummy_dataframe_for_analysis)
    hot_sangams = analyzer.get_hot_sangams(lookback_days=30, top_n=3)
    assert isinstance(hot_sangams, dict)
    assert 'hot_open_sangams' in hot_sangams
    assert 'hot_close_sangams' in hot_sangams
    assert isinstance(hot_sangams['hot_open_sangams'], list)
    assert isinstance(hot_sangams['hot_close_sangams'], list)
    assert len(hot_sangams['hot_open_sangams']) <= 3

def test_sangam_analyzer_get_due_sangams(dummy_dataframe_for_analysis):
    # Manipulate data to create a "due" open sangam
    test_df = dummy_dataframe_for_analysis.copy()
    # Find an open_sangam to make due, e.g., '002'
    if not '002' in test_df['open_sangam'].values: # Ensure '002' exists for manipulation
        test_df.loc[len(test_df)] = {'date': datetime.now() - timedelta(days=100), 'open': 0, 'close': 2, 'jodi': '02', 'open_sangam': '002', 'close_sangam': '456'}
    test_df.loc[test_df['open_sangam'] == '002', 'date'] = datetime.now() - timedelta(days=70) # Make '002' due
    analyzer = SangamAnalyzer(test_df)
    due_sangams = analyzer.get_due_sangams(lookback_days=60) # top_n is no longer used
    assert isinstance(due_sangams, dict)
    assert 'due_open_sangams' in due_sangams
    assert 'due_close_sangams' in due_sangams
    assert isinstance(due_sangams['due_open_sangams'], list)
    assert isinstance(due_sangams['due_close_sangams'], list)
    if '002' in due_sangams['due_open_sangams']:
        assert '002' in due_sangams['due_open_sangams']

# --- Tests for generate_daily_summary_and_confidence in core_logic.py ---

@pytest.fixture
def mock_config_weights():
    with patch('kalyan_v2.config.SCORING_WEIGHTS', {
        "HIGH_FREQUENCY_JODI": 1.0,
        "TREND_ALIGNED_JODI": 1.0,
        "EXTENDED_ABSENCE_JODI": 1.0,
        "EXHAUSTED_PATTERN_PENALTY": -1.0,
        "HIGH_FREQUENCY_OPEN_SANGAM": 1.0,
        "HIGH_FREQUENCY_CLOSE_SANGAM": 1.0,
        "EXTENDED_ABSENCE_OPEN_SANGAM": 1.0,
        "EXTENDED_ABSENCE_CLOSE_SANGAM": 1.0,
    }), patch('kalyan_v2.config.CONFIDENCE_THRESHOLDS', {
        "HIGH": 0.5,
        "MEDIUM": 0.1,
    }):
        yield

def test_generate_daily_summary_and_confidence_scoring(mock_config_weights):
    # Create dummy analysis results matching the new dictionary structure
    analysis_results = {
        "hot_jodis": ["12", "34"],
        "due_jodis": ["01"],
        "trend_due_jodis": ["02"],
        "exhausted_jodis": ["34"],
        "hot_open_sangams": ["123"],
        "hot_close_sangams": ["456"],
        "due_open_sangams": ["789"],
        "due_close_sangams": ["012"],
    }
    summary = generate_daily_summary_and_confidence(analysis_results)
    assert 'top_picks_with_confidence' in summary
    assert isinstance(summary['top_picks_with_confidence'], list)
    
    # Expected scores calculation:
    # "12": hot_jodi (5 * 1.0) = 5.0 -> High
    # "01": due_jodi (10 * 1.0) = 10.0 -> High
    # "02": trend_due_jodi (15 * 1.0) = 15.0 -> High
    # "34": hot_jodi (3 * 1.0) + exhausted (4 * -1.0) = 3 - 4 = -1.0 -> Low
    # "123": hot_open_sangam (2 * 1.0) = 2.0 -> Medium
    # "456": hot_close_sangam (3 * 1.0) = 3.0 -> High
    # "789": due_open_sangam (5 * 1.0) = 5.0 -> High
    # "012": due_close_sangam (8 * 1.0) = 8.0 -> High

    # Let's check for specific picks and their scores/confidence
    found_12 = False
    found_01 = False
    for pick in summary['top_picks_with_confidence']:
        if pick['value'] == '12':
            assert pick['score'] == 1.0
            assert pick['confidence'] == 'High'
            found_12 = True
        elif pick['value'] == '01':
            assert pick['score'] == 1.0
            assert pick['confidence'] == 'High'
            found_01 = True

    assert found_12, "Pick '12' not found or scored incorrectly"
    assert found_01, "Pick '01' not found or scored incorrectly"

    # Test analytical_confidence_score calculation
    # Count of High confidence picks in top_picks_with_confidence will be 5
    # min(10, 6 + 5) = min(10, 11) = 10
    assert len([s for s in summary['top_picks_with_confidence'] if s["confidence"] == "High"]) == 5
    assert summary["analytical_confidence_score"] == 10
