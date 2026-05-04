import json
from datetime import date
from pathlib import Path

import pandas as pd

from config.settings import EXPORT_TOP_N, SIGNALS_DIR


def ranked_output(signals: pd.DataFrame, top_n: int = EXPORT_TOP_N) -> dict[str, pd.DataFrame]:
    """
    Return dict { signal_class: top_n DataFrame } diurutkan by total_score desc.
    """
    classes = ["Breakout Candidate", "Pre-breakout", "Watchlist"]
    result = {}
    for cls in classes:
        subset = signals[signals["signal_class"] == cls].copy()
        subset = subset.sort_values("total_score", ascending=False).head(top_n)
        result[cls] = subset
    return result


def to_telegram_json(signals: pd.DataFrame, scan_date: str | None = None) -> str:
    """Format ranked signals sebagai JSON string siap kirim ke Telegram handler."""
    label = scan_date or date.today().strftime("%Y-%m-%d")
    ranked = ranked_output(signals)
    output = {"scan_date": label, "signals": {}}

    for cls, df in ranked.items():
        output["signals"][cls] = df[["ticker", "total_score", "signal_class"]].to_dict(orient="records")

    return json.dumps(output, indent=2, default=str)


def save_ranked_csv(signals: pd.DataFrame, scan_date: str | None = None) -> Path:
    label = scan_date or date.today().strftime("%Y-%m-%d")
    ranked = ranked_output(signals)
    frames = []
    for cls, df in ranked.items():
        frames.append(df)

    if not frames:
        return Path()

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values(["signal_class", "total_score"], ascending=[True, False])
    path = SIGNALS_DIR / f"ranked_{label}.csv"
    combined.to_csv(path, index=False)
    return path


def print_summary(signals: pd.DataFrame) -> None:
    ranked = ranked_output(signals)
    for cls, df in ranked.items():
        print(f"\n{'='*50}")
        print(f"  {cls} ({len(df)} tickers)")
        print(f"{'='*50}")
        cols = ["ticker", "total_score", "trend_score", "breakout_score", "volume_score"]
        avail = [c for c in cols if c in df.columns]
        print(df[avail].to_string(index=False))
