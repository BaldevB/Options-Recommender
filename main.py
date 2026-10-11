"""Command-line interface (CLI) for Options Suggester.

Enhanced with Delta targeting (0.30-0.55), volume confirmation, earnings blackout,
High/Medium/Low confidence tiers, position sizing, debit spread alternatives,
high-risk speculative setups (OTM moonshots & lotto spreads with uncapped sizing),
full Options Chain Matrix & Black-Scholes Greeks, and
expanded AI, Commodities & sector watchlists (100+ tickers).
"""

import sys
import io

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        elif hasattr(sys.stdout, "buffer"):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        elif hasattr(sys.stderr, "buffer"):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

import argparse
from typing import List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import (
    AppConfig, DEFAULT_CONFIG, WATCHLIST_CATEGORIES, EXPANDED_WATCHLIST,
    COMMODITIES_CATEGORIES, COMMODITIES_UNIVERSE,
    AI_STOCKS_UNIVERSE, AI_STOCKS_CATEGORIES,
    HIGH_RISK_UNIVERSE, HIGH_RISK_CATEGORIES, HIGH_RISK_FILTER_CONFIG,
    ZERO_DTE_UNIVERSE, ZERO_DTE_FILTER_CONFIG
)
from data.price_data import get_price_history, get_current_quote, get_earnings_info
from data.news_data import get_company_news
from data.options_data import get_options_chains, get_options_chain_matrix
from analysis.momentum import analyze_momentum, MomentumResult
from analysis.sentiment import analyze_news_sentiment, SentimentResult
from analysis.signals import generate_signal, TradeSignal, BiasDirection, ConfidenceTier
from options.suggester import (
    suggest_options, ScreeningResult, OptionSuggestion, DebitSpreadSuggestion,
    HighRiskTradeSetup, ZeroDteTradeSetup, OptionTradePlan
)

console = Console(legacy_windows=False)


def print_banner():
    """Print header banner."""
    title = "[bold cyan]🎯 US Stock Options Suggester[/bold cyan] [dim](Disciplined Core | 🪙 Commodities | ⚡ High-Risk Lab | ⛓️ Chain Matrix)[/dim]"
    subtitle = "[italic]Recency Sentiment + Multi-Timeframe Momentum + Greeks Matrix + High-Risk Lotto Setups[/italic]"
    console.print(Panel(f"{title}\n{subtitle}", expand=False, border_style="cyan"))


def print_disclaimer():
    """Print compliance disclaimer."""
    console.print(f"\n[bold yellow]{DEFAULT_CONFIG.disclaimer}[/bold yellow]\n")


def display_ticker_analysis(
    quote: dict,
    momentum: MomentumResult,
    sentiment: SentimentResult,
    signal: TradeSignal,
    screening: ScreeningResult,
    cfg: AppConfig
):
    """Render detailed single-ticker breakdown with Rich tables and panels."""
    symbol = quote["symbol"]
    price = quote["current_price"]
    chg = quote["change"]
    chg_pct = quote["change_percent"]
    color = "green" if chg >= 0 else "red"

    # 1. Header & Quote Summary
    e_info = signal.earnings_info
    e_badge = ""
    if e_info.get("is_blackout"):
        e_badge = f"\n[bold red]⛔ {e_info.get('status_message')}[/bold red]"
    elif e_info.get("is_warning"):
        e_badge = f"\n[bold yellow]⚠️ {e_info.get('status_message')}[/bold yellow]"

    summary_text = (
        f"[bold white]{quote['name']} ({symbol})[/bold white]\n"
        f"Price: [bold {color}]${price:,.2f} ({chg:+.2f} / {chg_pct:+.2f}%)[/bold {color}] | "
        f"Day: ${quote['day_low']:.2f} - ${quote['day_high']:.2f} | "
        f"52W: ${quote['fifty_two_week_low']:.2f} - ${quote['fifty_two_week_high']:.2f}{e_badge}"
    )
    console.print(Panel(summary_text, title=f"📊 [bold]{symbol} Market Overview[/bold]", border_style="blue"))

    # 2. Technical Momentum Table
    mom_table = Table(title="📈 Technical Momentum & Confirmations", show_header=True, header_style="bold magenta")
    mom_table.add_column("Indicator", style="dim")
    mom_table.add_column("Value", justify="right")
    mom_table.add_column("Confirmation / Status", style="bold")

    rsi_interp = "Overbought (>70)" if momentum.rsi >= 70 else ("Oversold (<30)" if momentum.rsi <= 30 else "Neutral (30-70)")
    mom_table.add_row("RSI (14)", f"{momentum.rsi:.1f}", rsi_interp)

    macd_interp = f"Line: {momentum.macd_line:+.2f} | Sig: {momentum.macd_signal:+.2f} ({'Bullish' if momentum.macd_hist > 0 else 'Bearish'})"
    mom_table.add_row("MACD (12,26,9)", f"Hist: {momentum.macd_hist:+.3f}", macd_interp)

    ma_interp = f"SMA20: ${momentum.sma_short:.2f} | SMA50: ${momentum.sma_long:.2f}"
    mom_table.add_row("Moving Averages", "SMA20 / SMA50", ma_interp)

    vol_status = "[bold green]CONFIRMED (>= 1.0x)[/]" if momentum.volume_confirmed else "[yellow]UNCONFIRMED (< 1.0x)[/]"
    mom_table.add_row("Volume Ratio (20d)", f"{momentum.volume_ratio:.2f}x", vol_status)

    mtf_status = f"[bold green]Aligned ({momentum.weekly_trend})[/]" if momentum.multi_timeframe_aligned else f"[yellow]Divergence ({momentum.weekly_trend})[/]"
    mom_table.add_row("Weekly Trend (MTF)", f"W-SMA10: ${momentum.details.get('weekly_sma10', 0):.2f}", mtf_status)

    mom_table.add_row("Blended Momentum", f"{momentum.momentum_score:+.2f}", f"[{'green' if momentum.momentum_score > 0 else 'red'}]{momentum.trend_description}[/]")
    console.print(mom_table)

    # 3. Sentiment Table
    sent_table = Table(title="📰 Recency-Weighted News Sentiment (VADER Local)", show_header=True, header_style="bold yellow")
    sent_table.add_column("Metric", style="dim")
    sent_table.add_column("Value", justify="right")
    sent_table.add_column("Details", style="bold")

    sent_table.add_row("Headlines Analyzed", str(sentiment.article_count), f"{sentiment.positive_count} Pos | {sentiment.negative_count} Neg | {sentiment.neutral_count} Neu")
    sent_table.add_row("Weighted Sentiment", f"{sentiment.overall_score:+.2f}", f"[{'green' if sentiment.overall_score > 0 else 'red' if sentiment.overall_score < 0 else 'white'}]{sentiment.sentiment_label}[/]")
    console.print(sent_table)

    # 4. Signal Synthesis Panel
    badge_color = "green" if signal.bias == BiasDirection.BULLISH else ("red" if signal.bias == BiasDirection.BEARISH else "yellow")
    tier_color = "bold green" if signal.confidence_tier == ConfidenceTier.HIGH else ("bold yellow" if signal.confidence_tier == ConfidenceTier.MEDIUM else "dim")

    signal_body = (
        f"Directional Bias: [bold {badge_color}]{signal.bias.value}[/bold {badge_color}]  |  "
        f"Confidence Tier: [{tier_color}][{signal.confidence_tier.value}][/{tier_color}] ({signal.confidence * 100:.1f}%)  |  "
        f"Combined Score: [bold]{signal.combined_score:+.2f}[/bold]\n\n"
        f"[bold underline]Rationale:[/bold underline]\n" + "\n".join([f" • {r}" for r in signal.rationale]) + "\n\n"
        f"[bold]Action Guidance:[/bold] {signal.action_suggestion}"
    )
    console.print(Panel(signal_body, title="⚡ Trade Signal Synthesis", border_style=badge_color))

    # 5. Core Options Recommendations Table
    suggestions = screening.single_leg_suggestions
    if suggestions:
        opt_table = Table(
            title=f"💡 Core Ranked {suggestions[0].option_type} Contracts (Target Delta 0.30–0.55 | Spread <= 10%)",
            show_header=True,
            header_style="bold green" if suggestions[0].option_type == "CALL" else "bold red"
        )
        opt_table.add_column("Rank", justify="center")
        opt_table.add_column("Contract Symbol", style="cyan")
        opt_table.add_column("Strike", justify="right")
        opt_table.add_column("Delta", justify="right", style="bold")
        opt_table.add_column("Exp (DTE)", justify="center")
        opt_table.add_column("Bid / Ask", justify="right")
        opt_table.add_column("Spread %", justify="right")
        opt_table.add_column("Vol / OI", justify="right")
        opt_table.add_column("IV %", justify="right")
        opt_table.add_column("Breakeven", justify="right")
        opt_table.add_column("Position Sizing (1% Risk)", justify="right", style="bold cyan")

        for idx, opt in enumerate(suggestions, start=1):
            opt_table.add_row(
                f"#{idx}",
                opt.contract_symbol,
                f"${opt.strike:.2f}",
                f"{opt.delta:+.2f} Delta",
                f"{opt.expiration} ({opt.dte}d)",
                f"${opt.bid:.2f} / ${opt.ask:.2f}",
                f"{opt.spread_pct_of_mid:.1f}%",
                f"{opt.volume:,} / {opt.open_interest:,}",
                f"{opt.implied_volatility_pct:.1f}%",
                f"${opt.breakeven_price:.2f}",
                f"{opt.suggested_contracts}x (${opt.total_dollar_risk:,.0f} max / stop @ ${opt.suggested_stop_loss_price:.2f})"
            )
        console.print(opt_table)

        # Highlight Best Contract & Institutional Trade Execution Plan
        best = suggestions[0]
        tp = best.trade_plan

        if tp:
            # 1. Scaling Profit Ladder Table
            tp_table = Table(title=f"🎯 Scaling Profit Targets ({best.contract_symbol})", show_header=True, header_style="bold cyan")
            tp_table.add_column("Target Tier", style="bold")
            tp_table.add_column("Option Price", justify="right", style="bold green")
            tp_table.add_column("Stock Target", justify="right", style="bold white")
            tp_table.add_column("Gain / Contract", justify="right", style="green")
            tp_table.add_column("Execution Action & Rule", style="italic")

            tp_table.add_row(
                "TP1 (+50% Quick Trim)",
                f"${tp.tp1_option_price:.2f}",
                f"${tp.tp1_underlying_target:.2f}",
                f"+${tp.tp1_dollar_gain:,.2f}",
                tp.tp1_action
            )
            tp_table.add_row(
                "TP2 (+100% Core Target)",
                f"${tp.tp2_option_price:.2f}",
                f"${tp.tp2_underlying_target:.2f}",
                f"+${tp.tp2_dollar_gain:,.2f}",
                tp.tp2_action
            )
            tp_table.add_row(
                "TP3 (+150% Runner)",
                f"${tp.tp3_runner_price:.2f}",
                f"${tp.tp3_underlying_target:.2f}",
                f"+${tp.tp3_dollar_gain:,.2f}",
                tp.tp3_action
            )

            plan_body = (
                f"[bold white]Strategy Setup:[/bold white] {best.option_type} ${best.strike:.2f} ({best.delta:+.2f}Δ) | Exp: {best.expiration} ({best.dte}d DTE)\n"
                f"• [bold]Entry Execution:[/bold] Limit Order at Mid-Price [bold cyan]${tp.entry_limit_price:.2f}[/bold cyan] (Zone: [cyan]{tp.entry_zone}[/cyan]) | Current Ask: ${tp.entry_market_price:.2f}\n"
                f"• [bold]Underlying Spot:[/bold] ${tp.underlying_spot:.2f} | [bold]Chart Invalidation Price:[/bold] [bold red]${tp.underlying_invalidation_price:.2f}[/bold red]\n\n"
                f"[bold underline]🛡️ Capital Protection & Theta Defense:[/bold underline]\n"
                f"• [bold]Strict Stop-Loss:[/bold] Exit if option touches [bold red]${tp.stop_loss_option_price:.2f}[/bold red] (-50% loss | Max Planned Risk: [bold red]${tp.total_planned_risk:.2f}[/bold red])\n"
                f"  [dim]{tp.stop_loss_rule}[/dim]\n"
                f"• [bold]Time-Stop / Theta Burn:[/bold] Decay [bold yellow]-${tp.daily_theta_decay:.2f}/day[/bold yellow] per contract | Max Holding: [bold yellow]{tp.max_holding_period_days} trading days[/bold yellow]\n"
                f"  [dim]{tp.time_stop_rule}[/dim]\n\n"
                f"[bold underline]📊 Quantitative Edge Analytics:[/bold underline]\n"
                f"• [bold]Probability of Profit (PoP):[/bold] [bold cyan]{tp.probability_of_profit_pct:.1f}%[/bold cyan] (Black-Scholes N(d2))\n"
                f"• [bold]Risk / Reward Ratio:[/bold] [bold green]{tp.risk_reward_ratio:.2f}:1[/bold green] (Core TP2 gain vs 50% stop loss)\n"
                f"• [bold]Expected Value (EV):[/bold] [bold green]+${tp.expected_value_per_contract:.2f}[/bold green] per contract\n\n"
                f"[bold underline]📋 Disciplined Execution Checklist Playbook:[/bold underline]\n" +
                "\n".join([f"  {step}" for step in tp.playbook_steps])
            )
            console.print(Panel(plan_body, title=f"🎯 Institutional Trade Plan & Execution Playbook ({best.contract_symbol})", border_style="cyan"))
            console.print(tp_table)
        else:
            risk_box = (
                f"[bold]Contract Spotlight:[/bold] {best.contract_symbol} (Strike ${best.strike:.2f} {best.option_type}, Delta {best.delta:+.2f} Delta)\n"
                f"• [bold]Account Sizing:[/bold] On ${cfg.risk.account_equity:,.0f} equity with {cfg.risk.max_risk_pct * 100:.1f}% max risk (${cfg.risk.account_equity * cfg.risk.max_risk_pct:.0f} budget):\n"
                f"  Trade [bold cyan]{best.suggested_contracts} contract(s)[/bold cyan] -> Max Capital Loss: [bold red]${best.total_dollar_risk:.2f}[/bold red]\n"
                f"• [bold]Practical Stop-Loss Exit:[/bold] Sell if option hits [bold]${best.suggested_stop_loss_price:.2f}[/bold] (50% premium loss, risk capped at ${best.stop_loss_dollar_risk:.2f})\n"
                f"• [bold]Breakeven at Expiration:[/bold] ${best.breakeven_price:.2f} (Requires {best.required_move_pct:+.1f}% underlying move)\n"
                f"• [bold]Warnings / Notes:[/bold] " + (" | ".join(best.risk_warnings) if best.risk_warnings else "Clean liquidity and spread profile.")
            )
            console.print(Panel(risk_box, title="🛡️ Disciplined Risk Management & Trade Plan", border_style="cyan"))

    # 6. Debit Spread Alternative
    if screening.spread_suggestions:
        spd = screening.spread_suggestions[0]
        spread_title = f"📦 Defined-Risk Alternative: {spd.spread_type} (IV: {screening.avg_iv_pct}%)"
        spread_text = (
            f"[bold]Strategy:[/bold] Buy {spd.long_contract} (${spd.long_strike:.2f} / {spd.long_delta:+.2f} Delta) | "
            f"Sell {spd.short_contract} (${spd.short_strike:.2f} / {spd.short_delta:+.2f} Delta)\n"
            f"• [bold]Net Debit Entry:[/bold] [bold cyan]${spd.net_debit:.2f}[/bold cyan] (${spd.max_loss_per_contract:.2f} max loss per contract)\n"
            f"• [bold]Max Profit Potential:[/bold] [bold green]${spd.max_profit_per_contract:.2f}[/bold green] (Risk/Reward: {spd.risk_reward_ratio:.2f}:1)\n"
            f"• [bold]Breakeven:[/bold] ${spd.breakeven_price:.2f}  |  "
            f"[bold]Position Sizing:[/bold] {spd.suggested_contracts} contract(s) (${spd.total_dollar_risk:.2f} total risk)\n"
            f"• [bold]Why Debit Spread?[/bold] {spd.spread_notes}"
        )
        if spd.trade_plan and isinstance(spd.trade_plan, dict):
            sp_steps = spd.trade_plan.get("playbook_steps", [])
            if sp_steps:
                spread_text += "\n\n[bold underline]📋 Defined-Risk Spread Playbook:[/bold underline]\n" + "\n".join([f"  {s}" for s in sp_steps])
        console.print(Panel(spread_text, title=spread_title, border_style="green"))

    # 7. High-Risk / Speculative Setups (OTM Moonshot & Lotto Spread)
    if screening.high_risk_setup:
        hrs = screening.high_risk_setup
        hr_title = f"[bold red]⚡ Speculative High-Risk Setup: {hrs.setup_name}[/bold red]"
        hr_text = (
            f"[bold]Target Delta Range:[/bold] 0.15–0.28 Delta | [bold]Position Sizing:[/bold] Full Trade Risk Budget (Uncapped)\n"
            f"[bold cyan]🎯 OTM Moonshot ({hrs.option_type}):[/bold cyan] {hrs.contract_symbol}\n"
            f"  • Strike: ${hrs.strike:.2f} | Delta: {hrs.delta:+.2f} Delta | Exp: {hrs.expiration} ({hrs.dte}d) | Ask: ${hrs.ask:.2f}\n"
            f"  • Sizing: {hrs.suggested_contracts} contract(s) | Max Capital Loss: [bold red]${hrs.total_dollar_risk:.2f}[/bold red]\n"
            f"  • Breakeven: ${hrs.breakeven_price:.2f} ({hrs.required_move_pct:+.1f}% move needed) | Upside Leverage: {hrs.upside_leverage:.1f}x\n"
        )
        if hrs.risk_warnings:
            hr_text += f"  • [bold yellow]Warnings:[/bold yellow] " + " | ".join(hrs.risk_warnings) + "\n"
        if hrs.lotto_spread:
            ls = hrs.lotto_spread
            hr_text += (
                f"\n[bold magenta]🎰 Asymmetric Lotto Spread ({ls.spread_type}):[/bold magenta]\n"
                f"  • Long: Strike ${ls.long_strike:.2f} ({ls.long_delta:+.2f} Delta) | Short: Strike ${ls.short_strike:.2f} ({ls.short_delta:+.2f} Delta)\n"
                f"  • Net Debit: [bold cyan]${ls.net_debit:.2f}[/bold cyan] | Max Profit: [bold green]${ls.max_profit_per_contract:.2f}[/bold green] | [bold green]R:R: {ls.risk_reward_ratio:.1f}:1[/bold green]\n"
                f"  • Sizing: {ls.suggested_contracts} spread(s) (${ls.total_dollar_risk:.2f} total risk)\n"
            )
        if hrs.trade_plan and isinstance(hrs.trade_plan, dict):
            hr_steps = hrs.trade_plan.get("playbook_steps", [])
            tp1_rule = hrs.trade_plan.get("tp1", {}).get("action", "")
            hr_text += f"\n[bold underline]🚀 Free-Ride Profit Scaling Rule (House Money):[/bold underline]\n  • {tp1_rule}\n"
            if hr_steps:
                hr_text += "\n[bold underline]📋 Speculative Execution Checklist:[/bold underline]\n" + "\n".join([f"  {s}" for s in hr_steps])
        console.print(Panel(hr_text, title=hr_title, border_style="red"))

    # 8. 0DTE Flash Scalper Setup (if present)
    if screening.zero_dte_setup:
        zds = screening.zero_dte_setup
        zd_title = f"[bold yellow]⚡ 0DTE High-Velocity Flash Lab: {zds.symbol} ({zds.expiration})[/bold yellow]"
        zd_text = (
            f"[bold]Intraday Velocity Requirement:[/bold] [bold yellow]~{zds.breakeven_velocity_per_hour:.2f}%/hr[/bold yellow] to outpace theta decay\n\n"
            f"[bold cyan]🎯 ATM Momentum Scalp (~0.50Δ):[/bold cyan] {zds.scalp_contract}\n"
            f"  • Strike: ${zds.scalp_strike:.1f} {zds.scalp_type} | Delta: {zds.scalp_delta:+.2f}Δ | Ask: ${zds.scalp_ask:.2f} | Gamma: {zds.scalp_gamma:.4f}\n"
            f"  • Theta Burn: [bold red]-${abs(zds.scalp_theta_per_hour * 100):.1f}/hr[/bold red] per contract | Sizing: {zds.scalp_suggested_contracts}x (${zds.scalp_total_risk:.0f})\n"
            f"  • Breakeven: ${zds.scalp_breakeven:.2f} ({zds.scalp_req_move_pct:+.1f}% move needed)\n\n"
            f"[bold magenta]🚀 OTM Gamma Moonshot (~0.20Δ):[/bold magenta] {zds.lotto_contract}\n"
            f"  • Strike: ${zds.lotto_strike:.1f} | Delta: {zds.lotto_delta:+.2f}Δ | Ask: ${zds.lotto_ask:.2f} | Leverage: [bold green]{zds.lotto_upside_leverage:.1f}x[/bold green]\n"
            f"  • Sizing: {zds.lotto_suggested_contracts}x (${zds.lotto_total_risk:.0f}) | Breakeven: ${zds.lotto_breakeven:.2f}\n"
        )
        if zds.lotto_spread:
            zls = zds.lotto_spread
            zd_text += (
                f"\n[bold green]🛡️ 0DTE Defined-Risk Spread ({zls.risk_reward_ratio:.1f}:1 R:R):[/bold green]\n"
                f"  • Long: ${zls.long_strike:.1f} / Short: ${zls.short_strike:.1f} @ [bold cyan]${zls.net_debit:.2f} net debit[/bold cyan]\n"
                f"  • Max Profit: [bold green]${zls.max_profit_per_contract:.2f}[/bold green] | Sized: {zls.suggested_contracts}x (${zls.total_dollar_risk:.0f})\n"
            )
        if zds.trade_plan and isinstance(zds.trade_plan, dict):
            zd_steps = zds.trade_plan.get("playbook_steps", [])
            if zd_steps:
                zd_text += "\n[bold underline]📋 0DTE Intraday Scalping Playbook:[/bold underline]\n" + "\n".join([f"  {s}" for s in zd_steps])
        console.print(Panel(zd_text, title=zd_title, border_style="yellow"))

    if not suggestions and not screening.spread_suggestions and not screening.high_risk_setup and not screening.zero_dte_setup:
        if signal.is_earnings_blackout:
            console.print("[dim red]⛔ Directional options blocked due to active earnings blackout window.[/dim red]")
        elif signal.bias == BiasDirection.NEUTRAL:
            console.print("[dim yellow]ℹ️ Neutral signal: No directional options contract recommendations generated.[/dim yellow]")
        else:
            console.print("[dim red]⚠️ No contracts passed liquidity and spread filters.[/dim red]")


def run_single_ticker(symbol: str, cfg: AppConfig, interval: str = "1d"):
    """Run full deep-dive analysis on a single ticker."""
    symbol = symbol.strip().upper()
    with console.status(f"[cyan]Analyzing {symbol} (earnings, momentum, recency sentiment, delta, high-risk)...[/cyan]"):
        quote = get_current_quote(symbol)
        if not quote["valid"]:
            console.print(f"[bold red]❌ Could not retrieve valid market data for ticker '{symbol}'.[/bold red]")
            return

        hist = get_price_history(symbol, period=cfg.history_period, interval=interval)
        if hist is None:
            console.print(f"[bold red]❌ Insufficient historical price data for '{symbol}'.[/bold red]")
            return

        earnings_info = get_earnings_info(
            symbol,
            blackout_days=cfg.earnings.blackout_days,
            warning_days=cfg.earnings.warning_days
        )

        momentum = analyze_momentum(hist, symbol, cfg.technicals)
        if momentum is None:
            console.print(f"[bold red]❌ Failed calculating momentum indicators for '{symbol}'.[/bold red]")
            return

        articles = get_company_news(symbol, limit=cfg.news_limit)
        sentiment = analyze_news_sentiment(articles, symbol)

        signal = generate_signal(
            momentum=momentum,
            sentiment=sentiment,
            earnings_info=earnings_info,
            weights=cfg.weights,
            earnings_cfg=cfg.earnings
        )

        calls_df, puts_df, _ = get_options_chains(
            symbol,
            min_dte=cfg.options_filter.min_dte,
            max_dte=cfg.options_filter.max_dte
        )

        screening = suggest_options(
            signal=signal,
            spot_price=quote["current_price"],
            calls_df=calls_df,
            puts_df=puts_df,
            filter_cfg=cfg.options_filter,
            risk_cfg=cfg.risk
        )

    display_ticker_analysis(quote, momentum, sentiment, signal, screening, cfg)


def run_chain_matrix(symbol: str, expiration: Optional[str] = None):
    """Retrieve and display the full options chain strike ladder with Greeks and analytics."""
    symbol = symbol.strip().upper()
    with console.status(f"[cyan]Loading options chain matrix for {symbol}...[/cyan]"):
        matrix_data = get_options_chain_matrix(symbol, expiration)

    if matrix_data.get("error") and not matrix_data.get("strikes"):
        console.print(f"[bold red]❌ Failed to retrieve options chain for {symbol}: {matrix_data.get('error')}[/bold red]")
        return

    spot = matrix_data.get("current_price", 0.0)
    chg = matrix_data.get("change", 0.0)
    chg_pct = matrix_data.get("change_pct", 0.0)
    color = "green" if chg >= 0 else "red"
    selected_exp = matrix_data.get("selected_expiration", "N/A")
    dte = matrix_data.get("dte", 0)
    analytics = matrix_data.get("analytics", {})

    # Analytics Header
    exp_move = analytics.get("expected_move", 0.0)
    exp_pct = analytics.get("expected_move_pct", 0.0)
    low_b = analytics.get("expected_lower", 0.0)
    high_b = analytics.get("expected_upper", 0.0)
    max_pain = analytics.get("max_pain", 0.0)
    pcr_vol = analytics.get("pcr_volume", 0.0)
    pcr_oi = analytics.get("pcr_oi", 0.0)
    sentiment = analytics.get("pcr_sentiment", "Neutral")
    tot_calls = analytics.get("total_call_volume", 0)
    tot_puts = analytics.get("total_put_volume", 0)

    overview_text = (
        f"[bold white]{matrix_data.get('name', symbol)} ({symbol})[/bold white] | Spot: [bold {color}]${spot:,.2f} ({chg:+.2f} / {chg_pct:+.2f}%)[/bold {color}] | "
        f"Exp: [bold cyan]{selected_exp}[/bold cyan] ({dte} DTE)\n"
        f"• [bold]Expected Move:[/bold] [bold cyan]±${exp_move:.2f} (±{exp_pct:.1f}%)[/bold cyan] → 1σ Range: [bold]${low_b:.2f} – ${high_b:.2f}[/bold]\n"
        f"• [bold]Max Pain Strike:[/bold] [bold yellow]${max_pain:.2f}[/bold yellow] (Buyer payout minimizing pin price)\n"
        f"• [bold]Put/Call Ratio:[/bold] Vol [bold]{pcr_vol:.2f}[/bold] | OI [bold]{pcr_oi:.2f}[/bold] ({sentiment}) | "
        f"Flow: Calls {tot_calls:,} vs Puts {tot_puts:,}"
    )
    console.print(Panel(overview_text, title=f"⛓️ Options Chain Matrix & Analytics: {symbol}", border_style="cyan"))

    strikes = matrix_data.get("strikes", [])
    if not strikes:
        console.print("[dim red]No strikes available for this expiration.[/dim red]")
        return

    table = Table(
        title=f"Strike Ladder & Black-Scholes Greeks ({selected_exp} | {dte}d)",
        show_header=True,
        header_style="bold magenta"
    )
    table.add_column("C Delta", justify="right", style="bold green")
    table.add_column("C Bid / Ask", justify="right")
    table.add_column("C Vol / OI", justify="right")
    table.add_column("C IV%", justify="right")
    table.add_column("STRIKE", justify="center", style="bold white")
    table.add_column("P IV%", justify="right")
    table.add_column("P Vol / OI", justify="right")
    table.add_column("P Bid / Ask", justify="right")
    table.add_column("P Delta", justify="right", style="bold red")

    # Center around ATM strike: show strikes within +/- 12 strikes of ATM
    atm_idx = min(range(len(strikes)), key=lambda i: abs(strikes[i]["strike"] - spot))
    start_i = max(0, atm_idx - 12)
    end_i = min(len(strikes), atm_idx + 13)
    visible_strikes = strikes[start_i:end_i]

    for row in visible_strikes:
        k = row["strike"]
        is_atm = row.get("is_atm", False)
        is_mp = (abs(k - max_pain) < 0.01)

        strike_label = f"${k:.2f}"
        if is_atm:
            strike_label = f"[bold yellow]👉 ${k:.2f} ATM[/bold yellow]"
        elif is_mp:
            strike_label = f"[bold magenta]★ ${k:.2f} MP[/bold magenta]"

        c = row.get("call")
        p = row.get("put")

        c_delta = f"{c['delta']:+.2f}" if c and c.get("delta") is not None else "-"
        c_quote = f"${c['bid']:.2f}/${c['ask']:.2f}" if c else "-"
        c_flow = f"{c['volume']:,}/{c['open_interest']:,}" if c else "-"
        c_iv = f"{c['iv']:.1f}%" if c and c.get("iv") else "-"

        p_delta = f"{p['delta']:+.2f}" if p and p.get("delta") is not None else "-"
        p_quote = f"${p['bid']:.2f}/${p['ask']:.2f}" if p else "-"
        p_flow = f"{p['volume']:,}/{p['open_interest']:,}" if p else "-"
        p_iv = f"{p['iv']:.1f}%" if p and p.get("iv") else "-"

        table.add_row(
            c_delta, c_quote, c_flow, c_iv,
            strike_label,
            p_iv, p_flow, p_quote, p_delta
        )

    console.print(table)

    # Expirations list hint
    avail = matrix_data.get("available_expirations", [])
    exp_summary = ", ".join([f"{e['expiration']} ({e['dte']}d)" for e in avail[:8]])
    console.print(f"[dim]Available Expirations: {exp_summary} ...[/dim]\n")


def run_watchlist_scan(symbols: List[str], cfg: AppConfig, high_confidence_only: bool = False):
    """Scan multiple tickers and output an executive summary comparison table."""
    console.print(f"\n[bold cyan]🔍 Scanning Watchlist ({len(symbols)} tickers) | High/Med/Low Tiers...[/bold cyan]\n")

    summary_table = Table(
        title="📋 Watchlist Signal Scanner (Disciplined Filters)",
        show_header=True,
        header_style="bold blue"
    )
    summary_table.add_column("Symbol", style="bold cyan")
    summary_table.add_column("Price", justify="right")
    summary_table.add_column("Chg %", justify="right")
    summary_table.add_column("Momentum", justify="center")
    summary_table.add_column("Vol Conf", justify="center")
    summary_table.add_column("Signal", justify="center")
    summary_table.add_column("Tier", justify="center")
    summary_table.add_column("Earnings", justify="center")
    summary_table.add_column("Top Option Suggestion", style="italic")

    for sym in symbols:
        sym = sym.strip().upper()
        try:
            quote = get_current_quote(sym)
            if not quote["valid"]:
                continue

            hist = get_price_history(sym, period=cfg.history_period)
            if hist is None:
                continue

            earnings_info = get_earnings_info(
                sym,
                blackout_days=cfg.earnings.blackout_days,
                warning_days=cfg.earnings.warning_days
            )

            momentum = analyze_momentum(hist, sym, cfg.technicals)
            if momentum is None:
                continue

            articles = get_company_news(sym, limit=5)
            sentiment = analyze_news_sentiment(articles, sym)

            signal = generate_signal(
                momentum=momentum,
                sentiment=sentiment,
                earnings_info=earnings_info,
                weights=cfg.weights,
                earnings_cfg=cfg.earnings
            )

            if high_confidence_only and signal.confidence_tier != ConfidenceTier.HIGH:
                continue

            top_rec = "None"
            if signal.bias != BiasDirection.NEUTRAL and not signal.is_earnings_blackout:
                calls_df, puts_df, _ = get_options_chains(
                    sym,
                    min_dte=cfg.options_filter.min_dte,
                    max_dte=cfg.options_filter.max_dte
                )
                screening = suggest_options(
                    signal=signal,
                    spot_price=quote["current_price"],
                    calls_df=calls_df,
                    puts_df=puts_df,
                    filter_cfg=cfg.options_filter,
                    risk_cfg=cfg.risk
                )
                if screening.single_leg_suggestions:
                    r = screening.single_leg_suggestions[0]
                    top_rec = f"{r.option_type} ${r.strike:.0f} ({r.delta:+.2f} Delta) exp {r.expiration} (${r.ask:.2f})"

            # Styling
            chg_c = "green" if quote["change_percent"] >= 0 else "red"
            sig_c = "green" if signal.bias == BiasDirection.BULLISH else ("red" if signal.bias == BiasDirection.BEARISH else "yellow")
            tier_c = "bold green" if signal.confidence_tier == ConfidenceTier.HIGH else ("yellow" if signal.confidence_tier == ConfidenceTier.MEDIUM else "dim")

            e_status = "[dim]OK[/]"
            if signal.is_earnings_blackout:
                e_status = f"[bold red]⛔ {earnings_info.get('days_to_earnings')}d[/]"
            elif earnings_info.get("is_warning"):
                e_status = f"[yellow]⚠️ {earnings_info.get('days_to_earnings')}d[/]"

            vol_c = "[green]YES[/]" if momentum.volume_confirmed else "[yellow]NO[/]"

            summary_table.add_row(
                sym,
                f"${quote['current_price']:.2f}",
                f"[{chg_c}]{quote['change_percent']:+.2f}%[/{chg_c}]",
                f"{momentum.momentum_score:+.2f}",
                vol_c,
                f"[bold {sig_c}]{signal.bias.value}[/bold {sig_c}]",
                f"[{tier_c}]{signal.confidence_tier.value}[/{tier_c}]",
                e_status,
                top_rec
            )
        except Exception as exc:
            console.print(f"[dim red]Error analyzing {sym}: {exc}[/dim red]")

    console.print(summary_table)


def run_high_risk_scan(symbols: List[str], cfg: AppConfig):
    """Scan high-risk speculative tickers and display OTM Moonshot & Lotto Spread setups."""
    console.print(f"\n[bold red]⚡ Scanning High-Risk & Speculative Universe ({len(symbols)} tickers)...[/bold red]")
    console.print("[dim]Targeting 0.15–0.28 Delta OTM Moonshots & Asymmetric Lotto Spreads (Uncapped Sizing Budget)[/dim]\n")

    table = Table(
        title="⚡ High-Risk Speculative Setups (OTM Moonshots & Lotto Spreads)",
        show_header=True,
        header_style="bold red"
    )
    table.add_column("Symbol", style="bold cyan")
    table.add_column("Price", justify="right")
    table.add_column("Bias / Score", justify="center")
    table.add_column("Moonshot Strike / DTE", justify="center")
    table.add_column("Delta", justify="right")
    table.add_column("Ask / Sizing", justify="right")
    table.add_column("Lotto Spread / Net Debit", justify="center")
    table.add_column("R:R Ratio", justify="right", style="bold green")

    for sym in symbols:
        sym = sym.strip().upper()
        try:
            quote = get_current_quote(sym)
            if not quote["valid"]:
                continue

            hist = get_price_history(sym, period=cfg.history_period)
            if hist is None:
                continue

            momentum = analyze_momentum(hist, sym, cfg.technicals)
            if momentum is None:
                continue

            articles = get_company_news(sym, limit=5)
            sentiment = analyze_news_sentiment(articles, sym)

            earnings_info = get_earnings_info(sym, blackout_days=cfg.earnings.blackout_days)

            signal = generate_signal(
                momentum=momentum,
                sentiment=sentiment,
                earnings_info=earnings_info,
                weights=cfg.weights,
                earnings_cfg=cfg.earnings
            )

            if signal.bias == BiasDirection.NEUTRAL:
                continue

            calls_df, puts_df, _ = get_options_chains(
                sym,
                min_dte=HIGH_RISK_FILTER_CONFIG.min_dte,
                max_dte=HIGH_RISK_FILTER_CONFIG.max_dte
            )

            screening = suggest_options(
                signal=signal,
                spot_price=quote["current_price"],
                calls_df=calls_df,
                puts_df=puts_df,
                filter_cfg=cfg.options_filter,
                risk_cfg=cfg.risk
            )

            hrs = screening.high_risk_setup
            if not hrs:
                continue

            ms_str = f"{hrs.option_type} ${hrs.strike:.1f} ({hrs.dte}d)"
            delta_str = f"{hrs.delta:+.2f} Delta"
            ask_str = f"${hrs.ask:.2f} ({hrs.suggested_contracts}x)"

            spd_str = "None"
            rr_str = "-"
            if hrs.lotto_spread:
                ls = hrs.lotto_spread
                spd_str = f"${ls.long_strike:.0f}/${ls.short_strike:.0f} (${ls.net_debit:.2f})"
                rr_str = f"{ls.risk_reward_ratio:.1f}:1"

            bias_c = "green" if signal.bias == BiasDirection.BULLISH else "red"

            table.add_row(
                sym,
                f"${quote['current_price']:.2f}",
                f"[{bias_c}]{signal.bias.value} ({signal.combined_score:+.2f})[/{bias_c}]",
                ms_str,
                delta_str,
                ask_str,
                spd_str,
                rr_str
            )
        except Exception as exc:
            console.print(f"[dim red]Error analyzing high-risk setup for {sym}: {exc}[/dim red]")

    console.print(table)




def run_zero_dte_scan(symbols: List[str], cfg: AppConfig):
    """Scan high-velocity 0DTE universe (SPY, QQQ, NVDA, TSLA, etc.) for same-day scalps."""
    console.print(f"\n[bold yellow]⚡ Scanning 0DTE High-Velocity Universe ({len(symbols)} tickers)...[/bold yellow]")
    console.print("[dim]Analyzing ATM Momentum Scalps (~0.50Δ), OTM Gamma Moonshots (~0.20Δ), and Intraday Theta Decay/hr[/dim]\n")

    table = Table(
        title="⚡ 0DTE High-Velocity Options Lab (Front Cycle / Intraday Scalps)",
        show_header=True,
        header_style="bold yellow"
    )
    table.add_column("Symbol", style="bold cyan")
    table.add_column("Price", justify="right")
    table.add_column("Bias / Score", justify="center")
    table.add_column("ATM Scalp (~0.50Δ)", justify="center")
    table.add_column("Ask / Sizing", justify="right")
    table.add_column("Theta Burn/hr", justify="right", style="bold red")
    table.add_column("OTM Moonshot (~0.20Δ)", justify="center")
    table.add_column("Leverage", justify="right", style="bold green")
    table.add_column("0DTE Spread R:R", justify="center")

    for sym in symbols:
        sym = sym.strip().upper()
        try:
            quote = get_current_quote(sym)
            if not quote["valid"]:
                continue

            hist = get_price_history(sym, period=cfg.history_period)
            if hist is None:
                continue

            momentum = analyze_momentum(hist, sym, cfg.technicals)
            if momentum is None:
                continue

            articles = get_company_news(sym, limit=5)
            sentiment = analyze_news_sentiment(articles, sym)

            earnings_info = get_earnings_info(sym, blackout_days=cfg.earnings.blackout_days)

            signal = generate_signal(
                momentum=momentum,
                sentiment=sentiment,
                earnings_info=earnings_info,
                weights=cfg.weights,
                earnings_cfg=cfg.earnings
            )

            calls_df, puts_df, _ = get_options_chains(
                sym,
                min_dte=0,
                max_dte=5
            )

            screening = suggest_options(
                signal=signal,
                spot_price=quote["current_price"],
                calls_df=calls_df,
                puts_df=puts_df,
                filter_cfg=cfg.options_filter,
                risk_cfg=cfg.risk
            )

            zds = screening.zero_dte_setup
            if not zds:
                continue

            scalp_str = f"{zds.scalp_type} ${zds.scalp_strike:.1f} ({zds.scalp_delta:+.2f}Δ)"
            ask_str = f"${zds.scalp_ask:.2f} ({zds.scalp_suggested_contracts}x)"
            burn_str = f"-${abs(zds.scalp_theta_per_hour * 100):.1f}/hr"
            lotto_str = f"${zds.lotto_strike:.1f} ({zds.lotto_ask:.2f})"
            lev_str = f"{zds.lotto_upside_leverage:.1f}x"
            spd_str = f"{zds.lotto_spread.risk_reward_ratio:.1f}:1" if zds.lotto_spread else "-"

            bias_c = "green" if signal.bias == BiasDirection.BULLISH else ("red" if signal.bias == BiasDirection.BEARISH else "yellow")

            table.add_row(
                sym,
                f"${quote['current_price']:.2f}",
                f"[{bias_c}]{signal.bias.value} ({signal.combined_score:+.2f})[/{bias_c}]",
                scalp_str,
                ask_str,
                burn_str,
                lotto_str,
                lev_str,
                spd_str
            )
        except Exception as exc:
            console.print(f"[dim red]Error analyzing 0DTE for {sym}: {exc}[/dim red]")

    console.print(table)


def list_categories():
    """Print all available categorized sector watchlists."""
    console.print("\n[bold cyan]📁 Available Sector Watchlists:[/bold cyan]\n")
    for cat_name, tickers in WATCHLIST_CATEGORIES.items():
        console.print(f" • [bold white]{cat_name}[/bold white]: [dim cyan]{', '.join(tickers)}[/dim cyan]")
    console.print(f"\n[bold yellow]Total Liquid Universe: {len(EXPANDED_WATCHLIST)} unique tickers[/bold yellow]")

    console.print("\n[bold yellow]🪙 Commodities & Natural Resources Categories:[/bold yellow]\n")
    for cat_name, tickers in COMMODITIES_CATEGORIES.items():
        console.print(f" • [bold white]{cat_name}[/bold white]: [dim yellow]{', '.join(tickers)}[/dim yellow]")
    console.print(f"[bold yellow]Total Commodities Universe: {len(COMMODITIES_UNIVERSE)} unique tickers[/bold yellow]\n")

    console.print("\n[bold red]⚡ High-Risk & Speculative Categories:[/bold red]\n")
    for cat_name, tickers in HIGH_RISK_CATEGORIES.items():
        console.print(f" • [bold white]{cat_name}[/bold white]: [dim red]{', '.join(tickers)}[/dim red]")
    console.print(f"[bold yellow]Total High-Risk Universe: {len(HIGH_RISK_UNIVERSE)} unique tickers[/bold yellow]\n")


def main():
    parser = argparse.ArgumentParser(
        description="US Stock Options Suggester (Disciplined Core, Commodities, High-Risk Setups, AI Ecosystem, Options Chain Matrix)"
    )
    parser.add_argument(
        "-t", "--ticker",
        type=str,
        help="Analyze a single ticker symbol (e.g. AAPL, NVDA, GLD, USO, FCX, MSTR, ASTS)"
    )
    parser.add_argument(
        "-i", "--interval",
        type=str,
        default="1d",
        choices=["1m", "5m", "15m", "30m", "1h", "1d", "1wk"],
        help="Candle bar timeframe interval for analysis (1m, 5m, 15m, 1h, 1d, 1wk, default: 1d)"
    )
    parser.add_argument(
        "--chain",
        action="store_true",
        help="Display full interactive options chain strike ladder with Greeks and analytics"
    )
    parser.add_argument(
        "--expiration",
        type=str,
        default=None,
        help="Target expiration date (YYYY-MM-DD) for options chain matrix (default: closest >= 7 DTE)"
    )
    parser.add_argument(
        "-s", "--scan",
        action="store_true",
        help="Scan the default watchlist"
    )
    parser.add_argument(
        "--commodities",
        action="store_true",
        help="Scan the Commodities & Natural Resources universe (GLD, SLV, GDX, USO, UNG, FCX, CCJ, DBA, etc.)"
    )
    parser.add_argument(
        "--high-risk",
        action="store_true",
        help="Scan the High-Risk & Speculative Universe with uncapped sizing (MSTR, COIN, ASTS, IONQ, MARA, etc.)"
    )
    parser.add_argument(
        "--zero-dte",
        action="store_true",
        help="Scan the 0DTE High-Velocity Universe (SPY, QQQ, IWM, NVDA, TSLA, AAPL, AMD) for same-day scalps"
    )
    parser.add_argument(
        "--ai-leaders",
        action="store_true",
        help="Scan the full 40+ ticker AI Stock Ecosystem"
    )
    parser.add_argument(
        "--neoclouds",
        action="store_true",
        help="Scan AI NeoClouds & GPU Compute stocks (NBIS, CORZ, APLD, IREN, WULF, HUT)"
    )
    parser.add_argument(
        "--opticals",
        action="store_true",
        help="Scan AI Optical Interconnect & Photonics stocks (COHR, LITE, AAOI, FN, CIEN, GLW, POET)"
    )
    parser.add_argument(
        "--memory",
        action="store_true",
        help="Scan AI Memory & Storage HBM stocks (MU, WDC, STX, LRCX, AMAT)"
    )
    parser.add_argument(
        "-c", "--category",
        type=str,
        help="Scan a specific sector category (e.g. 'Commodities', 'Precious Metals', 'Semiconductors', 'Opticals', 'High-Risk', 'All')"
    )
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List all predefined sector watchlists and supported tickers"
    )
    parser.add_argument(
        "-w", "--watchlist",
        type=str,
        help="Comma-separated list of symbols to scan (e.g. AAPL,MSFT,NVDA,GLD)"
    )
    parser.add_argument(
        "--equity",
        type=float,
        default=10000.0,
        help="Account equity in dollars for position sizing (default: 10000)"
    )
    parser.add_argument(
        "--risk-pct",
        type=float,
        default=1.0,
        help="Max risk percentage per trade (default: 1.0 percent)"
    )
    parser.add_argument(
        "--high-confidence-only",
        action="store_true",
        help="Only display HIGH confidence tier candidates during watchlist scan"
    )
    parser.add_argument(
        "--min-dte",
        type=int,
        default=14,
        help="Minimum Days to Expiration (default: 14)"
    )
    parser.add_argument(
        "--max-dte",
        type=int,
        default=45,
        help="Maximum Days to Expiration (default: 45)"
    )

    args = parser.parse_args()
    print_banner()

    if args.list_categories:
        list_categories()
        return

    cfg = AppConfig()
    cfg.options_filter.min_dte = args.min_dte
    cfg.options_filter.max_dte = args.max_dte
    cfg.risk.account_equity = args.equity
    cfg.risk.max_risk_pct = args.risk_pct / 100.0

    if args.chain:
        run_chain_matrix(args.ticker or "NVDA", args.expiration)
    elif args.ticker:
        run_single_ticker(args.ticker, cfg, interval=args.interval)
    elif args.commodities:
        console.print("[dim]Scanning [bold yellow]Commodities & Natural Resources Universe (25+ Tickers)[/bold yellow]...[/dim]")
        run_watchlist_scan(COMMODITIES_UNIVERSE, cfg, high_confidence_only=args.high_confidence_only)
    elif args.zero_dte:
        run_zero_dte_scan(ZERO_DTE_UNIVERSE, cfg)
    elif args.high_risk:
        run_high_risk_scan(HIGH_RISK_UNIVERSE, cfg)
    elif args.ai_leaders:
        console.print("[dim]Scanning [bold cyan]AI Stock Ecosystem (40+ Tickers)[/bold cyan]...[/dim]")
        run_watchlist_scan(AI_STOCKS_UNIVERSE, cfg, high_confidence_only=args.high_confidence_only)
    elif args.neoclouds:
        console.print("[dim]Scanning [bold cyan]AI NeoClouds & GPU Compute[/bold cyan]...[/dim]")
        run_watchlist_scan(AI_STOCKS_CATEGORIES["AI NeoClouds & GPU Compute"], cfg, high_confidence_only=args.high_confidence_only)
    elif args.opticals:
        console.print("[dim]Scanning [bold cyan]AI Optical Interconnect & Photonics[/bold cyan]...[/dim]")
        run_watchlist_scan(AI_STOCKS_CATEGORIES["AI Optical Interconnect & Photonics"], cfg, high_confidence_only=args.high_confidence_only)
    elif args.memory:
        console.print("[dim]Scanning [bold cyan]AI Memory & Storage (HBM)[/bold cyan]...[/dim]")
        run_watchlist_scan(AI_STOCKS_CATEGORIES["AI Memory & Storage (HBM)"], cfg, high_confidence_only=args.high_confidence_only)
    elif args.category:
        cat_query = args.category.strip().lower()
        matched_symbols = []
        if cat_query == "all":
            matched_symbols = EXPANDED_WATCHLIST
        elif "comm" in cat_query or "metal" in cat_query or "gold" in cat_query or "oil" in cat_query:
            for cat_name, tickers in COMMODITIES_CATEGORIES.items():
                if cat_query in cat_name.lower():
                    matched_symbols = tickers
                    console.print(f"[dim]Selected commodities category: [bold yellow]{cat_name}[/bold yellow][/dim]")
                    break
            if not matched_symbols:
                matched_symbols = COMMODITIES_UNIVERSE
                console.print("[dim]Selected full [bold yellow]Commodities Universe[/bold yellow][/dim]")
            run_watchlist_scan(matched_symbols, cfg, high_confidence_only=args.high_confidence_only)
            print_disclaimer()
            return
        elif "risk" in cat_query or "spec" in cat_query or "crypto" in cat_query:
            for cat_name, tickers in HIGH_RISK_CATEGORIES.items():
                if cat_query in cat_name.lower():
                    matched_symbols = tickers
                    console.print(f"[dim]Selected high-risk category: [bold red]{cat_name}[/bold red][/dim]")
                    break
            if not matched_symbols:
                matched_symbols = HIGH_RISK_UNIVERSE
                console.print("[dim]Selected full [bold red]High-Risk Universe[/bold red][/dim]")
            run_high_risk_scan(matched_symbols, cfg)
            print_disclaimer()
            return
        else:
            for cat_name, tickers in WATCHLIST_CATEGORIES.items():
                if cat_query in cat_name.lower():
                    matched_symbols = tickers
                    console.print(f"[dim]Selected sector category: [bold cyan]{cat_name}[/bold cyan][/dim]")
                    break
        if not matched_symbols:
            console.print(f"[bold red]Category '{args.category}' not found. Use --list-categories to see options.[/bold red]")
            return
        run_watchlist_scan(matched_symbols, cfg, high_confidence_only=args.high_confidence_only)
    elif args.scan or args.watchlist:
        if args.watchlist:
            symbols = [s.strip().upper() for s in args.watchlist.split(",") if s.strip()]
        else:
            symbols = cfg.default_watchlist
        run_watchlist_scan(symbols, cfg, high_confidence_only=args.high_confidence_only)
    else:
        console.print("[dim]No ticker specified. Defaulting to analyzing NVDA. Use --help or --list-categories.[/dim]\n")
        run_single_ticker("NVDA", cfg, interval=args.interval)

    print_disclaimer()


if __name__ == "__main__":
    main()
