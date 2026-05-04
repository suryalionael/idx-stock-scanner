import pandas as pd

from app.signals.rules import SignalRules, load_rules


def compute_scores(features: pd.DataFrame, rules: SignalRules | None = None) -> pd.DataFrame:
    """
    Hitung 5 komponen score untuk setiap baris feature (latest row per ticker).
    Score tiap komponen: 0–10.
    """
    if rules is None:
        rules = load_rules()

    df = features.copy()

    df["trend_score"] = _trend_score(df, rules)
    df["momentum_score"] = _momentum_score(df, rules)
    df["breakout_score"] = _breakout_score(df, rules)
    df["volume_score"] = _volume_score(df, rules)
    df["penalty_score"] = _penalty_score(df, rules)

    w = rules.weights
    df["total_score"] = (
        df["trend_score"] * w.trend
        + df["momentum_score"] * w.momentum
        + df["breakout_score"] * w.breakout
        + df["volume_score"] * w.volume
        + df["penalty_score"] * abs(w.penalty)
    ).clip(0, 10)

    score_cols = [
        "date", "ticker", "close",
        "trend_score", "momentum_score", "breakout_score",
        "volume_score", "penalty_score", "total_score",
    ]
    available = [c for c in score_cols if c in df.columns]
    return df[available]


def _trend_score(df: pd.DataFrame, rules: SignalRules) -> pd.Series:
    score = pd.Series(0.0, index=df.index)
    if "ma_full_alignment" in df.columns:
        score += df["ma_full_alignment"].fillna(False).astype(float) * 10
    elif "ma_partial_alignment" in df.columns:
        score += df["ma_partial_alignment"].fillna(False).astype(float) * 5
    if "slope_ma20" in df.columns:
        score += (df["slope_ma20"].fillna(0) > 0).astype(float) * 2
    return score.clip(0, 10)


def _momentum_score(df: pd.DataFrame, rules: SignalRules) -> pd.Series:
    score = pd.Series(0.0, index=df.index)
    if "rsi14" in df.columns:
        rsi = df["rsi14"].fillna(50)
        ideal = (rsi >= rules.rsi_ideal_min) & (rsi <= rules.rsi_ideal_max)
        score += ideal.astype(float) * 5
    if "macd_histogram" in df.columns:
        score += (df["macd_histogram"].fillna(0) > 0).astype(float) * 3
    if "roc5" in df.columns:
        score += (df["roc5"].fillna(0) > 0).astype(float) * 1
    if "roc20" in df.columns:
        score += (df["roc20"].fillna(0) > 0).astype(float) * 1
    return score.clip(0, 10)


def _breakout_score(df: pd.DataFrame, rules: SignalRules) -> pd.Series:
    score = pd.Series(0.0, index=df.index)
    if "pct_from_52w_high" in df.columns:
        pct = df["pct_from_52w_high"].fillna(0)
        score += (pct >= rules.pct_52w_high_strong).astype(float) * 5
        score += ((pct >= rules.pct_52w_high_mid) & (pct < rules.pct_52w_high_strong)).astype(float) * 2
    if "atr_breakout" in df.columns:
        score += df["atr_breakout"].fillna(False).astype(float) * 5
    return score.clip(0, 10)


def _volume_score(df: pd.DataFrame, rules: SignalRules) -> pd.Series:
    score = pd.Series(0.0, index=df.index)
    if "vol_ratio_20d" in df.columns:
        vr = df["vol_ratio_20d"].fillna(0)
        score += (vr >= rules.vol_ratio_strong).astype(float) * 5
        score += ((vr >= rules.vol_ratio_mid) & (vr < rules.vol_ratio_strong)).astype(float) * 3
    if "obv_trend" in df.columns:
        score += df["obv_trend"].fillna(False).astype(float) * 5
    return score.clip(0, 10)


def _penalty_score(df: pd.DataFrame, rules: SignalRules) -> pd.Series:
    """Penalty score: nilai positif = besar penalti (dikurangkan dari total)."""
    penalty = pd.Series(0.0, index=df.index)
    if "rsi14" in df.columns:
        rsi = df["rsi14"].fillna(50)
        penalty += (rsi > rules.rsi_overbought).astype(float) * rules.rsi_overbought_penalty
    if "volume" in df.columns:
        penalty += (df["volume"].fillna(0) < rules.low_volume_threshold).astype(float) * rules.low_volume_penalty
    return penalty.clip(0, 10)
