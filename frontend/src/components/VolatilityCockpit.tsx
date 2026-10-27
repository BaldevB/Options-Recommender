"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Activity,
  Gauge,
  TrendingUp,
  TrendingDown,
  Compass,
  Layers,
  ShieldAlert,
  ShieldCheck,
  Zap,
  Info,
  Calendar,
  RefreshCw,
  Sliders,
  ChevronRight,
  ArrowUpRight,
  ArrowDownRight,
  Target,
} from "lucide-react";

interface ExpectedMoveItem {
  id: string;
  label: string;
  days: number;
  expected_move: number;
  expected_move_pct: number;
  lower_cone: number;
  upper_cone: number;
}

interface TermStructureItem {
  expiration: string;
  dte: number;
  atm_iv_pct: number;
}

interface VolatilityCockpitData {
  symbol: string;
  name: string;
  current_price: number;
  change: number;
  change_pct: number;
  current_iv: number;
  current_hv_21d: number;
  current_hv_60d: number;
  iv_rank: number;
  iv_percentile: number;
  hv_benchmarked_iv_rank?: number;
  hv_benchmarked_iv_percentile?: number;
  metric_methodology?: string;
  methodology_disclaimer?: string;
  data_source?: string;
  retrieved_at_utc?: string;
  last_trade_time?: string;
  bid_ask_sizes?: string;
  iv_floor: number;
  iv_ceiling: number;
  hv_min_1y: number;
  hv_max_1y: number;
  vrp_ratio: number;
  vrp_desc: string;
  regime: "LOW_VOLATILITY" | "MODERATE_VOLATILITY" | "HIGH_VOLATILITY";
  regime_title: string;
  regime_badge: string;
  regime_color: "emerald" | "cyan" | "rose";
  playbook: string[];
  term_structure: TermStructureItem[];
  expected_moves: ExpectedMoveItem[];
}

interface VolatilityCockpitProps {
  ticker: string;
  onOpenChain?: (exp?: string) => void;
  onOpenZeroDte?: () => void;
}

export default function VolatilityCockpit({
  ticker,
  onOpenChain,
  onOpenZeroDte,
}: VolatilityCockpitProps) {
  const [data, setData] = useState<VolatilityCockpitData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedHorizon, setSelectedHorizon] = useState<string>("30d");

  const fetchCockpit = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/volatility-cockpit?ticker=${encodeURIComponent(ticker)}`);
      if (!res.ok) throw new Error(`Failed to load Volatility Cockpit for ${ticker}`);
      const json = await res.json();
      setData(json);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed loading volatility analytics");
    } finally {
      setLoading(false);
    }
  }, [ticker]);

  useEffect(() => {
    fetchCockpit();
  }, [fetchCockpit]);

  if (loading && !data) {
    return (
      <div className="flex h-72 w-full items-center justify-center rounded-2xl border border-slate-800 bg-[#090e1a] text-slate-400">
        <RefreshCw className="mr-2 h-5 w-5 animate-spin text-cyan-400" />
        Computing Volatility Surface, IV Rank & 1-Sigma Expected Move Cones for {ticker}...
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="rounded-xl border border-rose-500/30 bg-rose-950/20 p-5 text-xs text-rose-300">
        <div className="font-bold flex items-center space-x-2">
          <ShieldAlert className="h-4 w-4" />
          <span>Volatility Analytics Unavailable</span>
        </div>
        <p className="mt-1 text-slate-400">{error || "Could not retrieve options volatility data."}</p>
        <button
          onClick={fetchCockpit}
          className="mt-3 rounded bg-slate-800 px-3 py-1 font-semibold text-slate-200 hover:bg-slate-700"
        >
          Try Again
        </button>
      </div>
    );
  }

  const activeMove = data.expected_moves.find((m) => m.id === selectedHorizon) || data.expected_moves[2];

  // Visual gauge colors
  const rank = Math.min(100, Math.max(0, data.hv_benchmarked_iv_rank ?? data.iv_rank));
  const percentile = Math.min(100, Math.max(0, data.hv_benchmarked_iv_percentile ?? data.iv_percentile));

  const getGaugeColor = (val: number) => {
    if (val < 30) return "text-emerald-400 stroke-emerald-400";
    if (val > 65) return "text-rose-400 stroke-rose-400";
    return "text-cyan-400 stroke-cyan-400";
  };

  const getGaugeGradient = (val: number) => {
    if (val < 30) return "from-emerald-500/20 to-emerald-950/40 border-emerald-500/30";
    if (val > 65) return "from-rose-500/20 to-rose-950/40 border-rose-500/30";
    return "from-cyan-500/20 to-cyan-950/40 border-cyan-500/30";
  };

  return (
    <div className="space-y-6">
      {/* ---------------- 0. DATA QUALITY & TRANSPARENCY BAR ---------------- */}
      <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-slate-800 bg-[#070b14] px-4 py-2 text-[11px] text-slate-400">
        <div className="flex flex-wrap items-center gap-3">
          <span className="flex items-center space-x-1">
            <span className="h-2 w-2 rounded-full bg-emerald-400 inline-block" />
            <strong className="text-slate-300">Source:</strong>
            <span>{data.data_source || "yfinance (~15m delay)"}</span>
          </span>
          <span className="text-slate-700">|</span>
          <span>
            <strong className="text-slate-300">Retrieved (UTC):</strong> {data.retrieved_at_utc || "Recent"}
          </span>
          <span className="text-slate-700">|</span>
          <span>
            <strong className="text-slate-300">Bid/Ask Size:</strong> {data.bid_ask_sizes || "unavailable"}
          </span>
        </div>
        <div className="flex items-center space-x-1.5 text-amber-400/90 font-medium">
          <Info className="h-3.5 w-3.5 shrink-0" />
          <span>Realized Vol Benchmark (Historical IV Series Not Stored by Free Feeds)</span>
        </div>
      </div>

      {/* ---------------- 1. TOP HEADER & VOLATILITY REGIME ---------------- */}
      <div
        className={`rounded-2xl border bg-gradient-to-r p-6 shadow-2xl transition ${
          data.regime === "LOW_VOLATILITY"
            ? "border-emerald-500/30 from-[#0c1f1c] via-[#091524] to-[#070b14]"
            : data.regime === "HIGH_VOLATILITY"
            ? "border-rose-500/30 from-[#271015] via-[#1a0e1c] to-[#070b14]"
            : "border-cyan-500/30 from-[#0c192c] via-[#0b1322] to-[#070b14]"
        }`}
      >
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2.5">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-500/20 border border-cyan-500/40 text-cyan-300">
                <Activity className="h-4 w-4" />
              </span>
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Implied Volatility & Expected Move Cockpit
                </span>
                <h2 className="text-xl font-black text-white flex items-center space-x-2">
                  <span>{data.name}</span>
                  <span className="font-mono text-cyan-300">({data.symbol})</span>
                </h2>
              </div>
            </div>
            <p className="mt-1 text-xs text-slate-300 max-w-2xl leading-relaxed">
              Institutional surface comparing <strong>ATM Implied Volatility ({data.current_iv}%)</strong> against 
              realized <strong>21-day Historical Volatility ({data.current_hv_21d}%)</strong> to quantify 
              premium mispricing and statistical price distribution.
            </p>
          </div>

          <div className="flex flex-col items-end gap-1.5">
            <div className="flex items-center space-x-2">
              <span
                className={`rounded-full px-3 py-1 text-xs font-black uppercase tracking-wider border shadow-md ${
                  data.regime === "LOW_VOLATILITY"
                    ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40 shadow-emerald-950"
                    : data.regime === "HIGH_VOLATILITY"
                    ? "bg-rose-500/20 text-rose-300 border-rose-500/40 shadow-rose-950"
                    : "bg-cyan-500/20 text-cyan-300 border-cyan-500/40 shadow-cyan-950"
                }`}
              >
                {data.regime_badge}
              </span>
              <button
                onClick={fetchCockpit}
                disabled={loading}
                title="Refresh Volatility Data"
                className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-700 bg-slate-800/80 text-slate-300 hover:text-white transition"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-cyan-400" : ""}`} />
              </button>
            </div>
            <span className="text-[11px] text-slate-400">
              VRP: <strong className="text-white font-mono">{data.vrp_ratio}x</strong> ({data.vrp_desc})
            </span>
          </div>
        </div>
      </div>

      {/* ---------------- 2. THREE CORE GAUGES (IV RANK, IV PERCENTILE, VRP) ---------------- */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {/* Gauge 1: HV-Benchmarked IV Rank */}
        <div
          className={`flex flex-col justify-between rounded-xl border bg-gradient-to-b p-5 shadow-lg ${getGaugeGradient(
            rank
          )}`}
        >
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
                <Gauge className="h-4 w-4 text-cyan-400" />
                <span>HV-Benchmarked IV Rank (1Y)</span>
              </span>
              <span className={`text-xs font-black font-mono ${getGaugeColor(rank)}`}>
                {rank < 30 ? "CHEAP" : rank > 65 ? "EXPENSIVE" : "FAIR"}
              </span>
            </div>

            <div className="mt-4 flex items-baseline justify-between">
              <span className="text-3xl font-black font-mono text-white">
                {rank.toFixed(1)}%
              </span>
              <span className="text-xs text-slate-400 font-mono">
                ATM IV: <strong className="text-cyan-300">{data.current_iv}%</strong>
              </span>
            </div>

            {/* Linear Progress Bar */}
            <div className="mt-3">
              <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-900 border border-slate-800">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${
                    rank < 30 ? "bg-emerald-400" : rank > 65 ? "bg-rose-400" : "bg-cyan-400"
                  }`}
                  style={{ width: `${Math.max(5, rank)}%` }}
                />
              </div>
              <div className="mt-1.5 flex justify-between text-[10px] font-mono text-slate-500">
                <span>0% (Floor {data.iv_floor}%)</span>
                <span>50%</span>
                <span>100% (Ceiling {data.iv_ceiling}%)</span>
              </div>
            </div>
          </div>

          <p className="mt-4 text-[11px] text-slate-400 leading-relaxed border-t border-slate-800/80 pt-2.5">
            Scales current ATM IV against 1-year 21-day realized historical volatility extremes. (Realized Vol Benchmark: free feeds do not archive historical IV).
          </p>
        </div>

        {/* Gauge 2: IV vs Realized Vol Percentile */}
        <div className="flex flex-col justify-between rounded-xl border border-indigo-500/30 bg-gradient-to-b from-indigo-500/10 to-indigo-950/30 p-5 shadow-lg">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
                <Compass className="h-4 w-4 text-indigo-400" />
                <span>IV vs 1Y Realized Vol %ile</span>
              </span>
              <span className="text-xs font-black font-mono text-indigo-300">BENCHMARK</span>
            </div>

            <div className="mt-4 flex items-baseline justify-between">
              <span className="text-3xl font-black font-mono text-white">
                {percentile.toFixed(1)}%
              </span>
              <span className="text-xs text-slate-400 font-mono">
                21d HV: <strong className="text-indigo-300">{data.current_hv_21d}%</strong>
              </span>
            </div>

            {/* Linear Progress Bar */}
            <div className="mt-3">
              <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-900 border border-slate-800">
                <div
                  className="h-full rounded-full bg-indigo-500 transition-all duration-700"
                  style={{ width: `${Math.max(5, percentile)}%` }}
                />
              </div>
              <div className="mt-1.5 flex justify-between text-[10px] font-mono text-slate-500">
                <span>0% of Days</span>
                <span>50% Days</span>
                <span>100% of Days</span>
              </div>
            </div>
          </div>

          <p className="mt-4 text-[11px] text-slate-400 leading-relaxed border-t border-slate-800/80 pt-2.5">
            Percentage of trading days over past year where 21-day realized volatility was lower than today&apos;s implied pricing.
          </p>
        </div>

        {/* Gauge 3: Volatility Risk Premium (VRP) & HV Comparison */}
        <div className="flex flex-col justify-between rounded-xl border border-slate-800 bg-[#0b1220] p-5 shadow-lg">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
                <Zap className="h-4 w-4 text-amber-400" />
                <span>Volatility Risk Premium (VRP)</span>
              </span>
              <span
                className={`text-xs font-black font-mono ${
                  data.vrp_ratio > 1.05
                    ? "text-rose-400"
                    : data.vrp_ratio < 0.95
                    ? "text-emerald-400"
                    : "text-amber-400"
                }`}
              >
                {data.vrp_ratio > 1.05 ? "IV PREMIUM" : data.vrp_ratio < 0.95 ? "IV DISCOUNT" : "PARITY"}
              </span>
            </div>

            <div className="mt-4 flex items-baseline justify-between">
              <span className="text-3xl font-black font-mono text-white">
                {data.vrp_ratio.toFixed(2)}x
              </span>
              <span className="text-xs text-slate-400 font-mono">
                60d HV: <strong className="text-slate-200">{data.current_hv_60d}%</strong>
              </span>
            </div>

            <div className="mt-3 flex items-center justify-between rounded-lg bg-slate-900/80 p-2.5 text-xs border border-slate-800">
              <span className="text-slate-400">1-Yr Realized Envelope:</span>
              <span className="font-mono font-semibold text-slate-200">
                {data.hv_min_1y}% - {data.hv_max_1y}%
              </span>
            </div>
          </div>

          <p className="mt-4 text-[11px] text-slate-400 leading-relaxed border-t border-slate-800/80 pt-2.5">
            Ratio of implied pricing vs actual movement. Ratios &gt; 1.00 signify option buyers paying an uncertainty markup.
          </p>
        </div>
      </div>

      {/* ---------------- 3. MULTI-HORIZON 1-SIGMA EXPECTED MOVE CONE ---------------- */}
      <div className="rounded-2xl border border-slate-800 bg-[#0a1120] p-6 shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
          <div className="flex items-center space-x-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
              <Target className="h-4 w-4" />
            </span>
            <div>
              <h3 className="text-base font-bold text-white">
                1-Sigma Expected Move Cones & Price Distribution
              </h3>
              <p className="text-xs text-slate-400">
                Theoretical 68.2% probability bell-curve boundaries implied by the current volatility smile.
              </p>
            </div>
          </div>

          {/* Horizon Selector Buttons */}
          <div className="flex items-center space-x-1 rounded-lg border border-slate-800 bg-[#070d18] p-1 text-xs">
            {data.expected_moves.map((m) => (
              <button
                key={m.id}
                onClick={() => setSelectedHorizon(m.id)}
                className={`rounded-md px-3 py-1 font-bold transition ${
                  selectedHorizon === m.id
                    ? "bg-cyan-500 text-black shadow-md font-black"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>
        </div>

        {/* Selected Move Highlight Hero */}
        {activeMove && (
          <div className="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-4">
            {/* Cone Visual Card */}
            <div className="lg:col-span-2 flex flex-col justify-between rounded-xl border border-cyan-500/30 bg-gradient-to-r from-cyan-950/30 to-indigo-950/30 p-5">
              <div>
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>Selected Horizon: <strong>{activeMove.label}</strong> ({activeMove.days} Days)</span>
                  <span className="rounded bg-cyan-500/10 px-2 py-0.5 text-[11px] font-bold text-cyan-300 border border-cyan-500/20">
                    68.2% Confidence Cone
                  </span>
                </div>

                <div className="mt-4 flex items-baseline space-x-3">
                  <span className="text-3xl font-black font-mono text-cyan-300">
                    &plusmn;${activeMove.expected_move.toFixed(2)}
                  </span>
                  <span className="text-sm font-bold font-mono text-slate-200">
                    (&plusmn;{activeMove.expected_move_pct.toFixed(2)}%)
                  </span>
                </div>

                {/* Cone Range Visualization */}
                <div className="mt-5 space-y-2">
                  <div className="flex justify-between items-center text-xs font-mono">
                    <span className="text-rose-400 font-bold flex items-center">
                      <ArrowDownRight className="mr-1 h-3.5 w-3.5" />
                      Lower Cone: ${activeMove.lower_cone.toFixed(2)}
                    </span>
                    <span className="text-slate-400">Spot: ${data.current_price.toFixed(2)}</span>
                    <span className="text-emerald-400 font-bold flex items-center">
                      <ArrowUpRight className="mr-1 h-3.5 w-3.5" />
                      Upper Cone: ${activeMove.upper_cone.toFixed(2)}
                    </span>
                  </div>

                  {/* Range visual bar */}
                  <div className="relative h-4 w-full rounded-full bg-slate-900 border border-slate-800">
                    {/* Lower boundary marker */}
                    <div className="absolute top-0 bottom-0 left-[15%] right-[15%] rounded-full bg-gradient-to-r from-rose-500/30 via-cyan-500/40 to-emerald-500/30 border border-cyan-500/50" />
                    {/* Center Spot Marker */}
                    <div className="absolute top-0 bottom-0 left-1/2 w-1 -translate-x-1/2 bg-white rounded shadow-sm shadow-white" />
                  </div>
                </div>
              </div>

              <div className="mt-4 flex items-center justify-between text-[11px] text-slate-400 pt-3 border-t border-slate-800/80">
                <span>Calculated via: <code>Spot &times; IV &times; &radic;(T/365)</code></span>
                <button
                  onClick={() => onOpenChain && onOpenChain()}
                  className="text-cyan-400 hover:text-cyan-300 font-semibold flex items-center"
                >
                  Inspect Strike Ladder &rarr;
                </button>
              </div>
            </div>

            {/* Strategic Implications & Playbook */}
            <div className="lg:col-span-2 flex flex-col justify-between rounded-xl border border-slate-800 bg-[#090f1d] p-5">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
                  <ShieldCheck className="h-4 w-4 text-emerald-400" />
                  <span>Volatility Regime Action Playbook</span>
                </span>
                <h4 className="mt-2 text-sm font-bold text-white">
                  {data.regime_title}
                </h4>

                <ul className="mt-3 space-y-2 text-xs text-slate-300">
                  {data.playbook.map((rule, idx) => (
                    <li key={idx} className="flex items-start space-x-2">
                      <span className="text-cyan-400 font-bold mt-0.5">&bull;</span>
                      <span className="leading-relaxed">{rule}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="mt-4 flex flex-wrap gap-2 pt-3 border-t border-slate-800">
                {onOpenChain && (
                  <button
                    onClick={() => onOpenChain()}
                    className="flex items-center space-x-1.5 rounded-lg border border-cyan-500/30 bg-cyan-950/40 px-3 py-1.5 text-xs font-semibold text-cyan-300 hover:bg-cyan-900/40 hover:text-white transition"
                  >
                    <Layers className="h-3.5 w-3.5" />
                    <span>View Chain Matrix</span>
                  </button>
                )}
                {onOpenZeroDte && (
                  <button
                    onClick={onOpenZeroDte}
                    className="flex items-center space-x-1.5 rounded-lg border border-amber-500/30 bg-amber-950/30 px-3 py-1.5 text-xs font-semibold text-amber-300 hover:bg-amber-900/40 transition"
                  >
                    <Zap className="h-3.5 w-3.5" />
                    <span>Open 0DTE Flash Scalper</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Multi-Horizon Summary Table */}
        <div className="mt-6 overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-[11px] text-slate-400 uppercase">
                <th className="pb-2">Time Horizon</th>
                <th className="pb-2">Days Out</th>
                <th className="pb-2">Expected Move ($)</th>
                <th className="pb-2">Expected Move (%)</th>
                <th className="pb-2">Lower Cone (1-&sigma;)</th>
                <th className="pb-2">Upper Cone (1-&sigma;)</th>
                <th className="pb-2">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {data.expected_moves.map((em) => {
                const isSelected = em.id === selectedHorizon;
                return (
                  <tr
                    key={em.id}
                    className={`transition ${
                      isSelected ? "bg-cyan-950/30 text-white" : "hover:bg-slate-800/30 text-slate-300"
                    }`}
                  >
                    <td className="py-2.5 font-sans font-semibold text-white">{em.label}</td>
                    <td className="py-2.5 text-slate-400">{em.days}d</td>
                    <td className="py-2.5 font-bold text-cyan-300">&plusmn;${em.expected_move.toFixed(2)}</td>
                    <td className="py-2.5 text-slate-200">&plusmn;{em.expected_move_pct.toFixed(2)}%</td>
                    <td className="py-2.5 text-rose-400 font-semibold">${em.lower_cone.toFixed(2)}</td>
                    <td className="py-2.5 text-emerald-400 font-semibold">${em.upper_cone.toFixed(2)}</td>
                    <td className="py-2.5">
                      <button
                        onClick={() => setSelectedHorizon(em.id)}
                        className={`rounded px-2 py-0.5 text-[10px] font-sans font-bold transition ${
                          isSelected
                            ? "bg-cyan-500 text-black"
                            : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                        }`}
                      >
                        {isSelected ? "Active" : "Select"}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* ---------------- 4. IMPLIED VOLATILITY TERM STRUCTURE (EXPIRATION LADDER) ---------------- */}
      {data.term_structure && data.term_structure.length > 0 && (
        <div className="rounded-2xl border border-slate-800 bg-[#0a1120] p-6 shadow-xl">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div>
              <h3 className="text-base font-bold text-white flex items-center space-x-2">
                <span>Implied Volatility Term Structure</span>
                <span className="rounded bg-indigo-500/10 px-2 py-0.5 text-[11px] font-bold text-indigo-300 border border-indigo-500/20">
                  {data.term_structure.length} Expirations
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                ATM implied volatility across expiration cycles. Contango (upward curve) vs Backwardation (front inversion).
              </p>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            {data.term_structure.map((item, idx) => (
              <button
                key={item.expiration}
                onClick={() => onOpenChain && onOpenChain(item.expiration)}
                className="group flex flex-col justify-between rounded-xl border border-slate-800 bg-[#080e1a] p-3 text-left hover:border-cyan-500/50 hover:bg-slate-800/60 transition"
              >
                <div>
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span className="font-semibold text-slate-300 group-hover:text-cyan-300 transition">
                      {item.expiration}
                    </span>
                    <span className="font-mono text-cyan-400">{item.dte}d</span>
                  </div>
                  <div className="mt-2 text-lg font-black font-mono text-white">
                    {item.atm_iv_pct.toFixed(1)}%
                  </div>
                </div>

                <div className="mt-3 flex items-center justify-between text-[10px] text-slate-500 pt-2 border-t border-slate-800/80">
                  <span>Cycle #{idx + 1}</span>
                  <span className="text-cyan-400 font-semibold group-hover:underline">Open &rarr;</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
