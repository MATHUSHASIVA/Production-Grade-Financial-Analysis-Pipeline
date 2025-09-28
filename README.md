# Financial Analyzer

A production-grade, modular financial analysis pipeline for screening stocks, calculating technical/fundamental metrics, detecting signals, and exporting results. Built for robustness, extensibility, and real-world data challenges.

## Features
- Fetches 5 years of daily OHLCV and fundamental data (via yfinance)
- Cleans, validates, and merges price and fundamental data
- Calculates technical indicators (SMA-50, SMA-200, 52-week high, % from high)
- Computes fundamental ratios (book value per share, price-to-book, etc.)
- Detects Golden Cross and Death Cross signals
- Stores results in a local SQLite database (via SQLAlchemy)
- Exports results to JSON
- CLI interface (Typer)
- Robust error handling and test coverage

## Installation
```bash
# Recommended: use uv for fast, modern dependency management
uv pip install   
uv add pandas yfinance pydantic "typer[all]" sqlalchemy pyyaml
uv add --dev ruff pytest
```

## Usage
Run the full pipeline for a ticker and export results to JSON:
```bash
python -m financial_analyzer.src.main --ticker NVDA --output nvda_results.json
```

## Project Structure
- `src/data_fetcher.py` — Fetches and validates raw price/fundamental data
- `src/processor.py` — Merges, cleans, and computes all metrics
- `src/signals.py` — Detects technical signals (crossovers)
- `src/database.py` — ORM models and DB persistence
- `src/models.py` — Pydantic schemas for all data types
- `src/main.py` — Typer CLI orchestrator
- `tests/` — Pytest-based unit tests for all modules


## Testing
```bash
pytest financial_analyzer/tests --disable-warnings -v
```

## Database Schema & Output Example
Results are stored in a local SQLite database (`results.db`) with a table structure similar to:

| Column                | Type    | Description                       |
|-----------------------|---------|-----------------------------------|
| id                    | INTEGER | Primary key                       |
| ticker                | TEXT    | Stock ticker                      |
| date                  | DATE    | Date of record                    |
| sma_50                | REAL    | 50-day simple moving average      |
| sma_200               | REAL    | 200-day simple moving average     |
| high_52w              | REAL    | 52-week high                      |
| pct_from_high         | REAL    | % from 52-week high               |
| book_value_per_share  | REAL    | Book value per share              |
| price_to_book         | REAL    | Price-to-book ratio               |
| golden_cross_dates    | TEXT    | Golden cross dates (JSON array)   |
| death_cross_dates     | TEXT    | Death cross dates (JSON array)    |
| fundamentals          | TEXT    | JSON-encoded fundamentals         |

Sample JSON output: see `output/sample_output.json`.

## Design Decisions
- **Forward-fill**: Missing values in time series are forward-filled to maintain continuity for technical indicators.
- **Missing Data**: If fundamental data is missing, the pipeline logs a warning and continues with available data.
- **Idempotency**: Running the pipeline multiple times for the same ticker/date will not create duplicate DB entries.
- **Ticker Handling**: Supports both US (e.g., NVDA) and India (e.g., TCS.NS) tickers; ticker is always validated.

## Data Quality Notes
- Data is fetched from yfinance and may be subject to provider limitations or missing fields.
- All calculations are robust to missing or partial data; warnings are logged for any data issues.
- Results are only as accurate as the source data.

## Testing Instructions (India & US, Old & Recent Stocks)
To ensure robustness, run tests and the CLI for a variety of tickers:

```bash
# US stock, recent: NVIDIA
python -m financial_analyzer.src.main --ticker NVDA --output output/nvda.json
# US stock, old: IBM
python -m financial_analyzer.src.main --ticker IBM --output output/ibm.json
# India stock, recent: TCS
python -m financial_analyzer.src.main --ticker TCS.NS --output output/tcs.json
# India stock, old: INFY
python -m financial_analyzer.src.main --ticker INFY.NS --output output/infy.json
```
Check the generated JSON files and database for expected results.



