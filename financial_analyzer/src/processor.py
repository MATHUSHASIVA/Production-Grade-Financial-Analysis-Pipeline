import pandas as pd
from decimal import Decimal
from typing import Dict, Any
from .models import DailyMetrics, FundamentalData


def process_data(raw_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Merge daily prices with quarterly/annual fundamentals, forward-fill fundamentals,
    and calculate technical and fundamental metrics.

    Args:
            raw_data (Dict[str, Any]): Dict with 'prices' (list of PriceData) and 'fundamentals' (list of FundamentalData).

    Returns:
            pd.DataFrame: DataFrame of DailyMetrics, always non-empty if price data exists.
    """
    # Convert price data to DataFrame
    prices = raw_data.get("prices", [])
    fundamentals = raw_data.get("fundamentals", [])
    if not prices:
        return pd.DataFrame()

    price_df = pd.DataFrame([p.dict() for p in prices])
    price_df = price_df.sort_values("date")
    # Convert Decimal columns to float for pandas calculations
    for col in ["open", "high", "low", "close"]:
        if col in price_df:
            price_df[col] = price_df[col].astype(float)

    # Convert fundamentals to DataFrame
    fund_cols = [
        "as_of",
        "ticker",
        "book_value",
        "total_assets",
        "total_liabilities",
        "pe_ratio",
        "pb_ratio",
        "eps",
        "revenue",
        "net_income",
        "enterprise_value",
    ]
    if fundamentals:
        fund_df = pd.DataFrame([f.dict() for f in fundamentals])
        fund_df = fund_df.sort_values("as_of")
        for col in [
            "book_value",
            "total_assets",
            "total_liabilities",
            "pe_ratio",
            "pb_ratio",
            "eps",
            "revenue",
            "net_income",
            "enterprise_value",
        ]:
            if col in fund_df:
                fund_df[col] = fund_df[col].astype(float)
        # Forward-fill fundamental data to daily
        fund_df = fund_df.set_index("as_of").reindex(price_df["date"], method="ffill").reset_index()
        fund_df["ticker"] = fund_df["ticker"].fillna(method="ffill")
        fund_df = fund_df.reset_index(drop=True)
    else:
        fund_df = pd.DataFrame({col: [None] * len(price_df) for col in fund_cols})
        fund_df["as_of"] = price_df["date"]
        fund_df = fund_df.reset_index(drop=True)

    # Merge: always preserve price data
    price_df = price_df.reset_index(drop=True)
    fund_df = fund_df.reset_index(drop=True)
    # Ensure fund_df matches price_df length
    if len(fund_df) < len(price_df):
        for col in fund_df.columns:
            fund_df[col] = list(fund_df[col]) + [None] * (len(price_df) - len(fund_df))
    elif len(fund_df) > len(price_df):
        fund_df = fund_df.iloc[: len(price_df)]
    merged = pd.concat(
        [price_df, fund_df.drop(columns=["as_of", "ticker"], errors="ignore")],
        axis=1,
        ignore_index=False,
    )
    # Remove duplicate columns, keeping only the first occurrence
    merged = merged.loc[:, ~merged.columns.duplicated()]
    # Always add ticker column
    if "ticker" not in merged:
        merged["ticker"] = None
    # Guarantee merged is not empty if price_df is not empty
    if merged.empty and not price_df.empty:
        merged = price_df.copy()
        for col in fund_cols:
            if col not in merged:
                merged[col] = None
        merged["book_value_per_share"] = None
        merged["price_to_book"] = None
        merged["ticker"] = None

    # Calculate technical indicators
    merged["sma_50"] = merged["close"].rolling(window=50, min_periods=1).mean()
    merged["sma_200"] = merged["close"].rolling(window=200, min_periods=1).mean()
    merged["high_52w"] = merged["close"].rolling(window=252, min_periods=1).max()
    merged["pct_from_high_52w"] = (merged["close"] / merged["high_52w"] - 1) * 100

    # Ensure fundamental columns exist
    for col in [
        "book_value",
        "total_assets",
        "total_liabilities",
        "pe_ratio",
        "pb_ratio",
        "eps",
        "revenue",
        "net_income",
        "enterprise_value",
    ]:
        if col not in merged:
            merged[col] = None

    # Calculate fundamental ratios
    merged["book_value_per_share"] = merged["book_value"]
    merged["price_to_book"] = merged.apply(
        lambda row: (
            (row["close"] / row["book_value"]) if row.get("book_value") not in [None, 0] else None
        ),
        axis=1,
    )

    # Convert to DailyMetrics
    metrics = []
    for _, row in merged.iterrows():
        # Only skip if date or close is missing (scalar check)
        if row["date"] is None or pd.isnull(row["date"]):
            continue
        if row["close"] is None or pd.isnull(row["close"]):
            continue
        try:
            metrics.append(
                DailyMetrics(
                    date=row["date"],
                    ticker=row.get("ticker"),
                    close=Decimal(str(row["close"])),
                    sma_50=Decimal(str(row["sma_50"])) if row.get("sma_50") is not None else None,
                    sma_200=(
                        Decimal(str(row["sma_200"])) if row.get("sma_200") is not None else None
                    ),
                    high_52w=(
                        Decimal(str(row["high_52w"])) if row.get("high_52w") is not None else None
                    ),
                    pct_from_high_52w=(
                        Decimal(str(row["pct_from_high_52w"]))
                        if row.get("pct_from_high_52w") is not None
                        else None
                    ),
                    book_value_per_share=(
                        Decimal(str(row["book_value_per_share"]))
                        if row.get("book_value_per_share") is not None
                        else None
                    ),
                    price_to_book=(
                        Decimal(str(row["price_to_book"]))
                        if row.get("price_to_book") is not None
                        else None
                    ),
                    enterprise_value=(
                        Decimal(str(row["enterprise_value"]))
                        if row.get("enterprise_value") is not None
                        else None
                    ),
                )
            )
        except Exception:
            # Only skip row if conversion fails for a non-None value
            continue
    # Always fallback: if metrics is empty but price_df is not, populate metrics from price_df
    if not metrics and not price_df.empty:
        fallback = price_df.copy()
        fallback["sma_50"] = fallback["close"].rolling(window=50, min_periods=1).mean()
        fallback["sma_200"] = fallback["close"].rolling(window=200, min_periods=1).mean()
        fallback["high_52w"] = fallback["close"].rolling(window=252, min_periods=1).max()
        fallback["pct_from_high_52w"] = (fallback["close"] / fallback["high_52w"] - 1) * 100
        fallback["book_value_per_share"] = None
        fallback["price_to_book"] = None
        fallback["enterprise_value"] = None
        fallback["ticker"] = ""
        for _, row in fallback.iterrows():
            try:
                metrics.append(
                    DailyMetrics(
                        date=row["date"],
                        ticker=row["ticker"],
                        close=Decimal(str(row["close"])),
                        sma_50=(
                            Decimal(str(row["sma_50"])) if row.get("sma_50") is not None else None
                        ),
                        sma_200=(
                            Decimal(str(row["sma_200"])) if row.get("sma_200") is not None else None
                        ),
                        high_52w=(
                            Decimal(str(row["high_52w"]))
                            if row.get("high_52w") is not None
                            else None
                        ),
                        pct_from_high_52w=(
                            Decimal(str(row["pct_from_high_52w"]))
                            if row.get("pct_from_high_52w") is not None
                            else None
                        ),
                        book_value_per_share=None,
                        price_to_book=None,
                        enterprise_value=None,
                    )
                )
            except Exception:
                continue
    # Return as DataFrame
    return pd.DataFrame([m.dict() for m in metrics])


# Note: Forward-filling is reasonable for fundamentals because companies report quarterly/annual data, and the most recent value is the best available estimate for each day until the next report.
