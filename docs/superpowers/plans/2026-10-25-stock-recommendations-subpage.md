# Stock Recommendations Sub-Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and launch a dedicated `/stocks` quantitative stock recommendations sub-page with dual views (Card Grid + Screener Table), covering 1,000+ US equities with automated background caching, exact trade plans, position sizing, and paper trading integration.

**Architecture:** A high-throughput batch screener and cache engine in Python/FastAPI (`data/stock_universe.py`, `analysis/stock_suggester.py`, `analysis/screener_cache.py`) feeds instant-response REST endpoints. The Next.js frontend (`frontend/src/app/stocks/page.tsx`) renders the sub-page matching the exact dark slate/cyan terminal aesthetic of the Options Recommender, integrating TradingView charting, horizon tabs, dual view toggles, and client-side paper trading execution.

**Tech Stack:** Python 3.11+, FastAPI, yfinance, pandas, numpy, Next.js 14+ (App Router), React, TypeScript, Tailwind CSS, Lucide icons, Lightweight Charts (TradingView).

**Spec:** `docs/superpowers/specs/2026-10-25-stock-recommendations-subpage-design.md`

## Global Constraints

- Must run 100% free with no paid third-party API keys required (using `yfinance` + VADER sentiment).
- Must adhere to the dark quantitative aesthetic: `#070b14` canvas, `#0d1424` container, cyan (`#22d3ee`) and emerald (`#10b981`) accents, `#1e293b` borders.
- Sub-page UI must be responsive across desktop and tablet/mobile viewports.
- 1,000+ stock screener endpoint must respond in sub-second time via thread-safe in-memory caching to prevent API rate limits.
- Paper trading positions must be preserved client-side in `localStorage` under `options_paper_positions` with `asset_type: "STOCK"` support.

## Review Focus

1. **Missing or Stale Stock Price Data:** If Yahoo Finance fails or returns empty data for a specific ticker during a batch scan, the system must gracefully omit that ticker without breaking the entire screener or throwing 500 errors.
2. **Extreme Volatility / Outliers:** High ATR or penny stock extremes must have bounded profit targets and stop losses (e.g. stop loss cannot be negative or zero; targets capped reasonably).
3. **Cache Expiry / Market Close Handling:** When off-hours, the background cache must serve the latest closing day scan without continuous redundant API hammering.
4. **Fractional vs Whole Shares in Position Sizing:** Position sizing calculator must produce integer whole shares by floor division to match standard equity execution rules.
5. **Route Navigation State Retention:** Switching between `/` (Options) and `/stocks` must seamlessly retain starred tickers in `localStorage` without resetting or corrupting state.

---

### Task 1: 1,000+ US Stock Universe Catalog

**Files:**
- Create: `data/stock_universe.py`
- Test: `tests/test_stock_universe.py`

**Interfaces:**
- Produces:
  - `STOCK_SECTORS: Dict[str, str]` (sector key to human-readable name)
  - `STOCK_UNIVERSE: List[Dict[str, str]]` (~1,000+ items: `{"symbol": str, "name": str, "sector": str, "market_cap_tier": str}`)
  - `get_stock_universe(sector: Optional[str] = None) -> List[Dict[str, str]]`
  - `get_stock_metadata(symbol: str) -> Optional[Dict[str, str]]`

- [ ] **Step 1: Write failing tests for stock universe catalog**
  Create `tests/test_stock_universe.py`:
  - `test_stock_universe_contains_over_1000_stocks()`: asserts `len(get_stock_universe()) >= 1000`.
  - `test_stock_universe_sector_filtering()`: asserts filtering by `"technology"` returns only technology stocks.
  - `test_get_stock_metadata_found()`: asserts lookup for `"NVDA"` returns symbol, name, and sector.
  - `test_get_stock_metadata_not_found()`: asserts lookup for `"UNKNOWN"` returns `None`.

- [ ] **Step 2: Run test to verify failure**
  Run: `pytest tests/test_stock_universe.py -v`
  Expected: FAIL (`ModuleNotFoundError: No module named 'data.stock_universe'`)

- [ ] **Step 3: Implement `data/stock_universe.py`**
  Compile comprehensive 1,000+ ticker dictionary covering S&P 500, Nasdaq 100, and liquid mid/large caps categorized across 11 GICS sectors (Technology, Healthcare, Financials, Consumer Discretionary, Consumer Staples, Communication Services, Industrials, Energy, Materials, Real Estate, Utilities, and AI/Specialty). Provide lookup and filter helper functions.

- [ ] **Step 4: Run test to verify it passes**
  Run: `pytest tests/test_stock_universe.py -v`
  Expected: PASS

- [ ] **Step 5: Commit**
  Run: `git add data/stock_universe.py tests/test_stock_universe.py && git commit -m "feat: add 1000+ stock universe catalog and sector filters"`

---

### Task 2: Quantitative Stock Recommendation Engine

**Files:**
- Create: `analysis/stock_suggester.py`
- Test: `tests/test_stock_suggester.py`

**Interfaces:**
- Consumes:
  - `analysis.momentum.MomentumResult`
  - `analysis.sentiment.SentimentResult`
  - `data.price_data.QuoteData`
- Produces:
  - `TradeHorizon(str, Enum): SWING = "SWING", LONG_TERM = "LONG_TERM"`
  - `StockTradePlan`: dataclass with `entry_zone: Tuple[float, float]`, `current_price: float`, `tp1: float`, `tp2: float`, `stop_loss: float`, `risk_reward_ratio: float`, `invalidation_pct: float`, `tp1_pct: float`, `tp2_pct: float`
  - `StockRecommendation`: dataclass with `symbol`, `name`, `sector`, `horizon: TradeHorizon`, `action: str`, `score: float`, `confidence: float`, `momentum_score: float`, `sentiment_score: float`, `trade_plan: StockTradePlan`, `rationale: List[str]`
  - `generate_stock_recommendation(...) -> StockRecommendation`
  - `calculate_stock_shares(cash: float, risk_pct: float, entry_price: float, stop_loss: float) -> Dict[str, Any]`

- [ ] **Step 1: Write failing tests for stock suggester**
  Create `tests/test_stock_suggester.py`:
  - `test_generate_stock_recommendation_bullish_swing()`: asserts strong momentum creates `SWING` setup with valid `tp1 > current_price > stop_loss` and `risk_reward_ratio >= 1.5`.
  - `test_generate_stock_recommendation_long_term()`: asserts trend alignment with low beta creates `LONG_TERM` setup with wider targets.
  - `test_calculate_stock_shares_normal()`: asserts risk allocation of \$10,000 cash at 2% risk with \$100 entry and \$95 stop produces 40 shares.
  - `test_calculate_stock_shares_zero_risk_fallback()`: handles zero or invalid stop without dividing by zero.

- [ ] **Step 2: Run test to verify failure**
  Run: `pytest tests/test_stock_suggester.py -v`
  Expected: FAIL (`ModuleNotFoundError: No module named 'analysis.stock_suggester'`)

- [ ] **Step 3: Implement `analysis/stock_suggester.py`**
  Implement ATR-based target and stop calculation, horizon classification based on momentum velocity vs moving average structure, risk-reward calculation, and integer share position sizing.

- [ ] **Step 4: Run test to verify it passes**
  Run: `pytest tests/test_stock_suggester.py -v`
  Expected: PASS

- [ ] **Step 5: Commit**
  Run: `git add analysis/stock_suggester.py tests/test_stock_suggester.py && git commit -m "feat: implement quantitative stock recommendation and trade plan engine"`

---

### Task 3: Screener Cache & Intraday Background Refresh Manager

**Files:**
- Create: `analysis/screener_cache.py`
- Test: `tests/test_screener_cache.py`

**Interfaces:**
- Consumes:
  - `data.stock_universe.get_stock_universe`
  - `analysis.stock_suggester.generate_stock_recommendation`
- Produces:
  - `StockScreenerCache`: thread-safe singleton cache with:
    - `get_recommendations(horizon=None, sector=None, search=None, sort_by="score", limit=50, offset=0) -> Dict[str, Any]`
    - `get_analysis(symbol: str) -> Optional[Dict[str, Any]]`
    - `get_status() -> Dict[str, Any]`
    - `refresh_cache(force=False) -> Dict[str, Any]`
    - `start_background_worker(interval_minutes=15)`

- [ ] **Step 1: Write failing tests for screener cache**
  Create `tests/test_screener_cache.py`:
  - `test_screener_cache_query_and_filter()`: loads mock data and tests filtering by sector and horizon.
  - `test_screener_cache_pagination()`: verifies limit and offset slice correctly.
  - `test_screener_cache_thread_safe_update()`: updates cache in background and verifies no race conditions.

- [ ] **Step 2: Run test to verify failure**
  Run: `pytest tests/test_screener_cache.py -v`
  Expected: FAIL (`ModuleNotFoundError: No module named 'analysis.screener_cache'`)

- [ ] **Step 3: Implement `analysis/screener_cache.py`**
  Implement batch downloading via `yfinance.download(tickers, period='3mo', group_by='ticker')`, calculate momentum and stock trade plans, rank by score, store in a thread-safe dict, and provide query/filter methods with background timer refresh.

- [ ] **Step 4: Run test to verify it passes**
  Run: `pytest tests/test_screener_cache.py -v`
  Expected: PASS

- [ ] **Step 5: Commit**
  Run: `git add analysis/screener_cache.py tests/test_screener_cache.py && git commit -m "feat: implement high-speed screener cache with background batch refresh"`

---

### Task 4: FastAPI REST Endpoints & Paper Trading Extensions

**Files:**
- Modify: `api.py`
- Test: `tests/test_stock_api.py`

**Interfaces:**
- Produces Endpoints:
  - `GET /api/stocks/recommendations`
  - `GET /api/stocks/analysis`
  - `GET /api/stocks/universe`
  - `GET /api/stocks/status`
  - `POST /api/stocks/refresh`
  - `POST /api/paper-quotes` (extended for `asset_type: "STOCK"`)

- [ ] **Step 1: Write failing tests for API endpoints**
  Create `tests/test_stock_api.py`:
  - `test_api_stocks_recommendations()`: queries `/api/stocks/recommendations` and asserts 200 OK with list of results.
  - `test_api_stocks_universe()`: queries `/api/stocks/universe` and asserts list of sectors returned.
  - `test_api_stocks_analysis_symbol()`: queries `/api/stocks/analysis?symbol=NVDA` and asserts trade plan returned.
  - `test_api_paper_quotes_with_stocks()`: sends both option contracts and plain stock symbols to `/api/paper-quotes` and verifies quotes returned for both.

- [ ] **Step 2: Run test to verify failure**
  Run: `pytest tests/test_stock_api.py -v`
  Expected: FAIL (`404 Not Found`)

- [ ] **Step 3: Implement endpoints in `api.py`**
  Mount stock endpoints connecting to `StockScreenerCache`, add on-demand analysis handler with sanitization, and extend `/api/paper-quotes` to handle stock symbols.

- [ ] **Step 4: Run test to verify it passes**
  Run: `pytest tests/test_stock_api.py -v`
  Expected: PASS

- [ ] **Step 5: Commit**
  Run: `git add api.py tests/test_stock_api.py && git commit -m "feat: expose stock recommendations endpoints and extend paper quotes in FastAPI"`

---

### Task 5: Frontend Shared Navigation & Layout Switcher

**Files:**
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/src/components/MarketRibbon.tsx`
- Modify: `frontend/src/components/StarredWatchlistView.tsx`

**Interfaces:**
- Produces:
  - Header Route Switcher button between `/` (Options) and `/stocks` (Stocks).
  - Watchlist integration: "Stock Plan" button on starred tickers in `StarredWatchlistView.tsx` linking to `/stocks?symbol=XYZ`.

- [ ] **Step 1: Add top-level route switcher to `page.tsx`**
  In the top navbar branding area of `page.tsx`, add styled route links:
  - Active: "⚡ Options Pro" (current page)
  - Link: "📈 Stock Picks Pro" (`/stocks`) with hover styling and glow effect.

- [ ] **Step 2: Add "Stock Plan" action to `StarredWatchlistView.tsx`**
  Add a button for each starred ticker that navigates directly to `/stocks?symbol=${item.symbol}`.

- [ ] **Step 3: Commit**
  Run: `git add frontend/src/app/page.tsx frontend/src/components/StarredWatchlistView.tsx && git commit -m "feat: add cross-navigation between options terminal and stock picks"`

---

### Task 6: Stock Picks Sub-Page UI & Components

**Files:**
- Create: `frontend/src/app/stocks/page.tsx`
- Create: `frontend/src/components/StockCard.tsx`
- Create: `frontend/src/components/StockScreenerTable.tsx`
- Create: `frontend/src/components/StockPositionCalculator.tsx`
- Create: `frontend/src/components/StockPaperTradingDrawer.tsx`

**Interfaces:**
- Consumes:
  - `GET /api/stocks/recommendations`
  - `GET /api/stocks/analysis`
  - `POST /api/paper-quotes`
  - `components/StockChart.tsx` (TradingView chart)
  - `components/MarketRibbon.tsx`
- Produces:
  - Complete Next.js `/stocks` page supporting:
    - Horizon filter tabs (All, Swing Momentum, Long-Term Conviction, Breakouts)
    - View switcher (Card Grid vs Pro Screener Table)
    - Search bar & Sector dropdown filter
    - Interactive Deep-Dive panel with TradingView chart and Trade Plan
    - Stock Position Sizing Calculator
    - One-click "Paper Buy Shares" into `localStorage` paper portfolio
    - Slide-over Paper Portfolio Drawer with real-time stock and option P&L

- [ ] **Step 1: Create `StockCard.tsx`**
  Renders ticker, sector badge, action tier badge, current price, entry zone, target 1 & 2, stop loss, R:R ratio, sentiment badge, and "Deep Dive" & "Paper Buy" buttons.

- [ ] **Step 2: Create `StockScreenerTable.tsx`**
  Renders responsive sortable data table with Ticker, Sector, Horizon, Action, Price, 24h %, Vol Ratio, RSI, Target %, Sentiment, and quick action buttons.

- [ ] **Step 3: Create `StockPositionCalculator.tsx`**
  Provides cash input, risk % slider, calculates shares to buy and total capital at risk. Includes "Simulate Paper Buy" button.

- [ ] **Step 4: Create `StockPaperTradingDrawer.tsx`**
  Slide-over modal displaying active paper positions (stocks and options), live prices, unrealized P&L %, and close position action.

- [ ] **Step 5: Create `frontend/src/app/stocks/page.tsx`**
  Assembles header with MarketRibbon, route switcher, horizon tabs, search & sector filters, dual view switcher, deep dive inspection drawer/panel with TradingView `StockChart`, and paper portfolio toast notifications.

- [ ] **Step 6: Commit**
  Run: `git add frontend/src/app/stocks/page.tsx frontend/src/components/StockCard.tsx frontend/src/components/StockScreenerTable.tsx frontend/src/components/StockPositionCalculator.tsx frontend/src/components/StockPaperTradingDrawer.tsx && git commit -m "feat: implement full stock recommendations sub-page with dual views and paper trading"`

---

### Task 7: Full System Verification & End-to-End Build

**Files:**
- Verify all backend test suites
- Verify frontend Next.js production build

- [ ] **Step 1: Run all Python test suites**
  Run: `pytest tests/ -v`
  Expected: All tests pass.

- [ ] **Step 2: Run frontend Next.js build check**
  Run: `cd frontend && npm run build`
  Expected: Build succeeds with 0 errors and generates static/server routes for both `/` and `/stocks`.

- [ ] **Step 3: Run quick API sanity check**
  Verify `/api/stocks/recommendations` and `/api/stocks/universe` return valid data.

- [ ] **Step 4: Final commit**
  Run: `git commit -am "chore: verify end-to-end stock recommendations sub-page"`
