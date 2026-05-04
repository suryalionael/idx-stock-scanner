from datetime import date

import pandas as pd

from app.signals.rules import SignalRules, load_rules
from config.settings import SIGNALS_DIR


def classify_signals(scores: pd.DataFrame, rules: SignalRules | None = None) -> pd.DataFrame:
    """Map score columns → signal_class label."""
    if rules is None:
        rules = load_rules()

    df = scores.copy()
    t = rules.thresholds

    def _classify(row):
        if row["penalty_score"] >= t.avoid_max_penalty:
            return "Avoid"
        if (row["total_score"] >= t.breakout_candidate_min
                and row.get("breakout_score", 0) >= t.breakout_candidate_min_breakout
                and row.get("volume_score", 0) >= t.breakout_candidate_min_volume):
            return "Breakout Candidate"
        if (row["total_score"] >= t.pre_breakout_min
                and row.get("trend_score", 0) >= t.pre_breakout_min_trend):
            return "Pre-breakout"
        if row["total_score"] >= t.watchlist_min:
            return "Watchlist"
        return "Avoid"

    df["signal_class"] = df.apply(_classify, axis=1)
    df["close_at_signal"] = df.get("close", pd.Series(dtype=float))
    return df


def save_signals(df: pd.DataFrame, scan_date: str | None = None) -> None:
    label = scan_date or date.today().strftime("%Y-%m-%d")
    path = SIGNALS_DIR / f"{label}.parquet"
    df.to_parquet(path, index=False)


def load_signals(scan_date: str) -> pd.DataFrame:
    path = SIGNALS_DIR / f"{scan_date}.parquet"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


def load_all_signals() -> pd.DataFrame:
    files = sorted(SIGNALS_DIR.glob("*.parquet"))
    if not files:
        return pd.DataFrame()
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
