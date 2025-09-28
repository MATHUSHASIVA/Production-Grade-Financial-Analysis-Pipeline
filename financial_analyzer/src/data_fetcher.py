import yfinance as yf
import pandas as pd
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any, List
from pydantic import ValidationError
from .models import PriceData, FundamentalData
import logging


def fetch_stock_data(ticker: str) -> Dict[str, Any]:
    """
    Fetch 5 years of daily OHLCV and fundamental data for a ticker using yfinance.
    Returns dict with 'prices' (list of PriceData) and 'fundamentals' (list of FundamentalData).
    Handles API errors, timeouts, and logs data quality issues.

    Args:
            ticker (str): Stock ticker symbol (e.g., 'AAPL', 'RELIANCE.NS').

    Returns:
            Dict[str, Any]: {'prices': [...], 'fundamentals': [...]}
    """
    result = {"prices": [], "fundamentals": []}
    try:
        stock = yf.Ticker(ticker)
        # Fetch daily OHLCV (5y)
        df = stock.history(period="5y", interval="1d")
        if df.empty:
            logging.error(f"No price data for {ticker}")
            return result
        df = df.reset_index()
        for _, row in df.iterrows():
            try:
                price = PriceData(
                    date=(
                        row["Date"].date()
                        if hasattr(row["Date"], "date")
                        else pd.to_datetime(row["Date"]).date()
                    ),
                    open=Decimal(str(row["Open"])),
                    high=Decimal(str(row["High"])),
                    low=Decimal(str(row["Low"])),
                    close=Decimal(str(row["Close"])),
                    volume=int(row["Volume"]),
                )
                result["prices"].append(price)
            except (ValidationError, Exception) as e:
                logging.warning(f"Invalid price row for {ticker} on {row['Date']}: {e}")

        # Fundamental data strategy
        fundamentals = []
        source = None
        # Try quarterly balance sheet
        try:
            qbs = stock.quarterly_balance_sheet
            if not qbs.empty:
                source = "quarterly"
                for col in qbs.columns:
                    fundamentals.append(
                        FundamentalData(
                            as_of=(
                                col.date() if hasattr(col, "date") else pd.to_datetime(col).date()
                            ),
                            ticker=ticker,
                            book_value=(
                                Decimal(str(qbs.at["Total Stockholder Equity", col]))
                                if "Total Stockholder Equity" in qbs.index
                                and pd.notna(qbs.at["Total Stockholder Equity", col])
                                else None
                            ),
                            total_assets=(
                                Decimal(str(qbs.at["Total Assets", col]))
                                if "Total Assets" in qbs.index
                                and pd.notna(qbs.at["Total Assets", col])
                                else None
                            ),
                            total_liabilities=(
                                Decimal(str(qbs.at["Total Liab", col]))
                                if "Total Liab" in qbs.index and pd.notna(qbs.at["Total Liab", col])
                                else None
                            ),
                            pe_ratio=None,
                            pb_ratio=None,
                            eps=None,
                            revenue=None,
                            net_income=None,
                            enterprise_value=None,
                            source=source,
                        )
                    )
        except Exception as e:
            logging.info(f"Quarterly balance sheet not available for {ticker}: {e}")

        # Fallback: annual balance sheet
        if not fundamentals:
            try:
                abs_ = stock.balance_sheet
                if not abs_.empty:
                    source = "annual"
                    for col in abs_.columns:
                        fundamentals.append(
                            FundamentalData(
                                as_of=(
                                    col.date()
                                    if hasattr(col, "date")
                                    else pd.to_datetime(col).date()
                                ),
                                ticker=ticker,
                                book_value=(
                                    Decimal(str(abs_.at["Total Stockholder Equity", col]))
                                    if "Total Stockholder Equity" in abs_.index
                                    and pd.notna(abs_.at["Total Stockholder Equity", col])
                                    else None
                                ),
                                total_assets=(
                                    Decimal(str(abs_.at["Total Assets", col]))
                                    if "Total Assets" in abs_.index
                                    and pd.notna(abs_.at["Total Assets", col])
                                    else None
                                ),
                                total_liabilities=(
                                    Decimal(str(abs_.at["Total Liab", col]))
                                    if "Total Liab" in abs_.index
                                    and pd.notna(abs_.at["Total Liab", col])
                                    else None
                                ),
                                pe_ratio=None,
                                pb_ratio=None,
                                eps=None,
                                revenue=None,
                                net_income=None,
                                enterprise_value=None,
                                source=source,
                            )
                        )
            except Exception as e:
                logging.info(f"Annual balance sheet not available for {ticker}: {e}")

        # Fallback: info dict
        if not fundamentals:
            try:
                info = stock.info
                source = "info"
                fundamentals.append(
                    FundamentalData(
                        as_of=datetime.now().date(),
                        ticker=ticker,
                        book_value=(
                            Decimal(str(info.get("bookValue")))
                            if info.get("bookValue") is not None
                            else None
                        ),
                        total_assets=None,
                        total_liabilities=None,
                        pe_ratio=(
                            Decimal(str(info.get("trailingPE")))
                            if info.get("trailingPE") is not None
                            else None
                        ),
                        pb_ratio=(
                            Decimal(str(info.get("priceToBook")))
                            if info.get("priceToBook") is not None
                            else None
                        ),
                        eps=(
                            Decimal(str(info.get("trailingEps")))
                            if info.get("trailingEps") is not None
                            else None
                        ),
                        revenue=(
                            Decimal(str(info.get("totalRevenue")))
                            if info.get("totalRevenue") is not None
                            else None
                        ),
                        net_income=(
                            Decimal(str(info.get("netIncomeToCommon")))
                            if info.get("netIncomeToCommon") is not None
                            else None
                        ),
                        enterprise_value=(
                            Decimal(str(info.get("enterpriseValue")))
                            if info.get("enterpriseValue") is not None
                            else None
                        ),
                        source=source,
                    )
                )
            except Exception as e:
                logging.error(f"No fundamental data for {ticker}: {e}")

        result["fundamentals"] = fundamentals
        return result
    except Exception as e:
        logging.error(f"Failed to fetch data for {ticker}: {e}")
        return result
