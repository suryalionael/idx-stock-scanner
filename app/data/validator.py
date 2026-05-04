import logging

import pandas as pd

from config.settings import MAX_GAP_FILL_DAYS

logger = logging.getLogger(__name__)

REQUIRED_COLS = {"date", "ticker", "open", "high", "low", "close", "volume"}

# Gap lebih kecil dari ini → ffill (weekend panjang, cuti bersama pendek)
_FFILL_GAP_LIMIT = MAX_GAP_FILL_DAYS
# Gap antara _FFILL_GAP_LIMIT dan ini → log INFO "likely holidays"
# Gap lebih besar dari ini → log WARNING (kemungkinan suspend/delisted)
_HOLIDAY_GAP_LIMIT = 30


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
    # Standarisasi ke pd.Timestamp tz-naive — mencegah Timestamp vs datetime.date error
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
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

    # Hitung gap terbesar berturut-turut, bukan total — lebih akurat deteksi suspend
    max_consecutive_gap = _max_consecutive_gap(missing_dates)

    if max_consecutive_gap > 0:
        if max_consecutive_gap <= _FFILL_GAP_LIMIT:
            # Gap kecil: ffill tanpa ribut
            df = df.reindex(all_dates)
            _ffill_ohlc(df, ticker, _FFILL_GAP_LIMIT)
            report["gaps_filled"] = len(missing_dates)
        elif max_consecutive_gap <= _HOLIDAY_GAP_LIMIT:
            # Gap sedang: kemungkinan libur panjang / provider gap — log INFO saja
            logger.info(
                f"{ticker}: {len(missing_dates)} missing business days "
                f"(max consecutive: {max_consecutive_gap}) — likely holidays/provider gaps"
            )
            report["issues"].append(f"holiday/provider gaps ({len(missing_dates)} days)")
        else:
            # Gap besar: kemungkinan suspend atau delisted — baru log WARNING
            logger.warning(
                f"{ticker}: {len(missing_dates)} missing business days "
                f"(max consecutive: {max_consecutive_gap}) — possible suspension or delisting"
            )
            report["issues"].append(f"large gap detected ({max_consecutive_gap} consecutive days)")

    df = df.reset_index().rename(columns={"index": "date"})
    df = df.dropna(subset=["close"])

    real_issues = [i for i in report["issues"] if not i.startswith("holiday")]
    if real_issues:
        logger.warning(f"{ticker}: {real_issues}")
    else:
        logger.info(f"{ticker}: validation OK ({len(df)} rows)")

    return df, report


def _max_consecutive_gap(missing_dates: pd.DatetimeIndex) -> int:
    """Hitung panjang gap berturut-turut terbesar dari index tanggal yang hilang."""
    if len(missing_dates) == 0:
        return 0
    sorted_dates = missing_dates.sort_values()
    max_run = run = 1
    for i in range(1, len(sorted_dates)):
        diff = (sorted_dates[i] - sorted_dates[i - 1]).days
        if diff <= 3:  # toleransi weekend di antara hari libur
            run += 1
            max_run = max(max_run, run)
        else:
            run = 1
    return max_run


def _ffill_ohlc(df: pd.DataFrame, ticker: str, limit: int) -> None:
    """In-place ffill untuk kolom OHLC pada DataFrame yang sudah di-reindex."""
    price_cols = [c for c in ["open", "high", "low", "close", "adj_close"] if c in df.columns]
    df[price_cols] = df[price_cols].ffill(limit=limit)
    df["volume"] = df["volume"].fillna(0)
    df["ticker"] = ticker


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
