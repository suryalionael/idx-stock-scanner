from dataclasses import dataclass, field
from pathlib import Path

import yaml

from config.settings import SIGNAL_RULES_PATH


@dataclass
class Weights:
    trend: float = 0.25
    momentum: float = 0.25
    breakout: float = 0.25
    volume: float = 0.15
    penalty: float = -0.10


@dataclass
class ClassificationThresholds:
    breakout_candidate_min: float = 7.5
    breakout_candidate_min_breakout: float = 7.0
    breakout_candidate_min_volume: float = 6.0
    pre_breakout_min: float = 5.5
    pre_breakout_min_trend: float = 5.0
    watchlist_min: float = 3.5
    avoid_max_penalty: float = 8.0


@dataclass
class SignalRules:
    weights: Weights = field(default_factory=Weights)
    thresholds: ClassificationThresholds = field(default_factory=ClassificationThresholds)
    rsi_ideal_min: float = 40.0
    rsi_ideal_max: float = 70.0
    rsi_overbought: float = 80.0
    rsi_overbought_penalty: float = 5.0
    pct_52w_high_strong: float = 0.95
    pct_52w_high_mid: float = 0.85
    vol_ratio_strong: float = 2.0
    vol_ratio_mid: float = 1.5
    low_volume_threshold: int = 1_000_000
    low_volume_penalty: float = 5.0
    data_gap_penalty: float = 3.0


def load_rules(path: Path = SIGNAL_RULES_PATH) -> SignalRules:
    if not path.exists():
        return SignalRules()

    with open(path) as f:
        cfg = yaml.safe_load(f)

    w = cfg.get("weights", {})
    t = cfg.get("thresholds", {})
    cl = t.get("classification", cfg.get("classification", {}))
    pen = t.get("penalty", {})
    mom = t.get("momentum", {})
    brk = t.get("breakout", {})
    vol = t.get("volume", {})

    weights = Weights(
        trend=w.get("trend", 0.25),
        momentum=w.get("momentum", 0.25),
        breakout=w.get("breakout", 0.25),
        volume=w.get("volume", 0.15),
        penalty=w.get("penalty", -0.10),
    )
    thresholds = ClassificationThresholds(
        breakout_candidate_min=cl.get("breakout_candidate", {}).get("min_total", 7.5),
        breakout_candidate_min_breakout=cl.get("breakout_candidate", {}).get("min_breakout_score", 7.0),
        breakout_candidate_min_volume=cl.get("breakout_candidate", {}).get("min_volume_score", 6.0),
        pre_breakout_min=cl.get("pre_breakout", {}).get("min_total", 5.5),
        pre_breakout_min_trend=cl.get("pre_breakout", {}).get("min_trend_score", 5.0),
        watchlist_min=cl.get("watchlist", {}).get("min_total", 3.5),
        avoid_max_penalty=cl.get("avoid", {}).get("max_penalty", 8.0),
    )
    return SignalRules(
        weights=weights,
        thresholds=thresholds,
        rsi_ideal_min=mom.get("rsi_ideal_min", 40.0),
        rsi_ideal_max=mom.get("rsi_ideal_max", 70.0),
        rsi_overbought=pen.get("rsi_overbought", 80.0),
        rsi_overbought_penalty=pen.get("rsi_overbought_penalty", 5.0),
        pct_52w_high_strong=brk.get("pct_52w_high_strong", 0.95),
        pct_52w_high_mid=brk.get("pct_52w_high_mid", 0.85),
        vol_ratio_strong=vol.get("vol_ratio_strong", 2.0),
        vol_ratio_mid=vol.get("vol_ratio_mid", 1.5),
        low_volume_threshold=pen.get("low_volume_threshold", 1_000_000),
        low_volume_penalty=pen.get("low_volume_penalty", 5.0),
        data_gap_penalty=pen.get("data_gap_penalty", 3.0),
    )
