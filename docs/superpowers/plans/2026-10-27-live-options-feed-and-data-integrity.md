# Implementation Plan: Live Options Feed, Contract & Risk Eligibility, and Data Transparency

This plan upgrades the options recommendation engine and user interface to eliminate fabricated data, enforce strict risk budgets, separate last trade from quote retrieval time, clarify volatility methodology, and explain why contracts are selected or excluded.

---

### Global Constraints & Principles
1. **Zero Mock/Fabricated Data**:
   - No hardcoded option contracts or static market regime values in endpoints.
   - If market data or option chains are unavailable, return an honest empty state with status metadata.
   - Do not fabricate bid/ask prices around `lastPrice`.
2. **Strict Risk-to-Budget Enforcement**:
   - If an option's contract cost exceeds the risk allocation budget, `suggested_contracts` must be `0` (not forced to `1`).
   - Every Python and TypeScript caller must handle `0` contracts gracefully without defaulting `contracts || 1`.
3. **Execution & Market-Data Transparency**:
   - Clearly distinguish retrieval time (UTC) from last trade time.
   - Rename Volatility Cockpit IV Rank/Percentile to accurately describe its benchmark against historical realized volatility.
   - Long positions must illustrate entry at ask and exit at bid; state clearly that fees and slippage are excluded and midpoint fills are not guaranteed.
   - Label Black-Scholes probability of profit as a theoretical model estimate, not a proven historical win rate.
4. **Cloud Memory Safety**:
   - Stay strictly under 120MB RSS memory limit on Render single-worker containers.

---

### Task 1: Contract Eligibility & Risk-Sizing Budget Enforcement (Backend Core)
**Files:**
- `data/options_data.py`
- `options/suggester.py`
- `tests/test_eligibility_and_risk.py`

**Steps:**
1. Write failing tests in `tests/test_eligibility_and_risk.py`:
   - `test_options_data_rejects_missing_bid_or_ask_and_does_not_fabricate`: verifies contracts with `bid <= 0` or `ask <= 0` or `ask <= bid` are not given synthetic quotes from `lastPrice`.
   - `test_options_data_respects_dte_bounds`: verifies `filter_expirations_by_dte` and `get_options_chains` do not substitute out-of-bound expirations.
   - `test_position_sizing_returns_zero_when_exceeding_budget`: verifies `compute_position_sizing` returns `contracts = 0` when `budget < max_loss_one`.
   - `test_suggester_marks_unaffordable_contracts_as_zero_contracts`: verifies suggestions with cost exceeding budget have `suggested_contracts = 0`.
2. In `data/options_data.py`:
   - Remove lines 127–133 (`zero_quote_mask` fabricated bid/ask). Keep `lastPrice` as `last_price`.
   - In `filter_expirations_by_dte`: remove the fallback that selected expirations outside `[min_dte, max_dte]`. If none match, return `[]`.
   - In `get_options_chains`: remove fallback overrides that expanded to `[0, 7]` or `[2, 60]` when target was empty.
3. In `options/suggester.py`:
   - In `compute_position_sizing`: when `contracts < 1`, set `contracts = 0` and `total_max_loss = 0.0`.
   - In `rank_and_filter_contracts`: record audit entry `"rejected_budget"` when contract exceeds risk budget, and set `contracts = 0`.
4. Run tests: `pytest tests/test_eligibility_and_risk.py -v`.
5. Commit: `git commit -am "fix(options-core): enforce strict contract quote validity, DTE bounds, and non-zero risk budget sizing"`

---

### Task 2: Live Options Feed & Market Regime Generation (Backend API)
**Files:**
- `api.py`
- `tests/test_live_options_feed.py`

**Steps:**
1. Write failing tests in `tests/test_live_options_feed.py`:
   - `test_options_recommendations_endpoint_returns_live_metadata`: tests that response includes `data_source`, `retrieved_at_utc`, and honest empty list if no screened picks.
   - `test_options_recommendations_dynamic_vix_regime`: tests that `market_regime` reflects actual `^VIX` or null/unavailable if VIX quote is missing.
   - `test_options_recommend_preserves_actual_confidence`: tests that `/api/options/recommend` reflects real signal confidence instead of fixed 0.85.
2. In `api.py`:
   - Replace `_get_curated_options_recommendations`:
     - Fetch screened stocks from `get_screener_cache().get_recommendations(limit=10)`.
     - For top screened stocks with active bias, generate live option recommendations using real option chains (`get_options_chains` + `suggest_options`).
     - If screener cache is cold or empty, screen from a curated benchmark universe (`["SPY", "QQQ", "NVDA", "AAPL", "MSFT", "AMZN", "META", "TSLA"]`).
     - If no option qualifies or chains fail, return `items: []`.
   - Update `/api/options/recommendations`:
     - Retrieve `^VIX` quote via `get_current_quote("^VIX")`. If valid, compute regime dynamically based on current VIX level; if invalid or unavailable, return `market_regime: null` or with `status: "unavailable"`.
     - Add metadata: `data_source: "yfinance (delayed ~15m)"`, `retrieved_at_utc: <ISO>`, `disclaimer: ...`.
   - Update `/api/options/recommend`:
     - Preserve true signal confidence and score from `generate_signal` (or derive proportionally from momentum). Never force `0.85`.
3. Run tests: `pytest tests/test_live_options_feed.py -v`.
4. Commit: `git commit -am "feat(api): make options feed genuinely live with dynamic VIX regime and honest empty states"`

---

### Task 3: Volatility Cockpit Metric Renaming & Market-Data Transparency
**Files:**
- `data/options_data.py`
- `api.py`
- `frontend/src/components/VolatilityCockpit.tsx`
- `tests/test_volatility_cockpit.py`

**Steps:**
1. Write tests in `tests/test_volatility_cockpit.py` verifying metric keys and methodology explanations in `get_volatility_cockpit`.
2. In `data/options_data.py`:
   - In `get_volatility_cockpit`:
     - Rename/clarify metric keys: add `hv_benchmarked_iv_rank`, `hv_benchmarked_iv_percentile`, `methodology_note: "Benchmarked against 1-year historical realized volatility (21d HV) distribution"`.
     - Retain `iv_rank` and `iv_percentile` for backward compatibility.
     - Add `data_source: "yfinance (delayed ~15m)"`, `retrieved_at_utc`, and `last_trade_time`.
3. In `frontend/src/components/VolatilityCockpit.tsx`:
   - Relabel cards to "HV-Benchmarked IV Rank" and "IV vs Realized Vol %ile".
   - Add explanation badge noting that historical IV is benchmarked against realized volatility distribution.
   - Display data source and UTC retrieval time.
4. Run tests: `pytest tests/test_volatility_cockpit.py -v`.
5. Commit: `git commit -am "fix(volatility): clarify IV rank benchmark methodology and display data source metadata"`

---

### Task 4: Frontend Contract Explanation, Data Quality Headers & Risk Sizing Safeguards
**Files:**
- `frontend/src/components/BestOptionsHome.tsx`
- `frontend/src/components/OptionPayoffModal.tsx`
- `frontend/src/app/page.tsx`

**Steps:**
1. In `BestOptionsHome.tsx`:
   - Header & Status:
     - Show Market Data Quality bar: Data Source (`yfinance ~15m delay`), Retrieval Time (UTC), and Cache Status.
     - Add execution disclaimer banner: "Modeled at Ask (entry) and Bid (exit). Midpoint fills not guaranteed. Broker fees/slippage excluded."
   - Risk Sizing Safeguards:
     - Inspect `rec.suggested_contracts`. If `=== 0`, display warning "Exceeds Risk Budget" and disable the Paper Buy button.
     - Never default `rec.suggested_contracts || 1`.
   - Contract Explanation & Exclusion Diagnostics:
     - Add "Why this contract?" collapsible summary: Delta fit, spread friction %, volume/OI liquidity, theta decay, and event risk.
     - Relabel "Win POP %" to "Model PoP (BS Estimate)".
   - State Handling:
     - Handle stale data, loading, API errors, and honest empty state ("No options currently qualify for this strategy/risk budget").
2. In `OptionPayoffModal.tsx`:
   - If `contracts <= 0`, display risk warning that position exceeds account risk allocation; disable Paper Buy action.
   - Clarify in milestones and payoff footer that calculations represent theoretical Black-Scholes expiration payoff, not guaranteed returns.
   - Show Bid-Ask spread slippage drag.
3. In `page.tsx`:
   - Ensure Paper Trading buy handler checks for `order.contracts <= 0` and rejects zero-contract orders.
4. Verify Next.js build: `npm run build` in `frontend/`.
5. Commit: `git commit -am "feat(ui): add market data quality bar, contract explanations, and strict zero-contract risk safeguards"`

---

### Task 5: End-to-End Verification, Full Regression & Final Code Review
**Files:**
- Complete codebase test suite

**Steps:**
1. Run all pytest test suites: `.venv\Scripts\python.exe -m pytest tests/ -v`.
2. Run frontend production build: `cmd.exe /c "npm run build"` in `frontend/`.
3. Check memory diagnostics on `/api/health` to confirm RSS is `< 120MB`.
4. Perform whole-branch code review and summarize all delivered improvements.
