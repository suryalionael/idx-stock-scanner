import logging
from datetime import date

import pandas as pd

from app.features.breakout import add_breakout_features
from app.features.momentum import add_momentum_features
from app.features.trend import add_trend_features
from app.features.volume import add_volume_features
from app.features.volatility import add_volatility_features
from config.settings import FEATURES_DIR

logger = logging.getLogger(__name__)

FEATURE_COLS = [
    "date", "ticker",
    "ma20", "ma50", "ma200", "ma_full_alignment", "ma_partial_alignment",
    "slope_ma20", "golden_cross", "price_vs_ma200",
    "rsi14", "macd", "macd_signal", "macd_histogram", "roc5", "roc20",
    "high_52w", "pct_from_52w_high", "atr14", "atr_breakout", "pivot_high_20d", "price_above_pivot",
    "vol_ratio_20d", "vol_spike", "obv_trend",
    "atr_pct", "bb_width", "hist_vol_20d",
    "close", "volume",
]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Hitung semua fitur untuk satu ticker DataFrame."""
    df = add_trend_features(df)
    df = add_momentum_features(df)
    df = add_breakout_features(df)
    df = add_volume_features(df)
    df = add_volatility_features(df)

    available = [c for c in FEATURE_COLS if c in df.columns]
    return df[available]


def build_features_batch(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build features untuk semua ticker dan gabungkan ke satu DataFrame."""
    frames = []
    for ticker, df in data.items():
        try:
            features = build_features(df)
            frames.append(features)
            logger.info(f"{ticker}: features computed ({len(features)} rows)")
        except Exception as e:
            logger.error(f"{ticker}: feature computation failed — {e}")

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def save_features(df: pd.DataFrame, scan_date: str | None = None) -> None:
    label = scan_date or date.today().strftime("%Y-%m-%d")
    path = FEATURES_DIR / f"{label}.parquet"
    df.to_parquet(path, index=False)
    logger.info(f"Feature store saved → {path}")


def load_features(scan_date: str) -> pd.DataFrame:
    path = FEATURES_DIR / f"{scan_date}.parquet"
    if not path.exists():
        logger.warning(f"Feature file not found: {path}")
        return pd.DataFrame()
    return pd.read_parquet(path)
