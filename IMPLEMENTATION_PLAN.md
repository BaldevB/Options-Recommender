# Implementation Plan: US Stock Options Suggester (No Finnhub)

A modular, free-tier US stock options suggestion engine utilizing Yahoo Finance (`yfinance`) for market data and options chains, combined with VADER sentiment and technical momentum indicators.

## 1. System Overview & Architecture

```
Optionsrecommender/
├── config.py              # User settings, thresholds, DTE bounds, weights
├── data/
│   ├── __init__.py
│   ├── price_data.py      # yfinance OHLCV historical data & live quotes
│   ├── news_data.py       # yfinance news headline retrieval & normalization
│   └── options_data.py    # yfinance options chain retrieval & DTE filtering
├── analysis/
│   ├── __init__.py
│   ├── momentum.py        # Technical indicators (RSI-14, MACD, SMA20/50, Volume Ratio)
│   ├── sentiment.py       # VADER sentiment analysis on news headlines
│   └── signals.py         # Signal synthesis: weighted scoring, bias, & confidence
├── options/
│   ├── __init__.py
│   └── suggester.py       # Contract filtering (liquidity, delta/moneyness, spread) & ranking
├── main.py                # Rich CLI interface for single ticker & watchlist scanning
├── app.py                 # Streamlit web application with interactive charts and tables
├── requirements.txt       # Dependencies (yfinance, pandas, numpy, vaderSentiment, streamlit, rich)
├── README.md              # Documentation, setup guide, and usage examples
└── .agents/skills/options-suggester/SKILL.md # Antigravity skill specification
```

---

## 2. Component Specifications

### 2.1 Configuration (`config.py`)
- **Default Watchlist**: Liquid US stocks (`AAPL`, `MSFT`, `NVDA`, `TSLA`, `AMD`, `AMZN`, `GOOGL`, `META`, `SPY`, `QQQ`).
- **Technical Indicator Parameters**:
  - RSI period: 14 (Oversold < 30, Overbought > 70)
  - MACD fast: 12, slow: 26, signal: 9
  - Short SMA: 20, Long SMA: 50
  - Volume window: 20 days
- **Weights & Thresholds**:
  - Momentum weight: 0.60
  - Sentiment weight: 0.40
  - Confidence threshold for suggestions: 0.20
- **Options Filtering**:
  - DTE range: 14 to 45 days
  - Minimum Open Interest: 100
  - Minimum Volume: 20
  - Maximum Bid-Ask Spread ratio: 0.25 (spread / ask)
  - Moneyness / Delta targeting: Near-The-Money / slightly OTM (0.95 to 1.08 of spot price)

### 2.2 Data Layer (`data/`)
- **`price_data.py`**:
  - Fetches 6-month to 1-year daily OHLCV bars via `yfinance`.
  - Fetches real-time / delayed current quote (`regularMarketPrice`, `dayHigh`, `dayLow`, 52-week ranges).
  - Robust exception handling and fallback for ticker validity.
- **`news_data.py`**:
  - Fetches news from `yf.Ticker(symbol).news`.
  - Handles variations in Yahoo Finance news schema (both modern `content.title` and legacy `title`).
  - Cleans headline timestamps and publishers.
- **`options_data.py`**:
  - Retrieves available expiration dates.
  - Filters expirations within target DTE (14 to 45 days).
  - Fetches Call and Put chains, sanitizing columns (`bid`, `ask`, `volume`, `openInterest`, `impliedVolatility`).

### 2.3 Analysis Layer (`analysis/`)
- **`momentum.py`**:
  - Pure pandas/numpy calculation of:
    - RSI-14
    - MACD line, Signal line, MACD Histogram
    - SMA20 vs SMA50 crossover status & price distance
    - Volume ratio (current volume vs 20-day SMA volume)
  - Normalized momentum score between `-1.0` (strongly bearish) and `+1.0` (strongly bullish).
- **`sentiment.py`**:
  - Local `vaderSentiment.SentimentIntensityAnalyzer`.
  - Scores individual headlines (compound score) with recency weighting.
  - Aggregates overall news sentiment score between `-1.0` and `+1.0`.
- **`signals.py`**:
  - Blends momentum score and sentiment score using configured weights.
  - Produces:
    - **Directional Bias**: `BULLISH`, `BEARISH`, or `NEUTRAL`.
    - **Confidence Score**: `0.0` to `1.0`.
    - **Summary Rationale**: Human-readable bullet points explaining the signal.

### 2.4 Options Suggester Layer (`options/`)
- **`suggester.py`**:
  - Given directional bias and confidence:
    - If `BULLISH`: Targets Calls.
    - If `BEARISH`: Targets Puts.
    - If `NEUTRAL`: Highlights neutral condition and risk.
  - Applies strict liquidity filters:
    - Bid > 0.05, Ask > Bid
    - Spread ratio <= 25%
    - Volume >= 20, Open Interest >= 100
  - Computes ranking score:
    - Balances liquidity (volume + OI), spread tightness, and delta/strike proximity.
  - Formats top 3 to 5 ranked contracts with risk notes (IV, break-even price, max loss = premium).

### 2.5 Presentation Layer
- **`main.py` (CLI)**:
  - Supports `--ticker <SYMBOL>` for single stock deep dive.
  - Supports `--scan` for running across watchlist.
  - Uses `rich` tables and colored badges for clear visual output.
  - Displays explicit **"NOT FINANCIAL ADVICE"** disclaimer.
- **`app.py` (Streamlit UI)**:
  - Interactive sidebar: select or input ticker, customize DTE, adjust indicator weights.
  - Metrics cards: Current Price, Trend, Momentum Score, Sentiment Score, Signal.
  - Interactive price chart with SMA20/50 and volume.
  - News headlines table with sentiment breakdown.
  - Filtered & ranked options recommendation table with interactive strike selection.

---

## 3. Step-by-Step Execution Plan

1. **Environment & Dependency Setup**:
   - Create `requirements.txt` containing `yfinance`, `pandas`, `numpy`, `vaderSentiment`, `streamlit`, `rich`, `python-dotenv`.
   - Install packages into the local virtual environment `.venv`.
2. **Directory Structure Creation**:
   - Create `data/`, `analysis/`, and `options/` packages.
3. **Core Module Implementation**:
   - Write `config.py`
   - Write `data/price_data.py`, `data/news_data.py`, `data/options_data.py`
   - Write `analysis/momentum.py`, `analysis/sentiment.py`, `analysis/signals.py`
   - Write `options/suggester.py`
4. **Application Interfaces**:
   - Write `main.py` (CLI with rich formatted tables and arguments)
   - Write `app.py` (Streamlit web application)
   - Write `README.md`
5. **Validation & Verification**:
   - Run CLI test against liquid tickers (e.g., `AAPL`, `NVDA`, `SPY`).
   - Verify indicator calculations, news retrieval, sentiment scoring, and options filtering.
   - Verify Streamlit syntax and startup.
