# Gemini SOP: Improve the Options Recommender

Use this document as the prompt for Gemini with the repository opened at its root. It is based on the current checkout, including the options terminal, stock screener, and Render deployment.

## Copy/paste instructions for Gemini

```text
You are the senior engineer improving this existing options research application. Read this SOP and inspect the repository before changing code. The goals, in order, are:

1. Make displayed option ideas genuinely based on current fetched option-chain data and remove misleading or fabricated trade metrics.
2. Show the age, source, and limitations of market data so users can tell whether a result is current enough to investigate.
3. Make the dashboard explain why an idea qualified, why a contract was selected, and when there is no eligible trade.

Work in this repository's existing Python/FastAPI and Next.js/TypeScript stack. Preserve unrelated user changes. Follow repository instructions such as AGENTS.md if present. Give a concise audit of the current implementation, then implement the phases below in order, keeping each phase small and reviewable. Do not stop after providing generic recommendations.

Do not deploy, push, commit, place real orders, add credentials, sign up for a provider, or introduce a paid service. Do not add a new data provider unless the repository already has credentials and its terms/cost are understood. Do not claim Yahoo Finance/yfinance quotes are real-time or execution-grade. Do not invent thresholds, fees, probabilities, quote timestamps, or market-regime values. If a choice requires paid data, an external account, or a breaking product decision, leave that part unimplemented and state the exact blocker.

Before coding, check git status and preserve existing work. Trace each change through backend callers, API response shapes, UI consumers, and paper-trading flows. Use deterministic tests with mocked market-data calls; never make live network requests from tests. Do not rewrite large files or add dependencies unless an existing pattern cannot solve the requirement.

## Current repository map

- `api.py`: FastAPI routes, including dynamic `/api/options/recommend`, the `/api/options/recommendations` home feed, option-chain routes, stock screener routes, and paper-trading quote routes.
- `options/suggester.py`: Black-Scholes calculations, position sizing, contract filtering/ranking, spreads, and 0DTE setup generation.
- `data/options_data.py`: yfinance option-chain retrieval, expiration selection, chain cleaning, matrix and volatility-cockpit data.
- `data/price_data.py`: underlying prices, candles, earnings, market ribbon, and in-memory quote/history caches.
- `analysis/signals.py` and `analysis/momentum.py`: directional signal and technical inputs.
- `analysis/screener_cache.py` and `analysis/stock_suggester.py`: separate stock screener and stock trade plans; preserve these while working on options.
- `frontend/src/components/BestOptionsHome.tsx`: main option-recommendation home cards and filters.
- `frontend/src/app/page.tsx`: large options terminal; change only the relevant sections and keep its existing interactions working.
- `frontend/src/app/stocks/page.tsx`, `StockScreenerTable.tsx`, and `StockCard.tsx`: separate stock screener UI.
- Existing Python tests are under `tests/`. `frontend/package.json` defines `npm run build`.
- `render.yaml` targets a single-worker free Render service, caps the screener universe, and disables the background worker to limit memory use.

## Audit findings to verify before acting

These are specific leads from the current code, not permission to make assumptions. Re-read the surrounding code and confirm each one:

1. `api.py::_get_curated_options_recommendations` returns hard-coded contract data, confidence/PoP values, and rationales. `/api/options/recommendations` refreshes some underlying prices but still returns those fixed option metrics. Its market-regime response contains a fixed VIX value and fixed narrative. `BestOptionsHome` presents these records as recommendations. Ensure the live UI cannot present those records as current market picks. Replace the feed with genuine screening results or clearly isolate and label sample data; show an honest empty/no-eligible-trades state when live data is unavailable.
2. `api.py::get_options_recommend_for_ticker` constructs a `TradeSignal` with fixed high confidence values even when deriving direction from market inputs. Do not turn a requested or inferred direction into an artificial confidence claim. Preserve the actual measured signal or mark confidence unavailable.
3. `data/options_data.py::_clean_chain_df` fabricates a bid and ask around `lastPrice` when the ask is missing. That synthetic quote can pass the spread/liquidity filters and look tradable. Do not use last trade as a substitute NBBO; retain the last trade as a separate field and reject or mark contracts without a valid bid and ask.
4. `data/options_data.py::get_options_chains` falls back to expirations outside the requested DTE window. A fallback must never silently become the selected trade. Prefer strict eligibility and an explicit empty result; if the UI offers alternatives outside the requested window, identify the actual DTE and make the user opt into them.
5. `options/suggester.py::compute_position_sizing` forces at least one contract when the budget cannot cover one contract. Find all callers, including spread, high-risk, 0DTE, and UI/paper-trading paths. Represent unaffordable as zero/no eligible position and ensure no frontend `Math.max(1, ...)` or fallback silently converts it back to one.
6. `data/options_data.py::get_volatility_cockpit` derives its current “IV Rank” and “IV Percentile” from realized historical volatility, not a historical implied-volatility series. Rename these metrics as IV-versus-realized-volatility comparisons unless genuine IV history is available. Do not present them as conventional IV Rank/Percentile.
7. Distinguish a model-derived risk-neutral probability estimate from a historically validated win rate. Preserve API compatibility where practical, but use accurate UI labels and document assumptions. The app currently has tests for stock APIs, the screener, and dynamic options endpoints, but no focused options-selection test module.
8. README architecture/features should be checked against the current stock-screener and options implementations; update documentation only where it is materially stale.

## Implementation phases

### Phase 1 — Correctness and eligibility (highest priority)

Files likely involved: `options/suggester.py`, `data/options_data.py`, `api.py`, `frontend/src/components/BestOptionsHome.tsx`, and any relevant option-card/paper-trading components in `frontend/src/app/page.tsx`.

- Make the options home feed use current fetched underlying and option-chain data for every displayed contract. Remove hard-coded live-looking Greeks, prices, volume, open interest, confidence, rationale, and market regime. If examples are retained, make them unmistakably sample data and exclude them from live sorting and paper-buy actions.
- Preserve the real signal strength when creating a dynamic recommendation. Direction alone is not confidence.
- Require valid positive bid and ask with `ask > bid` for execution-sensitive selection. Never synthesize a spread from `lastPrice`; retain and label last-trade data separately.
- Respect the requested DTE bounds. Surface “no matching expiration” instead of silently crossing the user’s window.
- Enforce the risk budget: if one contract exceeds it, return no position rather than forcing one. Update all consumers so zero contracts disables paper-buy actions and is rendered as “over budget/no eligible size.”
- Keep hard eligibility filters separate from ranking. Return concise exclusion counts/reasons where feasible, reusing the existing `audit_log` pattern instead of inventing a parallel framework.
- Do not relax strict filters invisibly when no contract passes. Any explicitly supported relaxed mode must be labelled and must not outrank strict candidates.

Acceptance checks:

- No live recommendation card can be built from static sample option data.
- Missing/zero/crossed quotes, out-of-window DTEs, and over-budget contracts cannot become eligible picks.
- A no-data or no-eligible response produces a clear empty state rather than a made-up recommendation.
- Existing API consumers and paper-trading flows handle zero recommendations and zero affordable contracts safely.

### Phase 2 — Market-data quality and honest volatility labels

Files likely involved: `data/price_data.py`, `data/options_data.py`, `api.py`, relevant TypeScript response interfaces, and `frontend/src/components/VolatilityCockpit.tsx` / `BestOptionsHome.tsx`.

- Carry source and retrieval metadata through API responses: provider name, UTC retrieval time, whether cached, and cache age when known. For contracts, keep the provider’s last-trade time distinct from retrieval time.
- State plainly when quote age or NBBO quote-size data is unavailable. Never infer NBBO freshness from `lastTradeDate` or call a yfinance snapshot “real-time.” Use a concise “verify in broker” indicator for execution-sensitive data.
- Make cache state visible in the UI so a cached result is not mistaken for a fresh chain. Keep current TTLs/memory bounds in mind and add no unbounded cache.
- Rename the volatility cockpit’s IV-vs-HV fields and related playbook language unless true historical IV observations are added and tested. Do not approximate historical IV with realized volatility.
- Keep yfinance as the default free source. If its data cannot support a requested quality field, display “unavailable” and document that limitation; do not fabricate a substitute.

Acceptance checks:

- Every live idea and chain view shows its data source and retrieval time, plus cache age/status where available.
- Unknown quote age/size is displayed as unknown, not silently treated as fresh/liquid.
- Volatility labels match the actual inputs used.
- Render memory limits and the one-worker setup remain respected; do not turn on the background scanner or raise scan concurrency by default.

### Phase 3 — Explainable contract selection

Files likely involved: `options/suggester.py`, `api.py`, the option recommendation response types, and `BestOptionsHome.tsx` / option detail components.

- Keep eligibility gates deterministic and apply them before ranking.
- Expose a small score breakdown using inputs already available: delta fit, bid/ask spread cost, volume/open interest, DTE fit, theta exposure, and event/earnings status. Do not call any component a probability of success.
- Show the selected contract’s bid, ask, midpoint (when valid), spread in dollars and percent, breakeven, DTE, delta, IV, estimated maximum loss, and why it ranked above other eligible candidates.
- Use conservative assumptions for a long option: entry at ask and liquidation value at bid for the simple spread-cost illustration. Identify fees/slippage as excluded unless the user has configured them; do not imply midpoint fills are guaranteed.
- Label Black-Scholes probability as a model estimate with its assumptions. Do not clip it to make a weak estimate look more certain or rank by an uncalibrated “win rate.”
- Prefer “no qualified trade” over choosing a poor contract when all candidates fail.

Acceptance checks:

- Same mocked inputs produce stable eligibility and ranking.
- A user can see why a candidate passed, why a candidate failed, and what cost assumptions affect the displayed result.
- The UI distinguishes model estimate, heuristic signal score, and observed historical performance.

### Phase 4 — Dashboard and workflow

Files likely involved: reuse `BestOptionsHome.tsx` for option discovery, `frontend/src/app/page.tsx` for the terminal, and existing option detail/payoff components.

- Make the first view decision-oriented: a short ranked list of eligible setups, market/data status, signal thesis, invalidation, key contract economics, and event risk.
- Add a visible “No qualified setup” state and stale/unavailable warnings.
- Provide a compact “Why this contract?” breakdown and a way to inspect rejected candidates/reasons without cluttering the main view.
- Keep the stock screener as its own workflow; do not conflate stock share recommendations with options contract picks.
- Reuse existing components and styling. Avoid a wholesale rewrite of the large app page. Maintain keyboard use, responsive layout, and loading/error/empty states.

Acceptance checks:

- The screen makes it clear whether a displayed idea is live, cached, sample, or unavailable.
- The most important risk and data limitations are visible without opening several tabs.
- Existing navigation, watchlist, chain inspector, payoff view, and paper portfolio still work.

### Phase 5 — Validation and honest performance tracking

- Add focused deterministic tests for sizing boundaries, quote cleaning, DTE window behavior, signal-confidence preservation, static/sample-feed exclusion, and response freshness metadata. Mock yfinance; do not make network calls in tests.
- Extend the closest existing API test instead of duplicating broad fixtures. Likely starting points are `tests/test_dynamic_options_endpoint.py`, `tests/test_stock_api.py`, and a new focused `tests/test_options_selection.py` if that keeps coverage coherent.
- Run the Python suite with `python -m pytest -q` and the frontend production build with `npm run build` from `frontend/`; report exact commands and outcomes.
- Historical underlying bars alone cannot validate historical option-contract performance. Do not claim a profitable backtest unless timestamped option-chain snapshots and realistic fill assumptions exist. If adding an outcome ledger, make it a clearly labelled forward shadow log with export and identify where it is stored; Render’s local filesystem/in-memory cache is not durable across restarts unless persistent storage is configured.
- Do not add a database, Redis, paid provider, or background worker without an existing configured service and a clear need.

## Completion report Gemini must provide

At the end, summarize:

1. The verified issues found and the user-visible behavior changed.
2. Files changed and any API contract changes.
3. Test/build commands run and their actual results.
4. Data limitations that remain, including any fields yfinance does not provide.
5. Anything deliberately deferred because it requires historical options data, a paid provider, persistent storage, or user credentials.

Do not say the recommendations are profitable or reliable based only on code changes or passing tests. Reliability claims require measured out-of-sample results.
```

## Project-specific priority order

The highest-priority issue is that the `/api/options/recommendations` home feed is backed by hard-coded option records while presenting them as current picks. Correcting that source of truth comes before polishing the card design. Next are the synthetic bid/ask fallback, forced one-contract sizing, and silent DTE fallback; then data freshness and honest volatility/confidence labels. The dashboard work should make those corrected facts easy to judge.

The project already has useful groundwork: Python tests, an option audit log, bounded in-memory caches, a stock screener status endpoint, and a distinct stock page. Gemini should build on those existing seams rather than replacing the application architecture.
