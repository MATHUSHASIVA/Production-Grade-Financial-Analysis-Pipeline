import typer
import logging
import json
import pandas as pd
from pathlib import Path
from .data_fetcher import fetch_stock_data
from .processor import process_data
from .signals import detect_golden_crossover, detect_death_cross
from .database import init_db, get_engine, save_ticker, save_daily_metrics, save_signal_events
from .models import ExportData, SignalEvent
from sqlalchemy.orm import sessionmaker

app = typer.Typer()


@app.command()
def main(
    ticker: str = typer.Option(..., help="Stock ticker symbol (e.g., NVDA, RELIANCE.NS)"),
    output: str = typer.Option(..., help="Output file path (JSON or CSV)"),
    start: str = typer.Option(None, help="Start date (YYYY-MM-DD) for analysis"),
    end: str = typer.Option(None, help="End date (YYYY-MM-DD) for analysis"),
    format: str = typer.Option("json", help="Output format: json or csv"),
):
    """
    Run the full financial analysis pipeline for a given ticker.

    Args:
            ticker (str): Stock ticker symbol (e.g., NVDA, RELIANCE.NS)
            output (str): Output file path
            start (str): Start date (YYYY-MM-DD)
            end (str): End date (YYYY-MM-DD)
            format (str): Output format: json or csv
    """
    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.info(f"Starting analysis for {ticker}")

    # Initialize DB
    db_path = "financial_data.db"
    engine = init_db(db_path)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Fetch and validate data
    raw_data = fetch_stock_data(ticker)
    if not raw_data["prices"]:
        logging.error("No price data available. Exiting.")
        raise typer.Exit(code=1)

    # Optionally filter by date range
    if start or end:
        import datetime

        start_dt = datetime.date.fromisoformat(start) if start else None
        end_dt = datetime.date.fromisoformat(end) if end else None
        raw_data["prices"] = [
            p
            for p in raw_data["prices"]
            if (not start_dt or p.date >= start_dt) and (not end_dt or p.date <= end_dt)
        ]
        if raw_data["fundamentals"]:
            raw_data["fundamentals"] = [
                f
                for f in raw_data["fundamentals"]
                if (not start_dt or f.as_of >= start_dt) and (not end_dt or f.as_of <= end_dt)
            ]

    # Save ticker info
    save_ticker(session, ticker)

    # Process and calculate metrics
    metrics_df = process_data(raw_data)
    if metrics_df.empty:
        logging.error("No metrics calculated. Exiting.")
        raise typer.Exit(code=1)
    save_daily_metrics(session, ticker, metrics_df)

    # Detect signals
    golden_cross_dates = detect_golden_crossover(metrics_df)
    death_cross_dates = detect_death_cross(metrics_df)
    save_signal_events(session, ticker, "golden_cross", golden_cross_dates)
    save_signal_events(session, ticker, "death_cross", death_cross_dates)

    # Prepare export data
    export = ExportData(
        ticker=ticker,
        price_data=raw_data["prices"],
        fundamentals=raw_data["fundamentals"],
        daily_metrics=[row for row in metrics_df.to_dict(orient="records")],
        signals=[
            SignalEvent(date=d, ticker=ticker, signal_type="golden_cross")
            for d in golden_cross_dates
        ]
        + [
            SignalEvent(date=d, ticker=ticker, signal_type="death_cross") for d in death_cross_dates
        ],
    )

    # Export to JSON or CSV
    if format.lower() == "json":
        with open(output, "w") as f:
            json.dump(export.dict(), f, default=str, indent=2)
        logging.info(f"Analysis complete. Results saved to {output}")
    elif format.lower() == "csv":
        metrics_df.to_csv(output, index=False)
        logging.info(f"Metrics CSV saved to {output}")
    else:
        logging.error("Unsupported output format. Use 'json' or 'csv'.")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
