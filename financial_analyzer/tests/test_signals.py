import pandas as pd
from financial_analyzer.src.signals import detect_golden_crossover, detect_death_cross

def test_golden_and_death_cross():
	# Simulate SMA data
	df = pd.DataFrame({
		'date': pd.date_range('2023-01-01', periods=5),
		'sma_50': [1, 2, 3, 5, 7],
		'sma_200': [2, 2, 2, 2, 2]
	})
	golden = detect_golden_crossover(df)
	death = detect_death_cross(df)
	assert isinstance(golden, list)
	assert isinstance(death, list)
	


def test_golden_cross_edge_cases():
	# No SMA columns
	df = pd.DataFrame({'date': pd.date_range('2023-01-01', periods=3)})
	golden = detect_golden_crossover(df)
	assert golden == []
	# Not enough data
	df = pd.DataFrame({'date': pd.date_range('2023-01-01', periods=1), 'sma_50': [1], 'sma_200': [2]})
	golden = detect_golden_crossover(df)
	assert golden == []
	
def test_multiple_crosses():
	# Simulate multiple golden and death crosses
	df = pd.DataFrame({
		'date': pd.date_range('2023-01-01', periods=10),
		'sma_50': [1, 2, 3, 4, 5, 4, 3, 4, 5, 6],
		'sma_200': [2, 2, 2, 2, 2, 3, 4, 3, 2, 1]
	})
	golden = detect_golden_crossover(df)
	death = detect_death_cross(df)
	# There should be at least one golden and one death cross
	assert any(isinstance(d, pd.Timestamp) or isinstance(d, pd._libs.tslibs.timestamps.Timestamp) for d in golden)
	assert any(isinstance(d, pd.Timestamp) or isinstance(d, pd._libs.tslibs.timestamps.Timestamp) for d in death)

def test_no_crosses():
    # SMA lines never cross
    df = pd.DataFrame({
        'date': pd.date_range('2023-01-01', periods=5),
        'sma_50': [1, 1, 1, 1, 1],
        'sma_200': [2, 2, 2, 2, 2]
    })
    golden = detect_golden_crossover(df)
    death = detect_death_cross(df)
    assert golden == []
    assert death == []

def test_nan_values():
    # SMA columns with NaN values
    df = pd.DataFrame({
        'date': pd.date_range('2023-01-01', periods=5),
        'sma_50': [1, None, 3, None, 5],
        'sma_200': [2, 2, None, 4, None]
    })
    golden = detect_golden_crossover(df)
    death = detect_death_cross(df)
    assert golden == []
    assert death == []

def test_insufficient_data():
    # Only one valid data point
    df = pd.DataFrame({
        'date': pd.date_range('2023-01-01', periods=3),
        'sma_50': [1, None, None],
        'sma_200': [2, None, None]
    })
    golden = detect_golden_crossover(df)
    death = detect_death_cross(df)
    assert golden == []
    assert death == []

