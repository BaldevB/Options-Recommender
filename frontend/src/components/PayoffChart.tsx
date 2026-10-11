"use client";

import React, { useState, useMemo, useRef } from "react";
import {
  Sliders,
  Calendar,
  Clock,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Table,
  Activity,
  Layers,
  Zap,
} from "lucide-react";

interface PayoffChartProps {
  spotPrice: number;
  strike: number;
  askPrice: number;
  optionType: string; // "CALL" or "PUT"
  breakeven: number;
  contracts?: number;
  dte?: number;
  iv?: number; // implied volatility percentage, e.g. 35.0
}

// Abramowitz & Stegun erf approximation
function erf(x: number): number {
  const sign = x >= 0 ? 1 : -1;
  const absX = Math.abs(x);
  const a1 = 0.254829592;
  const a2 = -0.284496736;
  const a3 = 1.421413741;
  const a4 = -1.453152027;
  const a5 = 1.061405429;
  const p = 0.3275911;

  const t = 1.0 / (1.0 + p * absX);
  const y = 1.0 - (((((a5 * t + a4) * t + a3) * t + a2) * t + a1) * t) * Math.exp(-absX * absX);
  return sign * y;
}

function normCdf(x: number): number {
  return 0.5 * (1.0 + erf(x / Math.SQRT2));
}

// Analytical Black-Scholes pricing function
function calcBlackScholesPrice(
  spot: number,
  strike: number,
  dteDays: number,
  ivDecimal: number,
  isCall: boolean,
  riskFreeRate: number = 0.045
): number {
  if (dteDays <= 0.001) {
    return isCall ? Math.max(0, spot - strike) : Math.max(0, strike - spot);
  }

  const t = Math.max(dteDays / 365.0, 0.0002);
  const sigma = Math.max(ivDecimal, 0.02);
  const r = riskFreeRate;

  try {
    const d1 = (Math.log(spot / strike) + (r + 0.5 * sigma * sigma) * t) / (sigma * Math.sqrt(t));
    const d2 = d1 - sigma * Math.sqrt(t);

    const nd1 = normCdf(d1);
    const nd2 = normCdf(d2);

    if (isCall) {
      const price = spot * nd1 - strike * Math.exp(-r * t) * nd2;
      return Math.max(0, price);
    } else {
      const nNegD1 = normCdf(-d1);
      const nNegD2 = normCdf(-d2);
      const price = strike * Math.exp(-r * t) * nNegD2 - spot * nNegD1;
      return Math.max(0, price);
    }
  } catch {
    return isCall ? Math.max(0, spot - strike) : Math.max(0, strike - spot);
  }
}

export default function PayoffChart({
  spotPrice,
  strike,
  askPrice,
  optionType,
  breakeven,
  contracts = 1,
  dte = 30,
  iv = 35.0,
}: PayoffChartProps) {
  const isCall = optionType.toUpperCase() === "CALL";
  const totalDte = Math.max(dte || 30, 1);
  const baseIv = Math.max(iv || 35.0, 5.0);

  // Interactive What-If Simulator state
  const [daysElapsed, setDaysElapsed] = useState<number>(0);
  const [ivShiftPct, setIvShiftPct] = useState<number>(0);
  const [activeTab, setActiveTab] = useState<"chart" | "matrix">("chart");
  const [hoverXPrice, setHoverXPrice] = useState<number | null>(null);

  const effectiveDte = Math.max(0, totalDte - daysElapsed);
  const effectiveIvDecimal = Math.max(0.05, (baseIv + ivShiftPct) / 100.0);
  const initialCost = askPrice * 100 * contracts;

  // Chart range calculations
  const { minX, maxX, stepPoints } = useMemo(() => {
    const low = Math.max(1, spotPrice * 0.82);
    const high = spotPrice * 1.18;
    const steps = 70;
    const stepSize = (high - low) / steps;

    const points: {
      x: number;
      expPnl: number;
      simPnl: number;
      simPrice: number;
    }[] = [];

    for (let i = 0; i <= steps; i++) {
      const px = low + i * stepSize;

      // 1. Expiration P&L (Intrinsic value at expiry)
      const expOptVal = isCall ? Math.max(0, px - strike) : Math.max(0, strike - px);
      const expPnl = (expOptVal - askPrice) * 100 * contracts;

      // 2. Simulated P&L at T + daysElapsed with IV shift
      const simOptVal = calcBlackScholesPrice(
        px,
        strike,
        effectiveDte,
        effectiveIvDecimal,
        isCall
      );
      const simPnl = (simOptVal - askPrice) * 100 * contracts;

      points.push({
        x: px,
        expPnl,
        simPnl,
        simPrice: simOptVal,
      });
    }

    return { minX: low, maxX: high, stepPoints: points };
  }, [spotPrice, strike, askPrice, isCall, contracts, effectiveDte, effectiveIvDecimal]);

  // SVG Dimensions & Scales
  const svgWidth = 580;
  const svgHeight = 250;
  const padding = { top: 25, right: 35, bottom: 40, left: 60 };
  const innerW = svgWidth - padding.left - padding.right;
  const innerH = svgHeight - padding.top - padding.bottom;

  // Y-Range scale with dynamic padding
  const allY = useMemo(() => {
    const vals: number[] = [];
    stepPoints.forEach((p) => {
      vals.push(p.expPnl, p.simPnl);
    });
    const minVal = Math.min(...vals, -initialCost);
    const maxVal = Math.max(...vals, initialCost * 0.5);
    const bound = Math.max(Math.abs(minVal), Math.abs(maxVal), initialCost);
    return bound;
  }, [stepPoints, initialCost]);

  const scaleX = (val: number) => padding.left + ((val - minX) / (maxX - minX)) * innerW;
  const scaleY = (val: number) => padding.top + (1 - (val - -allY) / (allY * 2)) * innerH;

  const zeroY = scaleY(0);
  const spotX = scaleX(spotPrice);
  const strikeX = scaleX(strike);
  const beX = scaleX(breakeven);

  // Expiration Path (Dashed)
  const expPath = useMemo(() => {
    return stepPoints
      .map((p, i) => `${i === 0 ? "M" : "L"} ${scaleX(p.x).toFixed(1)} ${scaleY(p.expPnl).toFixed(1)}`)
      .join(" ");
  }, [stepPoints, minX, maxX, allY]);

  // Simulated Curve Path (Solid Glowing)
  const simPath = useMemo(() => {
    return stepPoints
      .map((p, i) => `${i === 0 ? "M" : "L"} ${scaleX(p.x).toFixed(1)} ${scaleY(p.simPnl).toFixed(1)}`)
      .join(" ");
  }, [stepPoints, minX, maxX, allY]);

  // Current Hover Inspection
  const currentHover = useMemo(() => {
    const targetPx = hoverXPrice ?? spotPrice;
    const simOptVal = calcBlackScholesPrice(
      targetPx,
      strike,
      effectiveDte,
      effectiveIvDecimal,
      isCall
    );
    const simPnl = (simOptVal - askPrice) * 100 * contracts;
    const simRoi = (simPnl / initialCost) * 100.0;

    const expOptVal = isCall ? Math.max(0, targetPx - strike) : Math.max(0, strike - targetPx);
    const expPnl = (expOptVal - askPrice) * 100 * contracts;
    const expRoi = (expPnl / initialCost) * 100.0;

    const movePct = ((targetPx - spotPrice) / spotPrice) * 100.0;

    return {
      price: targetPx,
      movePct,
      simOptVal,
      simPnl,
      simRoi,
      expOptVal,
      expPnl,
      expRoi,
      xPos: scaleX(targetPx),
    };
  }, [
    hoverXPrice,
    spotPrice,
    strike,
    effectiveDte,
    effectiveIvDecimal,
    isCall,
    askPrice,
    contracts,
    initialCost,
    minX,
    maxX,
  ]);

  // Multi-Horizon Scenario Matrix Data
  const matrixData = useMemo(() => {
    const priceDeltas = [-0.10, -0.05, -0.02, 0.0, 0.02, 0.05, 0.10, 0.15];
    const timeHorizons = [
      { label: "Today (T+0)", dteLeft: totalDte },
      { label: `+${Math.max(1, Math.round(totalDte * 0.25))}d`, dteLeft: Math.round(totalDte * 0.75) },
      { label: `+${Math.max(2, Math.round(totalDte * 0.50))}d`, dteLeft: Math.round(totalDte * 0.50) },
      { label: `+${Math.max(3, Math.round(totalDte * 0.75))}d`, dteLeft: Math.round(totalDte * 0.25) },
      { label: "Expiration", dteLeft: 0 },
    ];

    return priceDeltas.map((pct) => {
      const scenarioPrice = spotPrice * (1 + pct);
      const rowReturns = timeHorizons.map((th) => {
        const optVal = calcBlackScholesPrice(
          scenarioPrice,
          strike,
          th.dteLeft,
          effectiveIvDecimal,
          isCall
        );
        const pnl = (optVal - askPrice) * 100 * contracts;
        const roi = (pnl / initialCost) * 100;
        return {
          dteLeft: th.dteLeft,
          optVal,
          pnl,
          roi,
        };
      });

      return {
        pctLabel: `${pct >= 0 ? "+" : ""}${(pct * 100).toFixed(0)}%`,
        stockPrice: scenarioPrice,
        returns: rowReturns,
      };
    });
  }, [spotPrice, strike, totalDte, effectiveIvDecimal, isCall, askPrice, contracts, initialCost]);

  // Mouse handler on SVG
  const svgRef = useRef<SVGSVGElement | null>(null);
  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    const clientX = e.clientX - rect.left;
    const clampedX = Math.max(padding.left, Math.min(svgWidth - padding.right, clientX));
    const priceAtX = minX + ((clampedX - padding.left) / innerW) * (maxX - minX);
    setHoverXPrice(priceAtX);
  };

  const handleMouseLeave = () => {
    setHoverXPrice(null);
  };

  const resetSimulator = () => {
    setDaysElapsed(0);
    setIvShiftPct(0);
    setHoverXPrice(null);
  };

  return (
    <div className="w-full rounded-2xl border border-slate-800 bg-[#0a1120] p-4 text-xs shadow-2xl">
      {/* Simulator Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
        <div className="flex items-center space-x-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
            <Zap className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-white text-sm">
                Interactive &quot;What-If&quot; P&amp;L Simulator
              </span>
              <span className="rounded bg-cyan-950/90 px-2 py-0.5 text-[10px] font-mono text-cyan-300 border border-cyan-800/50">
                {contracts}x Contract{contracts > 1 ? "s" : ""} • ${initialCost.toFixed(0)} Capital
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Model non-linear Black-Scholes pricing with dynamic time decay ($T+N$ days) and IV fluctuations.
            </p>
          </div>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex items-center space-x-1 rounded-lg border border-slate-800 bg-[#070d18] p-1 text-xs">
          <button
            onClick={() => setActiveTab("chart")}
            className={`flex items-center space-x-1.5 rounded px-2.5 py-1 font-bold transition ${
              activeTab === "chart"
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Activity className="h-3.5 w-3.5" />
            <span>Dual Curve Chart</span>
          </button>
          <button
            onClick={() => setActiveTab("matrix")}
            className={`flex items-center space-x-1.5 rounded px-2.5 py-1 font-bold transition ${
              activeTab === "matrix"
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Table className="h-3.5 w-3.5" />
            <span>Scenario Heatmap</span>
          </button>
        </div>
      </div>

      {/* Simulator Control Sliders (Interactive What-If Engine) */}
      <div className="mt-3 rounded-xl border border-slate-800/80 bg-[#070e1c] p-3 space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Slider 1: Days Elapsed (Theta Decay Clock) */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-[11px]">
              <span className="flex items-center text-slate-300 font-medium">
                <Clock className="mr-1.5 h-3.5 w-3.5 text-amber-400" />
                Time Passed: <strong className="ml-1 text-amber-300 font-mono">+{daysElapsed} Day{daysElapsed !== 1 ? "s" : ""}</strong>
              </span>
              <span className="text-[10px] text-slate-400 font-mono">
                {effectiveDte} DTE Remaining (of {totalDte}d)
              </span>
            </div>
            <input
              type="range"
              min={0}
              max={totalDte}
              step={1}
              value={daysElapsed}
              onChange={(e) => setDaysElapsed(Number(e.target.value))}
              className="w-full accent-amber-400 cursor-pointer h-1.5 rounded-lg bg-slate-800"
            />
            <div className="flex justify-between text-[9px] text-slate-500">
              <span>Today (T+0)</span>
              <span>Halfway (+{Math.round(totalDte / 2)}d)</span>
              <span>Expiration ({totalDte}d)</span>
            </div>
          </div>

          {/* Slider 2: Implied Volatility Shift (Vega Shock) */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-[11px]">
              <span className="flex items-center text-slate-300 font-medium">
                <Sliders className="mr-1.5 h-3.5 w-3.5 text-cyan-400" />
                IV Shift:{" "}
                <strong
                  className={`ml-1 font-mono ${
                    ivShiftPct > 0
                      ? "text-emerald-300"
                      : ivShiftPct < 0
                      ? "text-rose-400"
                      : "text-slate-300"
                  }`}
                >
                  {ivShiftPct > 0 ? "+" : ""}{ivShiftPct}%
                </strong>
              </span>
              <span className="text-[10px] text-slate-400 font-mono">
                Simulated IV: {(effectiveIvDecimal * 100).toFixed(1)}% (Base: {baseIv.toFixed(1)}%)
              </span>
            </div>
            <input
              type="range"
              min={-25}
              max={25}
              step={1}
              value={ivShiftPct}
              onChange={(e) => setIvShiftPct(Number(e.target.value))}
              className="w-full accent-cyan-400 cursor-pointer h-1.5 rounded-lg bg-slate-800"
            />
            <div className="flex justify-between text-[9px] text-slate-500">
              <span>-25% (Crush)</span>
              <span>0% (Neutral)</span>
              <span>+25% (Surge)</span>
            </div>
          </div>
        </div>

        {/* Quick Presets & Reset Row */}
        <div className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-800/80 pt-2 text-[11px]">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-slate-500 text-[10px]">Quick Presets:</span>
            <button
              onClick={() => {
                setDaysElapsed(0);
                setIvShiftPct(0);
              }}
              className={`rounded px-2 py-0.5 text-[10px] font-semibold transition ${
                daysElapsed === 0 && ivShiftPct === 0
                  ? "bg-cyan-500 text-black font-bold"
                  : "bg-slate-800 text-slate-300 hover:text-white"
              }`}
            >
              Today (T+0)
            </button>
            <button
              onClick={() => {
                setDaysElapsed(Math.round(totalDte / 2));
              }}
              className="rounded bg-slate-800 px-2 py-0.5 text-[10px] text-slate-300 hover:text-white"
            >
              Halfway (+{Math.round(totalDte / 2)}d)
            </button>
            <button
              onClick={() => {
                setDaysElapsed(totalDte);
              }}
              className={`rounded px-2 py-0.5 text-[10px] font-semibold transition ${
                daysElapsed === totalDte
                  ? "bg-amber-500 text-black font-bold"
                  : "bg-slate-800 text-slate-300 hover:text-white"
              }`}
            >
              At Expiry
            </button>
            <button
              onClick={() => {
                setIvShiftPct(-15);
              }}
              className="rounded bg-rose-950/80 border border-rose-800/50 px-2 py-0.5 text-[10px] text-rose-300 hover:bg-rose-900"
            >
              -15% IV Crush
            </button>
            <button
              onClick={() => {
                setIvShiftPct(15);
              }}
              className="rounded bg-emerald-950/80 border border-emerald-800/50 px-2 py-0.5 text-[10px] text-emerald-300 hover:bg-emerald-900"
            >
              +15% IV Expansion
            </button>
          </div>

          {(daysElapsed !== 0 || ivShiftPct !== 0 || hoverXPrice !== null) && (
            <button
              onClick={resetSimulator}
              className="flex items-center space-x-1 text-slate-400 hover:text-cyan-300 transition text-[10px]"
            >
              <RefreshCw className="h-3 w-3" />
              <span>Reset Simulator</span>
            </button>
          )}
        </div>
      </div>

      {/* VIEW 1: DUAL CURVE CHART */}
      {activeTab === "chart" && (
        <div className="mt-3">
          {/* Live Hover / Target Inspector Readout */}
          <div className="mb-2 flex flex-wrap items-center justify-between rounded-lg bg-[#070b14] px-3 py-2 text-xs border border-slate-800">
            <div className="flex items-center space-x-2">
              <span className="text-slate-400 text-[11px]">Underlying Stock:</span>
              <span className="font-mono text-sm font-bold text-white">
                ${currentHover.price.toFixed(2)}
              </span>
              <span
                className={`text-[10px] font-bold ${
                  currentHover.movePct >= 0 ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                ({currentHover.movePct >= 0 ? "+" : ""}{currentHover.movePct.toFixed(1)}%)
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-4 text-xs">
              <div className="flex items-center space-x-1.5">
                <span className="text-slate-400 text-[11px]">Simulated Value:</span>
                <span className="font-mono font-bold text-cyan-300">
                  ${currentHover.simOptVal.toFixed(2)}
                </span>
                <span
                  className={`font-mono font-bold ${
                    currentHover.simPnl >= 0 ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  ({currentHover.simPnl >= 0 ? "+" : ""}${currentHover.simPnl.toFixed(0)} /{" "}
                  {currentHover.simRoi >= 0 ? "+" : ""}{currentHover.simRoi.toFixed(1)}%)
                </span>
              </div>

              <div className="hidden sm:flex items-center space-x-1 text-[11px] text-slate-500">
                <span>Exp P&amp;L:</span>
                <span
                  className={`font-mono ${
                    currentHover.expPnl >= 0 ? "text-emerald-400/80" : "text-rose-400/80"
                  }`}
                >
                  {currentHover.expPnl >= 0 ? "+" : ""}${currentHover.expPnl.toFixed(0)}
                </span>
              </div>
            </div>
          </div>

          {/* Interactive SVG Chart */}
          <div className="relative overflow-hidden rounded-xl bg-[#070b14] border border-slate-800/90 p-1">
            <svg
              ref={svgRef}
              viewBox={`0 0 ${svgWidth} ${svgHeight}`}
              className="h-auto w-full select-none cursor-crosshair"
              onMouseMove={handleMouseMove}
              onMouseLeave={handleMouseLeave}
            >
              {/* Zero P&L horizontal baseline */}
              <line
                x1={padding.left}
                y1={zeroY}
                x2={svgWidth - padding.right}
                y2={zeroY}
                stroke="rgba(255,255,255,0.25)"
                strokeDasharray="3 3"
                strokeWidth="1"
              />

              {/* Breakeven vertical line */}
              {beX >= padding.left && beX <= svgWidth - padding.right && (
                <line
                  x1={beX}
                  y1={padding.top}
                  x2={beX}
                  y2={svgHeight - padding.bottom}
                  stroke="#fbbf24"
                  strokeDasharray="2 2"
                  strokeWidth="1"
                />
              )}

              {/* Current Spot vertical line */}
              {spotX >= padding.left && spotX <= svgWidth - padding.right && (
                <line
                  x1={spotX}
                  y1={padding.top}
                  x2={spotX}
                  y2={svgHeight - padding.bottom}
                  stroke="#10b981"
                  strokeWidth="1.5"
                />
              )}

              {/* Strike vertical line */}
              {strikeX >= padding.left && strikeX <= svgWidth - padding.right && (
                <line
                  x1={strikeX}
                  y1={padding.top}
                  x2={strikeX}
                  y2={svgHeight - padding.bottom}
                  stroke="#a855f7"
                  strokeDasharray="2 2"
                  strokeWidth="1"
                />
              )}

              {/* Hover crosshair vertical line */}
              {hoverXPrice !== null && (
                <line
                  x1={currentHover.xPos}
                  y1={padding.top}
                  x2={currentHover.xPos}
                  y2={svgHeight - padding.bottom}
                  stroke="#38bdf8"
                  strokeWidth="1.5"
                  strokeDasharray="2 2"
                />
              )}

              {/* 1. Expiration Payoff Path (Dashed gray) */}
              <path
                d={expPath}
                fill="none"
                stroke="#64748b"
                strokeWidth="1.75"
                strokeDasharray="4 4"
                opacity="0.8"
              />

              {/* 2. Simulated Payoff Path (Solid Bright Glowing Cyan) */}
              <path
                d={simPath}
                fill="none"
                stroke="#06b6d4"
                strokeWidth="2.75"
                strokeLinecap="round"
              />

              {/* Labels & Markers */}
              <text x={padding.left} y={zeroY - 4} fill="#64748b" fontSize="10">
                $0
              </text>
              <text
                x={svgWidth - padding.right}
                y={padding.top + 10}
                fill="#10b981"
                textAnchor="end"
                fontSize="10"
                fontWeight="bold"
              >
                +Profit
              </text>
              <text
                x={svgWidth - padding.right}
                y={svgHeight - padding.bottom - 4}
                fill="#ef4444"
                textAnchor="end"
                fontSize="10"
              >
                -Max Loss: -${initialCost.toFixed(0)}
              </text>

              <text x={spotX} y={svgHeight - 12} fill="#10b981" textAnchor="middle" fontSize="10">
                Spot ${spotPrice.toFixed(1)}
              </text>
              <text x={beX} y={svgHeight - 12} fill="#fbbf24" textAnchor="middle" fontSize="10">
                B/E ${breakeven.toFixed(1)}
              </text>
            </svg>
          </div>

          {/* Legend and Dual Curve Badges */}
          <div className="mt-2.5 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-400">
            <div className="flex flex-wrap items-center gap-3">
              <span className="flex items-center space-x-1.5">
                <span className="inline-block h-2 w-4 rounded bg-cyan-400" />
                <span className="text-white font-medium">
                  What-If Curve (T+{daysElapsed}d)
                </span>
              </span>
              <span className="flex items-center space-x-1.5">
                <span className="inline-block h-0.5 w-4 border-b border-dashed border-slate-400" />
                <span>Expiration Payoff</span>
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <span className="flex items-center space-x-1">
                <span className="inline-block h-2 w-2 rounded-full bg-emerald-500" />
                <span>Spot: ${spotPrice.toFixed(2)}</span>
              </span>
              <span className="flex items-center space-x-1">
                <span className="inline-block h-2 w-2 rounded-full bg-purple-400" />
                <span>Strike: ${strike.toFixed(2)}</span>
              </span>
              <span className="flex items-center space-x-1">
                <span className="inline-block h-2 w-2 rounded-full bg-amber-400" />
                <span>B/E: ${breakeven.toFixed(2)}</span>
              </span>
            </div>
          </div>
        </div>
      )}

      {/* VIEW 2: MULTI-HORIZON SCENARIO HEATMAP MATRIX */}
      {activeTab === "matrix" && (
        <div className="mt-3">
          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-[#070b14]">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#0e1628] text-[10px] uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-3 py-2.5">Stock Price</th>
                  <th className="px-3 py-2.5">Move %</th>
                  <th className="px-3 py-2.5 text-center">Today (T+0)</th>
                  <th className="px-3 py-2.5 text-center">+{Math.max(1, Math.round(totalDte * 0.25))}d</th>
                  <th className="px-3 py-2.5 text-center">+{Math.max(2, Math.round(totalDte * 0.50))}d</th>
                  <th className="px-3 py-2.5 text-center">+{Math.max(3, Math.round(totalDte * 0.75))}d</th>
                  <th className="px-3 py-2.5 text-center">Expiration</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                {matrixData.map((row, idx) => {
                  const isCurrentSpot = Math.abs(row.stockPrice - spotPrice) < 0.05;
                  return (
                    <tr
                      key={idx}
                      className={`transition hover:bg-slate-800/40 ${
                        isCurrentSpot ? "bg-cyan-950/20 font-bold" : ""
                      }`}
                    >
                      <td className="px-3 py-2 whitespace-nowrap text-white font-bold">
                        ${row.stockPrice.toFixed(2)}
                      </td>
                      <td
                        className={`px-3 py-2 whitespace-nowrap ${
                          row.stockPrice >= spotPrice ? "text-emerald-400" : "text-rose-400"
                        }`}
                      >
                        {row.pctLabel}
                      </td>
                      {row.returns.map((ret, rIdx) => {
                        const isProfitable = ret.pnl > 0;
                        const isHighWin = ret.roi >= 50.0;
                        const isMaxLoss = ret.pnl <= -initialCost * 0.95;

                        return (
                          <td
                            key={rIdx}
                            className={`px-2.5 py-2 text-center whitespace-nowrap ${
                              isHighWin
                                ? "bg-emerald-950/70 text-emerald-300 font-bold"
                                : isProfitable
                                ? "bg-emerald-950/30 text-emerald-400"
                                : isMaxLoss
                                ? "bg-rose-950/70 text-rose-300 font-bold"
                                : "bg-rose-950/20 text-rose-400"
                            }`}
                          >
                            <div>
                              {ret.pnl >= 0 ? "+" : ""}${ret.pnl.toFixed(0)}
                            </div>
                            <div className="text-[9px] opacity-80">
                              {ret.roi >= 0 ? "+" : ""}{ret.roi.toFixed(1)}%
                            </div>
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="mt-2 text-[10px] text-slate-500 flex justify-between">
            <span>• Cells project net dollar P&amp;L and ROI % for {contracts} contract(s).</span>
            <span>Simulated with IV: {(effectiveIvDecimal * 100).toFixed(1)}%</span>
          </div>
        </div>
      )}
    </div>
  );
}
