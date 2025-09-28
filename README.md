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
uv pip install   # for legacy support
# or, for modern workflow:
uv venv .venv
uv pip install -e .
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

## Configuration
- Edit `config.yaml.example` to set up custom parameters (if needed)

## Testing
```bash
pytest tests --disable-warnings -v
```

## Extending
- Add new technical/fundamental metrics in `processor.py`
- Add new signals in `signals.py`
- Add new CLI commands in `main.py`

## Requirements
All dependencies are tracked in `pyproject.toml` (managed by uv). You do not need `requirements.txt` if using uv.

## License
MIT
