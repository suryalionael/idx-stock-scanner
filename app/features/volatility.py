import numpy as np
import pandas as pd


def add_volatility_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    close = df["close"]

    if "atr14" not in df.columns:
        from app.features.breakout import _atr
        df["atr14"] = _atr(df, 14)

    df["atr_pct"] = df["atr14"] / close

    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    df["bb_upper"] = sma20 + 2 * std20
    df["bb_lower"] = sma20 - 2 * std20
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / sma20

    log_returns = np.log(close / close.shift(1))
    df["hist_vol_20d"] = log_returns.rolling(20).std() * np.sqrt(252)

    return df
