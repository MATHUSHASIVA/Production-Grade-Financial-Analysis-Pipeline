import pandas as pd
from typing import List
import logging


def detect_golden_crossover(df: pd.DataFrame) -> List[pd.Timestamp]:
    """
    Detect Golden Crossovers (50-day SMA crosses above 200-day SMA).
    Returns a list of crossover dates.
    Handles edge cases (insufficient data, NaN values).

    Args:
            df (pd.DataFrame): DataFrame with 'sma_50' and 'sma_200' columns.

    Returns:
            List[pd.Timestamp]: List of crossover dates.
    """
    if "sma_50" not in df or "sma_200" not in df:
        logging.warning("SMA columns missing for crossover detection.")
        return []
    # Ensure no NaNs for comparison
    mask = df["sma_50"].notna() & df["sma_200"].notna()
    if mask.sum() < 2:
        return []
    sma_50 = df.loc[mask, "sma_50"]
    sma_200 = df.loc[mask, "sma_200"]
    prev = sma_50.shift(1) <= sma_200.shift(1)
    curr = sma_50 > sma_200
    cross = prev & curr
    crossover_dates = df.loc[mask].loc[cross].index.to_list()
    return [df.loc[i, "date"] for i in crossover_dates]


def detect_death_cross(df: pd.DataFrame) -> List[pd.Timestamp]:
    """
    Detect Death Crosses (50-day SMA crosses below 200-day SMA).
    Returns a list of crossover dates.
    Handles edge cases (insufficient data, NaN values).

    Args:
            df (pd.DataFrame): DataFrame with 'sma_50' and 'sma_200' columns.

    Returns:
            List[pd.Timestamp]: List of crossover dates.
    """
    if "sma_50" not in df or "sma_200" not in df:
        logging.warning("SMA columns missing for crossover detection.")
        return []
    mask = df["sma_50"].notna() & df["sma_200"].notna()
    if mask.sum() < 2:
        return []
    sma_50 = df.loc[mask, "sma_50"]
    sma_200 = df.loc[mask, "sma_200"]
    prev = sma_50.shift(1) >= sma_200.shift(1)
    curr = sma_50 < sma_200
    cross = prev & curr
    crossover_dates = df.loc[mask].loc[cross].index.to_list()
    return [df.loc[i, "date"] for i in crossover_dates]
