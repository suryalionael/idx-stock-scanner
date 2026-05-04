import logging
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from app.data.fetch_base import BaseFetcher
from config.settings import BATCH_SIZE, LOOKBACK_YEARS, RAW_DIR

logger = logging.getLogger(__name__)


class YFinanceFetcher(BaseFetcher):

    def fetch(self, tickers: list[str], start: str, end: str) -> dict[str, pd.DataFrame]:
        results = {}
        batches = [tickers[i:i + BATCH_SIZE] for i in range(0, len(tickers), BATCH_SIZE)]

        for batch in batches:
            logger.info(f"Downloading batch: {batch}")
            try:
                raw = yf.download(
                    batch,
                    start=start,
                    end=end,
                    auto_adjust=True,
                    progress=False,
                    group_by="ticker",
                    threads=True,
                )
                for ticker in batch:
                    df = self._extract_ticker(raw, ticker, len(batch))
                    if df is not None and not df.empty:
                        results[ticker] = df
                    else:
                        logger.warning(f"No data returned for {ticker}")
            except Exception as e:
                logger.error(f"Batch download failed: {e}")
                for ticker in batch:
                    try:
                        df = self.fetch_single(ticker, start, end)
                        if df is not None and not df.empty:
                            results[ticker] = df
                    except Exception as e2:
                        logger.error(f"Single fetch fallback failed for {ticker}: {e2}")

        return results

    def fetch_single(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        raw = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
        if raw.empty:
            return pd.DataFrame()
        return self._normalize(raw, ticker)

    def _extract_ticker(self, raw: pd.DataFrame, ticker: str, n_tickers: int) -> pd.DataFrame | None:
        try:
            if n_tickers == 1:
                df = raw.copy()
            else:
                df = raw[ticker].copy()
            # Drop ticker-level from MultiIndex after slicing (yfinance >= 0.2.x)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if df.empty:
                return None
            return self._normalize(df, ticker)
        except KeyError:
            return None

    def _normalize(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        df = df.copy()
        # yfinance >= 0.2.x returns MultiIndex columns for single-ticker downloads
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.columns = [c.lower() for c in df.columns]
        df.index.name = "date"
        df = df.reset_index()
        # Standarisasi ke pd.Timestamp (normalize ke midnight, tz-naive)
        df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
        df["ticker"] = ticker

        rename = {"adj close": "adj_close"}
        df = df.rename(columns=rename)

        keep = ["date", "ticker", "open", "high", "low", "close", "volume"]
        if "adj_close" in df.columns:
            keep.append("adj_close")
        else:
            df["adj_close"] = df["close"]
            keep.append("adj_close")

        return df[keep].dropna(subset=["close"])


def default_start_date() -> str:
    return (datetime.today() - timedelta(days=365 * LOOKBACK_YEARS)).strftime("%Y-%m-%d")


def default_end_date() -> str:
    return datetime.today().strftime("%Y-%m-%d")


def save_raw(ticker: str, df: pd.DataFrame) -> None:
    path = RAW_DIR / f"{ticker}.parquet"
    df.to_parquet(path, index=False)
    logger.info(f"Saved {ticker} → {path} ({len(df)} rows)")


def load_raw(ticker: str) -> pd.DataFrame:
    path = RAW_DIR / f"{ticker}.parquet"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


def incremental_update(ticker: str, fetcher: BaseFetcher) -> pd.DataFrame:
    existing = load_raw(ticker)
    if existing.empty:
        start = default_start_date()
    else:
        # Pastikan kolom date adalah Timestamp agar perbandingan string aman
        last_date = pd.to_datetime(existing["date"]).max()
        start = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")

    end = default_end_date()
    # Bandingkan sebagai string "YYYY-MM-DD" — aman, tidak ada Timestamp vs date
    if start >= end:
        logger.info(f"{ticker} already up to date")
        return existing

    new_data = fetcher.fetch_single(ticker, start, end)
    if new_data.empty:
        # Tidak ada data baru — bisa libur bursa, bukan delisted
        logger.debug(f"{ticker}: no new data {start} → {end}, keeping existing")
        return existing

    combined = pd.concat([existing, new_data], ignore_index=True)
    combined["date"] = pd.to_datetime(combined["date"]).dt.tz_localize(None).dt.normalize()
    combined = combined.drop_duplicates(subset=["date", "ticker"]).sort_values("date").reset_index(drop=True)
    save_raw(ticker, combined)
    return combined
