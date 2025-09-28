import pandas as pd
from financial_analyzer.src.processor import process_data
from financial_analyzer.src.models import PriceData, FundamentalData

def test_sma_and_metrics():
	# Minimal price and fundamental data
	raw_data = {
		'prices': [
			PriceData(date=pd.Timestamp('2023-01-01').date(), open=10, high=12, low=9, close=11, volume=1000),
			PriceData(date=pd.Timestamp('2023-01-02').date(), open=11, high=13, low=10, close=12, volume=1100),
			PriceData(date=pd.Timestamp('2023-01-03').date(), open=12, high=14, low=11, close=13, volume=1200),
		],
		'fundamentals': [
			FundamentalData(as_of=pd.Timestamp('2022-12-31').date(), ticker='TEST', book_value=10, total_assets=100, total_liabilities=50, pe_ratio=15, pb_ratio=1.1, eps=2, revenue=1000, net_income=100, enterprise_value=200, source='quarterly')
		]
	}
	df = process_data(raw_data)
	assert not df.empty
	assert 'sma_50' in df.columns
	assert df['sma_50'].iloc[-1] > 0
	

def test_empty_prices():
	from financial_analyzer.src.models import PriceData, FundamentalData
	raw_data = {'prices': [], 'fundamentals': []}
	df = process_data(raw_data)
	assert df.empty

def test_missing_fundamentals():
	from financial_analyzer.src.models import PriceData
	raw_data = {
		'prices': [
			PriceData(date=pd.Timestamp('2023-01-01').date(), open=10, high=12, low=9, close=11, volume=1000)
		],
		'fundamentals': []
	}
	df = process_data(raw_data)
	assert not df.empty
	assert 'book_value_per_share' in df.columns

