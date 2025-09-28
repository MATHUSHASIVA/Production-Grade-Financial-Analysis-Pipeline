from pydantic import BaseModel, Field, model_validator, validator
from typing import Optional, List, Literal
from decimal import Decimal
from datetime import date


class PriceData(BaseModel):
    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

    @model_validator(mode="after")
    def check_price_relationships(self):
        if self.high is not None and self.low is not None and self.high < self.low:
            raise ValueError("High price must be >= Low price")
        if self.open is not None and (self.open > self.high or self.open < self.low):
            raise ValueError("Open price must be between Low and High")
        if self.close is not None and (self.close > self.high or self.close < self.low):
            raise ValueError("Close price must be between Low and High")
        return self


class FundamentalData(BaseModel):
    as_of: date
    ticker: str
    book_value: Optional[Decimal]
    total_assets: Optional[Decimal]
    total_liabilities: Optional[Decimal]
    pe_ratio: Optional[Decimal]
    pb_ratio: Optional[Decimal]
    eps: Optional[Decimal]
    revenue: Optional[Decimal]
    net_income: Optional[Decimal]
    enterprise_value: Optional[Decimal]
    source: Literal["quarterly", "annual", "info"]


class DailyMetrics(BaseModel):
    date: date
    ticker: str
    close: Decimal
    sma_50: Optional[Decimal]
    sma_200: Optional[Decimal]
    high_52w: Optional[Decimal]
    pct_from_high_52w: Optional[Decimal]
    book_value_per_share: Optional[Decimal]
    price_to_book: Optional[Decimal]
    enterprise_value: Optional[Decimal]


class SignalEvent(BaseModel):
    date: date
    ticker: str
    signal_type: Literal["golden_cross", "death_cross"]
    meta: Optional[dict]


class ExportData(BaseModel):
    ticker: str
    price_data: List[PriceData]
    fundamentals: List[FundamentalData]
    daily_metrics: List[DailyMetrics]
    signals: List[SignalEvent]
