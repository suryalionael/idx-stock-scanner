import logging
from datetime import date

import pandas as pd

from config.settings import MAX_GAP_FILL_DAYS

logger = logging.getLogger(__name__)

REQUIRED_COLS = {"date", "ticker", "open", "high", "low", "close", "volume"}


def validate(df: pd.DataFrame, ticker: str) -> tuple[pd.DataFrame, dict]:
    """
    Validate dan clean raw OHLCV DataFrame untuk satu ticker.

    Returns:
        (cleaned_df, report) — report berisi info anomali yang ditemukan.
    """
    report = {"ticker": ticker, "issues": [], "rows_dropped": 0, "gaps_filled": 0}

    missing_cols = REQUIRED_COLS - set(df.columns)
    if missing_cols:
        msg = f"Missing columns: {missing_cols}"
        report["issues"].append(msg)
        logger.warning(f"{ticker}: {msg}")
        return pd.DataFrame(), report

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    original_len = len(df)
    df = df.dropna(subset=["close", "open", "high", "low"])
    dropped = original_len - len(df)
    if dropped:
        report["rows_dropped"] = dropped
        report["issues"].append(f"Dropped {dropped} rows with NaN OHLC")

    negative_mask = (df[["open", "high", "low", "close"]] < 0).any(axis=1)
    if negative_mask.any():
        count = negative_mask.sum()
        df = df[~negative_mask]
        report["issues"].append(f"Dropped {count} rows with negative prices")

    hl_invalid = df["high"] < df["low"]
    if hl_invalid.any():
        count = hl_invalid.sum()
        df = df[~hl_invalid]
        report["issues"].append(f"Dropped {count} rows where high < low")

    df = df.set_index("date")
    all_dates = pd.date_range(df.index.min(), df.index.max(), freq="B")
    missing_dates = all_dates.difference(df.index)
    gap_count = len(missing_dates)

    if gap_count > 0:
        report["issues"].append(f"{gap_count} missing business days detected")
        if gap_count <= MAX_GAP_FILL_DAYS * 5:
            df = df.reindex(all_dates)
            df[["open", "high", "low", "close", "adj_close"]] = (
                df[["open", "high", "low", "close", "adj_close"]]
                .ffill(limit=MAX_GAP_FILL_DAYS)
            )
            df["volume"] = df["volume"].fillna(0)
            df["ticker"] = ticker
            report["gaps_filled"] = gap_count

    df = df.reset_index().rename(columns={"index": "date"})
    df = df.dropna(subset=["close"])

    if report["issues"]:
        logger.warning(f"{ticker} validation issues: {report['issues']}")
    else:
        logger.info(f"{ticker}: validation OK ({len(df)} rows)")

    return df, report


def validate_batch(data: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], list[dict]]:
    """Validate semua ticker sekaligus. Returns (clean_data, all_reports)."""
    clean = {}
    reports = []
    for ticker, df in data.items():
        cleaned, report = validate(df, ticker)
        if not cleaned.empty:
            clean[ticker] = cleaned
        reports.append(report)
    return clean, reports
