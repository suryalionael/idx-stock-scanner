from abc import ABC, abstractmethod
import pandas as pd


class BaseFetcher(ABC):
    """Interface contract untuk semua data provider."""

    @abstractmethod
    def fetch(self, tickers: list[str], start: str, end: str) -> dict[str, pd.DataFrame]:
        """
        Download OHLCV data untuk list ticker.

        Returns:
            dict { ticker: DataFrame[date, open, high, low, close, volume, adj_close] }
        """
        ...

    @abstractmethod
    def fetch_single(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        """Download OHLCV untuk satu ticker."""
        ...
