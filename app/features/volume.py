import pandas as pd


def add_volume_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    volume = df["volume"]
    close = df["close"]

    df["vol_ma20"] = volume.rolling(20).mean()
    df["vol_ratio_20d"] = volume / df["vol_ma20"].replace(0, float("nan"))
    df["vol_spike"] = df["vol_ratio_20d"] > 2.0

    df["obv"] = (close.diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0)) * volume).cumsum()
    df["obv_ma10"] = df["obv"].rolling(10).mean()
    df["obv_trend"] = df["obv"] > df["obv_ma10"]

    return df
