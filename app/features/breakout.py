import pandas as pd


def add_breakout_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    close = df["close"]
    high = df["high"]

    df["high_52w"] = high.rolling(252).max()
    df["pct_from_52w_high"] = close / df["high_52w"]

    atr = _atr(df, 14)
    df["atr14"] = atr
    prev_high = high.shift(1)
    df["atr_breakout"] = close > (prev_high + 0.5 * atr)

    df["pivot_high_20d"] = high.rolling(20).max().shift(1)
    df["price_above_pivot"] = close > df["pivot_high_20d"]

    return df


def _atr(df: pd.DataFrame, period: int) -> pd.Series:
    high = df["high"]
    low = df["low"]
    prev_close = df["close"].shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(com=period - 1, adjust=False).mean()
