"""Interactive Streamlit Web Application for Disciplined Options Suggester.

Enhanced with:
- Modern financial terminal UI (deep dark theme, glass cards, glow badges)
- Interactive Expiration Payoff (P&L) diagrams for single-leg contracts & debit spreads
- Dedicated High-Confidence AI recommendations page & mode
- Expanded stock universe across 8 curated market sectors + dedicated AI ecosystem
- Category quick-selector & custom ticker exploration
- Black-Scholes Delta targeting (0.30 - 0.55), volume confirmation & MTF alignment
- Earnings blackout window protection alerts
- Defined-risk vertical debit spread alternatives with visual risk/reward breakdown
- Disciplined position sizing calculator (Account equity & % risk)
- Interactive Watchlist Scanner with category filtering and CSV export
"""

from datetime import datetime
import io
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import (
    AppConfig, DEFAULT_CONFIG, WATCHLIST_CATEGORIES, EXPANDED_WATCHLIST,
    AI_STOCKS_CATEGORIES, AI_STOCKS_UNIVERSE
)
from data.price_data import get_price_history, get_current_quote, get_earnings_info
from data.news_data import get_company_news
from data.options_data import get_options_chains
from analysis.momentum import analyze_momentum
from analysis.sentiment import analyze_news_sentiment
from analysis.signals import generate_signal, BiasDirection, ConfidenceTier
from options.suggester import suggest_options, ScreeningResult, OptionSuggestion, DebitSpreadSuggestion

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Options Suggester Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# Custom Modern CSS Styling
# ---------------------------------------------------------
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .stApp {
        background-color: #0b0f19;
        color: #f3f4f6;
    }

    /* Metric cards styling */
    div[data-testid="stMetric"] {
        background: #131c2e;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 14px 18px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    div[data-testid="stMetric"]:hover {
        border-color: rgba(0, 210, 255, 0.35);
        transform: translateY(-2px);
    }

    /* Card container */
    .trade-card {
        background: #131c2e;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 14px;
        padding: 22px;
        margin-bottom: 20px;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.35);
    }

    /* Badge Pills */
    .badge-bullish {
        display: inline-block;
        padding: 4px 14px;
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid #10b981;
        color: #34d399;
        font-weight: 700;
        font-size: 0.85rem;
        border-radius: 9999px;
        letter-spacing: 0.03em;
    }
    .badge-bearish {
        display: inline-block;
        padding: 4px 14px;
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid #ef4444;
        color: #f87171;
        font-weight: 700;
        font-size: 0.85rem;
        border-radius: 9999px;
        letter-spacing: 0.03em;
    }
    .badge-neutral {
        display: inline-block;
        padding: 4px 14px;
        background: rgba(245, 158, 11, 0.15);
        border: 1px solid #f59e0b;
        color: #fbbf24;
        font-weight: 700;
        font-size: 0.85rem;
        border-radius: 9999px;
        letter-spacing: 0.03em;
    }
    .badge-tier-high {
        background: rgba(6, 182, 212, 0.2);
        border: 1px solid #06b6d4;
        color: #22d3ee;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
    }
    .badge-tier-med {
        background: rgba(139, 92, 246, 0.2);
        border: 1px solid #8b5cf6;
        color: #a78bfa;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
    }
    .badge-tier-low {
        background: rgba(107, 114, 128, 0.2);
        border: 1px solid #6b7280;
        color: #9ca3af;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
    }

    .text-subtle {
        color: #9ca3af;
        font-size: 0.875rem;
    }

    .hero-banner {
        background: linear-gradient(135deg, #111e38 0%, #162444 50%, #0d1527 100%);
        border: 1px solid rgba(0, 210, 255, 0.2);
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 24px;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #111a2d;
        border-radius: 8px 8px 0px 0px;
        padding: 10px 18px;
        color: #9ca3af;
        font-weight: 500;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .stTabs [aria-selected="true"] {
        background-color: #1e293b !important;
        color: #38bdf8 !important;
        border-top: 2px solid #38bdf8 !important;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def create_price_chart(df: pd.DataFrame, symbol: str, sma_short: int = 20, sma_long: int = 50):
    """Generate an interactive Plotly candlestick chart with SMA overlays and volume."""
    df = df.copy()
    df["SMA20"] = df["Close"].rolling(window=sma_short).mean()
    df["SMA50"] = df["Close"].rolling(window=sma_long).mean()

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.78, 0.22],
        subplot_titles=(f"", "Volume")
    )

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price",
            increasing_line_color="#10b981",
            decreasing_line_color="#ef4444",
            increasing_fillcolor="#10b981",
            decreasing_fillcolor="#ef4444",
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df.index, y=df["SMA20"],
            line=dict(color="#00d2ff", width=1.5),
            name=f"SMA {sma_short}"
        ),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=df.index, y=df["SMA50"],
            line=dict(color="#a855f7", width=1.5),
            name=f"SMA {sma_long}"
        ),
        row=1, col=1
    )

    colors = ["#10b981" if c >= o else "#ef4444" for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(
        go.Bar(
            x=df.index, y=df["Volume"],
            marker_color=colors,
            name="Volume",
            showlegend=False
        ),
        row=2, col=1
    )

    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="#0c121e",
        paper_bgcolor="#0c121e",
        xaxis_rangeslider_visible=False,
        margin=dict(l=15, r=15, t=15, b=15),
        height=480,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="right",
            x=1,
            font=dict(size=11, color="#cbd5e1")
        ),
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        yaxis2=dict(gridcolor="rgba(255,255,255,0.05)"),
    )
    return fig


def create_payoff_chart(
    spot_price: float,
    strike: float,
    ask_price: float,
    option_type: str,
    breakeven: float,
    contracts: int = 1
):
    """Generate an interactive Plotly expiration P&L payoff graph."""
    is_call = (option_type.upper() == "CALL")
    price_range = np.linspace(spot_price * 0.85, spot_price * 1.15, 80)

    if is_call:
        pnl = (np.maximum(price_range - strike, 0) - ask_price) * 100 * contracts
    else:
        pnl = (np.maximum(strike - price_range, 0) - ask_price) * 100 * contracts

    fig = go.Figure()

    # Zero line
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.25)", line_width=1)

    # Payoff curve
    fig.add_trace(go.Scatter(
        x=price_range,
        y=pnl,
        mode="lines",
        line=dict(color="#38bdf8", width=2.5),
        name="P&L at Expiry",
        fill="tozeroy",
        fillcolor="rgba(56, 189, 248, 0.08)"
    ))

    # Breakeven point
    fig.add_vline(x=breakeven, line_dash="dot", line_color="#fbbf24", line_width=1.5,
                  annotation_text=f"Breakeven: ${breakeven:.2f}", annotation_position="top right")

    # Current spot price
    fig.add_vline(x=spot_price, line_dash="solid", line_color="#10b981", line_width=1.5,
                  annotation_text=f"Current: ${spot_price:.2f}", annotation_position="bottom left")

    # Strike price
    fig.add_vline(x=strike, line_dash="dot", line_color="#a855f7", line_width=1.5,
                  annotation_text=f"Strike: ${strike:.2f}", annotation_position="top left")

    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="#0c121e",
        paper_bgcolor="#0c121e",
        title=dict(text=f"Expiration Payoff Analysis ({contracts} Contract{'s' if contracts > 1 else ''})", font=dict(size=13, color="#cbd5e1")),
        xaxis=dict(title="Underlying Stock Price ($)", gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(title="Net P&L ($)", gridcolor="rgba(255,255,255,0.05)"),
        height=320,
        margin=dict(l=15, r=15, t=35, b=15),
        showlegend=False
    )
    return fig


def create_spread_payoff_chart(
    spot_price: float,
    long_strike: float,
    short_strike: float,
    net_debit: float,
    spread_type: str,
    breakeven: float,
    contracts: int = 1
):
    """Generate an interactive Plotly vertical debit spread expiration P&L payoff graph."""
    is_bull = "Bull" in spread_type
    price_range = np.linspace(spot_price * 0.85, spot_price * 1.15, 80)

    if is_bull:
        long_val = np.maximum(price_range - long_strike, 0)
        short_val = np.maximum(price_range - short_strike, 0)
    else:
        long_val = np.maximum(long_strike - price_range, 0)
        short_val = np.maximum(short_strike - price_range, 0)

    pnl = (long_val - short_val - net_debit) * 100 * contracts

    fig = go.Figure()
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.25)", line_width=1)

    fig.add_trace(go.Scatter(
        x=price_range,
        y=pnl,
        mode="lines",
        line=dict(color="#10b981", width=2.5),
        name="Spread P&L",
        fill="tozeroy",
        fillcolor="rgba(16, 185, 129, 0.08)"
    ))

    fig.add_vline(x=breakeven, line_dash="dot", line_color="#fbbf24", line_width=1.5,
                  annotation_text=f"Breakeven: ${breakeven:.2f}", annotation_position="top right")
    fig.add_vline(x=spot_price, line_dash="solid", line_color="#38bdf8", line_width=1.5,
                  annotation_text=f"Current: ${spot_price:.2f}", annotation_position="bottom left")

    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="#0c121e",
        paper_bgcolor="#0c121e",
        title=dict(text=f"{spread_type} Payoff ({contracts} Contract{'s' if contracts > 1 else ''})", font=dict(size=13, color="#cbd5e1")),
        xaxis=dict(title="Underlying Stock Price ($)", gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(title="Net P&L ($)", gridcolor="rgba(255,255,255,0.05)"),
        height=320,
        margin=dict(l=15, r=15, t=35, b=15),
        showlegend=False
    )
    return fig


def render_high_confidence_view(cfg: AppConfig):
    """Render the high-confidence screener focusing on AI stocks and market leaders."""
    st.markdown(
        """
        <div class="hero-banner" style="background: linear-gradient(135deg, #1e1b4b 0%, #172554 50%, #0f172a 100%); border-color: rgba(99, 102, 241, 0.4);">
            <h2 style="margin: 0; color: #818cf8;">🔥 High-Confidence Options Recommendations (AI Ecosystem)</h2>
            <p style="margin: 6px 0 0 0; color: #cbd5e1;">
                Surfaces only higher confidence directional setups (>= 35% score) across AI leaders and mega-caps.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    c_sec, c_conf, c_dir = st.columns([2, 1, 1])
    with c_sec:
        ai_sector_choices = [
            "All AI Leaders (25 Tickers)",
            "AI Chips & Semiconductors",
            "AI Hyperscalers & Platforms",
            "AI Enterprise Software & Cyber",
            "AI Hardware & Data Center Infra",
            "Mega-Cap Tech (Mag 7)",
        ]
        chosen_ai_sector = st.selectbox("AI / Sector Universe", ai_sector_choices)

    with c_conf:
        min_conf = st.slider("Min Confidence %", min_value=25, max_value=65, value=35, step=5)

    with c_dir:
        dir_filter = st.selectbox("Direction", ["All Directions", "Bullish (Calls)", "Bearish (Puts)"])

    if chosen_ai_sector == "All AI Leaders (25 Tickers)":
        tickers = AI_STOCKS_UNIVERSE
    elif chosen_ai_sector in AI_STOCKS_CATEGORIES:
        tickers = AI_STOCKS_CATEGORIES[chosen_ai_sector]
    elif chosen_ai_sector == "Mega-Cap Tech (Mag 7)":
        tickers = WATCHLIST_CATEGORIES["Mega-Cap Tech (Mag 7)"]
    else:
        tickers = AI_STOCKS_UNIVERSE

    if st.button("🚀 Screen for High-Confidence Setups", type="primary"):
        prog = st.progress(0)
        status = st.empty()
        picks = []

        for idx, sym in enumerate(tickers):
            status.caption(f"Analyzing {sym} ({idx+1}/{len(tickers)})...")
            prog.progress((idx + 1) / len(tickers))

            quote = get_current_quote(sym)
            if not quote["valid"]:
                continue

            hist = get_price_history(sym, period=cfg.history_period)
            if hist is None:
                continue

            e_info = get_earnings_info(sym, cfg.earnings.blackout_days, cfg.earnings.warning_days)
            mom = analyze_momentum(hist, sym, cfg.technicals)
            articles = get_company_news(sym, limit=6)
            sent = analyze_news_sentiment(articles, sym)
            sig = generate_signal(mom, sent, e_info, cfg.weights, cfg.earnings)

            if sig.is_earnings_blackout:
                continue

            conf_score_pct = sig.confidence * 100.0
            if conf_score_pct < min_conf:
                continue

            if dir_filter == "Bullish (Calls)" and sig.bias != BiasDirection.BULLISH:
                continue
            if dir_filter == "Bearish (Puts)" and sig.bias != BiasDirection.BEARISH:
                continue
            if sig.bias == BiasDirection.NEUTRAL:
                continue

            calls_df, puts_df, _ = get_options_chains(sym, cfg.options_filter.min_dte, cfg.options_filter.max_dte)
            screening = suggest_options(sig, quote["current_price"], calls_df, puts_df, cfg.options_filter, cfg.risk)

            if screening.single_leg_suggestions:
                picks.append({
                    "symbol": sym,
                    "quote": quote,
                    "mom": mom,
                    "sent": sent,
                    "signal": sig,
                    "screening": screening,
                    "conf": conf_score_pct
                })

        prog.empty()
        status.empty()

        if not picks:
            st.warning(f"No setups met the {min_conf}% confidence criteria in '{chosen_ai_sector}'. Try lowering the threshold.")
            return

        picks.sort(key=lambda x: x["conf"], reverse=True)
        st.success(f"🎯 Discovered **{len(picks)} High-Confidence Setup(s)**!")

        # Leaderboard Table
        table_rows = []
        for p in picks:
            q = p["quote"]
            s = p["signal"]
            opt = p["screening"].single_leg_suggestions[0]
            spd = p["screening"].spread_suggestions[0] if p["screening"].spread_suggestions else None
            spd_text = f"${spd.net_debit:.2f} debit (R:R {spd.risk_reward_ratio:.1f}:1)" if spd else "N/A"

            table_rows.append({
                "Rank": f"#{len(table_rows)+1}",
                "Ticker": p["symbol"],
                "Price": f"${q['current_price']:.2f}",
                "Direction": s.bias.value,
                "Confidence": f"{p['conf']:.1f}% [{s.confidence_tier.value}]",
                "Contract Pick": f"{opt.option_type} ${opt.strike:.0f} ({opt.delta:+.2f}Δ) exp {opt.expiration}",
                "Ask": f"${opt.ask:.2f}",
                "Breakeven": f"${opt.breakeven_price:.2f} ({opt.required_move_pct:+.1f}%)",
                "Sizing (1% Risk)": f"{opt.suggested_contracts}x (${opt.total_dollar_risk:,.0f})",
                "Stop Loss": f"${opt.suggested_stop_loss_price:.2f}",
                "Debit Spread Alt": spd_text,
            })

        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

        st.markdown("---")
        # Visual Cards for Top Picks with Payoff Chart
        for idx, pick in enumerate(picks, start=1):
            sym = pick["symbol"]
            q = pick["quote"]
            sig = pick["signal"]
            opt = pick["screening"].single_leg_suggestions[0]
            spd = pick["screening"].spread_suggestions[0] if pick["screening"].spread_suggestions else None

            badge_col = "#10b981" if sig.bias == BiasDirection.BULLISH else "#ef4444"

            st.markdown(
                f"""
                <div class="trade-card" style="border-left: 4px solid {badge_col};">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                        <div>
                            <span style="font-size: 1.25rem; font-weight: 700; color: #ffffff;">
                                #{idx}. {q['name']} ({sym}) — ${q['current_price']:.2f}
                            </span>
                            <span style="margin-left: 10px; font-weight: 700; color: {badge_col};">[{sig.bias.value}]</span>
                            <span style="margin-left: 6px; color: #22d3ee; font-weight: 600;">{pick['conf']:.1f}% Confidence</span>
                        </div>
                        <div style="color: #94a3b8; font-size: 0.85rem;">
                            Vol Ratio: {pick['mom'].volume_ratio:.2f}x | MTF: {pick['mom'].weekly_trend}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            col_l, col_r = st.columns(2)
            with col_l:
                st.markdown(f"**💡 Primary Contract**: `{opt.contract_symbol}`")
                st.write(
                    f"- Strike: **${opt.strike:.2f} {opt.option_type}** ({opt.delta:+.2f}Δ) exp **{opt.expiration}** ({opt.dte}d)\n"
                    f"- Ask: **${opt.ask:.2f}** | Bid: ${opt.bid:.2f} (Spread: {opt.spread_pct_of_mid:.1f}%)\n"
                    f"- Breakeven: **${opt.breakeven_price:.2f}** (Requires {opt.required_move_pct:+.1f}% move)\n"
                    f"- **Position Sizing**: **{opt.suggested_contracts} contract(s)** ➔ Max loss: **${opt.total_dollar_risk:.2f}**\n"
                    f"- **Stop-Loss (50%)**: Exit at **${opt.suggested_stop_loss_price:.2f}**\n"
                )
                payoff_fig = create_payoff_chart(
                    q["current_price"], opt.strike, opt.ask, opt.option_type, opt.breakeven_price, opt.suggested_contracts
                )
                st.plotly_chart(payoff_fig, use_container_width=True)

            with col_r:
                if spd:
                    st.markdown(f"**📦 Debit Spread Alternative**: `{spd.spread_type}`")
                    st.write(
                        f"- Long Leg: Buy `{spd.long_contract}` (${spd.long_strike:.2f}) @ ${spd.long_ask:.2f}\n"
                        f"- Short Leg: Sell `{spd.short_contract}` (${spd.short_strike:.2f}) @ ${spd.short_bid:.2f}\n"
                        f"- Net Debit: **${spd.net_debit:.2f}** (${spd.max_loss_per_contract:.2f} max loss/contract)\n"
                        f"- Max Profit: **${spd.max_profit_per_contract:.2f}** (Risk/Reward **{spd.risk_reward_ratio:.2f}:1**)\n"
                        f"- Breakeven: **${spd.breakeven_price:.2f}**\n"
                    )
                    spread_fig = create_spread_payoff_chart(
                        q["current_price"], spd.long_strike, spd.short_strike, spd.net_debit, spd.spread_type, spd.breakeven_price, spd.suggested_contracts
                    )
                    st.plotly_chart(spread_fig, use_container_width=True)
                else:
                    st.markdown("**Strategic Rationale**")
                    for r in sig.rationale[:4]:
                        st.write(f"- {r}")


def main():
    # -----------------------------------------------------
    # Sidebar: Mode, Watchlist Universe & Risk Controls
    # -----------------------------------------------------
    st.sidebar.markdown("## ⚡ **Options Suggester**")
    st.sidebar.caption("Institutional-Grade Signals • 100% Free Stack")

    mode = st.sidebar.radio(
        "Operating Mode",
        [
            "🔥 High-Confidence AI Picks",
            "Single Ticker Deep Dive",
            "Multi-Sector Watchlist Scanner"
        ]
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🛡️ **Risk & Sizing Model**")
    account_equity = st.sidebar.number_input("Account Equity ($)", min_value=1000.0, value=10000.0, step=1000.0, format="%.0f")
    risk_pct = st.sidebar.slider("Max Capital Risk per Trade (%)", min_value=0.25, max_value=3.0, value=1.0, step=0.25) / 100.0
    stop_loss_pct = st.sidebar.slider("Option Premium Stop Loss (%)", min_value=20, max_value=80, value=50, step=5) / 100.0

    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ **Contract Selection Filters**")
    dte_range = st.sidebar.slider("DTE Range (Days to Expiry)", min_value=7, max_value=90, value=(14, 45))
    delta_bounds = st.sidebar.slider("Delta Target Range", min_value=0.20, max_value=0.70, value=(0.30, 0.55), step=0.05)
    max_spread = st.sidebar.slider("Max Bid-Ask Spread (% of Mid)", min_value=3, max_value=25, value=10) / 100.0
    min_volume = st.sidebar.number_input("Min Volume", min_value=0, value=20, step=5)
    min_oi = st.sidebar.number_input("Min Open Interest", min_value=0, value=100, step=25)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚖️ **Signal Weighting**")
    mom_weight = st.sidebar.slider("Technical Momentum Weight", 0.0, 1.0, 0.60, 0.05)
    sent_weight = round(1.0 - mom_weight, 2)
    st.sidebar.caption(f"News Sentiment Weight: **{sent_weight}**")
    high_conf_only = st.sidebar.checkbox("High Confidence Tier Only", value=False)

    # Assemble AppConfig
    cfg = AppConfig()
    cfg.risk.account_equity = float(account_equity)
    cfg.risk.max_risk_pct = float(risk_pct)
    cfg.risk.stop_loss_pct = float(stop_loss_pct)
    cfg.options_filter.min_dte = dte_range[0]
    cfg.options_filter.max_dte = dte_range[1]
    cfg.options_filter.min_delta = delta_bounds[0]
    cfg.options_filter.max_delta = delta_bounds[1]
    cfg.options_filter.max_spread_pct_of_mid = float(max_spread)
    cfg.options_filter.min_volume = int(min_volume)
    cfg.options_filter.min_open_interest = int(min_oi)
    cfg.weights.momentum_weight = float(mom_weight)
    cfg.weights.sentiment_weight = float(sent_weight)

    # Route to Mode
    if mode == "🔥 High-Confidence AI Picks":
        render_high_confidence_view(cfg)
        return

    # -----------------------------------------------------
    # MODE: MULTI-SECTOR WATCHLIST SCANNER
    # -----------------------------------------------------
    if mode == "Multi-Sector Watchlist Scanner":
        st.markdown(
            """
            <div class="hero-banner">
                <h2 style="margin: 0; color: #38bdf8;">📋 Multi-Sector Watchlist Scanner</h2>
                <p style="margin: 6px 0 0 0; color: #94a3b8;">
                    Scan over 50 liquid US stocks and ETFs categorized across AI, Tech, Semiconductors, Financials, Healthcare, and Energy.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        col_cat, col_btn = st.columns([3, 1])
        with col_cat:
            category_names = ["All Liquid Equities (50+ Tickers)"] + list(WATCHLIST_CATEGORIES.keys())
            chosen_cat = st.selectbox("Choose Sector Watchlist", category_names)

        with col_btn:
            st.write("")
            st.write("")
            start_scan = st.button("🚀 Run Live Scan", type="primary", use_container_width=True)

        if chosen_cat == "All Liquid Equities (50+ Tickers)":
            scan_tickers = EXPANDED_WATCHLIST
        else:
            scan_tickers = WATCHLIST_CATEGORIES.get(chosen_cat, cfg.default_watchlist)

        st.caption(f"Universe: **{len(scan_tickers)} tickers** selected in '{chosen_cat}'.")

        if start_scan:
            progress_bar = st.progress(0)
            status_text = st.empty()
            rows = []

            for idx, sym in enumerate(scan_tickers):
                status_text.caption(f"Analyzing {sym} ({idx+1}/{len(scan_tickers)})...")
                progress_bar.progress((idx + 1) / len(scan_tickers))

                quote = get_current_quote(sym)
                if not quote["valid"]:
                    continue

                hist = get_price_history(sym, period=cfg.history_period)
                if hist is None:
                    continue

                e_info = get_earnings_info(sym, cfg.earnings.blackout_days, cfg.earnings.warning_days)
                mom = analyze_momentum(hist, sym, cfg.technicals)
                articles = get_company_news(sym, limit=5)
                sent = analyze_news_sentiment(articles, sym)
                sig = generate_signal(mom, sent, e_info, cfg.weights, cfg.earnings)

                if high_conf_only and sig.confidence_tier != ConfidenceTier.HIGH:
                    continue

                top_opt_str = "None"
                if sig.bias != BiasDirection.NEUTRAL and not sig.is_earnings_blackout:
                    c_df, p_df, _ = get_options_chains(sym, cfg.options_filter.min_dte, cfg.options_filter.max_dte)
                    screening = suggest_options(sig, quote["current_price"], c_df, p_df, cfg.options_filter, cfg.risk)
                    if screening.single_leg_suggestions:
                        s = screening.single_leg_suggestions[0]
                        top_opt_str = f"{s.option_type} ${s.strike:.0f} ({s.delta:+.2f}Δ) {s.expiration} (${s.ask:.2f})"

                e_status = "OK"
                if sig.is_earnings_blackout:
                    e_status = f"⛔ In {e_info.get('days_to_earnings')}d"
                elif e_info.get("is_warning"):
                    e_status = f"⚠️ In {e_info.get('days_to_earnings')}d"

                rows.append({
                    "Symbol": sym,
                    "Price": f"${quote['current_price']:.2f}",
                    "Change %": f"{quote['change_percent']:+.2f}%",
                    "Direction": sig.bias.value,
                    "Confidence": sig.confidence_tier.value,
                    "Combined Score": f"{sig.combined_score:+.2f}",
                    "Momentum": f"{mom.momentum_score:+.2f}",
                    "Volume Conf": "✅ Confirmed" if mom.volume_confirmed else "⚠️ Below Avg",
                    "MTF Weekly": mom.weekly_trend,
                    "Sentiment": f"{sent.overall_score:+.2f}",
                    "Earnings": e_status,
                    "Top Contract Suggestion": top_opt_str,
                })

            progress_bar.empty()
            status_text.empty()

            if rows:
                scan_df = pd.DataFrame(rows)
                st.dataframe(scan_df, use_container_width=True, hide_index=True)

                csv_buffer = io.StringIO()
                scan_df.to_csv(csv_buffer, index=False)
                st.download_button(
                    label="📥 Export Scanner Results to CSV",
                    data=csv_buffer.getvalue(),
                    file_name=f"options_scan_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                )
            else:
                st.info("No candidates passed the selected filters.")
        return

    # -----------------------------------------------------
    # MODE: SINGLE TICKER DEEP DIVE
    # -----------------------------------------------------
    col_sel_cat, col_sel_sym, col_custom = st.columns([2, 2, 2])
    with col_sel_cat:
        category_choice = st.selectbox(
            "Browse by Sector",
            ["All Expanded Equities"] + list(WATCHLIST_CATEGORIES.keys())
        )

    with col_sel_sym:
        if category_choice == "All Expanded Equities":
            sym_list = EXPANDED_WATCHLIST
        else:
            sym_list = WATCHLIST_CATEGORIES.get(category_choice, EXPANDED_WATCHLIST)
        selected_ticker = st.selectbox("Select Stock", ["Custom..."] + sym_list, index=1 if "NVDA" in sym_list else 0)

    with col_custom:
        if selected_ticker == "Custom...":
            ticker_input = st.text_input("Enter Ticker Symbol", value="NVDA").strip().upper()
        else:
            ticker_input = selected_ticker

    if not ticker_input:
        st.warning("Please specify a ticker symbol.")
        return

    with st.spinner(f"Analyzing {ticker_input} (Prices, News, Chains, Greeks)..."):
        quote = get_current_quote(ticker_input)
        if not quote["valid"]:
            st.error(f"Could not retrieve market data for '{ticker_input}'. Please check the ticker symbol.")
            return

        hist = get_price_history(ticker_input, period=cfg.history_period)
        if hist is None:
            st.error(f"Insufficient historical data available for '{ticker_input}'.")
            return

        earnings_info = get_earnings_info(ticker_input, cfg.earnings.blackout_days, cfg.earnings.warning_days)
        momentum = analyze_momentum(hist, ticker_input, cfg.technicals)
        news_articles = get_company_news(ticker_input, limit=cfg.news_limit)
        sentiment = analyze_news_sentiment(news_articles, ticker_input)
        signal = generate_signal(momentum, sentiment, earnings_info, cfg.weights, cfg.earnings)

    # Header KPI Metrics
    k1, k2, k3, k4, k5 = st.columns(5)
    chg_delta = f"{quote['change']:+.2f} ({quote['change_percent']:+.2f}%)"
    k1.metric("Current Price", f"${quote['current_price']:.2f}", chg_delta)
    k2.metric("Day Range", f"${quote['day_low']:.2f} - ${quote['day_high']:.2f}")
    k3.metric("52W Range", f"${quote['fifty_two_week_low']:.2f} - ${quote['fifty_two_week_high']:.2f}")
    k4.metric("20d Vol Ratio", f"{momentum.volume_ratio:.2f}x", "Confirmed" if momentum.volume_confirmed else "Below Avg")
    k5.metric("MTF Weekly Trend", momentum.weekly_trend, "Aligned" if momentum.multi_timeframe_aligned else "Divergent")

    if signal.is_earnings_blackout:
        st.error(f"### {earnings_info.get('status_message')}")
    elif earnings_info.get("is_warning"):
        st.warning(f"### {earnings_info.get('status_message')}")

    bias_badge_class = "badge-bullish" if signal.bias == BiasDirection.BULLISH else ("badge-bearish" if signal.bias == BiasDirection.BEARISH else "badge-neutral")
    tier_badge_class = f"badge-tier-{signal.confidence_tier.value.lower()}"

    st.markdown(
        f"""
        <div class="hero-banner">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                <div>
                    <span style="font-size: 1.3rem; font-weight: 700; color: #ffffff; margin-right: 14px;">
                        {quote['name']} ({ticker_input})
                    </span>
                    <span class="{bias_badge_class}">{signal.bias.value}</span>
                    <span class="{tier_badge_class}" style="margin-left: 8px;">[{signal.confidence_tier.value} CONFIDENCE]</span>
                </div>
                <div style="font-size: 0.95rem; color: #94a3b8;">
                    Combined Score: <strong style="color: #38bdf8;">{signal.combined_score:+.2f}</strong> &nbsp;|&nbsp;
                    Confidence: <strong style="color: #f8fafc;">{signal.confidence * 100:.1f}%</strong>
                </div>
            </div>
            <p style="margin: 14px 0 0 0; color: #cbd5e1; font-size: 0.95rem;">
                <strong>Strategic Directive:</strong> {signal.action_suggestion}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_opts, tab_spreads, tab_chart, tab_tech, tab_news, tab_audit = st.tabs([
        "💡 Options Suggestions",
        "📦 Debit Spread Alternatives",
        "📊 Technical Price Chart",
        "📈 Momentum & Multi-Timeframe",
        "📰 News & Recency Sentiment",
        "🛡️ Screening Audit Log"
    ])

    with tab_opts:
        with st.spinner("Filtering options chain (Delta 0.30–0.55)..."):
            calls_df, puts_df, _ = get_options_chains(ticker_input, cfg.options_filter.min_dte, cfg.options_filter.max_dte)
            screening = suggest_options(signal, quote["current_price"], calls_df, puts_df, cfg.options_filter, cfg.risk)

        if screening.single_leg_suggestions:
            suggestions = screening.single_leg_suggestions
            best = suggestions[0]

            st.markdown(
                f"""
                <div class="trade-card" style="border-left: 4px solid #38bdf8;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
                        <div>
                            <span style="font-size: 1.15rem; font-weight: 700; color: #ffffff;">
                                🏆 Primary Pick: {best.contract_symbol}
                            </span>
                            <div style="margin-top: 4px; color: #94a3b8; font-size: 0.9rem;">
                                Strike: <strong style="color: #f8fafc;">${best.strike:.2f} {best.option_type}</strong> &nbsp;|&nbsp;
                                Delta: <strong style="color: #38bdf8;">{best.delta:+.2f}Δ</strong> &nbsp;|&nbsp;
                                Expiration: <strong style="color: #f8fafc;">{best.expiration} ({best.dte}d DTE)</strong>
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <span style="font-size: 1.3rem; font-weight: 700; color: #10b981;">
                                Ask: ${best.ask:.2f}
                            </span>
                            <div style="color: #94a3b8; font-size: 0.8rem;">
                                Bid: ${best.bid:.2f} | Spread: {best.spread_pct_of_mid:.1f}%
                            </div>
                        </div>
                    </div>
                    <hr style="border-color: rgba(255,255,255,0.08); margin: 16px 0;">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
                        <div>
                            <div class="text-subtle">Recommended Sizing</div>
                            <div style="font-size: 1.1rem; font-weight: 600; color: #38bdf8;">
                                {best.suggested_contracts} Contract(s) (${best.total_dollar_risk:,.0f} Max Loss)
                            </div>
                            <div style="font-size: 0.78rem; color: #94a3b8;">
                                Sized for {cfg.risk.max_risk_pct * 100:.1f}% risk on ${cfg.risk.account_equity:,.0f} equity
                            </div>
                        </div>
                        <div>
                            <div class="text-subtle">Stop-Loss Exit Level</div>
                            <div style="font-size: 1.1rem; font-weight: 600; color: #f87171;">
                                Exit @ ${best.suggested_stop_loss_price:.2f} (50% Premium Stop)
                            </div>
                            <div style="font-size: 0.78rem; color: #94a3b8;">
                                Limits loss to ~${best.stop_loss_dollar_risk:,.0f}
                            </div>
                        </div>
                        <div>
                            <div class="text-subtle">Breakeven at Expiry</div>
                            <div style="font-size: 1.1rem; font-weight: 600; color: #fbbf24;">
                                ${best.breakeven_price:.2f} ({best.required_move_pct:+.1f}% move)
                            </div>
                            <div style="font-size: 0.78rem; color: #94a3b8;">
                                IV: {best.implied_volatility_pct:.1f}% | OI: {best.open_interest:,}
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Interactive Payoff diagram for Primary Pick
            st.markdown("##### 📈 Contract Payoff Diagram (P&L at Expiry)")
            single_payoff = create_payoff_chart(
                quote["current_price"], best.strike, best.ask, best.option_type, best.breakeven_price, best.suggested_contracts
            )
            st.plotly_chart(single_payoff, use_container_width=True)

            st.markdown("#### 📋 Filtered Candidates Ranked by Liquidity & Delta Alignment")
            rows = []
            for idx, s in enumerate(suggestions, start=1):
                rows.append({
                    "Rank": f"#{idx}",
                    "Contract Symbol": s.contract_symbol,
                    "Type": s.option_type,
                    "Strike": f"${s.strike:.2f}",
                    "Delta": f"{s.delta:+.2f}Δ",
                    "Expiration": s.expiration,
                    "DTE": f"{s.dte}d",
                    "Bid / Ask": f"${s.bid:.2f} / ${s.ask:.2f}",
                    "Spread %": f"{s.spread_pct_of_mid:.1f}%",
                    "Volume": f"{s.volume:,}",
                    "Open Interest": f"{s.open_interest:,}",
                    "IV": f"{s.implied_volatility_pct:.1f}%",
                    "Breakeven": f"${s.breakeven_price:.2f}",
                    "Req Move": f"{s.required_move_pct:+.1f}%",
                    "Sizing (Contracts)": f"{s.suggested_contracts}x (${s.total_dollar_risk:,.0f})",
                    "Stop Loss (50%)": f"${s.suggested_stop_loss_price:.2f}",
                    "Score": s.rank_score,
                })

            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            if signal.is_earnings_blackout:
                st.error("Directional trades blocked: Active earnings blackout window.")
            elif signal.bias == BiasDirection.NEUTRAL:
                st.info("Neutral signal: No directional contracts recommended.")
            else:
                st.warning("No contracts satisfied strict delta (0.30–0.55), spread, or liquidity thresholds.")

    with tab_spreads:
        if screening.spread_suggestions:
            spd = screening.spread_suggestions[0]
            st.markdown(
                f"""
                <div class="trade-card" style="border-left: 4px solid #10b981;">
                    <h3 style="margin-top: 0; color: #10b981;">📦 {spd.spread_type}</h3>
                    <p style="color: #94a3b8; font-size: 0.95rem;">
                        Vertical debit spreads cap your risk and substantially mitigate Implied Volatility crush.
                    </p>
                    <div style="background: rgba(0,0,0,0.25); border-radius: 8px; padding: 14px; margin: 14px 0;">
                        <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
                            <div>
                                <span style="color: #10b981; font-weight: 600;">[BUY LONG LEG]</span>
                                <strong>{spd.long_contract}</strong> (${spd.long_strike:.2f} Strike / {spd.long_delta:+.2f}Δ) @ Ask ${spd.long_ask:.2f}
                            </div>
                            <div>
                                <span style="color: #ef4444; font-weight: 600;">[SELL SHORT LEG]</span>
                                <strong>{spd.short_contract}</strong> (${spd.short_strike:.2f} Strike / {spd.short_delta:+.2f}Δ) @ Bid ${spd.short_bid:.2f}
                            </div>
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin-top: 14px;">
                        <div>
                            <div class="text-subtle">Net Debit Entry</div>
                            <div style="font-size: 1.2rem; font-weight: 700; color: #38bdf8;">${spd.net_debit:.2f} / share</div>
                            <div style="font-size: 0.8rem; color: #94a3b8;">${spd.max_loss_per_contract:.2f} max loss / contract</div>
                        </div>
                        <div>
                            <div class="text-subtle">Max Profit Potential</div>
                            <div style="font-size: 1.2rem; font-weight: 700; color: #10b981;">${spd.max_profit_per_contract:.2f}</div>
                            <div style="font-size: 0.8rem; color: #94a3b8;">Risk/Reward Ratio: {spd.risk_reward_ratio:.2f}:1</div>
                        </div>
                        <div>
                            <div class="text-subtle">Breakeven at Expiry</div>
                            <div style="font-size: 1.2rem; font-weight: 700; color: #fbbf24;">${spd.breakeven_price:.2f}</div>
                            <div style="font-size: 0.8rem; color: #94a3b8;">Expiration: {spd.expiration} ({spd.dte}d)</div>
                        </div>
                        <div>
                            <div class="text-subtle">Position Sizing</div>
                            <div style="font-size: 1.2rem; font-weight: 700; color: #f8fafc;">{spd.suggested_contracts} Contract(s)</div>
                            <div style="font-size: 0.8rem; color: #94a3b8;">Total Risk: ${spd.total_dollar_risk:.2f}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Spread Payoff diagram
            st.markdown("##### 📈 Spread Payoff Diagram")
            spread_chart = create_spread_payoff_chart(
                quote["current_price"], spd.long_strike, spd.short_strike, spd.net_debit, spd.spread_type, spd.breakeven_price, spd.suggested_contracts
            )
            st.plotly_chart(spread_chart, use_container_width=True)
        else:
            st.info("No debit spread candidates generated for current market conditions.")

    with tab_chart:
        chart_fig = create_price_chart(hist, ticker_input, cfg.technicals.sma_short, cfg.technicals.sma_long)
        st.plotly_chart(chart_fig, use_container_width=True)

    with tab_tech:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Blended Momentum", f"{momentum.momentum_score:+.2f}", momentum.trend_description)
        m2.metric("RSI (14)", f"{momentum.rsi:.1f}", "Overbought" if momentum.rsi > 70 else ("Oversold" if momentum.rsi < 30 else "Neutral"))
        m3.metric("Volume Confirmation", f"{momentum.volume_ratio:.2f}x", "Confirmed" if momentum.volume_confirmed else "Unconfirmed")
        m4.metric("MTF Alignment", momentum.weekly_trend, "Aligned" if momentum.multi_timeframe_aligned else "Divergence")

        st.markdown("#### Strategic Rationale Checklist")
        for r in signal.rationale:
            st.markdown(f"- **{r}**")

    with tab_news:
        n1, n2, n3 = st.columns(3)
        n1.metric("Weighted Sentiment", f"{sentiment.overall_score:+.2f}", sentiment.sentiment_label)
        n2.metric("Headlines Scored", f"{sentiment.article_count}")
        n3.metric("Sentiment Breakdown", f"{sentiment.positive_count} Pos | {sentiment.negative_count} Neg | {sentiment.neutral_count} Neu")

        if sentiment.scored_articles:
            st.markdown("#### Recent News with Time-Decay Weights")
            news_df = pd.DataFrame(sentiment.scored_articles)
            st.dataframe(
                news_df[["published_at", "publisher", "title", "compound", "weight", "category"]],
                use_container_width=True,
                hide_index=True
            )

    with tab_audit:
        st.markdown("#### 🛡️ Transparent Filter Audit")
        st.caption("Detailed diagnostics showing why contracts were accepted or rejected during the quantitative screen:")
        st.json(screening.audit_log)

    st.markdown("---")
    st.caption(DEFAULT_CONFIG.disclaimer)


if __name__ == "__main__":
    main()
