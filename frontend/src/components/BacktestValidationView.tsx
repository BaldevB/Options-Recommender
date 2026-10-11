"use client";

import React, { useState, useEffect } from "react";
import {
  BarChart3,
  RefreshCw,
  TrendingUp,
  ShieldCheck,
  AlertTriangle,
  Layers,
  ArrowRight,
  Activity,
  CheckCircle2,
  DollarSign,
  Sliders,
  Scale,
  Calendar,
  Zap,
} from "lucide-react";

interface StrategyMetrics {
  strategy_name: string;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate_pct: number;
  gross_pnl: number;
  total_transaction_costs: number;
  net_pnl: number;
  profit_factor: number;
  expectancy_per_trade: number;
  max_drawdown_dollar: number;
  max_drawdown_pct: number;
  sharpe_ratio: number;
  avg_holding_days: number;
  regime_breakdown: Record<string, { trades: number; win_rate_pct: number; net_pnl: number }>;
}

interface TradeSnapshot {
  trade_id: string;
  symbol: string;
  strategy_name: string;
  entry_date: string;
  exit_date: string;
  market_regime: string;
  underlying_spot_entry: number;
  underlying_spot_exit: number;
  option_type: string;
  strike: number;
  dte_entry: number;
  dte_exit: number;
  implied_volatility: number;
  delta_entry: number;
  bid_entry: number;
  ask_entry: number;
  realized_entry_fill: number;
  realized_exit_fill: number;
  contracts: number;
  capital_invested: number;
  round_trip_friction: number;
  gross_pnl: number;
  net_pnl: number;
  pnl_pct: number;
  exit_reason: string;
  max_favorable_excursion_pct: number;
  max_adverse_excursion_pct: number;
  holding_days: number;
}

interface BacktestResult {
  validation_timestamp: string;
  symbol: string;
  period_start: string;
  period_end: string;
  total_regime_bars: number;
  selector_metrics: StrategyMetrics;
  baseline_atm_metrics: StrategyMetrics;
  baseline_fixed_delta_metrics: StrategyMetrics;
  net_outperformance_vs_atm: number;
  net_outperformance_vs_fixed_delta: number;
  rule_recommendation: string;
  trade_snapshots: TradeSnapshot[];
}

export default function BacktestValidationView({ defaultTicker = "NVDA" }: { defaultTicker?: string }) {
  const [ticker, setTicker] = useState<string>(defaultTicker);
  const [period, setPeriod] = useState<string>("1y");
  const [sampleStep, setSampleStep] = useState<number>(15);
  const [equity, setEquity] = useState<number>(10000);
  const [riskPct, setRiskPct] = useState<number>(1.0);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

  const fetchBacktestSummary = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/backtest/summary`);
      if (res.ok) {
        const data = await res.json();
        if (data && data.selector_metrics) {
          setResult(data);
        }
      }
    } catch (e) {
      console.warn("No cached backtest results available:", e);
    }
  };

  useEffect(() => {
    fetchBacktestSummary();
  }, []);

  const runBacktest = async () => {
    setLoading(true);
    setError(null);
    try {
      const url = `${API_BASE}/api/backtest/run?ticker=${encodeURIComponent(ticker.trim().toUpperCase())}&period=${period}&sample_step=${sampleStep}&equity=${equity}&risk_pct=${riskPct}`;
      const res = await fetch(url);
      if (!res.ok) {
        const errJson = await res.json();
        throw new Error(errJson.detail || "Failed to execute walk-forward backtest");
      }
      const data = await res.json();
      setResult(data);
    } catch (e: any) {
      setError(e.message || "An unexpected error occurred while running backtest.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Control Header & Parameters */}
      <div className="rounded-2xl border border-slate-800 bg-[#090e1a] p-5 shadow-2xl">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800/80 pb-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="rounded bg-indigo-500/20 px-2 py-0.5 text-[10px] font-black uppercase text-indigo-300 border border-indigo-500/40">
                🔬 Institutional Validation Engine
              </span>
              <span className="rounded bg-cyan-950/80 px-2 py-0.5 text-[10px] font-semibold text-cyan-400 border border-cyan-800/50">
                Walk-Forward Out-Of-Sample
              </span>
            </div>
            <h2 className="mt-1.5 text-xl font-black tracking-tight text-white flex items-center">
              Walk-Forward Rule Validation & Baseline Comparison
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Stress-test the Institutional Net EV selector against naive baselines (ATM 35 DTE & Fixed-Delta 0.40) strictly after full execution friction ($1.30 commissions + bid-ask spread + 2% slippage).
            </p>
          </div>

          <button
            type="button"
            onClick={runBacktest}
            disabled={loading}
            className="flex items-center justify-center space-x-2 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 px-5 py-2.5 text-xs font-black text-white hover:from-cyan-400 hover:to-indigo-500 active:scale-95 transition shadow-lg shadow-cyan-500/20 disabled:opacity-50"
          >
            {loading ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin text-white" />
                <span>Running Simulation...</span>
              </>
            ) : (
              <>
                <Zap className="h-4 w-4 text-amber-300" />
                <span>Run Walk-Forward Backtest</span>
              </>
            )}
          </button>
        </div>

        {/* Input Parameters */}
        <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 text-xs">
          <div>
            <label className="text-[11px] text-slate-400 block mb-1">Target Symbol</label>
            <input
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 font-bold text-white focus:outline-none focus:border-cyan-500 uppercase"
              placeholder="e.g. NVDA, SPY"
            />
          </div>

          <div>
            <label className="text-[11px] text-slate-400 block mb-1">History Period</label>
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 font-semibold text-white focus:outline-none focus:border-cyan-500"
            >
              <option value="6mo">6 Months</option>
              <option value="1y">1 Year (Recommended)</option>
              <option value="2y">2 Years</option>
            </select>
          </div>

          <div>
            <label className="text-[11px] text-slate-400 block mb-1">Sample Frequency</label>
            <select
              value={sampleStep}
              onChange={(e) => setSampleStep(parseInt(e.target.value))}
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 font-semibold text-white focus:outline-none focus:border-cyan-500"
            >
              <option value={10}>Every 10 Days</option>
              <option value={15}>Every 15 Days (Bi-weekly)</option>
              <option value={20}>Every 20 Days (Monthly)</option>
            </select>
          </div>

          <div>
            <label className="text-[11px] text-slate-400 block mb-1">Account Equity ($)</label>
            <input
              type="number"
              value={equity}
              onChange={(e) => setEquity(parseFloat(e.target.value) || 10000)}
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 font-bold text-white focus:outline-none focus:border-cyan-500 font-mono"
            />
          </div>

          <div>
            <label className="text-[11px] text-slate-400 block mb-1">Risk Budget (%)</label>
            <input
              type="number"
              step="0.5"
              value={riskPct}
              onChange={(e) => setRiskPct(parseFloat(e.target.value) || 1.0)}
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 font-bold text-white focus:outline-none focus:border-cyan-500 font-mono"
            />
          </div>
        </div>

        {error && (
          <div className="mt-3 rounded-lg bg-red-950/60 border border-red-800 p-3 text-xs text-red-300 flex items-center space-x-2">
            <AlertTriangle className="h-4 w-4 text-red-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Results View */}
      {result && (
        <div className="space-y-6">
          {/* Top Summary Banner */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="rounded-xl border border-slate-800 bg-[#090e1a] p-4 flex flex-col justify-between">
              <div>
                <span className="text-[10px] uppercase font-bold text-slate-400">Rule Recommendation</span>
                <div className="mt-1 flex items-center space-x-2">
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-xs font-black border ${
                      result.rule_recommendation === "Keep All Rules"
                        ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                        : "bg-amber-500/20 text-amber-300 border-amber-500/40"
                    }`}
                  >
                    {result.rule_recommendation}
                  </span>
                </div>
              </div>
              <p className="mt-2 text-[11px] text-slate-400">
                {result.rule_recommendation === "Keep All Rules"
                  ? "Net EV + Hard Affordability rules demonstrably improved out-of-sample risk-adjusted return."
                  : "Consider relaxing strict bounds for low-volatility regimes."}
              </p>
            </div>

            <div className="rounded-xl border border-slate-800 bg-[#090e1a] p-4">
              <span className="text-[10px] uppercase font-bold text-slate-400">Alpha vs ATM Baseline</span>
              <div className={`mt-1 text-xl font-black font-mono ${result.net_outperformance_vs_atm >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                {result.net_outperformance_vs_atm >= 0 ? "+" : ""}${result.net_outperformance_vs_atm.toFixed(2)}
              </div>
              <p className="mt-1 text-[11px] text-slate-400">
                Net gain over naive ATM 35-DTE holding after round-trip transaction costs.
              </p>
            </div>

            <div className="rounded-xl border border-slate-800 bg-[#090e1a] p-4">
              <span className="text-[10px] uppercase font-bold text-slate-400">Alpha vs Fixed-Delta Baseline</span>
              <div className={`mt-1 text-xl font-black font-mono ${result.net_outperformance_vs_fixed_delta >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                {result.net_outperformance_vs_fixed_delta >= 0 ? "+" : ""}${result.net_outperformance_vs_fixed_delta.toFixed(2)}
              </div>
              <p className="mt-1 text-[11px] text-slate-400">
                Net gain over unmanaged 0.40 Delta contract without 21-DTE defense.
              </p>
            </div>

            <div className="rounded-xl border border-slate-800 bg-[#090e1a] p-4">
              <span className="text-[10px] uppercase font-bold text-slate-400">Simulated Window</span>
              <div className="mt-1 text-sm font-bold text-white">
                {result.period_start} → {result.period_end}
              </div>
              <p className="mt-1 text-[11px] text-slate-400 font-mono">
                {result.total_regime_bars} trading bars analyzed for {result.symbol}.
              </p>
            </div>
          </div>

          {/* 3-Column Comparative Metrics Table */}
          <div className="rounded-2xl border border-slate-800 bg-[#090e1a] p-5 shadow-2xl">
            <h3 className="text-sm font-bold uppercase tracking-wider text-cyan-300 mb-4 flex items-center">
              <Scale className="h-4 w-4 mr-2 text-cyan-400" />
              Strategy Performance Comparison Net of Round-Trip Friction
            </h3>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-[11px] text-slate-400 uppercase tracking-wider">
                    <th className="py-2.5 px-3">Metric</th>
                    <th className="py-2.5 px-3 text-cyan-300 font-black bg-cyan-950/20">Institutional Net EV Selector</th>
                    <th className="py-2.5 px-3">Baseline 1: ATM 35 DTE</th>
                    <th className="py-2.5 px-3">Baseline 2: Fixed Delta 0.40</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  <tr>
                    <td className="py-2 px-3 text-slate-400 font-sans">Total Trades Filtered</td>
                    <td className="py-2 px-3 text-white font-bold bg-cyan-950/20">{result.selector_metrics.total_trades}</td>
                    <td className="py-2 px-3 text-slate-300">{result.baseline_atm_metrics.total_trades}</td>
                    <td className="py-2 px-3 text-slate-300">{result.baseline_fixed_delta_metrics.total_trades}</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 text-slate-400 font-sans">Win Rate %</td>
                    <td className="py-2 px-3 text-emerald-400 font-bold bg-cyan-950/20">{result.selector_metrics.win_rate_pct}%</td>
                    <td className="py-2 px-3 text-slate-300">{result.baseline_atm_metrics.win_rate_pct}%</td>
                    <td className="py-2 px-3 text-slate-300">{result.baseline_fixed_delta_metrics.win_rate_pct}%</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 text-slate-400 font-sans">Gross P&L ($)</td>
                    <td className="py-2 px-3 text-slate-200 bg-cyan-950/20">${result.selector_metrics.gross_pnl.toFixed(2)}</td>
                    <td className="py-2 px-3 text-slate-300">${result.baseline_atm_metrics.gross_pnl.toFixed(2)}</td>
                    <td className="py-2 px-3 text-slate-300">${result.baseline_fixed_delta_metrics.gross_pnl.toFixed(2)}</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 text-slate-400 font-sans">Total Friction Paid ($)</td>
                    <td className="py-2 px-3 text-rose-400 bg-cyan-950/20">-${result.selector_metrics.total_transaction_costs.toFixed(2)}</td>
                    <td className="py-2 px-3 text-rose-400">-${result.baseline_atm_metrics.total_transaction_costs.toFixed(2)}</td>
                    <td className="py-2 px-3 text-rose-400">-${result.baseline_fixed_delta_metrics.total_transaction_costs.toFixed(2)}</td>
                  </tr>
                  <tr className="bg-slate-900/40">
                    <td className="py-2.5 px-3 text-white font-bold font-sans">Realized Net P&L ($)</td>
                    <td className={`py-2.5 px-3 font-black text-sm bg-cyan-950/40 ${result.selector_metrics.net_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                      {result.selector_metrics.net_pnl >= 0 ? "+" : ""}${result.selector_metrics.net_pnl.toFixed(2)}
                    </td>
                    <td className={`py-2.5 px-3 font-bold ${result.baseline_atm_metrics.net_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                      {result.baseline_atm_metrics.net_pnl >= 0 ? "+" : ""}${result.baseline_atm_metrics.net_pnl.toFixed(2)}
                    </td>
                    <td className={`py-2.5 px-3 font-bold ${result.baseline_fixed_delta_metrics.net_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                      {result.baseline_fixed_delta_metrics.net_pnl >= 0 ? "+" : ""}${result.baseline_fixed_delta_metrics.net_pnl.toFixed(2)}
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 text-slate-400 font-sans">Profit Factor</td>
                    <td className="py-2 px-3 text-cyan-300 font-bold bg-cyan-950/20">{result.selector_metrics.profit_factor.toFixed(2)}</td>
                    <td className="py-2 px-3 text-slate-300">{result.baseline_atm_metrics.profit_factor.toFixed(2)}</td>
                    <td className="py-2 px-3 text-slate-300">{result.baseline_fixed_delta_metrics.profit_factor.toFixed(2)}</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 text-slate-400 font-sans">Net Expectancy per Trade</td>
                    <td className={`py-2 px-3 font-bold bg-cyan-950/20 ${result.selector_metrics.expectancy_per_trade >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                      ${result.selector_metrics.expectancy_per_trade.toFixed(2)}
                    </td>
                    <td className="py-2 px-3 text-slate-300">${result.baseline_atm_metrics.expectancy_per_trade.toFixed(2)}</td>
                    <td className="py-2 px-3 text-slate-300">${result.baseline_fixed_delta_metrics.expectancy_per_trade.toFixed(2)}</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 text-slate-400 font-sans">Max Drawdown (% of Capital)</td>
                    <td className="py-2 px-3 text-amber-400 font-bold bg-cyan-950/20">{result.selector_metrics.max_drawdown_pct}%</td>
                    <td className="py-2 px-3 text-slate-300">{result.baseline_atm_metrics.max_drawdown_pct}%</td>
                    <td className="py-2 px-3 text-slate-300">{result.baseline_fixed_delta_metrics.max_drawdown_pct}%</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 text-slate-400 font-sans">Sharpe Ratio (Annualized)</td>
                    <td className="py-2 px-3 text-cyan-300 font-bold bg-cyan-950/20">{result.selector_metrics.sharpe_ratio.toFixed(2)}</td>
                    <td className="py-2 px-3 text-slate-300">{result.baseline_atm_metrics.sharpe_ratio.toFixed(2)}</td>
                    <td className="py-2 px-3 text-slate-300">{result.baseline_fixed_delta_metrics.sharpe_ratio.toFixed(2)}</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 text-slate-400 font-sans">Avg Holding Duration</td>
                    <td className="py-2 px-3 text-slate-200 bg-cyan-950/20">{result.selector_metrics.avg_holding_days} days</td>
                    <td className="py-2 px-3 text-slate-300">{result.baseline_atm_metrics.avg_holding_days} days</td>
                    <td className="py-2 px-3 text-slate-300">{result.baseline_fixed_delta_metrics.avg_holding_days} days</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Market Regime Breakdown */}
          {result.selector_metrics.regime_breakdown && Object.keys(result.selector_metrics.regime_breakdown).length > 0 && (
            <div className="rounded-2xl border border-slate-800 bg-[#090e1a] p-5 shadow-2xl">
              <h3 className="text-sm font-bold uppercase tracking-wider text-cyan-300 mb-3 flex items-center">
                <Activity className="h-4 w-4 mr-2 text-cyan-400" />
                Performance Categorized By Macro Market Regime
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
                {Object.entries(result.selector_metrics.regime_breakdown).map(([rName, rData]) => (
                  <div key={rName} className="rounded-xl border border-slate-800/80 bg-[#0b1222] p-3.5">
                    <span className="text-[10px] font-bold uppercase text-slate-400 block">{rName}</span>
                    <div className="mt-2 flex items-baseline justify-between">
                      <span className="text-slate-300 text-[11px]">Win Rate:</span>
                      <span className="font-mono font-bold text-white">{rData.win_rate_pct}%</span>
                    </div>
                    <div className="mt-1 flex items-baseline justify-between">
                      <span className="text-slate-300 text-[11px]">Net P&L:</span>
                      <span className={`font-mono font-bold ${rData.net_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                        {rData.net_pnl >= 0 ? "+" : ""}${rData.net_pnl.toFixed(2)}
                      </span>
                    </div>
                    <div className="mt-1 flex items-baseline justify-between text-[10px] text-slate-400">
                      <span>Trades:</span>
                      <span>{rData.trades}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recent Walk-Forward Realized Trades Audit */}
          {result.trade_snapshots && result.trade_snapshots.length > 0 && (
            <div className="rounded-2xl border border-slate-800 bg-[#090e1a] p-5 shadow-2xl">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-bold uppercase tracking-wider text-cyan-300 flex items-center">
                  <BarChart3 className="h-4 w-4 mr-2 text-cyan-400" />
                  Realized Trade Snapshots Audit Log ({result.trade_snapshots.length} trades)
                </h3>
                <span className="text-[11px] text-slate-400">
                  Modeled fill proxy at ask + slippage, exit at bid - slippage
                </span>
              </div>

              <div className="overflow-x-auto max-h-96">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="sticky top-0 bg-[#0b1222] border-b border-slate-800 text-[10px] text-slate-400 uppercase">
                    <tr>
                      <th className="py-2 px-2.5">Date</th>
                      <th className="py-2 px-2.5">Strategy</th>
                      <th className="py-2 px-2.5">Regime</th>
                      <th className="py-2 px-2.5">Contract</th>
                      <th className="py-2 px-2.5">Entry Fill</th>
                      <th className="py-2 px-2.5">Exit Fill</th>
                      <th className="py-2 px-2.5">Exit Reason</th>
                      <th className="py-2 px-2.5 text-right">Net P&L</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/40 text-[11px]">
                    {result.trade_snapshots.slice(0, 30).map((t, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30 transition">
                        <td className="py-1.5 px-2.5 text-slate-400">{t.entry_date}</td>
                        <td className="py-1.5 px-2.5 text-cyan-300 font-sans">{t.strategy_name.replace("baseline_", "")}</td>
                        <td className="py-1.5 px-2.5 text-slate-300 font-sans">{t.market_regime}</td>
                        <td className="py-1.5 px-2.5 text-white font-bold">${t.strike} {t.option_type} ({t.dte_entry}d)</td>
                        <td className="py-1.5 px-2.5 text-slate-300">${t.realized_entry_fill.toFixed(2)}</td>
                        <td className="py-1.5 px-2.5 text-slate-300">${t.realized_exit_fill.toFixed(2)}</td>
                        <td className="py-1.5 px-2.5">
                          <span
                            className={`rounded px-1.5 py-0.5 text-[9px] font-sans font-bold ${
                              t.exit_reason.includes("TP")
                                ? "bg-emerald-500/20 text-emerald-300"
                                : t.exit_reason.includes("Stop")
                                ? "bg-rose-500/20 text-rose-300"
                                : "bg-amber-500/20 text-amber-300"
                            }`}
                          >
                            {t.exit_reason}
                          </span>
                        </td>
                        <td className={`py-1.5 px-2.5 text-right font-bold ${t.net_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          {t.net_pnl >= 0 ? "+" : ""}${t.net_pnl.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
