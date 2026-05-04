"""
Setup awal: verifikasi ticker_universe.csv dan download semua raw data historis.
Jalankan sekali di awal project.
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from app.data.fetch_yfinance import YFinanceFetcher, default_end_date, default_start_date, save_raw
from app.data.validator import validate_batch
from config.settings import LOG_LEVEL, TICKER_UNIVERSE_PATH

logging.basicConfig(level=getattr(logging, LOG_LEVEL), format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main():
    logger.info("=== init_universe: loading ticker universe ===")
    universe = pd.read_csv(TICKER_UNIVERSE_PATH)
    active = universe[universe["is_active"] == True]
    tickers = active["ticker"].tolist()
    logger.info(f"Active tickers: {len(tickers)}")

    fetcher = YFinanceFetcher()
    start = default_start_date()
    end = default_end_date()
    logger.info(f"Downloading data: {start} → {end}")

    raw_data = fetcher.fetch(tickers, start, end)
    logger.info(f"Downloaded: {len(raw_data)}/{len(tickers)} tickers")

    clean_data, reports = validate_batch(raw_data)
    logger.info(f"Valid after cleaning: {len(clean_data)} tickers")

    for ticker, df in clean_data.items():
        save_raw(ticker, df)

    issues = [r for r in reports if r["issues"]]
    if issues:
        logger.warning(f"Tickers with issues ({len(issues)}):")
        for r in issues:
            logger.warning(f"  {r['ticker']}: {r['issues']}")

    logger.info("=== init_universe complete ===")


if __name__ == "__main__":
    main()
