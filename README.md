# Stock Signal Scanner

A modular Python MVP for daily stock signal scanning using historical OHLCV data.

Scans a universe of tickers, computes technical features, scores each stock, and classifies it into one of four signal labels: **Breakout Candidate**, **Pre-breakout**, **Watchlist**, or **Avoid**.

Designed for solo builders running local experiments — no cloud, no real-time, no frontend required.

---

## Features

- Batch historical download via [yfinance](https://github.com/ranaroussi/yfinance) with incremental updates
- Modular feature engineering: trend, momentum, breakout, volume, volatility
- Rule-based scoring engine with configurable weights and thresholds (YAML — no code changes needed)
- Signal classification with penalty override logic
- Simple forward-return backtest (3D / 5D / 10D) with hit rate and drawdown metrics
- Outputs: Parquet, CSV, SQLite, and Telegram-ready JSON

---

## Architecture

```
config → data ingestion → storage → preprocessing → feature engineering → signal engine → backtest / reporting
```

Each layer communicates only through DataFrames or files — the data source (`yfinance`) can be swapped to any provider by implementing `BaseFetcher` without touching the rest of the pipeline.

---

## Project Structure

```
stock_scanner/
├── app/
│   ├── data/               # Data fetching and validation
│   │   ├── fetch_base.py   # Abstract fetcher interface
│   │   ├── fetch_yfinance.py
│   │   └── validator.py
│   ├── features/           # Technical indicator modules
│   │   ├── trend.py        # MA20/50/200, alignment, slope
│   │   ├── momentum.py     # RSI, MACD, ROC
│   │   ├── breakout.py     # 52w high, ATR breakout, pivot
│   │   ├── volume.py       # Volume ratio, OBV
│   │   ├── volatility.py   # ATR%, BB width, historical vol
│   │   └── feature_builder.py
│   ├── signals/            # Scoring and classification
│   │   ├── rules.py        # Load thresholds from YAML
│   │   ├── scoring.py      # Component scores (0–10 each)
│   │   └── classifier.py   # Map scores → signal label
│   ├── backtest/           # Forward-return backtesting
│   │   ├── engine.py
│   │   └── metrics.py
│   └── reporting/          # Output formatting and export
│       ├── exporter.py     # CSV, Parquet, SQLite
│       └── formatter.py    # Ranked output, Telegram JSON
├── config/
│   ├── settings.py         # Paths, constants — single source of truth
│   ├── ticker_universe.csv # Active tickers to scan
│   └── signal_rules.yaml   # Scoring weights and thresholds
├── data/
│   ├── raw/                # Raw OHLCV per ticker (Parquet)
│   ├── features/           # Feature store per scan date (Parquet)
│   ├── signals/            # Signal history (Parquet + SQLite)
│   └── backtest/           # Backtest results (CSV)
├── notebooks/              # Exploration and analysis
├── scripts/
│   ├── init_universe.py    # One-time: download all historical data
│   ├── run_daily_scan.py   # Main entry point
│   └── run_backtest.py     # Evaluate signal quality
├── tests/
├── requirements.txt
└── .env.example
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure your ticker universe

Edit `config/ticker_universe.csv` — set `is_active = False` for any ticker you want to exclude.

### 3. Download historical data (run once)

```bash
python scripts/init_universe.py
```

Downloads ~3 years of daily OHLCV data for all active tickers and stores them as Parquet files in `data/raw/`.

### 4. Run the daily scan

```bash
python scripts/run_daily_scan.py
```

Output files written to `data/signals/`:
- `signals_YYYY-MM-DD.csv` — full signal table
- `ranked_YYYY-MM-DD.csv` — top N per signal class, sorted by score

### 5. Run backtest (after accumulating signal history)

```bash
python scripts/run_backtest.py
```

Computes forward returns (3D / 5D / 10D) and writes results to `data/backtest/`.

---

## Signal Scoring

Each ticker receives five component scores (0–10 each):

| Component | Weight | Key Inputs |
|---|---|---|
| Trend | 25% | MA20/50/200 alignment, slope |
| Momentum | 25% | RSI14, MACD histogram, ROC |
| Breakout | 25% | Price vs 52w high, ATR breakout |
| Volume | 15% | Volume ratio vs 20D avg, OBV trend |
| Penalty | −10% | RSI overbought, low liquidity, data gaps |

**Signal classification:**

| Label | Condition |
|---|---|
| Breakout Candidate | Total ≥ 7.5, Breakout score ≥ 7, Volume score ≥ 6 |
| Pre-breakout | Total ≥ 5.5, Trend score ≥ 5 |
| Watchlist | Total ≥ 3.5 |
| Avoid | Total < 3.5 or Penalty ≥ 8 |

Penalty override: any ticker with Penalty ≥ 8 is forced to **Avoid** regardless of other scores.

All thresholds and weights are configurable in `config/signal_rules.yaml` — no code changes needed.

---

## Configuration

### `config/settings.py`

| Constant | Default | Description |
|---|---|---|
| `LOOKBACK_YEARS` | 3 | Years of history to download |
| `BATCH_SIZE` | 20 | Tickers per yfinance batch request |
| `MAX_GAP_FILL_DAYS` | 2 | Max trading days to forward-fill |
| `EXPORT_TOP_N` | 20 | Top N tickers per class in ranked output |
| `BACKTEST_WINDOWS` | [3, 5, 10] | Forward return windows (trading days) |

### `config/signal_rules.yaml`

Edit scoring weights, RSI thresholds, volume ratios, and classification cutoffs without touching Python code.

---

## Backtest Metrics

| Metric | Description |
|---|---|
| Hit Rate | % of signals with positive forward return |
| Avg Return | Mean forward return per window |
| Median Return | Median forward return |
| Max Drawdown | Worst intra-window loss from entry |
| Signals/Month | Volume of signals by class |

**Known biases (MVP stage):**
- **Survivorship bias** — universe only contains currently active tickers
- **Look-ahead bias** — mitigated by using only data ≤ signal date for feature computation
- **Small sample** — minimum ~30 signals per class needed for statistically meaningful conclusions

---

## Extending the System

**Swap data provider:** Implement `BaseFetcher` in `app/data/fetch_base.py` and pass the new fetcher to `run_daily_scan.py`. No other files need to change.

**Add a feature:** Add a function to the relevant module in `app/features/`, register the output column in `FEATURE_COLS` in `feature_builder.py`, and reference it in `scoring.py`.

**Adjust signal logic:** Edit `config/signal_rules.yaml` — no code required.

---

## Non-Goals (MVP)

- Real-time or intraday data
- Machine learning models
- Production frontend or dashboard
- Cloud deployment
- Telegram bot (formatter output is Telegram-ready; bot integration is a next step)
- Multi-user or authentication

---

## Requirements

- Python 3.11+
- yfinance, pandas, numpy, pyarrow, pyyaml

See `requirements.txt` for pinned versions.

---

## License

MIT
