"""
Run backtest dari signal history tersimpan.
Jalankan: python scripts/run_backtest.py
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.backtest.engine import run_backtest
from app.backtest.metrics import compute_metrics, signals_per_month
from app.reporting.exporter import export_backtest_csv
from app.signals.classifier import load_all_signals
from config.settings import LOG_LEVEL

logging.basicConfig(level=getattr(logging, LOG_LEVEL), format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main():
    logger.info("=== Running backtest ===")

    signals = load_all_signals()
    if signals.empty:
        logger.error("No signal history found. Run run_daily_scan.py first.")
        return

    logger.info(f"Loaded {len(signals)} signal rows from history")

    backtest = run_backtest(signals)
    if backtest.empty:
        logger.error("Backtest produced no results.")
        return

    metrics = compute_metrics(backtest)
    monthly = signals_per_month(backtest)

    export_backtest_csv(backtest, metrics)

    print("\n=== Backtest Metrics by Signal Class ===")
    print(metrics.to_string(index=False))
    print("\n=== Signals per Month ===")
    print(monthly.to_string(index=False))

    logger.info("=== Backtest complete ===")


if __name__ == "__main__":
    main()
