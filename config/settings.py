from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
FEATURES_DIR = DATA_DIR / "features"
SIGNALS_DIR = DATA_DIR / "signals"
BACKTEST_DIR = DATA_DIR / "backtest"
CONFIG_DIR = BASE_DIR / "config"

TICKER_UNIVERSE_PATH = CONFIG_DIR / "ticker_universe.csv"
SIGNAL_RULES_PATH = CONFIG_DIR / "signal_rules.yaml"

LOOKBACK_YEARS = 3
BATCH_SIZE = 20          # tickers per yfinance batch download
MAX_GAP_FILL_DAYS = 2    # max hari forward-fill gaps

SIGNAL_CLASSES = ["Breakout Candidate", "Pre-breakout", "Watchlist", "Avoid"]

BACKTEST_WINDOWS = [3, 5, 10]   # forward return windows in trading days

EXPORT_TOP_N = 20               # top N ticker per sinyal di ranked output

LOG_LEVEL = "INFO"

for _dir in [RAW_DIR, FEATURES_DIR, SIGNALS_DIR, BACKTEST_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)
