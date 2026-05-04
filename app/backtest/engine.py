import logging

import pandas as pd

from config.settings import BACKTEST_WINDOWS, RAW_DIR

logger = logging.getLogger(__name__)


def run_backtest(signals: pd.DataFrame) -> pd.DataFrame:
    """
    Untuk setiap sinyal, hitung forward return 3D/5D/10D dari data historis raw.
    Signals DataFrame harus punya kolom: date, ticker, signal_class, close_at_signal.
    """
    results = []
    for _, row in signals.iterrows():
        ticker = row["ticker"]
        signal_date = pd.to_datetime(row["date"])

        raw_path = RAW_DIR / f"{ticker}.parquet"
        if not raw_path.exists():
            logger.warning(f"No raw data for {ticker}, skipping backtest row")
            continue

        ohlcv = pd.read_parquet(raw_path)
        ohlcv["date"] = pd.to_datetime(ohlcv["date"])
        ohlcv = ohlcv.sort_values("date").reset_index(drop=True)

        future = ohlcv[ohlcv["date"] > signal_date].reset_index(drop=True)
        if future.empty:
            continue

        entry_price = row.get("close_at_signal") or row.get("close")
        if not entry_price or entry_price == 0:
            continue

        record = {
            "signal_date": signal_date.date(),
            "ticker": ticker,
            "signal_class": row.get("signal_class"),
            "close_at_signal": entry_price,
            "total_score": row.get("total_score"),
        }

        for window in BACKTEST_WINDOWS:
            if len(future) >= window:
                exit_price = future.iloc[window - 1]["close"]
                ret = (exit_price - entry_price) / entry_price
                record[f"return_{window}d"] = round(ret, 4)
                record[f"hit_{window}d"] = int(ret > 0)
                prices_in_window = future.iloc[:window]["close"]
                drawdown = (prices_in_window.min() - entry_price) / entry_price
                record[f"drawdown_{window}d"] = round(drawdown, 4)
            else:
                record[f"return_{window}d"] = None
                record[f"hit_{window}d"] = None
                record[f"drawdown_{window}d"] = None

        results.append(record)

    return pd.DataFrame(results)
