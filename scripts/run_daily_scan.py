"""
Entry point utama scan harian.
Jalankan: python scripts/run_daily_scan.py
"""
import logging
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from app.data.fetch_yfinance import YFinanceFetcher, incremental_update, load_raw
from app.data.validator import validate
from app.features.feature_builder import build_features, save_features
from app.signals.classifier import classify_signals, save_signals
from app.signals.scoring import compute_scores
from app.reporting.exporter import export_signals_csv, export_signals_sqlite
from app.reporting.formatter import print_summary, save_ranked_csv
from config.settings import LOG_LEVEL, TICKER_UNIVERSE_PATH

logging.basicConfig(level=getattr(logging, LOG_LEVEL), format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main():
    scan_date = date.today().strftime("%Y-%m-%d")
    logger.info(f"=== Daily scan: {scan_date} ===")

    # Step 1: Load ticker universe
    universe = pd.read_csv(TICKER_UNIVERSE_PATH)
    tickers = universe[universe["is_active"] == True]["ticker"].tolist()
    logger.info(f"Scanning {len(tickers)} tickers")

    # Step 2: Incremental update raw data
    fetcher = YFinanceFetcher()
    all_features = []

    for ticker in tickers:
        try:
            df = incremental_update(ticker, fetcher)
            if df.empty:
                logger.warning(f"{ticker}: empty data, skipping")
                continue

            # Step 3: Validate
            clean, report = validate(df, ticker)
            if clean.empty:
                logger.warning(f"{ticker}: failed validation, skipping")
                continue

            # Step 4: Compute features (latest row only for scanning)
            features = build_features(clean)
            latest = features.iloc[[-1]].copy()
            all_features.append(latest)

        except Exception as e:
            logger.error(f"{ticker}: error during processing — {e}")

    if not all_features:
        logger.error("No features computed. Exiting.")
        return

    feature_df = pd.concat(all_features, ignore_index=True)
    save_features(feature_df, scan_date)
    logger.info(f"Features computed: {len(feature_df)} tickers")

    # Step 5: Compute scores
    scores = compute_scores(feature_df)

    # Step 6: Classify signals
    signals = classify_signals(scores)
    signals["date"] = scan_date

    # Step 7: Save outputs
    save_signals(signals, scan_date)
    export_signals_csv(signals, scan_date)
    export_signals_sqlite(signals)

    # Step 8: Export ranked candidates
    ranked_path = save_ranked_csv(signals, scan_date)
    logger.info(f"Ranked output → {ranked_path}")

    print_summary(signals)
    logger.info(f"=== Scan complete: {scan_date} ===")


if __name__ == "__main__":
    main()
