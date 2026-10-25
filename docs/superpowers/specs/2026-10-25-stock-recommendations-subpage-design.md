# Stock Recommendations Sub-Page Design Specification

- **Date:** 2026-10-25
- **Status:** Complete / Approved for Implementation Planning
- **Target Route:** `/stocks`
- **Related Routes:** `/` (Options Recommender Pro)

---

## 1. Intent and The Why

The Options Recommender platform currently provides quantitative options contracts recommendations (calls/puts, strikes, expiries, Greeks). However, many traders either prefer trading underlying equity shares directly (avoiding theta decay, IV crush, and expiration risk) or want a dedicated equities scanner that complements their options strategies.

The goal is to introduce a dedicated sub-page (`/stocks`) that provides automated, high-confidence **Stock Recommendations** covering **1,000+ US equities**. It must mirror the visual design, interactive polish, and quantitative rigor of the Options Recommender while tailoring trade setups specifically for stock purchases (both short-term swing trades and long-term investment picks).

---

## 2. Goals, Non-Goals, and Anti-Goals

### Goals
- **Identical Visual Aesthetic:** Seamlessly adopt the deep-slate dark theme (`#070b14`), cyan/emerald accents, MarketRibbon, quick chips, and polished cards of the main options terminal.
- **Support All Horizons:** Provide dedicated tabs for **⚡ Short-Term Swing** (1–5 days, breakout momentum, tight stops) and **🌱 Long-Term Conviction** (weeks/months, multi-timeframe 20/50/200 DMA support, fundamental catalysts).
- **Dual Presentation Views:** Toggle between **Card Grid View** (visual setup cards with risk-reward gauges) and **Screener Table View** (data-dense sortable table with RSI, volume ratio, target return %, and sentiment).
- **1,000+ US Stock Universe:** Broad scanning covering the S&P 500, Nasdaq 100, and top liquid Russell 1000 names across 11 market sectors.
- **Automatic Background Refreshes:** Automated background cache updating to ensure instant (<100ms) UI page loads without hitting Yahoo Finance rate limits or stalling the client.
- **Actionable Trade Plans:** Explicit Entry Zone, Target 1, Target 2, Stop Loss price, and Risk/Reward ratio for every stock pick.
- **Stock Position Sizing Calculator:** Dynamic calculator computing exact share quantities based on account size and user risk tolerance.
- **TradingView Charting:** Interactive candlestick chart with SMA overlays for any selected stock.
- **Shared Watchlist & Paper Trading:** Star stocks to sync with the main watchlist and click "Paper Buy Shares" to execute simulated equity trades in the paper portfolio.

### Non-Goals
- Real-time millisecond level-2 book order execution (we are a quantitative suggester/screener, not an exchange broker-dealer).
- Options Greeks on this specific sub-page (options remain on `/`, while `/stocks` is pure equities).
- Mandatory paid third-party data APIs (system remains 100% free using `yfinance`, VADER sentiment, and quantitative formulas).

### Anti-Goals
- Sequential, un-cached on-demand scanning that causes the browser to freeze or take 2+ minutes to load.
- Disconnected visual design that feels like a separate, unstyled website.
- Generic buy/sell labels without concrete entry zones, profit targets, or stop losses.

---

## 3. Architecture & Technical Design

### A. Frontend Architecture (Next.js App Router)
- **New Page Route:** `frontend/src/app/stocks/page.tsx`
- **Navigation Integration:**
  - Header links/toggle added to both `frontend/src/app/page.tsx` and `frontend/src/app/stocks/page.tsx` allowing one-click switching between **"⚡ Options Suggester Pro"** and **"📈 Stock Picks Pro"**.
  - MarketRibbon component reused at the top for unified live market sentiment.
- **Components & Layout:**
  - `StockHeader`: Branding, mode switcher, global ticker search bar, quick leaders.
  - `HorizonTabs`: "All Recommendations", "⚡ Short-Term Swing (1–5d)", "🌱 Long-Term Growth (Weeks/Mo)", "🔥 Volume Breakouts".
  - `ViewToggle`: Toggle buttons for Card Grid (`grid`) vs Pro Table (`table`).
  - `StockCard`: Visual recommendation card with ticker, company name, sector badge, action tier (`STRONG BUY`, `BUY ACCUMULATE`), entry zone, TP1, TP2, stop loss, R:R ratio, sentiment tag, and "View Chart" / "Paper Buy" buttons.
  - `StockScreenerTable`: Sortable columns (Ticker, Sector, Horizon, Action, Price, 24h %, Vol Ratio, RSI, Target %, Sentiment, Actions).
  - `StockDeepDivePanel`: Active stock inspection panel featuring:
    - Interactive TradingView chart with 20/50/200 SMA overlays.
    - Trade Plan breakdown with rationales.
    - Stock Position Sizing widget (input: Portfolio Cash $ + Risk %, output: Shares to Buy + Capital Required).
    - News Sentiment feed with headline links and VADER compound score.
  - `PaperTradingModal`: Slide-over drawer / modal showing paper equity and options positions, live mark-to-market P&L, and one-click close position buttons.

### B. Backend Architecture (FastAPI + Python)
- **1,000+ Ticker Universe Registry (`data/stock_universe.py`):**
  - Predefined structured catalog of ~1,000+ liquid US equities categorized by sector (Technology, Healthcare, Financials, Consumer Discretionary, Communication Services, Industrials, Energy, Materials, Real Estate, Utilities, AI Ecosystem).
- **Stock Analysis & Trade Plan Engine (`analysis/stock_suggester.py`):**
  - Synthesizes technical momentum (RSI, multi-timeframe trend, 20d volume surge, ATR), news sentiment, and earnings blackout checks.
  - Generates concrete stock trade plans:
    - `entry_zone`: `[price * 0.99, price * 1.005]` (or support pullback)
    - `tp1`: `price + (1.5 * ATR)` (quick swing target)
    - `tp2`: `price + (3.0 * ATR)` (runner target)
    - `stop_loss`: `price - (1.2 * ATR)` (invalidation level)
    - `risk_reward_ratio`: `(tp1 - price) / (price - stop_loss)`
    - `horizon`: `"SWING"` or `"LONG_TERM"` based on trend duration and volatility.
- **Background Screener & Cache Manager (`analysis/screener_cache.py`):**
  - Background daemon thread/task running an automatic refresh loop (every 15 minutes during market hours, or cached to disk/memory).
  - Uses batch price downloads via `yfinance` to ingest price and volume metrics rapidly.
  - Pre-computes top 100+ ranked recommendations and stores them in an in-memory thread-safe cache.
- **REST Endpoints (`api.py`):**
  - `GET /api/stocks/recommendations?horizon={all|swing|long_term}&sector={all|tech|...}&view={cards|table}&search=&limit=50&offset=0`
  - `GET /api/stocks/analysis?symbol={ticker}` (on-demand deep dive analysis for any stock in or outside the 1,000+ universe)
  - `GET /api/stocks/universe` (list of available sectors and ticker counts)
  - `GET /api/stocks/status` (cache timestamp, next refresh time, total stocks tracked)
  - `POST /api/stocks/refresh` (manual trigger to force cache invalidation if needed)
  - `POST /api/paper-quotes` (extended to quote both equity tickers and option contracts seamlessly)

### C. Paper Trading Architecture & Storage
- **Storage Model (Client-Side `localStorage`):** Retains the application's clean, zero-friction client-side architecture (`options_paper_positions`, `options_paper_balance`).
- **Data Model:** Extends position schema to include `asset_type: "STOCK" | "OPTION"`.
  - For stocks: stores `shares`, `entry_price`, `current_price`, `stop_loss`, `target_price`.
  - P&L = `(Current Price - Execution Price) * Shares`.
- **Execution Flow:** Clicking "Paper Buy" opens the position sizing widget in `StockDeepDivePanel` or a quick confirmation dialog with pre-calculated share sizes based on available virtual cash. Fills immediately into `localStorage` with a confirmation toast.

---

## 4. Architectural Calls Made
1. **Paper Trading Storage:** Kept client-side in `localStorage` matching the existing options paper trading pattern, avoiding unnecessary database bloat while providing instant response times.
2. **Paper Trading UX:** Embedded quick-view modal on `/stocks` with a direct link to the full `/` portfolio tab, plus immediate one-click execution from the position sizing calculator.
3. **Shared Watchlist:** Reuses `options_starred_tickers` from `localStorage`. Added a "⭐ Starred" filter chip on `/stocks` and an optional "Stock Plan" action button in `StarredWatchlistView.tsx`.
4. **1,000+ Universe Caching:** Implemented in `analysis/screener_cache.py` using thread-safe in-memory caching with batch downloads, refreshed every 15 minutes during market hours.

---

## 5. Left to the Builder
- Selection of the specific top 1,000+ liquid stock list from major indices (S&P 500, Nasdaq 100, Russell 1000).
- Specific test fixtures and mocks for testing the background worker and API endpoints without hitting external network during test suites.
