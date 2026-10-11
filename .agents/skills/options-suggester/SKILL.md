---
name: options-suggester
description: Builds and runs a high-quality US stock options suggestion system using only free tools (yfinance + VADER). Combines recency-weighted news sentiment, multi-factor momentum, volume confirmation, earnings blackout, liquidity filters, delta targeting, risk-aware position sizing, expanded sector universes (100+ tickers), dedicated Commodities & Natural Resources coverage (Precious Metals, Energy, Industrial Metals, Agriculture, Uranium), dedicated AI ecosystem coverage (Chips, NeoClouds, Opticals, Memory, Software, Infra), high-risk speculative trade setups with uncapped position sizing (OTM Moonshots 0.15–0.28 Delta & Asymmetric Lotto Spreads 3:1 to 6:1+ R:R), high-velocity 0DTE Flash Lab (ATM momentum scalps, OTM gamma moonshots, theta burn rate per hour, and asymmetric 0DTE spreads), interactive Options Chain Matrix with complete Black-Scholes Greeks (Delta, Gamma, Theta, Vega, Rho), Expected Move, Max Pain, Put-Call Ratios, and modern Next.js + TradingView charting UI with high-confidence pick filtering, and risk-free Paper Trading virtual portfolio simulator with live mark-to-market P&L tracking. Use when the user asks for options recommendations, stock options signals, 0dte options, same day options, options chain analysis, Greeks calculations, commodities options, momentum + news analysis, free options ideas, high-risk speculative plays, or directional options strategies for US equities, or paper trading options testing profit/loss.
---

# Options Suggester Skill (High-Confidence, 0DTE Flash Lab, AI Stocks, Commodities, Uncapped Speculative Setups & Options Chain Matrix)

You are an expert quantitative developer and options strategist specializing in clean, free, production-grade signal systems.

## Core Goal
Build a modular, robust Python application that generates high-conviction US equity options suggestions with dedicated modes for **⚡ 0DTE Flash Lab**, **High-Confidence Scores**, the **Commodities & Natural Resources Universe**, the **AI Stock Ecosystem**, **⚡ High-Risk Speculative Setups (Uncapped)**, and **🕸️ Interactive Options Chain Matrix & Greeks** by combining:

1. **⚡ 0DTE High-Velocity Flash Lab (Same-Day / Front-Session Expirations)**:
   - **0DTE Universe (10 Liquid Leaders)**: Daily expiration vehicles: `SPY`, `QQQ`, `IWM`, `NVDA`, `TSLA`, `AAPL`, `AMD`, `META`, `AMZN`, `MSFT`.
   - **Intraday Black-Scholes Greeks Engine**: Models same-day expirations using intraday fractions ($t = 0.5/365 \approx 0.00137$) to avoid math singularities and output accurate intraday Greeks.
   - **🎯 ATM Momentum Scalp Plays (~0.45–0.55Δ)**: High delta sensitivity with real-time **Theta Burn Rate per hour** ($\Theta / 6.5\text{h}$) and **Breakeven Velocity Requirement** (% move/hour).
   - **🚀 OTM Gamma Moonshots (~0.15–0.28Δ)**: Low-premium contracts with 8:1 to 15:1+ upside leverage multiples on explosive intraday thrusts.
   - **🛡️ 0DTE Asymmetric Lotto Spreads (3:1 to 8:1+ R:R)**: Defined-risk vertical debit spreads pairing an OTM strike with a higher OTM short strike for maximum convex payoff with 100% risk containment.
   - **Dynamic Uncapped Sizing**: Sizing scales dynamically with user-chosen risk allocation (0.5%, 1%, 2%, 3%, 5%, or custom equity budget).
2. **High-Confidence Screener Page**: Filters out noise and surfaces setups with $\ge 35\%\text{--}45\%$ confidence.
3. **Dedicated Commodities & Natural Resources Universe (25+ Leaders)**: Complete coverage across:
   - **Precious Metals & Miners**: `GLD`, `SLV`, `GDX`, `GDXJ`, `NEM`, `GOLD`
   - **Energy, Crude & Natural Gas**: `USO`, `UNG`, `XLE`, `XOM`, `CVX`, `OXY`
   - **Industrial Metals, Copper & Materials**: `FCX`, `COPX`, `CPER`, `SCCO`, `CLF`, `NUE`, `ALB`
   - **Agriculture & Fertilizers**: `DBA`, `WEAT`, `CORN`, `MOS`, `CF`
   - **Uranium & Nuclear Fuel**: `CCJ`, `URA`, `NXE`
4. **Dedicated AI Stock Ecosystem (40+ Leaders)**: Complete coverage across:
   - **AI Chips & Semiconductors**: `NVDA`, `AMD`, `AVGO`, `TSM`, `ARM`, `MRVL`, `MU`, `QCOM`
   - **AI NeoClouds & GPU Compute**: `NBIS`, `CORZ`, `APLD`, `IREN`, `WULF`, `HUT`
   - **AI Optical Interconnect & Photonics**: `COHR`, `LITE`, `AAOI`, `FN`, `CIEN`, `GLW`, `POET`
   - **AI Memory & Storage (HBM)**: `MU`, `WDC`, `STX`, `LRCX`, `AMAT`
   - **AI Hyperscalers & Platforms**: `MSFT`, `GOOGL`, `AMZN`, `META`, `AAPL`
   - **AI Enterprise Software & Cyber**: `PLTR`, `CRWD`, `NOW`, `SNOW`, `ORCL`, `NET`
   - **AI Hardware & Data Center Infra**: `VRT`, `DELL`, `ANET`, `SMCI`
5. **⚡ High-Risk & Speculative Trade Lab (Uncapped)**: Targets high-beta tickers (`MSTR`, `COIN`, `ASTS`, `IONQ`, `MARA`, `RIOT`, `CLSK`, `CVNA`, `SOUN`, `SMCI`, etc.) with asymmetric setups:
   - **OTM Moonshot Contracts**: Low-cost 0.15–0.28 Delta options for explosive gamma leverage.
   - **Asymmetric Lotto Spreads**: Defined-risk vertical debit spreads with 3:1 to 6:1+ Risk/Reward ratios.
   - **Uncapped Position Sizing**: Arbitrary 0.5% risk caps are eliminated — position sizing dynamically scales with the trader's full configured trade risk allocation.
6. **🕸️ Options Chain Matrix & Black-Scholes Greeks Suite**:
   - **Full Greeks Cockpit**: Analytical Black-Scholes calculation ($\Delta$ Delta, $\Gamma$ Gamma, $\Theta$ Theta $/day, $\nu$ Vega $/1% IV shift, $\rho$ Rho) using pure Python standard library math.
   - **Expected Move & 1σ Range**: Calculated from ATM Straddle pricing ($0.85 \times \text{Straddle}$) with IV fallback ($S \cdot \text{IV} \cdot \sqrt{\text{DTE}/365}$).
   - **Max Pain Strike Pinning**: Iterative buyer loss minimization pinpointing the strike price where option sellers maximize profit.
   - **Put/Call Ratios (PCR)**: PCR Volume & PCR Open Interest with sentiment classification (Bullish, Bearish, or Neutral).
   - **Unified Call/Strike/Put Matrix Ladder**: 15-column institutional matrix with real-time Near ATM, All, ITM, and OTM filters, and one-click inspection loading interactive SVG expiration payoff diagrams and dynamic position sizing.
7. **Recency-weighted news sentiment** (VADER with exponential time decay).
8. **Multi-factor price momentum** with volume confirmation and weekly multi-timeframe alignment.
9. **Earnings blackout protection** (blocking directional trades within 7–10 days).
10. **Smart options screening** (Black-Scholes Delta 0.30–0.55 sweet spot for core trades, tight bid-ask spreads).
11. **Defined-risk debit spread alternatives** (Bull Call / Bear Put spreads when IV is elevated).
12. **Risk-aware position sizing** (sizing based on account equity and trader risk allocation without artificial ceilings).
13. **Modern Next.js 14 Web Terminal & Streamlit Dashboard** with TradingView Lightweight Charts, SVG payoff curves, KPI cards, and CSV export.

The system operates 100% free with no paid APIs and no Finnhub.

## Universe Categories
- **0DTE Universe**: `SPY`, `QQQ`, `IWM`, `NVDA`, `TSLA`, `AAPL`, `AMD`, `META`, `AMZN`, `MSFT`
- **Precious Metals & Miners**: `GLD`, `SLV`, `GDX`, `GDXJ`, `NEM`, `GOLD`
- **Energy, Crude & Natural Gas**: `USO`, `UNG`, `XLE`, `XOM`, `CVX`, `OXY`
- **Industrial Metals, Copper & Materials**: `FCX`, `COPX`, `CPER`, `SCCO`, `CLF`, `NUE`, `ALB`
- **Agriculture & Fertilizers**: `DBA`, `WEAT`, `CORN`, `MOS`, `CF`
- **Uranium & Nuclear Fuel**: `CCJ`, `URA`, `NXE`
- **AI NeoClouds & GPU Compute**: `NBIS`, `CORZ`, `APLD`, `IREN`, `WULF`, `HUT`
- **AI Optical Interconnect & Photonics**: `COHR`, `LITE`, `AAOI`, `FN`, `CIEN`, `GLW`, `POET`
- **AI Memory & Storage (HBM)**: `MU`, `WDC`, `STX`, `LRCX`, `AMAT`
- **AI Chips & Semiconductors**: `NVDA`, `AMD`, `AVGO`, `TSM`, `ARM`, `MRVL`, `QCOM`
- **AI Hyperscalers & Platforms**: `MSFT`, `GOOGL`, `AMZN`, `META`, `AAPL`
- **AI Enterprise Software & Cyber**: `PLTR`, `CRWD`, `NOW`, `SNOW`, `ORCL`, `NET`
- **AI Hardware & Data Center Infra**: `VRT`, `DELL`, `ANET`, `SMCI`
- **Crypto-Beta & AI Miners**: `MSTR`, `COIN`, `MARA`, `CLSK`, `RIOT`, `CIFR`
- **Speculative Tech & Quantum**: `ASTS`, `IONQ`, `RGTI`, `QBTS`, `SOUN`, `PLUG`
- **High-Vol Fintech & Squeeze Growth**: `CVNA`, `SMCI`, `UPST`, `AFRM`, `DJT`, `RDDT`, `OPEN`

## Mandatory Rules & Standards

### 1. 0DTE Flash Lab & Intraday Greeks
- When `dte == 0`, model time-to-expiration $T$ as an intraday fraction $t = 0.5/365.0 \approx 0.00137$ to prevent zero-division in Black-Scholes $d_1$.
- Provide ATM Momentum Scalps (~0.50Δ), OTM Gamma Moonshots (~0.20Δ), and defined-risk 0DTE Asymmetric Spreads (3:1 to 8:1+ R:R).
- Compute Theta burn per hour ($\Theta / 6.5$) and Breakeven velocity requirement (% move per hour).
- Provide Ticker Search Bar to look up any US equity/ETF for 0DTE options, plus an interactive Search & Filter Bar across all available same-day strikes (Calls, Puts, ATM, Moonshots, High Volume) with analytical Greeks, spreads, and risk-sized contracts.

### 2. Options Chain Matrix & Black-Scholes Greeks
- Calculate exact analytical Greeks: $\Delta$ (Delta), $\Gamma$ (Gamma), $\Theta$ (Theta $/day), $\nu$ (Vega $/1% IV shift), $\rho$ (Rho) using standard error function math.
- Display Expected Move ($\pm\$, $\pm\%$) with 1σ cone range and Max Pain strike.
- Highlight ATM strike and Max Pain strike clearly on the strike ladder.
- Support real-time strike filtering (Near ATM $\pm10$, All strikes, In-the-Money, Out-of-the-Money).

### 3. High-Confidence Priority
- Filter for setups with $\ge 35\%$ confidence score and confirmed momentum.
- Display ranking leaderboard and deep-dive cards for each high-conviction candidate.

### 4. Delta Targeting (0.30 – 0.55 Core Trades)
- Center targeting on ~0.42 Delta (directional sweet spot with balanced gamma, delta, and theta decay).

### 5. Volume & Timeframe Confirmation
- Momentum is only classified as "Strong" when confirmed by volume ratio $\ge 1.0\times$.
- Weekly trend alignment (Weekly SMA10) reinforces conviction; divergence dampens score.

### 6. Earnings Blackout Protection
- Check corporate earnings calendar.
- Automatically flag and block directional trades if earnings are scheduled within 7–10 days.

### 7. Position Sizing & Stop-Loss Plan
- Size contract count based on Account Equity ($) and Risk % budget.
- Compute a practical 50% option premium stop-loss level and dollar cap.

### 8. Defined-Risk Debit Spreads
- Automatically surface vertical Bull Call or Bear Put debit spreads when implied volatility is elevated ($\ge 45\%$).

### 9. High-Risk Speculative Setups (Uncapped Position Sizing)
- **OTM Moonshot Single-Legs**: Target Black-Scholes Delta between 0.15 and 0.28 (ideal ~0.22 Delta). Low entry cost per contract ($0.30–$3.50) with extreme convex payoff potential on rapid 8%–15%+ stock moves. DTE: 7–28 days.
- **Asymmetric Lotto Spreads**: Pair an OTM long option (~0.22 Delta) with an even further OTM short option (~0.10 Delta) to slash premium cost, delivering 3:1 to 6:1+ Risk/Reward ratios with 100% defined risk.
- **Uncapped Sizing Budget**: Artificial 0.5% risk caps are eliminated. Positioning dynamically utilizes the full trade risk allocation specified by the user (e.g. 1.0%, 2.0%, or custom risk budget) without restrictive ceiling limits.

### 10. Institutional Trade Execution Plans & Execution Playbooks (`OptionTradePlan`)
- **Multi-Tier Scaling Target Profit Plan**:
  - **TP1 (+50% Quick Trim)**: Exact option price $P_{\\text{entry}} \\times 1.50$, required underlying stock move using delta $\\Delta S \\approx \\frac{\\Delta P}{|\\Delta|}$. Rule: Trim 50% of contracts to lock profits; move stop loss on remaining contracts to Breakeven ($P_{\\text{entry}}$).
  - **TP2 (+100% Core Target)**: Exact option price $P_{\\text{entry}} \\times 2.00$, underlying move adjusted for gamma expansion $\\Delta_{\\text{eff}} \\approx \\min(|\\Delta| + 0.12, 0.85)$. Rule: Take core profit on 30–50% of position; trail runners.
  - **TP3 (+150–200% Runner)**: Option price $P_{\\text{entry}} \\times 2.50$, trailing rule: Trail final runners along 8-day EMA on underlying daily chart until structural breakdown.
- **Analytical Edge & Probability Metrics**:
  - Analytical **Probability of Profit (PoP %)** calculated using Black-Scholes risk-neutral cumulative distribution $N(d_2) = \\frac{1}{2}\\left[1 + \\text{erf}\\left(\\frac{d_2}{\\sqrt{2}}\\right)\\right]$.
  - **Risk-to-Reward Ratio (R:R)** ($TP2_{\\text{gain}} / Stop_{\\text{loss}}$) and **Expected Value (EV $/contract)**.
- **Capital Protection & Theta Defense (Time-Stop)**:
  - Strict 50% option premium stop price and underlying chart invalidation price level.
  - Real-time Daily Theta Decay meter ($-$/contract/day) and **21-DTE Cliff Defense Rule**: close or roll trades reaching 21 DTE to eliminate exponential theta decay cliff.
  - **Speculative Free-Ride Rule (House Money)**: For high-risk moonshots, sell 50% of contracts at +100% gain (2x) to recoup 100% initial capital, converting remaining position into a risk-free free-ride.
  - **Defined-Risk Spread 75% Rule**: Close debit spreads at 75% of maximum profit to eliminate expiration pin risk.
  - **0DTE Intraday Scalping Playbook**: Quick 15–30 min execution window at +30% TP1, strict -35% stop cut, and 60-minute stagnation time-stop.
- **Disciplined Execution Playbook Checklist**:
  Actionable step-by-step checklist from limit mid-price entry to scaled exits and time defense.
- **Phase 1: Dynamic Ratchet Stop Ladder (Phases 1 to 4)**:
  - *Phase 1 (Initial Entry & Capital Defense)*: Hard Stop at -50% option premium ($sl_opt_px) or underlying technical support/resistance breach.
  - *Phase 2 (Breakeven De-Risk post-TP1)*: Automatic Stop Ratchet to Breakeven ($Mid entry price), de-risking trade to 0 dollar risk.
  - *Phase 3 (Profit Floor Lock post-TP2)*: Stop Ratchet to Profit Lock (+50% premium price, guaranteeing locked net gain).
  - *Phase 4 (Momentum Runner Trail)*: Technical trailing exit based on 8-EMA daily close or 1.5x ATR trail on remainder for house money convexity.
- **Defensive Adjustment & Rolling Playbook**:
  - *Roll Down & Out (21-DTE Time Defense)*: If underlying consolidates near support and DTE hits 21, rule-based recommendation to roll strike out 30?45 days to eliminate catastrophic theta cliff decay.
  - *Synthetic Spread Conversion (Theta Freeze)*: If trade moves slightly adverse but bias remains intact, sell an OTM contract against the long option to convert into a vertical debit spread, instantly slashing theta burn and recovering 30?50% of capital.
  - *Profit-Lock Roll (Roll Up / De-Risk)*: When up +100%, roll long strike higher to extract 100% of the initial principal while letting house money ride on the new higher strike with zero downside risk.
- **GTC Broker Bracket Order Syntax Generator**:
  - Pre-calculated limit entry, multi-tier profit targets, and stop market orders with 1-click clipboard copy formatted for Standard OCO, Thinkorswim (TOS), Interactive Brokers (IBKR), and Webull.

### 11. Multi-Timeframe Interactive Candlestick Charts & Intraday VWAP Engine
- **Smaller Timeframe Intervals Supported**:
  - `1m` (1-Minute Scalp, 1-Day lookback): High-resolution intraday bars for micro-structure and 0DTE scalping.
  - `5m` (5-Minute Intraday, 5-Day lookback): Core intraday execution timeframe for directional momentum and volume flow.
  - `15m` (15-Minute Momentum, 5-Day lookback): Key swing breakout confirmation and intra-session trends.
  - `1h` (1-Hour Trend, 1-Month lookback): Intermediate support/resistance and trend channels.
  - `1D` (Daily Swing, 6-Month lookback): Standard swing momentum with SMA20 and SMA50.
  - `1W` (Weekly Macro, 1-Year lookback): Multi-timeframe trend alignment (MTF SMA10).
- **Intraday Technical Overlays**:
  - **Volume-Weighted Average Price (VWAP)**: Dynamically calculated on intraday intervals ($\text{VWAP} = \frac{\sum (P_{\text{typ}} \cdot V)}{\sum V}$) for institutional benchmark levels.
  - **SMA 20 & SMA 50**: Rolling trend overlays with interactive toggle buttons.
- **TradingView-Grade Interactive Controls**:
  - Timeframe switcher bar (`1m`, `5m`, `15m`, `1h`, `1D`, `1W`) with live asynchronous fetching via `/api/candles`.
  - Dynamic interactive crosshair legend displaying real-time candle stats (`O`, `H`, `L`, `C`, `Change $/%`, `Volume`, `SMA20`, `SMA50`, `VWAP`).
  - Fit Content / Maximize button and active bar count indicator.

### 12. Interactive "What-If" P&L Simulator & Multi-Horizon Scenario Matrix
- **Dual-Curve Payoff Visualizer**:
  - *Dashed Curve*: Terminal intrinsic payoff at expiration.
  - *Solid Glowing Cyan Curve*: Dynamic theoretical P&L today ($T+0$) or at $T+N$ days calculated via analytical Black-Scholes ($d_1, d_2, N(d_1), N(d_2)$).
- **Interactive Control Sliders**:
  - *Time Elapsed Slider ($0$ to $	ext{DTE}$ days)*: Real-time theta decay simulation demonstrating erosion of option value over time. Includes quick presets: `Today`, `Halfway`, and `At Expiry`.
  - *IV Shift Slider ($-25\%$ to $+25\%$)*: Vega stress testing for post-earnings IV crush ($-15\%$) or pre-announcement volatility expansion ($+15\%$).
- **Live Hover Crosshair & Target Inspector**:
  - Drag cursor or hover across the SVG payoff chart to inspect exact underlying stock price, move %, theoretical contract value, dollar P&L, and ROI % today vs expiration.
- **Multi-Horizon Scenario Heatmap Matrix**:
  - Dynamic table evaluating 8 price moves ($-10\%$, $-5\%$, $-2\%$, $0\%$, $+2\%$, $+5\%$, $+10\%$, $+15\%$) across 5 time horizons ($T+0$, $0.25 	imes 	ext{DTE}$, $0.50 	imes 	ext{DTE}$, $0.75 	imes 	ext{DTE}$, Expiration).
  - Color-coded cells display projected dollar return and ROI % for sized contracts.

### 13. Global Market Ticker Ribbon & Starred Watchlist System
- **Real-Time Market Ribbon & Session Status (/api/market-ribbon)**:
  - Displays streaming quotes for major benchmark indices and commodities: SPY (S&P 500), QQQ (Nasdaq 100), IWM (Russell 2000), DIA (Dow Jones), ^VIX (Volatility), BTC-USD (Bitcoin), GLD (Gold), and USO (Crude Oil).
  - Calculates Eastern Time (ET) session state: **Regular Open**, **Pre-Market**, **After-Hours**, or **Market Closed (Weekend/Overnight)**.
  - Interactive click navigation: Clicking any index card in the ribbon immediately opens that asset in the Terminal & TradingView Chart.
  - 45-second server-side caching avoids redundant yfinance requests.
- **Starred Watchlist (/api/watchlist-summary)**:
  - Persistent bookmarking (star) stored in browser localStorage (options_starred_tickers).
  - 1-click star toggles integrated in the main search bar, hero quote banner, High-Confidence AI cards, High-Risk setups, and 0DTE Flash Lab.
  - Dedicated **Watchlist** tab with batch quote and momentum synchronization, technical scoring bar, RSI gauges, and direct action triggers (Analyze, Options Chain, 0DTE Lab).
  - Quick-add ticker form with 1-click popular suggestion chips (NVDA, SPY, QQQ, TSLA, AAPL, AMD, GLD, COIN).

### 14. IV Rank & Visual Volatility Cockpit (/api/volatility-cockpit)
- **Institutional Volatility Surface Gauges**:
  - **IV Rank (0–100%)**: Dynamically measures where current ATM implied volatility sits relative to its 52-week envelope. Color-coded into *Low/Cheap Volatility* (&lt;30%), *Fair/Moderate Volatility* (30–65%), and *Rich/Expensive Volatility* (&gt;65%).
  - **IV Percentile (0–100%)**: Calculates the percentage of trading days over the past year where realized 21-day volatility was lower than today's pricing.
  - **Volatility Risk Premium (VRP = IV / HV)**: Real-time ratio quantifying the option premium markup paid by buyers over actual realized moves.
- **1-Sigma Expected Move Cones & Price Distribution**:
  - Analytical bell-curve boundaries (.2\%$ probability) across multiple horizons: **1 Week (7d)**, **2 Weeks (14d)**, **1 Month (30d)**, **45-Day Swing**, and **2 Months (60d)**.
  - Dual-boundary dollar ranges and percentage move projections ($\\pm \\Delta\\ and $\\pm \\Delta\\%$) with lower & upper cone thresholds.
- **Volatility Regime Action Playbooks**:
  - Automatically recommends directional debit spreads vs credit selling / calendars based on prevailing volatility conditions.
- **Implied Volatility Term Structure**:
  - Cycle-by-cycle ATM IV progression across all listed expiration cycles to identify contango or front-cycle inversion (backwardation).

### 15. Multi-Leg Strategy Builder & Power-User Keyboard Shortcuts
- **Interactive Multi-Leg Strategy Builder (MultiLegStrategyBuilder.tsx)**:
  - Custom leg combination visualizer supporting 1 to 4+ concurrent legs (Buy/Sell, Call/Put, Strike, Premium, Quantity).
  - Built-in institutional presets:
    - **Bull Call Debit Spread**: Long ATM Call + Short OTM Call (capped risk directional upside).
    - **Bear Put Debit Spread**: Long ATM Put + Short OTM Put (downside protection / delta hedge).
    - **Long Straddle**: ATM Call + ATM Put (bi-directional volatility breakout).
    - **Long Strangle**: OTM Call + OTM Put (low-cost wide move expansion).
    - **Iron Condor**: 4-leg credit envelope (OTM Bull Put Spread + OTM Bear Call Spread).
  - Live financial analytics:
    - Combined Net Debit (Cost) vs Net Credit (Income) with total dollar cash flow.
    - Max potential profit and max dollar risk thresholds.
    - Net Position Delta sum ($\\sum \\Delta$) across all active legs.
    - Exact breakeven price points computed via interpolated payoff curves.
- **Global Power-User Keyboard Shortcuts**:
  - / &rarr; Instant focus & highlight on the search bar from anywhere on the page.
  - 1 &rarr; Terminal & TradingView Chart view.
  - 2 &rarr; Interactive Options Chain Matrix (Greeks & Max Pain).
  - 3 &rarr; Volatility Cockpit (IV Rank, IV Percentile, 1-Sigma Expected Move Cones).
  - 4 &rarr; Multi-Leg Strategy Builder.
  - 5 &rarr; Starred Watchlist view.
  - 6 &rarr; High-Confidence AI screen.
  - 7 &rarr; High-Risk Speculative setups.
  - 8 &rarr; 0DTE High-Velocity Flash Lab.
  - 9 &rarr; Paper Portfolio & Virtual Simulator.
  - ? &rarr; Toggle keyboard shortcuts reference cheat sheet modal.
  - ESC &rarr; Dismiss shortcuts help modal or unfocus active input.

### 16. Paper Trading Simulation & Real-Time Virtual Portfolio (/api/paper-quotes)
- **Zero-Risk Virtual Account Execution**:
  - Starting virtual cash balance of **$10,000.00**, stored and persisted locally in browser `localStorage` (`options_paper_balance` and `options_paper_positions`).
  - Total portfolio valuation engine tracking:
    - **Total Account Value** (Cash + Mark-to-market value of open option contracts).
    - **All-Time P&L ($ and %)** against starting capital.
    - **Available Virtual Cash** remaining for allocation.
    - **Open Positions Unrealized P&L ($ and % ROI)** with active contract count.
    - **Realized P&L ($)** from closed trades with all-time **Win Rate %**.
- **Interactive Simulated Order Ticket**:
  - Order entry ticket supporting single-leg Calls or Puts across any US equity/ETF ticker.
  - Configurable strike, expiration date, premium per share, and contract quantity with instant capital validation against available cash.
  - Optional pre-set Profit Target ($) and Stop-Loss ($) triggers.
- **1-Click Quick Simulated Execution Across the Platform**:
  - Direct 1-click **"Simulate Paper Buy"** buttons on the primary disciplined recommendation card and high-risk moonshot card in the Terminal view.
  - Automatically formats the standard OCC option contract symbol and records the trade into the user's paper portfolio.
- **Live Mark-to-Market Pricing Engine (`/api/paper-quotes`)**:
  - Real-time batch options pricing endpoint querying `yfinance.Tickers` for live last-traded option contract prices.
  - Dynamic "Refresh P&L" action recalculates open position market value and unrealized dollar / percentage returns.
- **Position Lifecycle & Trade Log**:
  - **Open Positions Cockpit**: Live tracking cards showing ticker, strike, option type, quantity, entry price vs current market premium, dollar P&L, ROI %, and trade target/stop indicators.
  - **1-Click Close / Sell Position**: Instantly liquidates open option contracts at current market premium, credits cash proceeds back to the account balance, and records realized gains/losses.
  - **Trade Log / Closed Positions Audit**: Historical table logging underlying ticker, side, contracts, entry price, exit price, total cost, realized P&L, ROI %, and close dates.
  - **Account Reset**: 1-click reset restores virtual capital to $10,000 and clears historical positions.
- **Keyboard Shortcut**:
  - Press `9` to instantly switch to the Paper Portfolio view from any tab.
