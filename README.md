# 🎯 Disciplined US Stock Options Suggester & Next.js Terminal

A high-conviction, risk-managed US stock options suggestion and analytics system built with **yfinance**, **VADER Sentiment**, **Pandas**, **FastAPI**, and a modern **Next.js 14** web terminal featuring **TradingView Lightweight Charts**, an **Interactive Options Chain Matrix**, **⚡ 0DTE High-Velocity Flash Lab**, and **High-Risk Speculative Plays (Uncapped)**.

> ⚠️ **DISCLAIMER**: This software is strictly for informational and educational purposes only. It is **NOT** financial, investment, or trading advice. Options trading involves substantial risk of loss. Always conduct your own due diligence.

---

## 🌟 Key Capabilities & Highlights

1. **⚡ 0DTE High-Velocity Flash Lab (Same-Day / Front-Session Expirations)**:
   - **0DTE High-Volume Universe**: Dedicated daily expiration index & megacap leaders: `SPY`, `QQQ`, `IWM`, `NVDA`, `TSLA`, `AAPL`, `AMD`, `META`, `AMZN`, `MSFT`.
   - **Intraday Black-Scholes Greeks Engine**: Models expiration-day contracts using intraday trading session fractions ($t = 0.5/365.0 \approx 0.00137$), yielding accurate intraday Gamma, Vega, and Theta decay.
   - **🎯 ATM Momentum Scalp Plays (~0.45–0.55Δ)**: High directional sensitivity with real-time **Theta Burn Rate per hour** ($\Theta / 6.5\text{h}$) and **Breakeven Velocity Requirement** (% price move needed per hour).
   - **🚀 OTM Gamma Moonshots (~0.15–0.28Δ)**: Low-premium contracts ($0.30–$2.50) designed for explosive gamma expansion with **8:1 to 15:1+ upside leverage multiples**.
   - **🛡️ 0DTE Asymmetric Lotto Spreads (3:1 to 8:1+ R:R)**: Defined-risk vertical debit spreads pairing an OTM strike with a higher OTM short strike for maximum convex payoff with 100% risk containment.
   - **Uncapped Position Sizing**: Real-time position sizing dynamically scales based on user-chosen risk allocation (0.5%, 1%, 2%, 3%, 5%, or custom equity budget).

2. **🕸️ Interactive Options Chain Matrix & Black-Scholes Greeks Suite**:
   - **Unified Call / Strike / Put Matrix Ladder**: Institutional 15-column matrix aligning Calls and Puts across all strikes for any expiration date.
   - **Analytical Greeks Suite**: Pure Python zero-dependency Black-Scholes calculations computing $\Delta$ (Delta), $\Gamma$ (Gamma), $\Theta$ (Theta $/day decay), $\nu$ (Vega $/1% IV shift), and $\rho$ (Rho).
   - **Expected Move & 1σ Cone**: Derived from ATM straddle pricing ($0.85 \times \text{straddle}$), computing upper and lower boundaries and percentage move.
   - **Max Pain Strike Pinning**: Real-time calculation of strike price minimizing cumulative dollar payout to buyers.
   - **Put/Call Ratios (PCR)**: PCR Volume & PCR Open Interest metrics with sentiment classification (Bullish, Bearish, or Neutral).
   - **Interactive Option Inspector**: Click any contract on the matrix to instantly inspect its Greeks, position sizing, and interactive SVG expiration payoff diagram.
   - **Ladder Filters**: Real-time toggles for Near ATM (±10 strikes), All strikes, In-the-Money, and Out-of-the-Money.

3. **Modern Next.js 14 Web Terminal & TradingView Charts** (`frontend/`):
   - **Interactive TradingView Candlestick Charts**: Daily OHLCV bars with real-time volume histogram and SMA-20 / SMA-50 trend indicators.
   - **Visual Option Payoff Curves**: Interactive SVG expiration P&L diagram depicting max profit, max loss, and breakeven point.
   - **High-Confidence Screener View**: Dedicated screener identifying highest-conviction directional trade setups with confidence $\ge 35\%$.
   - **⚡ High-Risk & Speculative Lab View (Uncapped)**: Dedicated speculative cockpit targeting explosive high-beta names with OTM Moonshots and Asymmetric Lotto Spreads with customizable, uncapped risk budget sliders.
   - **⚡ 0DTE Flash Lab View**: High-speed same-day options terminal with instant ticker switching, dual ATM scalp & OTM moonshot comparison cards, and theta decay burn gauges.
   - **Commodities & Sector Quick Filters**: Instant screening across Commodities & Natural Resources, NeoClouds, Optical Interconnect, Memory (HBM), AI Chips, Software, and Infrastructure.

4. **🌾 Commodities & Natural Resources Universe (25+ Liquid Leaders)**:
   - **Precious Metals & Miners**: `GLD` (Gold), `SLV` (Silver), `GDX` (Gold Miners), `GDXJ` (Junior Gold Miners), `NEM` (Newmont), `GOLD` (Barrick)
   - **Energy, Crude Oil & Natural Gas**: `USO` (Oil Fund), `UNG` (Natural Gas), `XLE` (Energy Select), `XOM` (ExxonMobil), `CVX` (Chevron), `OXY` (Occidental)
   - **Industrial Metals, Copper & Materials**: `FCX` (Freeport-McMoRan), `COPX` (Copper Miners), `CPER` (Copper Index), `SCCO` (Southern Copper), `CLF` (Cleveland-Cliffs), `NUE` (Nucor), `ALB` (Albemarle Lithium)
   - **Agriculture & Fertilizers**: `DBA` (Agriculture Fund), `WEAT` (Wheat), `CORN` (Corn), `MOS` (Mosaic), `CF` (CF Industries)
   - **Uranium & Nuclear Fuel**: `CCJ` (Cameco), `URA` (Uranium ETF), `NXE` (NexGen Energy)

5. **⚡ High-Risk Speculative Trade Setups (Uncapped Sizing)**:
   - **High-Beta Universe**: Targets high-volatility names like `MSTR`, `COIN`, `ASTS`, `IONQ`, `MARA`, `CLSK`, `CVNA`, `SOUN`, `SMCI`, `UPST`, `RDDT`, and more.
   - **OTM Moonshot Contracts**: Black-Scholes Delta 0.15–0.28 (center ~0.22Δ) with low entry cost ($0.30–$3.50) and aggressive gamma leverage on 8%–15%+ underlying moves.
   - **Asymmetric Lotto Spreads**: Vertical debit spreads pairing an OTM long option (~0.22Δ) with an OTM short option (~0.10Δ) for 3:1 to 6:1+ Risk/Reward ratios.
   - **Uncapped Position Sizing**: Artificial 0.5% risk caps are eliminated. Position sizing dynamically scales based on the trader's full configured trade risk allocation (e.g. 1.0%, 2.0%, 3.0%, 5.0% or custom dollar budgets).

6. **Expanded AI Stock Universe (40+ Leaders across 7 Segments)**:
   - **AI NeoClouds & GPU Compute**: `NBIS` (Nebius Group), `CORZ` (Core Scientific), `APLD` (Applied Digital), `IREN` (Iris Energy), `WULF` (TeraWulf), `HUT` (Hut 8)
   - **AI Optical Interconnect & Photonics**: `COHR` (Coherent), `LITE` (Lumentum), `AAOI` (Applied Optoelectronics), `FN` (Fabrinet), `CIEN` (Ciena), `GLW` (Corning), `POET` (POET Tech)
   - **AI Memory & Storage (HBM)**: `MU` (Micron), `WDC` (Western Digital), `STX` (Seagate), `LRCX` (Lam Research), `AMAT` (Applied Materials)
   - **AI Chips & Semiconductors**: `NVDA`, `AMD`, `AVGO`, `TSM`, `ARM`, `MRVL`, `QCOM`
   - **AI Hyperscalers & Big Tech**: `MSFT`, `GOOGL`, `AMZN`, `META`, `AAPL`
   - **AI Enterprise Software & Cyber**: `PLTR`, `CRWD`, `NOW`, `SNOW`, `ORCL`, `NET`
   - **AI Hardware & Data Center Infra**: `VRT`, `DELL`, `ANET`, `SMCI`

7. **Core Quantitative Signals & Protection**:
   - **Recency-Weighted Sentiment**: Headlines are exponentially decayed based on actual age (fresh `<6h` news carries $1.0\times$ weight).
   - **Volume Confirmation**: High momentum is only treated as "Strong" when confirmed by 20-day volume ratio ($\ge 1.0\text{x}$).
   - **Multi-Timeframe Check (MTF)**: Checks daily momentum against the 10-week intermediate trend (`Weekly SMA10`).
   - **Earnings Blackout Window**: Automatically blocks directional signals if company earnings occur within **7–10 days**.

8. **Disciplined Options Screening & Risk Sizing**:
   - **Black-Scholes Delta (0.30 to 0.55)**: Targets the sweet spot centering on $\approx 0.42\Delta$ for standard swing trades.
   - **Position Sizing Calculator**: Dynamically calculates contracts based on account equity (default: $\$10,000$) and max risk (default: $1.0\% = \$100$).
   - **50% Stop-Loss Exit**: Computes practical stop-loss price and exact dollar loss cap.
   - **Defined-Risk Debit Spreads**: Automatically surfaces vertical Bull Call or Bear Put spreads when IV is elevated ($\ge 45\%$).

---

## 📁 Project Architecture

```
Optionsrecommender/
├── frontend/                     # Next.js 14 Modern Web Dashboard
│   ├── src/app/                  # App router, terminal interface, ⚡ 0DTE Flash Lab & High-Risk Lab
│   ├── src/components/
│   │   ├── StockChart.tsx        # TradingView Lightweight Charts (Candlesticks + SMA + Volume)
│   │   ├── PayoffChart.tsx       # Option Expiration P&L Payoff Diagram
│   │   └── OptionsChainMatrix.tsx# Interactive Options Chain Strike Ladder & Greeks Matrix
│   ├── package.json
│   └── tailwind.config.js
├── api.py                        # FastAPI REST API Backend (/api/zero-dte, /api/options-chain, /api/high-risk-setups, /api/universe, etc.)
├── config.py                     # Centralized thresholds, 0DTE universe, Commodities, AI stocks, High-Risk universe
├── data/
│   ├── price_data.py             # yfinance OHLCV, quotes, TTL caching, earnings blackout
│   ├── news_data.py              # yfinance news headline extraction
│   └── options_data.py           # Options chain retrieval, in-memory matrix caching & DTE filtering (dte >= 0)
├── analysis/
│   ├── momentum.py               # Technical momentum, volume confirmation, weekly MTF
│   ├── sentiment.py              # Time-decay recency-weighted VADER sentiment
│   └── signals.py                # Combined score + direction + High/Med/Low tiers
├── options/
│   └── suggester.py              # Black-Scholes Greeks (Delta, Gamma, Theta, Vega, Rho), 0DTE trade setups, Max Pain, Expected Move, spreads
├── pages/
│   └── 1_🔥_High_Confidence_AI_Picks.py # Streamlit High-Confidence page
├── main.py                       # CLI interface (--zero-dte, --commodities, --chain, --high-risk, --neoclouds, --opticals, --memory)
├── app.py                        # Streamlit web app
├── start-web.bat                 # One-click Windows CMD launcher
├── start-web.ps1                 # One-click Windows PowerShell launcher
├── requirements.txt              # Python dependencies
└── README.md                     # Documentation
```

---

## 🚀 Quick Start

### Option A: Launch Next.js Web Terminal + FastAPI Backend (Recommended)

Run either the PowerShell script or batch file:

```powershell
.\start-web.ps1
```
*or in Command Prompt:*
```cmd
start-web.bat
```

- **Frontend UI**: [http://localhost:3000](http://localhost:3000)
- **FastAPI Backend**: [http://127.0.0.1:8000](http://127.0.0.1:8000) (Interactive Swagger Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs))

---

### Option B: Run CLI Commands

Scan **⚡ 0DTE High-Velocity Options** (`SPY`, `QQQ`, `IWM`, `NVDA`, `TSLA`, `AAPL`, `AMD`, `META`, `AMZN`, `MSFT`):
```powershell
python main.py --zero-dte
```

Target a specific **0DTE contract** with custom equity and risk budget:
```powershell
python main.py --ticker SPY --zero-dte --equity 10000 --risk-pct 2.0
```

Scan **🌾 Commodities & Natural Resources Universe** (`GLD`, `SLV`, `USO`, `FCX`, `CCJ`, `NEM`, etc.):
```powershell
python main.py --commodities
```

View the **full options chain strike matrix & Greeks** directly in terminal:
```powershell
python main.py --ticker GLD --chain
```

Target a specific expiration date:
```powershell
python main.py --ticker NVDA --chain --expiration 2026-10-16
```

Scan **⚡ High-Risk & Speculative Universe** with uncapped sizing (`MSTR`, `COIN`, `ASTS`, `IONQ`, `MARA`, `CLSK`, etc.):
```powershell
python main.py --high-risk --equity 10000 --risk-pct 2.0
```

Scan **NeoClouds & GPU Compute** (`NBIS`, `CORZ`, `APLD`, `IREN`, `WULF`, `HUT`):
```powershell
python main.py --neoclouds
```

Scan **Optical Interconnect & Photonics** (`COHR`, `LITE`, `AAOI`, `FN`, `CIEN`, `GLW`, `POET`):
```powershell
python main.py --opticals
```

Scan **Memory & Storage (HBM)** (`MU`, `WDC`, `STX`, `LRCX`, `AMAT`):
```powershell
python main.py --memory
```

Filter for **High Confidence Only** across all AI leaders:
```powershell
python main.py --ai-leaders --high-confidence-only
```

Deep-dive into a single ticker (e.g. `SPY`, `GLD`, `FCX`, `MSTR`, `ASTS`, `NBIS`, `COHR`, `MU`):
```powershell
python main.py --ticker FCX --equity 10000 --risk-pct 1.5
```
