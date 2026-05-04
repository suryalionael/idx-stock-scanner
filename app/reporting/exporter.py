import logging
import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd

from config.settings import BACKTEST_DIR, SIGNALS_DIR

logger = logging.getLogger(__name__)

SIGNALS_DB = SIGNALS_DIR / "signal_history.db"


def export_signals_csv(signals: pd.DataFrame, scan_date: str | None = None) -> Path:
    label = scan_date or date.today().strftime("%Y-%m-%d")
    path = SIGNALS_DIR / f"signals_{label}.csv"
    signals.to_csv(path, index=False)
    logger.info(f"Signals exported → {path}")
    return path


def export_signals_sqlite(signals: pd.DataFrame) -> None:
    con = sqlite3.connect(SIGNALS_DB)
    signals.to_sql("signal_history", con, if_exists="append", index=False)
    con.close()
    logger.info(f"Signals appended to SQLite → {SIGNALS_DB}")


def export_backtest_csv(backtest: pd.DataFrame, metrics: pd.DataFrame) -> None:
    bt_path = BACKTEST_DIR / "backtest_results.csv"
    m_path = BACKTEST_DIR / "backtest_metrics.csv"
    backtest.to_csv(bt_path, index=False)
    metrics.to_csv(m_path, index=False)
    logger.info(f"Backtest saved → {bt_path}, {m_path}")


def load_signal_history_sqlite() -> pd.DataFrame:
    if not SIGNALS_DB.exists():
        return pd.DataFrame()
    con = sqlite3.connect(SIGNALS_DB)
    df = pd.read_sql("SELECT * FROM signal_history", con)
    con.close()
    return df
