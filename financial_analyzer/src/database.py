from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Date,
    Numeric,
    UniqueConstraint,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.exc import IntegrityError
import pandas as pd
import logging

Base = declarative_base()


class Ticker(Base):
    __tablename__ = "tickers"
    id = Column(Integer, primary_key=True)
    ticker = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)
    # Add more fields as needed


class DailyMetric(Base):
    __tablename__ = "daily_metrics"
    id = Column(Integer, primary_key=True)
    ticker = Column(String, ForeignKey("tickers.ticker"), nullable=False)
    date = Column(Date, nullable=False)
    close = Column(Numeric, nullable=False)
    sma_50 = Column(Numeric, nullable=True)
    sma_200 = Column(Numeric, nullable=True)
    high_52w = Column(Numeric, nullable=True)
    pct_from_high_52w = Column(Numeric, nullable=True)
    book_value_per_share = Column(Numeric, nullable=True)
    price_to_book = Column(Numeric, nullable=True)
    enterprise_value = Column(Numeric, nullable=True)
    __table_args__ = (UniqueConstraint("ticker", "date", name="_ticker_date_uc"),)


class SignalEvent(Base):
    __tablename__ = "signal_events"
    id = Column(Integer, primary_key=True)
    ticker = Column(String, ForeignKey("tickers.ticker"), nullable=False)
    date = Column(Date, nullable=False)
    signal_type = Column(String, nullable=False)
    meta = Column(String, nullable=True)
    __table_args__ = (
        UniqueConstraint("ticker", "date", "signal_type", name="_ticker_date_signal_uc"),
    )


def get_engine(db_path: str = "financial_data.db"):
    """
    Create a SQLAlchemy engine for the SQLite database.

    Args:
            db_path (str): Path to SQLite database file.

    Returns:
            Engine: SQLAlchemy engine instance.
    """
    return create_engine(f"sqlite:///{db_path}", echo=False, future=True)


def init_db(db_path: str = "financial_data.db"):
    """
    Initialize the SQLite database and create all tables.

    Args:
            db_path (str): Path to SQLite database file.

    Returns:
            Engine: SQLAlchemy engine instance.
    """
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    return engine


def save_ticker(session, ticker: str, name: str = None):
    """
    Save or update a ticker in the database.

    Args:
            session: SQLAlchemy session.
            ticker (str): Ticker symbol.
            name (str, optional): Ticker name.
    """
    try:
        session.merge(Ticker(ticker=ticker, name=name))
        session.commit()
    except IntegrityError:
        session.rollback()


def save_daily_metrics(session, ticker: str, df: pd.DataFrame):
    """
    Save daily metrics DataFrame to the database.

    Args:
            session: SQLAlchemy session.
            ticker (str): Ticker symbol.
            df (pd.DataFrame): DataFrame of daily metrics.
    """
    for _, row in df.iterrows():
        try:
            session.merge(
                DailyMetric(
                    ticker=ticker,
                    date=row["date"],
                    close=row["close"],
                    sma_50=row.get("sma_50"),
                    sma_200=row.get("sma_200"),
                    high_52w=row.get("high_52w"),
                    pct_from_high_52w=row.get("pct_from_high_52w"),
                    book_value_per_share=row.get("book_value_per_share"),
                    price_to_book=row.get("price_to_book"),
                    enterprise_value=row.get("enterprise_value"),
                )
            )
            session.commit()
        except IntegrityError:
            session.rollback()


def save_signal_events(session, ticker: str, signal_type: str, dates: list, meta: str = None):
    """
    Save signal events to the database.

    Args:
            session: SQLAlchemy session.
            ticker (str): Ticker symbol.
            signal_type (str): 'golden_cross' or 'death_cross'.
            dates (list): List of dates for the signal.
            meta (str, optional): Additional metadata.
    """
    for d in dates:
        try:
            session.merge(SignalEvent(ticker=ticker, date=d, signal_type=signal_type, meta=meta))
            session.commit()
        except IntegrityError:
            session.rollback()
