import pandas as pd


def add_trend_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    close = df["close"]

    df["ma20"] = close.rolling(20).mean()
    df["ma50"] = close.rolling(50).mean()
    df["ma200"] = close.rolling(200).mean()

    df["ma_full_alignment"] = (df["ma20"] > df["ma50"]) & (df["ma50"] > df["ma200"])
    df["ma_partial_alignment"] = df["ma20"] > df["ma50"]

    df["slope_ma20"] = df["ma20"].diff(5) / df["ma20"].shift(5)

    df["golden_cross"] = (df["ma50"] > df["ma200"]) & (df["ma50"].shift(1) <= df["ma200"].shift(1))
    df["death_cross"] = (df["ma50"] < df["ma200"]) & (df["ma50"].shift(1) >= df["ma200"].shift(1))

    df["price_vs_ma200"] = close / df["ma200"]

    return df
