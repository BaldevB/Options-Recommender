"use client";

import React, { useState, useEffect, useId } from "react";
import {
  TrendingUp,
  AlertTriangle,
  ShieldAlert,
  Target,
  RefreshCw,
  Info,
  Activity,
  Layers,
  Sparkles,
  BarChart3,
  Flame,
} from "lucide-react";

interface MonteCarloData {
  symbol: string;
  current_price: number;
  simulations: number;
  forecast_days: number;
  annualized_drift: number;
  annualized_volatility: number;
  daily_drift: number;
  daily_volatility: number;
  median_final_price: number;
  mean_final_price: number;
  expected_return_pct: number;
  prob_profit: number;
  prob_hit_tp1: number;
  prob_hit_stop_loss: number;
  win_rate_tp_before_sl: number;
  var_95_pct: number;
  var_95_dollar: number;
  var_99_pct: number;
  var_99_dollar: number;
  percentile_trajectories: {
    p5: number[];
    p10: number[];
    p25: number[];
    p50: number[];
    p75: number[];
    p90: number[];
    p95: number[];
  };
  days_labels: number[];
  tp1?: number;
  stop_loss?: number;
  distribution_bins?: Array<{
    bin_center: number;
    count: number;
    density_pct: number;
  }>;
}

interface StockMonteCarloProps {
  symbol: string;
  currentPrice: number;
  initialTp1?: number;
  initialStopLoss?: number;
}

export function StockMonteCarlo({
  symbol,
  currentPrice,
  initialTp1,
  initialStopLoss,
}: StockMonteCarloProps) {
  const gradientPrefix = useId();
  const [data, setData] = useState<MonteCarloData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Simulation controls
  const [days, setDays] = useState<number>(30);
  const [simulations, setSimulations] = useState<number>(2000);
  const [tp1Input, setTp1Input] = useState<string>(
    initialTp1 ? initialTp1.toFixed(2) : (currentPrice * 1.08).toFixed(2)
  );
  const [slInput, setSlInput] = useState<string>(
    initialStopLoss ? initialStopLoss.toFixed(2) : (currentPrice * 0.95).toFixed(2)
  );
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const fetchSimulation = async () => {
    setLoading(true);
    setError(null);
    try {
      const parsedTp1 = parseFloat(tp1Input);
      const parsedSl = parseFloat(slInput);

      let url = `/api/stocks/monte-carlo?symbol=${encodeURIComponent(
        symbol
      )}&simulations=${simulations}&days=${days}`;
      if (!isNaN(parsedTp1) && parsedTp1 > 0) url += `&tp1=${parsedTp1}`;
      if (!isNaN(parsedSl) && parsedSl > 0) url += `&stop_loss=${parsedSl}`;

      const res = await fetch(url);
      if (!res.ok) {
        throw new Error(`API returned status ${res.status}`);
      }
      const json = await res.json();
      setData(json);
    } catch (err: any) {
      setError(err?.message || "Failed to run Monte Carlo simulation");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSimulation();
  }, [symbol, days, simulations]);

  // Derived calculations for SVG Fan Chart
  const renderFanChart = () => {
    if (!data || !data.percentile_trajectories) return null;

    const traj = data.percentile_trajectories;
    const p5 = traj.p5 || [];
    const p10 = traj.p10 || [];
    const p25 = traj.p25 || [];
    const p50 = traj.p50 || [];
    const p75 = traj.p75 || [];
    const p90 = traj.p90 || [];
    const p95 = traj.p95 || [];

    const numPoints = p50.length;
    if (numPoints === 0) return null;

    // Determine min and max Y across all curves, plus TP1 and SL
    let allPrices = [...p5, ...p95];
    if (data.tp1) allPrices.push(data.tp1);
    if (data.stop_loss) allPrices.push(data.stop_loss);
    allPrices.push(data.current_price);

    const minPrice = Math.min(...allPrices) * 0.98;
    const maxPrice = Math.max(...allPrices) * 1.02;
    const priceRange = maxPrice - minPrice || 1;

    // SVG coordinates
    const width = 800;
    const height = 360;
    const padX = 55;
    const padY = 30;
    const chartW = width - padX * 2;
    const chartH = height - padY * 2;

    const getX = (idx: number) => padX + (idx / (numPoints - 1)) * chartW;
    const getY = (price: number) =>
      padY + chartH - ((price - minPrice) / priceRange) * chartH;

    // Build path strings
    const createArea = (upper: number[], lower: number[]) => {
      const topPts = upper.map((p, i) => `${getX(i)},${getY(p)}`).join(" L ");
      const btmPts = lower
        .map((p, i) => `${getX(i)},${getY(p)}`)
        .reverse()
        .join(" L ");
      return `M ${topPts} L ${btmPts} Z`;
    };

    const createLine = (pts: number[]) => {
      return pts.map((p, i) => `${i === 0 ? "M" : "L"} ${getX(i)},${getY(p)}`).join(" ");
    };

    const outerRibbon = createArea(p95, p5);
    const midRibbon = createArea(p90, p10);
    const innerRibbon = createArea(p75, p25);
    const medianLine = createLine(p50);

    const curY = getY(data.current_price);
    const tp1Y = data.tp1 ? getY(data.tp1) : null;
    const slY = data.stop_loss ? getY(data.stop_loss) : null;

    // Price ticks for grid
    const priceTicks = [
      minPrice,
      minPrice + priceRange * 0.25,
      minPrice + priceRange * 0.5,
      minPrice + priceRange * 0.75,
      maxPrice,
    ];

    const activeIndex = hoverIndex !== null ? hoverIndex : numPoints - 1;

    return (
      <div className="relative w-full overflow-hidden select-none">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto cursor-crosshair"
          onMouseMove={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            const relX = ((e.clientX - rect.left) / rect.width) * width;
            const idx = Math.round(((relX - padX) / chartW) * (numPoints - 1));
            if (idx >= 0 && idx < numPoints) {
              setHoverIndex(idx);
            }
          }}
          onMouseLeave={() => setHoverIndex(null)}
        >
          <defs>
            <linearGradient id={`${gradientPrefix}-outerCone`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.08" />
              <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.03" />
            </linearGradient>
            <linearGradient id={`${gradientPrefix}-midCone`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.14" />
              <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.06" />
            </linearGradient>
            <linearGradient id={`${gradientPrefix}-innerCone`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.12" />
            </linearGradient>
          </defs>

          {/* Grid lines and Price labels */}
          {priceTicks.map((p, idx) => {
            const y = getY(p);
            return (
              <g key={idx}>
                <line
                  x1={padX}
                  y1={y}
                  x2={width - padX}
                  y2={y}
                  stroke="#1e293b"
                  strokeDasharray="3 3"
                  strokeWidth="1"
                />
                <text
                  x={padX - 8}
                  y={y + 3}
                  textAnchor="end"
                  fontSize="10"
                  fill="#64748b"
                  fontFamily="monospace"
                >
                  ${p.toFixed(1)}
                </text>
              </g>
            );
          })}

          {/* Shaded Confidence Ribbons */}
          <path d={outerRibbon} fill={`url(#${gradientPrefix}-outerCone)`} />
          <path d={midRibbon} fill={`url(#${gradientPrefix}-midCone)`} />
          <path d={innerRibbon} fill={`url(#${gradientPrefix}-innerCone)`} />

          {/* Percentile Boundary Lines */}
          <path
            d={createLine(p95)}
            fill="none"
            stroke="#0891b2"
            strokeWidth="1"
            strokeDasharray="4 4"
            opacity="0.6"
          />
          <path
            d={createLine(p5)}
            fill="none"
            stroke="#0891b2"
            strokeWidth="1"
            strokeDasharray="4 4"
            opacity="0.6"
          />
          <path
            d={createLine(p75)}
            fill="none"
            stroke="#06b6d4"
            strokeWidth="1"
            strokeDasharray="2 2"
            opacity="0.8"
          />
          <path
            d={createLine(p25)}
            fill="none"
            stroke="#06b6d4"
            strokeWidth="1"
            strokeDasharray="2 2"
            opacity="0.8"
          />

          {/* Median P50 Trajectory */}
          <path
            d={medianLine}
            fill="none"
            stroke="#22d3ee"
            strokeWidth="2.5"
            className="filter drop-shadow-[0_0_8px_rgba(34,211,238,0.5)]"
          />

          {/* Current Price Base Line */}
          <line
            x1={padX}
            y1={curY}
            x2={width - padX}
            y2={curY}
            stroke="#94a3b8"
            strokeWidth="1.2"
            strokeDasharray="5 4"
            opacity="0.8"
          />
          <text
            x={padX + 6}
            y={curY - 4}
            fontSize="9"
            fill="#cbd5e1"
            fontFamily="monospace"
            fontWeight="bold"
          >
            START: ${data.current_price.toFixed(2)}
          </text>

          {/* Target Profit 1 Line */}
          {tp1Y !== null && data.tp1 && (
            <g>
              <line
                x1={padX}
                y1={tp1Y}
                x2={width - padX}
                y2={tp1Y}
                stroke="#10b981"
                strokeWidth="1.5"
                strokeDasharray="6 3"
              />
              <text
                x={width - padX - 4}
                y={tp1Y - 4}
                textAnchor="end"
                fontSize="10"
                fill="#10b981"
                fontFamily="monospace"
                fontWeight="bold"
              >
                TARGET TP1: ${data.tp1.toFixed(2)} (
                {(((data.tp1 - data.current_price) / data.current_price) * 100).toFixed(1)}%)
              </text>
            </g>
          )}

          {/* Stop Loss Line */}
          {slY !== null && data.stop_loss && (
            <g>
              <line
                x1={padX}
                y1={slY}
                x2={width - padX}
                y2={slY}
                stroke="#f43f5e"
                strokeWidth="1.5"
                strokeDasharray="6 3"
              />
              <text
                x={width - padX - 4}
                y={slY + 12}
                textAnchor="end"
                fontSize="10"
                fill="#f43f5e"
                fontFamily="monospace"
                fontWeight="bold"
              >
                STOP LOSS: ${data.stop_loss.toFixed(2)} (
                {(((data.stop_loss - data.current_price) / data.current_price) * 100).toFixed(1)}%)
              </text>
            </g>
          )}

          {/* Hover Tracker Vertical Line */}
          {activeIndex >= 0 && activeIndex < numPoints && (
            <g>
              <line
                x1={getX(activeIndex)}
                y1={padY}
                x2={getX(activeIndex)}
                y2={height - padY}
                stroke="#38bdf8"
                strokeWidth="1.5"
                strokeDasharray="2 2"
                opacity="0.9"
              />
              <circle
                cx={getX(activeIndex)}
                cy={getY(p50[activeIndex])}
                r="4.5"
                fill="#22d3ee"
                stroke="#082f49"
                strokeWidth="2"
              />
            </g>
          )}

          {/* Day Axis Ticks */}
          {[0, Math.floor(data.forecast_days * 0.25), Math.floor(data.forecast_days * 0.5), Math.floor(data.forecast_days * 0.75), data.forecast_days].map(
            (d, i) => {
              const x = padX + (d / data.forecast_days) * chartW;
              return (
                <text
                  key={i}
                  x={x}
                  y={height - padY + 16}
                  textAnchor="middle"
                  fontSize="10"
                  fill="#64748b"
                  fontFamily="monospace"
                >
                  Day {d}
                </text>
              );
            }
          )}
        </svg>

        {/* Dynamic Tooltip Bar */}
        <div className="flex flex-wrap items-center justify-between gap-2 px-3 py-2 bg-slate-950/80 border-t border-slate-800 text-[11px] font-mono">
          <div className="flex items-center gap-2">
            <span className="text-cyan-400 font-bold">
              Day {activeIndex} of {data.forecast_days}:
            </span>
            <span className="text-slate-300">
              Median (P50):{" "}
              <strong className="text-white">
                ${p50[activeIndex]?.toFixed(2)}
              </strong>{" "}
              ({(
                ((p50[activeIndex] - data.current_price) / data.current_price) *
                100
              ).toFixed(1)}%)
            </span>
          </div>

          <div className="flex items-center gap-3 text-slate-400">
            <span>
              P90: <span className="text-cyan-300 font-semibold">${p90[activeIndex]?.toFixed(2)}</span>
            </span>
            <span>
              P75: <span className="text-cyan-200 font-semibold">${p75[activeIndex]?.toFixed(2)}</span>
            </span>
            <span>
              P25: <span className="text-amber-200 font-semibold">${p25[activeIndex]?.toFixed(2)}</span>
            </span>
            <span>
              P10: <span className="text-rose-300 font-semibold">${p10[activeIndex]?.toFixed(2)}</span>
            </span>
          </div>
        </div>
      </div>
    );
  };

  // Render Histogram Distribution at Maturity
  const renderHistogram = () => {
    if (!data || !data.distribution_bins || data.distribution_bins.length === 0)
      return null;

    const maxDensity = Math.max(...data.distribution_bins.map((b) => b.density_pct), 0.01);

    return (
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-cyan-400" />
            <h4 className="text-xs font-bold text-slate-200 tracking-wider uppercase">
              Terminal Price Distribution (Day {data.forecast_days} Maturity)
            </h4>
          </div>
          <span className="text-[10px] text-slate-400 font-mono">
            {data.simulations.toLocaleString()} Vectorized Paths
          </span>
        </div>

        <div className="h-32 flex items-end gap-1.5 pt-4 pb-2 border-b border-slate-800">
          {data.distribution_bins.map((bin, idx) => {
            const heightPct = Math.max(4, (bin.density_pct / maxDensity) * 100);
            const isProfit = bin.bin_center >= data.current_price;
            const isAboveTp1 = data.tp1 && bin.bin_center >= data.tp1;
            const isBelowSl = data.stop_loss && bin.bin_center <= data.stop_loss;

            let barColor = "bg-cyan-500/40 hover:bg-cyan-400";
            if (isAboveTp1) barColor = "bg-emerald-500/60 hover:bg-emerald-400";
            else if (isBelowSl) barColor = "bg-rose-500/60 hover:bg-rose-400";
            else if (isProfit) barColor = "bg-cyan-500/60 hover:bg-cyan-400";
            else barColor = "bg-amber-500/50 hover:bg-amber-400";

            return (
              <div
                key={idx}
                className="flex-1 flex flex-col items-center group relative h-full justify-end"
              >
                {/* Tooltip on bar hover */}
                <div className="absolute -top-12 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-950 border border-slate-700 rounded px-2 py-1 text-[10px] font-mono pointer-events-none whitespace-nowrap z-20 shadow-xl">
                  <div className="text-cyan-300 font-bold">${bin.bin_center.toFixed(2)}</div>
                  <div className="text-slate-300">
                    {bin.density_pct.toFixed(1)}% ({bin.count} paths)
                  </div>
                </div>

                <div
                  style={{ height: `${heightPct}%` }}
                  className={`w-full rounded-t transition-all ${barColor}`}
                />
              </div>
            );
          })}
        </div>

        <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono px-1">
          <span>Min: ${data.distribution_bins[0]?.bin_center.toFixed(1)}</span>
          <span className="text-slate-300">
            Current: ${data.current_price.toFixed(2)}
          </span>
          <span>
            Max: ${data.distribution_bins[data.distribution_bins.length - 1]?.bin_center.toFixed(1)}
          </span>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-4 text-slate-100">
      {/* Simulation Controls & Parameters Bar */}
      <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <h3 className="text-xs uppercase font-bold text-cyan-300 tracking-wider">
              Monte Carlo Quantitative Engine (GBM with Drift)
            </h3>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={fetchSimulation}
              disabled={loading}
              className="px-3 py-1.5 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/40 text-cyan-300 text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              Re-Calculate Simulation
            </button>
          </div>
        </div>

        {/* Inputs Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs pt-1">
          <div>
            <label className="block text-[10px] font-mono text-slate-400 uppercase mb-1">
              Forecast Horizon (Days)
            </label>
            <div className="flex rounded-lg overflow-hidden border border-slate-700 bg-slate-950">
              {[15, 30, 60, 90].map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => setDays(d)}
                  className={`flex-1 py-1.5 text-center text-xs font-mono transition-colors ${
                    days === d
                      ? "bg-cyan-500 text-slate-950 font-bold"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {d}d
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-[10px] font-mono text-slate-400 uppercase mb-1">
              Sample Paths (Vectorized)
            </label>
            <select
              value={simulations}
              onChange={(e) => setSimulations(Number(e.target.value))}
              className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option value={1000}>1,000 Paths (Fast)</option>
              <option value={2000}>2,000 Paths (Standard)</option>
              <option value={5000}>5,000 Paths (Institutional)</option>
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-mono text-emerald-400 uppercase mb-1">
              Target Price (TP1 $)
            </label>
            <input
              type="number"
              step="0.01"
              value={tp1Input}
              onChange={(e) => setTp1Input(e.target.value)}
              className="w-full rounded-lg bg-slate-950 border border-emerald-900/60 px-3 py-1.5 text-xs font-mono text-emerald-300 focus:outline-none focus:border-emerald-500"
              placeholder="e.g. 150.00"
            />
          </div>

          <div>
            <label className="block text-[10px] font-mono text-rose-400 uppercase mb-1">
              Stop Loss Level ($)
            </label>
            <input
              type="number"
              step="0.01"
              value={slInput}
              onChange={(e) => setSlInput(e.target.value)}
              className="w-full rounded-lg bg-slate-950 border border-rose-900/60 px-3 py-1.5 text-xs font-mono text-rose-300 focus:outline-none focus:border-rose-500"
              placeholder="e.g. 135.00"
            />
          </div>
        </div>
      </div>

      {loading && !data && (
        <div className="py-16 text-center text-cyan-400 font-mono text-xs flex flex-col items-center justify-center gap-3">
          <RefreshCw className="w-6 h-6 animate-spin text-cyan-400" />
          <span>Simulating {simulations.toLocaleString()} Geometric Brownian Motion trajectories for {symbol}...</span>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/30 border border-rose-800 text-rose-300 text-xs flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {data && (
        <>
          {/* Key Quantitative Probability Metric Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            {/* First Touch Win Rate */}
            <div className="p-3.5 rounded-xl bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 shadow-md">
              <div className="flex items-center justify-between text-[10px] uppercase font-mono text-slate-400 mb-1">
                <span>First-Touch Win Rate</span>
                <Flame
                  className={`w-3.5 h-3.5 ${
                    data.win_rate_tp_before_sl >= 60
                      ? "text-emerald-400"
                      : data.win_rate_tp_before_sl >= 50
                      ? "text-cyan-400"
                      : "text-amber-400"
                  }`}
                />
              </div>
              <div
                className={`text-xl font-mono font-bold ${
                  data.win_rate_tp_before_sl >= 60
                    ? "text-emerald-400"
                    : data.win_rate_tp_before_sl >= 50
                    ? "text-cyan-300"
                    : "text-amber-300"
                }`}
              >
                {data.win_rate_tp_before_sl.toFixed(1)}%
              </div>
              <div className="text-[10px] text-slate-500 font-mono mt-1">
                Prob(Hits TP1 before Stop Loss)
              </div>
            </div>

            {/* Target Touch Rate */}
            <div className="p-3.5 rounded-xl bg-gradient-to-br from-slate-900 to-slate-950 border border-emerald-950/60 shadow-md">
              <div className="flex items-center justify-between text-[10px] uppercase font-mono text-emerald-400 mb-1">
                <span>Prob Touch Target 1</span>
                <Target className="w-3.5 h-3.5 text-emerald-400" />
              </div>
              <div className="text-xl font-mono font-bold text-emerald-300">
                {data.prob_hit_tp1.toFixed(1)}%
              </div>
              <div className="text-[10px] text-emerald-600 font-mono mt-1">
                Target: ${data.tp1?.toFixed(2) || "N/A"}
              </div>
            </div>

            {/* Invalidation / Stop Loss Risk */}
            <div className="p-3.5 rounded-xl bg-gradient-to-br from-slate-900 to-slate-950 border border-rose-950/60 shadow-md">
              <div className="flex items-center justify-between text-[10px] uppercase font-mono text-rose-400 mb-1">
                <span>Stop Loss Touch Risk</span>
                <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
              </div>
              <div className="text-xl font-mono font-bold text-rose-400">
                {data.prob_hit_stop_loss.toFixed(1)}%
              </div>
              <div className="text-[10px] text-rose-600 font-mono mt-1">
                Stop Level: ${data.stop_loss?.toFixed(2) || "N/A"}
              </div>
            </div>

            {/* 95% Value at Risk (VaR) */}
            <div className="p-3.5 rounded-xl bg-gradient-to-br from-slate-900 to-slate-950 border border-amber-950/60 shadow-md">
              <div className="flex items-center justify-between text-[10px] uppercase font-mono text-amber-400 mb-1">
                <span>95% VaR (Max Drawdown)</span>
                <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
              </div>
              <div className="text-xl font-mono font-bold text-amber-300">
                -${data.var_95_dollar.toFixed(2)}{" "}
                <span className="text-xs text-amber-400/80 font-normal">
                  ({data.var_95_pct.toFixed(1)}%)
                </span>
              </div>
              <div className="text-[10px] text-amber-600 font-mono mt-1">
                99% VaR: -${data.var_99_dollar.toFixed(2)} ({data.var_99_pct.toFixed(1)}%)
              </div>
            </div>
          </div>

          {/* Calibrated Model Parameters Badge Strip */}
          <div className="flex flex-wrap items-center gap-3 px-3.5 py-2.5 rounded-lg bg-slate-950/60 border border-slate-800 text-[11px] font-mono text-slate-400">
            <span className="text-slate-300 font-bold flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-cyan-400" />
              Calibrated GBM Parameters:
            </span>
            <span>
              Ann. Volatility (&sigma;):{" "}
              <strong className="text-cyan-300">
                {(data.annualized_volatility * 100).toFixed(1)}%
              </strong>{" "}
              ({(data.daily_volatility * 100).toFixed(2)}%/day)
            </span>
            <span className="text-slate-700">|</span>
            <span>
              Ann. Drift (&mu;):{" "}
              <strong className="text-emerald-300">
                {(data.annualized_drift * 100).toFixed(1)}%
              </strong>
            </span>
            <span className="text-slate-700">|</span>
            <span>
              Expected Median:{" "}
              <strong className="text-slate-100">
                ${data.median_final_price.toFixed(2)}
              </strong>{" "}
              ({data.expected_return_pct >= 0 ? "+" : ""}
              {data.expected_return_pct.toFixed(1)}%)
            </span>
          </div>

          {/* SVG Fan Chart Visualizer */}
          <div className="rounded-xl border border-slate-800 bg-[#0a0f1d] overflow-hidden shadow-2xl">
            <div className="px-4 py-3 border-b border-slate-800/80 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-cyan-400" />
                <h4 className="text-xs font-bold text-slate-200 tracking-wider uppercase">
                  Probability Fan Chart &amp; Trajectory Cones
                </h4>
              </div>
              <div className="flex items-center gap-3 text-[10px] font-mono">
                <span className="flex items-center gap-1 text-cyan-400">
                  <span className="w-3 h-0.5 bg-cyan-400 inline-block"></span> Median (P50)
                </span>
                <span className="flex items-center gap-1 text-cyan-200">
                  <span className="w-2.5 h-2.5 bg-cyan-500/30 border border-cyan-400/40 inline-block rounded-sm"></span> 25% - 75% Cone
                </span>
                <span className="flex items-center gap-1 text-cyan-100">
                  <span className="w-2.5 h-2.5 bg-cyan-500/10 border border-cyan-400/20 inline-block rounded-sm"></span> 5% - 95% Cone
                </span>
              </div>
            </div>

            {renderFanChart()}
          </div>

          {/* Terminal Price Histogram */}
          {renderHistogram()}

          {/* Quantitative Explainer Box */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs text-slate-400 space-y-2">
            <h5 className="font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5 text-[11px]">
              <Info className="w-3.5 h-3.5 text-cyan-400" />
              How the Quantitative Monte Carlo Model Works
            </h5>
            <p className="leading-relaxed">
              Stock prices follow continuous-time <strong>Geometric Brownian Motion (GBM)</strong>:
              <span className="block my-1.5 font-mono text-[11px] text-cyan-300 bg-slate-900/90 p-2 rounded border border-slate-800">
                S(t) = S(0) &times; exp[(&mu; - &frac12;&sigma;&sup2;) &Delta;t + &sigma; &radic;(&Delta;t) &times; Z]
              </span>
              Where <strong className="text-slate-200">&mu;</strong> is drift calibrated from 6-month historical returns (bounded to prevent runaway bias), <strong className="text-slate-200">&sigma;</strong> is annualized standard deviation of daily log-returns, and <strong className="text-slate-200">Z ~ N(0, 1)</strong> are standard normal random shocks.
            </p>
            <p className="leading-relaxed text-[11px] text-slate-500">
              Unlike simple endpoint probabilities, the <strong>First-Touch Win Rate</strong> evaluates path-dependent barrier crossings day-by-day: the percentage of simulated futures where price touches your Target (TP1) before ever breaching your Stop Loss invalidation line.
            </p>
          </div>
        </>
      )}
    </div>
  );
}
