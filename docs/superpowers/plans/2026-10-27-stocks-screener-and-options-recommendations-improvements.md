# Stocks Screener & Options Recommendations Improvements Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Elevate both the Stocks Screener (`/stocks`) and Options Recommendations (`/`) with institutional-grade selection filters (VCP squeeze, Minervini Stage 2, Institutional Inflow, Velocity Breakouts), upcoming earnings blackout countdowns, CSV exports, side-by-side stock comparison, an on-demand dynamic option contract generator for any screened ticker, interactive payoff diagrams on home cards, defined-risk spread toggles, and theta burn exit timers.

**Architecture:** 
1. **Backend Extensions:**
   - Enhance `analysis/stock_suggester.py` and `analysis/screener_cache.py` with multi-filter query support (price brackets, strategy presets, min R:R, upcoming earnings blackout proximity).
   - Expose dynamic `/api/options/recommend` endpoint in `api.py` to synthesize optimal Delta-targeted options recommendations and vertical debit spreads on-demand for any given ticker symbol.
   - Add earnings date and blackout countdown retrieval to screener cache items.
2. **Frontend Enhancements:**
   - Enhance `StockScreenerTable.tsx` and `StockCard.tsx` with strategy preset quick-chips, price range filters, earnings blackout warning tags, 1-click CSV export, and a "Find Best Option" action button.
   - Build `StockComparisonDrawer.tsx` allowing head-to-head comparison of up to 3 screened equities.
   - Enhance `BestOptionsHome.tsx` with a Payoff Diagram modal, Defined-Risk Spread toggle, Theta cliff exit countdown, and quick Paper Trading position management.

**Tech Stack:** Python 3.11+, FastAPI, yfinance, pandas, numpy, Next.js 14+ (App Router), React, TypeScript, Tailwind CSS, Lucide icons, Lightweight Charts (TradingView).

**Spec:** Synthesized from user requirements for comprehensive stock screening enhancements and actionable options recommendation upgrades.

## Global Constraints

- Must run 100% free with no paid third-party API keys required (using `yfinance` + VADER sentiment + Black-Scholes Greeks).
- Must adhere to the dark quantitative terminal aesthetic: `#070b14` canvas, `#0a1120` container, cyan (`#06b6d4`), emerald (`#10b981`), amber (`#f59e0b`), rose (`#f43f5e`), purple (`#a855f7`) accents, `#1e293b` borders.
- Container memory usage must remain strictly bounded (< 120MB RSS) using bounded cache sizes and avoiding unbounded concurrent requests.
- All paper trading additions must remain compatible with `localStorage` keys `options_paper_positions` and `options_paper_balance`.
- Every backend change must have corresponding pytest coverage and all existing 51 tests must continue to pass.

## Review Focus

1. **Earnings Date Fallbacks:** If `yfinance` has incomplete earnings calendar data for a small-cap ticker, the system must gracefully handle `None` without crashing or mislabeling blackout status.
2. **On-Demand Options Chain Availability:** If an equity has no active options chain (illiquid or penny stock), `/api/options/recommend` must return a clear informative status instead of raising 500 errors.
3. **Filter Combination Multi-Select:** When combining multiple filters (e.g., Minervini Stage 2 + Price under $50 + R:R >= 2.0), the screener must return empty results gracefully with a reset action if no matches exist.
4. **CSV Export Data Formatting:** Ensure numeric indicators (percentages, dollar values, dates) in the CSV export are formatted cleanly and escaped for spreadsheet compatibility.
5. **Payload Size & Memory Optimization:** On-demand option recommendations must only fetch necessary near-the-money chain slices to prevent container memory bloat on Render.

---

### Task 1: Screener Backend Multi-Filter & Earnings Proximity Enhancements

**Files:**
- Modify: `analysis/stock_suggester.py`
- Modify: `analysis/screener_cache.py`
- Modify: `api.py`
- Test: `tests/test_stock_screener_filters.py`

**Interfaces:**
- Consumes:
  - `data.price_data.get_earnings_info`
  - `analysis.stock_suggester.StockRecommendation`
- Produces:
  - Extended `StockRecommendation` fields:
    - `earnings_days_away: Optional[int]`
    - `is_earnings_imminent: bool` (within 7 days)
    - `market_cap_tier: str` ("MEGA", "LARGE", "MID", "SMALL")
  - Extended `StockScreenerCache.get_recommendations()` query parameters:
    - `strategy_preset: Optional[str]` ("STAGE_2_LEADERS", "VCP_SQUEEZES", "INSTITUTIONAL_INFLOW", "VELOCITY_BREAKOUT", "PULLBACK_DIP")
    - `min_price: Optional[float]`, `max_price: Optional[float]`
    - `min_rr: Optional[float]`
    - `exclude_earnings_blackout: bool`

- [ ] **Step 1: Write failing tests for screener multi-filters and earnings proximity**
  Create `tests/test_stock_screener_filters.py` with:
  - `test_screener_cache_strategy_preset_filtering()`: verifies `strategy_preset="STAGE_2_LEADERS"` returns only stage 2 stocks.
  - `test_screener_cache_price_range_filtering()`: verifies `min_price=50` and `max_price=150` filters correctly.
  - `test_screener_cache_min_rr_filtering()`: verifies `min_rr=2.0` filters items with `risk_reward_ratio >= 2.0`.
  - `test_screener_cache_earnings_proximity_flag()`: verifies stocks with upcoming earnings include `earnings_days_away` and `is_earnings_imminent`.

- [ ] **Step 2: Run test to verify failure**
  Run: `.venv\Scripts\python.exe -m pytest tests/test_stock_screener_filters.py -v`
  Expected: FAIL (`ModuleNotFoundError` or assertion error).

- [ ] **Step 3: Implement filter logic in `analysis/stock_suggester.py` and `analysis/screener_cache.py`**
  - Add `earnings_days_away` and `is_earnings_imminent` to `StockRecommendation` and populate them during analysis.
  - Update `StockScreenerCache.get_recommendations()` to filter by `strategy_preset`, `min_price`, `max_price`, `min_rr`, and `exclude_earnings_blackout`.
  - Expose query parameters in `GET /api/stocks/recommendations` in `api.py`.

- [ ] **Step 4: Run test to verify it passes**
  Run: `.venv\Scripts\python.exe -m pytest tests/test_stock_screener_filters.py -v`
  Expected: PASS.

- [ ] **Step 5: Commit**
  Run: `git add analysis/stock_suggester.py analysis/screener_cache.py api.py tests/test_stock_screener_filters.py && git commit -m "feat(screener): add strategy presets, price ranges, min R:R, and earnings blackout proximity filters"`

---

### Task 2: Dynamic On-Demand Options Recommendation Endpoint for Any Stock

**Files:**
- Modify: `api.py`
- Test: `tests/test_dynamic_options_endpoint.py`

**Interfaces:**
- Consumes:
  - `data.price_data.get_current_quote`
  - `data.price_data.get_price_history`
  - `data.options_data.get_options_chains`
  - `options.suggester.suggest_options`
- Produces:
  - Endpoint: `GET /api/options/recommend?ticker=XYZ&bias=BULLISH&min_dte=14&max_dte=45`
  - Returns:
    - `symbol`: str
    - `stock_price`: float
    - `bias`: str
    - `single_leg`: top Delta 0.40–0.50 option with Greeks, strike, breakeven, POP %, and TP1/Stop loss trade plan.
    - `vertical_spread`: defined-risk debit spread with long strike, short strike, net debit, max profit, and R:R.
    - `moonshot_setup`: asymmetric lotto setup if available.

- [ ] **Step 1: Write failing tests for dynamic options recommendation**
  Create `tests/test_dynamic_options_endpoint.py`:
  - `test_api_options_recommend_valid_stock()`: calls `/api/options/recommend?ticker=NVDA` with mocked options chain and verifies returned single_leg and vertical_spread structure.
  - `test_api_options_recommend_missing_chain()`: verifies ticker with no options returns clean 404 or `has_options: false`.
  - `test_api_options_recommend_respects_bias()`: verifies `bias=BEARISH` recommends a PUT contract.

- [ ] **Step 2: Run test to verify failure**
  Run: `.venv\Scripts\python.exe -m pytest tests/test_dynamic_options_endpoint.py -v`
  Expected: FAIL (`404 Not Found`).

- [ ] **Step 3: Implement `/api/options/recommend` in `api.py`**
  - Implement handler that queries the stock quote, analyzes recent momentum for bias (or uses requested bias), retrieves near-the-money calls and puts slice, runs `suggest_options`, and formats the response with Greeks, trade plans, and spread alternatives.

- [ ] **Step 4: Run test to verify it passes**
  Run: `.venv\Scripts\python.exe -m pytest tests/test_dynamic_options_endpoint.py -v`
  Expected: PASS.

- [ ] **Step 5: Commit**
  Run: `git add api.py tests/test_dynamic_options_endpoint.py && git commit -m "feat(options): add dynamic on-demand options and vertical spread recommendation endpoint"`

---

### Task 3: Stocks Screener UI Improvements (Presets, Earnings Badges, CSV Export & "Find Option" Action)

**Files:**
- Modify: `frontend/src/components/StockCard.tsx`
- Modify: `frontend/src/components/StockScreenerTable.tsx`
- Modify: `frontend/src/app/stocks/page.tsx`

**Interfaces:**
- Consumes:
  - Extended `/api/stocks/recommendations` with presets and earnings proximity.
- Produces:
  - Strategy preset chips bar on `/stocks`:
    - `⚡ All Setups`
    - `🏆 Minervini Stage 2`
    - `🗜️ VCP Squeezes`
    - `🏦 Institutional Inflow A+`
    - `🚀 Velocity Breakouts`
    - `📉 Pullback Dips`
  - Price Range dropdown selector ($0-$25, $25-$100, $100-$250, $250+).
  - Earnings warning countdown badge on cards and table rows (`⚠️ Earnings in Xd`).
  - "Export to CSV" button generating and downloading `.csv` file.
  - "Find Best Option" button on each card and table row linking directly to the Options Terminal for that symbol.

- [ ] **Step 1: Add strategy presets and price range selectors to `stocks/page.tsx`**
  - Wire state and query params to call `/api/stocks/recommendations`.
  - Render styled preset pills matching cyan/emerald aesthetic.

- [ ] **Step 2: Update `StockCard.tsx` and `StockScreenerTable.tsx`**
  - Display earnings countdown pill when `earnings_days_away` <= 14.
  - Add "Find Option" button (`<Zap className="h-3 w-3" />`) that links or passes callback to options view.

- [ ] **Step 3: Implement CSV Export utility in `stocks/page.tsx`**
  - Convert active filtered recommendations array to standard CSV format and trigger instant browser download (`stocks_screener_export_<date>.csv`).

- [ ] **Step 4: Run build check**
  Run: `cd frontend && npm run build`
  Expected: Compiled successfully with 0 errors.

- [ ] **Step 5: Commit**
  Run: `git add frontend/src/components/StockCard.tsx frontend/src/components/StockScreenerTable.tsx frontend/src/app/stocks/page.tsx && git commit -m "feat(stocks): add strategy presets, price range filters, earnings badges, and CSV export"`

---

### Task 4: Side-by-Side Stock Comparison Drawer

**Files:**
- Create: `frontend/src/components/StockComparisonDrawer.tsx`
- Modify: `frontend/src/app/stocks/page.tsx`

**Interfaces:**
- Consumes:
  - Array of up to 3 selected `StockRecommendation` items.
- Produces:
  - Slide-up or overlay comparison drawer with head-to-head metrics:
    - Score & Action tier
    - Relative Strength percentile & Minervini Stage 2 status
    - 3D/5D ROC & 8/21 EMA spread
    - Up/Down volume ratio & Accumulation rating
    - ATR volatility & Invalidation risk %
    - Target 1 & Target 2 potential gain %
    - 1-click "Paper Buy" or "Analyze" button for each compared stock.

- [ ] **Step 1: Create `StockComparisonDrawer.tsx`**
  - Implement multi-column comparative card layout with color-coded winner highlights (highest RS, highest score, best R:R).

- [ ] **Step 2: Integrate comparison selection in `stocks/page.tsx`**
  - Add comparison checkbox to `StockCard.tsx` and `StockScreenerTable.tsx`.
  - Show floating comparison counter bar (`2 of 3 selected - Compare Now`) when stocks are selected.

- [ ] **Step 3: Run build check**
  Run: `cd frontend && npm run build`
  Expected: Compiled successfully.

- [ ] **Step 4: Commit**
  Run: `git add frontend/src/components/StockComparisonDrawer.tsx frontend/src/app/stocks/page.tsx && git commit -m "feat(stocks): implement multi-stock head-to-head comparison drawer"`

---

### Task 5: Options Recommendations UI Improvements (Interactive Payoff, Spread Toggle & Theta Timers)

**Files:**
- Create: `frontend/src/components/OptionPayoffModal.tsx`
- Modify: `frontend/src/components/BestOptionsHome.tsx`
- Modify: `frontend/src/app/page.tsx`

**Interfaces:**
- Consumes:
  - `OptionRecommendation` object with strike, ask, type, delta, theta, tp1, stop loss, and spread data.
- Produces:
  - Interactive Payoff curve modal showing P&L across underlying stock prices at expiration.
  - "Naked Call/Put" vs "Defined-Risk Vertical Spread" toggle on recommendation cards.
  - Theta Cliff countdown indicator ("Optimal exit: Day 4–12; exit before 21 DTE to avoid rapid theta burn").
  - Quick Paper Trading status chip showing if the position is already active in the paper portfolio.

- [ ] **Step 1: Create `OptionPayoffModal.tsx`**
  - SVG or canvas-based visual payoff curve plotting underlying stock price on the X-axis and profit/loss on the Y-axis.
  - Highlights Breakeven, Max Loss, Target 1 (+75%), and Target 2 (+150%).

- [ ] **Step 2: Enhance `BestOptionsHome.tsx`**
  - Add "Payoff Curve" button to open `OptionPayoffModal`.
  - Add Single-Leg vs Debit Spread toggle allowing traders to choose between unlimited upside calls or defined-risk vertical spreads.
  - Add Theta decay cliff indicator and optimal holding days badge.
  - Display paper trading badge if contract is already open in portfolio.

- [ ] **Step 3: Run build check**
  Run: `cd frontend && npm run build`
  Expected: Compiled successfully with 0 errors.

- [ ] **Step 4: Commit**
  Run: `git add frontend/src/components/OptionPayoffModal.tsx frontend/src/components/BestOptionsHome.tsx frontend/src/app/page.tsx && git commit -m "feat(options): add interactive payoff modal, defined-risk spread toggle, and theta decay timers to recommendations"`

---

### Task 6: End-to-End System Verification & Regression Suite

**Files:**
- Verify all Python test suites in `tests/`
- Verify Next.js frontend production build

- [ ] **Step 1: Run complete pytest test suite**
  Run: `.venv\Scripts\python.exe -m pytest tests/ -v`
  Expected: All 51+ tests pass with 0 errors.

- [ ] **Step 2: Run frontend production build check**
  Run: `cd frontend && npm run build`
  Expected: Full production build passes with 0 TypeScript and lint errors.

- [ ] **Step 3: Verify memory footprint**
  Run health endpoint check (`/api/health`) to confirm RSS memory remains < 120MB.

- [ ] **Step 4: Final commit**
  Run: `git commit -am "chore: verify end-to-end stock screener and options recommendation improvements"`
