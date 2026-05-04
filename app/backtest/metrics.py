import pandas as pd

from config.settings import BACKTEST_WINDOWS


def compute_metrics(backtest: pd.DataFrame) -> pd.DataFrame:
    """
    Hitung aggregated metrics per signal_class.
    Returns DataFrame ringkasan: class | window | n_signals | hit_rate | avg_return | max_drawdown
    """
    rows = []
    classes = backtest["signal_class"].dropna().unique()

    for cls in classes:
        subset = backtest[backtest["signal_class"] == cls]
        for w in BACKTEST_WINDOWS:
            col_ret = f"return_{w}d"
            col_hit = f"hit_{w}d"
            col_dd = f"drawdown_{w}d"
            valid = subset.dropna(subset=[col_ret])
            if valid.empty:
                continue
            rows.append({
                "signal_class": cls,
                "window_days": w,
                "n_signals": len(valid),
                "hit_rate": valid[col_hit].mean(),
                "avg_return": valid[col_ret].mean(),
                "median_return": valid[col_ret].median(),
                "max_drawdown": valid[col_dd].min(),
                "std_return": valid[col_ret].std(),
            })

    return pd.DataFrame(rows).sort_values(["signal_class", "window_days"])


def signals_per_month(backtest: pd.DataFrame) -> pd.DataFrame:
    df = backtest.copy()
    df["signal_date"] = pd.to_datetime(df["signal_date"])
    df["month"] = df["signal_date"].dt.to_period("M")
    return df.groupby(["month", "signal_class"]).size().reset_index(name="count")
