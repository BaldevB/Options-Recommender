"use client";

import React, { useState, useMemo } from "react";
import {
  Layers,
  Plus,
  Trash2,
  TrendingUp,
  TrendingDown,
  Activity,
  Zap,
  ArrowRight,
  ShieldAlert,
  RotateCcw,
  Sparkles,
  Percent,
  DollarSign,
  Sliders,
  Scale,
} from "lucide-react";

export type StrategyType =
  | "CUSTOM"
  | "BULL_CALL_SPREAD"
  | "BEAR_PUT_SPREAD"
  | "LONG_STRADDLE"
  | "LONG_STRANGLE"
  | "IRON_CONDOR"
  | "CALENDAR_SPREAD";

export interface StrategyLeg {
  id: string;
  side: "BUY" | "SELL";
  type: "CALL" | "PUT";
  strike: number;
  expiration: string;
  dte: number;
  price: number; // bid for sell, ask for buy
  contracts: number;
  delta?: number;
  iv?: number;
}

interface MultiLegStrategyBuilderProps {
  spotPrice: number;
  ticker: string;
  availableExpirations?: { expiration: string; dte: number }[];
  strikes?: any[];
  onAddLegFromChain?: (leg: StrategyLeg) => void;
}

export default function MultiLegStrategyBuilder({
  spotPrice,
  ticker,
  availableExpirations = [],
  strikes = [],
}: MultiLegStrategyBuilderProps) {
  const [strategyPreset, setStrategyPreset] = useState<StrategyType>("BULL_CALL_SPREAD");
  const [legs, setLegs] = useState<StrategyLeg[]>(() => {
    // Default starter: Bull Call Spread (ATM Long Call + OTM Short Call)
    const atmStrike = Math.round(spotPrice);
    const otmStrike = Math.round(spotPrice * 1.05);
    const defaultExp = availableExpirations[0]?.expiration || "2026-10-30";
    const defaultDte = availableExpirations[0]?.dte || 30;

    return [
      {
        id: "leg-1",
        side: "BUY",
        type: "CALL",
        strike: atmStrike,
        expiration: defaultExp,
        dte: defaultDte,
        price: Math.max(1.0, spotPrice * 0.03),
        contracts: 1,
        delta: 0.50,
      },
      {
        id: "leg-2",
        side: "SELL",
        type: "CALL",
        strike: otmStrike,
        expiration: defaultExp,
        dte: defaultDte,
        price: Math.max(0.5, spotPrice * 0.012),
        contracts: 1,
        delta: 0.25,
      },
    ];
  });

  // Apply quick presets
  const applyPreset = (preset: StrategyType) => {
    setStrategyPreset(preset);
    const defaultExp = availableExpirations[0]?.expiration || "2026-10-30";
    const defaultDte = availableExpirations[0]?.dte || 30;
    const atm = Math.round(spotPrice);

    switch (preset) {
      case "BULL_CALL_SPREAD":
        setLegs([
          {
            id: `leg-${Date.now()}-1`,
            side: "BUY",
            type: "CALL",
            strike: atm,
            expiration: defaultExp,
            dte: defaultDte,
            price: Math.max(1.0, spotPrice * 0.035),
            contracts: 1,
            delta: 0.50,
          },
          {
            id: `leg-${Date.now()}-2`,
            side: "SELL",
            type: "CALL",
            strike: Math.round(spotPrice * 1.05),
            expiration: defaultExp,
            dte: defaultDte,
            price: Math.max(0.5, spotPrice * 0.015),
            contracts: 1,
            delta: 0.25,
          },
        ]);
        break;

      case "BEAR_PUT_SPREAD":
        setLegs([
          {
            id: `leg-${Date.now()}-1`,
            side: "BUY",
            type: "PUT",
            strike: atm,
            expiration: defaultExp,
            dte: defaultDte,
            price: Math.max(1.0, spotPrice * 0.035),
            contracts: 1,
            delta: -0.50,
          },
          {
            id: `leg-${Date.now()}-2`,
            side: "SELL",
            type: "PUT",
            strike: Math.round(spotPrice * 0.95),
            expiration: defaultExp,
            dte: defaultDte,
            price: Math.max(0.5, spotPrice * 0.015),
            contracts: 1,
            delta: -0.25,
          },
        ]);
        break;

      case "LONG_STRADDLE":
        setLegs([
          {
            id: `leg-${Date.now()}-1`,
            side: "BUY",
            type: "CALL",
            strike: atm,
            expiration: defaultExp,
            dte: defaultDte,
            price: Math.max(1.0, spotPrice * 0.03),
            contracts: 1,
            delta: 0.50,
          },
          {
            id: `leg-${Date.now()}-2`,
            side: "BUY",
            type: "PUT",
            strike: atm,
            expiration: defaultExp,
            dte: defaultDte,
            price: Math.max(1.0, spotPrice * 0.03),
            contracts: 1,
            delta: -0.50,
          },
        ]);
        break;

      case "LONG_STRANGLE":
        setLegs([
          {
            id: `leg-${Date.now()}-1`,
            side: "BUY",
            type: "CALL",
            strike: Math.round(spotPrice * 1.04),
            expiration: defaultExp,
            dte: defaultDte,
            price: Math.max(0.8, spotPrice * 0.018),
            contracts: 1,
            delta: 0.30,
          },
          {
            id: `leg-${Date.now()}-2`,
            side: "BUY",
            type: "PUT",
            strike: Math.round(spotPrice * 0.96),
            expiration: defaultExp,
            dte: defaultDte,
            price: Math.max(0.8, spotPrice * 0.018),
            contracts: 1,
            delta: -0.30,
          },
        ]);
        break;

      case "IRON_CONDOR":
        setLegs([
          {
            id: `leg-${Date.now()}-1`,
            side: "BUY",
            type: "PUT",
            strike: Math.round(spotPrice * 0.92),
            expiration: defaultExp,
            dte: defaultDte,
            price: Math.max(0.3, spotPrice * 0.008),
            contracts: 1,
            delta: -0.15,
          },
          {
            id: `leg-${Date.now()}-2`,
            side: "SELL",
            type: "PUT",
            strike: Math.round(spotPrice * 0.96),
            expiration: defaultExp,
            dte: defaultDte,
            price: Math.max(0.8, spotPrice * 0.02),
            contracts: 1,
            delta: -0.30,
          },
          {
            id: `leg-${Date.now()}-3`,
            side: "SELL",
            type: "CALL",
            strike: Math.round(spotPrice * 1.04),
            expiration: defaultExp,
            dte: defaultDte,
            price: Math.max(0.8, spotPrice * 0.02),
            contracts: 1,
            delta: 0.30,
          },
          {
            id: `leg-${Date.now()}-4`,
            side: "BUY",
            type: "CALL",
            strike: Math.round(spotPrice * 1.08),
            expiration: defaultExp,
            dte: defaultDte,
            price: Math.max(0.3, spotPrice * 0.008),
            contracts: 1,
            delta: 0.15,
          },
        ]);
        break;

      default:
        break;
    }
  };

  const addEmptyLeg = () => {
    setStrategyPreset("CUSTOM");
    const defaultExp = availableExpirations[0]?.expiration || "2026-10-30";
    const defaultDte = availableExpirations[0]?.dte || 30;
    setLegs((prev) => [
      ...prev,
      {
        id: `leg-${Date.now()}`,
        side: "BUY",
        type: "CALL",
        strike: Math.round(spotPrice),
        expiration: defaultExp,
        dte: defaultDte,
        price: 2.5,
        contracts: 1,
        delta: 0.5,
      },
    ]);
  };

  const removeLeg = (id: string) => {
    setStrategyPreset("CUSTOM");
    setLegs((prev) => prev.filter((leg) => leg.id !== id));
  };

  const updateLeg = (id: string, updates: Partial<StrategyLeg>) => {
    setStrategyPreset("CUSTOM");
    setLegs((prev) =>
      prev.map((leg) => (leg.id === id ? { ...leg, ...updates } : leg))
    );
  };

  // Financial calculations
  const summary = useMemo(() => {
    let netCostPerShare = 0;
    let netDelta = 0;

    for (const leg of legs) {
      const sign = leg.side === "BUY" ? 1 : -1;
      netCostPerShare += sign * leg.price * leg.contracts;
      if (leg.delta !== undefined) {
        netDelta += sign * leg.delta * leg.contracts;
      }
    }

    const isDebit = netCostPerShare >= 0;
    const netCashflowPerShare = Math.abs(netCostPerShare);
    const totalCashflow = netCashflowPerShare * 100;

    // Approximate Payoff Curve across underlying range
    const lowPx = Math.max(1, spotPrice * 0.80);
    const highPx = spotPrice * 1.20;
    const steps = 60;
    const stepSize = (highPx - lowPx) / steps;
    const curvePoints: { px: number; pnl: number }[] = [];

    let calculatedMaxProfit = -Infinity;
    let calculatedMaxLoss = Infinity;

    for (let i = 0; i <= steps; i++) {
      const px = lowPx + i * stepSize;
      let pnl = 0;

      for (const leg of legs) {
        const sign = leg.side === "BUY" ? 1 : -1;
        const intrinsic =
          leg.type === "CALL"
            ? Math.max(0, px - leg.strike)
            : Math.max(0, leg.strike - px);
        const legPnl = sign * (intrinsic - leg.price) * 100 * leg.contracts;
        pnl += legPnl;
      }

      curvePoints.push({ px, pnl });
      if (pnl > calculatedMaxProfit) calculatedMaxProfit = pnl;
      if (pnl < calculatedMaxLoss) calculatedMaxLoss = pnl;
    }

    // Identify approximate breakevens (zero crossings)
    const breakevens: number[] = [];
    for (let i = 1; i < curvePoints.length; i++) {
      const prev = curvePoints[i - 1];
      const curr = curvePoints[i];
      if ((prev.pnl <= 0 && curr.pnl >= 0) || (prev.pnl >= 0 && curr.pnl <= 0)) {
        // Linear interpolation
        const fraction = Math.abs(prev.pnl) / (Math.abs(prev.pnl) + Math.abs(curr.pnl) || 1);
        const bePx = prev.px + fraction * (curr.px - prev.px);
        breakevens.push(Math.round(bePx * 100) / 100);
      }
    }

    return {
      isDebit,
      netCostPerShare: Math.round(netCostPerShare * 100) / 100,
      totalCashflow: Math.round(totalCashflow),
      netDelta: Math.round(netDelta * 100) / 100,
      maxProfit: calculatedMaxProfit > 100000 ? "Uncapped" : `$${Math.round(calculatedMaxProfit)}`,
      maxLoss: calculatedMaxLoss < -100000 ? "Uncapped" : `$${Math.round(Math.abs(calculatedMaxLoss))}`,
      breakevens,
      curvePoints,
      lowPx,
      highPx,
    };
  }, [legs, spotPrice]);

  return (
    <div className="space-y-6">
      {/* ---------------- 1. STRATEGY PRESETS & HEADER ---------------- */}
      <div className="rounded-2xl border border-slate-800 bg-gradient-to-r from-[#0c1424] via-[#0b1220] to-[#0a101b] p-6 shadow-2xl">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
          <div className="flex items-center space-x-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
              <Scale className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-xl font-bold text-white">
                  Multi-Leg Strategy Builder
                </h3>
                <span className="rounded-full bg-cyan-500/10 px-2.5 py-0.5 text-xs font-semibold text-cyan-300 border border-cyan-500/20">
                  {ticker} &bull; ${spotPrice.toFixed(2)}
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Design custom vertical spreads, condors, and multi-strike combinations with real-time risk/reward modeling.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={addEmptyLeg}
              className="flex items-center space-x-1.5 rounded-lg border border-cyan-500/40 bg-cyan-600/80 px-3 py-1.5 text-xs font-semibold text-white hover:bg-cyan-500 transition shadow-sm"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Add Custom Leg</span>
            </button>
          </div>
        </div>

        {/* Strategy Presets Selector Chips */}
        <div className="mt-4 flex flex-wrap items-center gap-1.5 text-xs">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mr-2 flex items-center">
            <Sparkles className="mr-1 h-3 w-3 text-cyan-400" />
            Presets:
          </span>
          {(
            [
              { id: "BULL_CALL_SPREAD", label: "Bull Call Debit Spread" },
              { id: "BEAR_PUT_SPREAD", label: "Bear Put Debit Spread" },
              { id: "LONG_STRADDLE", label: "Long Straddle" },
              { id: "LONG_STRANGLE", label: "Long Strangle" },
              { id: "IRON_CONDOR", label: "Iron Condor" },
            ] as const
          ).map((preset) => (
            <button
              key={preset.id}
              onClick={() => applyPreset(preset.id)}
              className={`rounded-lg px-2.5 py-1 text-xs font-bold transition ${
                strategyPreset === preset.id
                  ? "bg-cyan-500 text-black shadow-md"
                  : "bg-slate-900 text-slate-300 hover:bg-slate-800 hover:text-white border border-slate-800"
              }`}
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      {/* ---------------- 2. LEGS CONFIGURATION TABLE ---------------- */}
      <div className="rounded-2xl border border-slate-800 bg-[#090e1a] shadow-xl overflow-hidden">
        <div className="border-b border-slate-800 bg-[#0c1424] px-5 py-3 flex items-center justify-between text-xs">
          <span className="font-bold uppercase tracking-wider text-slate-300">
            Active Strategy Legs ({legs.length})
          </span>
          <span className="text-slate-400 text-[11px]">
            Adjust strikes, side (Buy/Sell), or expiration below
          </span>
        </div>

        <div className="p-4 space-y-3">
          {legs.map((leg, index) => {
            const isBuy = leg.side === "BUY";
            const isCall = leg.type === "CALL";

            return (
              <div
                key={leg.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-800/80 bg-[#0d1526] p-3 text-xs"
              >
                {/* Leg Badge */}
                <div className="flex items-center space-x-2">
                  <span className="rounded bg-slate-800 px-2 py-1 font-mono font-bold text-slate-300 text-[11px]">
                    Leg #{index + 1}
                  </span>

                  {/* Side Switcher (Buy / Sell) */}
                  <div className="flex items-center rounded-lg border border-slate-700 bg-slate-900 p-0.5">
                    <button
                      onClick={() => updateLeg(leg.id, { side: "BUY" })}
                      className={`rounded px-2.5 py-1 text-[11px] font-bold transition ${
                        isBuy ? "bg-emerald-500 text-black" : "text-slate-400 hover:text-white"
                      }`}
                    >
                      BUY
                    </button>
                    <button
                      onClick={() => updateLeg(leg.id, { side: "SELL" })}
                      className={`rounded px-2.5 py-1 text-[11px] font-bold transition ${
                        !isBuy ? "bg-rose-500 text-black" : "text-slate-400 hover:text-white"
                      }`}
                    >
                      SELL
                    </button>
                  </div>

                  {/* Option Type (Call / Put) */}
                  <div className="flex items-center rounded-lg border border-slate-700 bg-slate-900 p-0.5">
                    <button
                      onClick={() => updateLeg(leg.id, { type: "CALL" })}
                      className={`rounded px-2.5 py-1 text-[11px] font-bold transition ${
                        isCall ? "bg-cyan-500 text-black" : "text-slate-400 hover:text-white"
                      }`}
                    >
                      CALL
                    </button>
                    <button
                      onClick={() => updateLeg(leg.id, { type: "PUT" })}
                      className={`rounded px-2.5 py-1 text-[11px] font-bold transition ${
                        !isCall ? "bg-indigo-500 text-white" : "text-slate-400 hover:text-white"
                      }`}
                    >
                      PUT
                    </button>
                  </div>
                </div>

                {/* Strike & Premium Controls */}
                <div className="flex flex-wrap items-center gap-3">
                  {/* Strike Input */}
                  <div className="flex items-center space-x-1.5">
                    <span className="text-slate-400 text-[11px]">Strike:</span>
                    <input
                      type="number"
                      value={leg.strike}
                      step="0.5"
                      onChange={(e) => updateLeg(leg.id, { strike: Number(e.target.value) })}
                      className="w-20 rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-center font-mono font-bold text-white focus:border-cyan-500 focus:outline-none"
                    />
                  </div>

                  {/* Price / Premium Input */}
                  <div className="flex items-center space-x-1.5">
                    <span className="text-slate-400 text-[11px]">Price:</span>
                    <div className="relative">
                      <span className="absolute left-2 top-1 text-slate-500 text-[11px]">$</span>
                      <input
                        type="number"
                        value={leg.price}
                        step="0.05"
                        min="0.01"
                        onChange={(e) => updateLeg(leg.id, { price: Math.max(0.01, Number(e.target.value)) })}
                        className="w-20 rounded-md border border-slate-700 bg-slate-900 pl-4 pr-1 py-1 text-center font-mono font-bold text-white focus:border-cyan-500 focus:outline-none"
                      />
                    </div>
                  </div>

                  {/* Quantity */}
                  <div className="flex items-center space-x-1.5">
                    <span className="text-slate-400 text-[11px]">Qty:</span>
                    <input
                      type="number"
                      value={leg.contracts}
                      min="1"
                      onChange={(e) => updateLeg(leg.id, { contracts: Math.max(1, Number(e.target.value)) })}
                      className="w-14 rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-center font-mono font-bold text-white focus:border-cyan-500 focus:outline-none"
                    />
                  </div>

                  {/* Delete Leg Button */}
                  <button
                    onClick={() => removeLeg(leg.id)}
                    title="Remove this leg"
                    className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-rose-400 transition"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ---------------- 3. STRATEGY SUMMARY KPIs ---------------- */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {/* Net Cost / Credit */}
        <div className="rounded-xl border border-slate-800 bg-[#0c1424] p-4 shadow-lg">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            {summary.isDebit ? "Net Debit (Cost)" : "Net Credit (Received)"}
          </div>
          <div className="mt-1 flex items-baseline space-x-1.5">
            <span
              className={`text-2xl font-black font-mono ${
                summary.isDebit ? "text-cyan-300" : "text-emerald-400"
              }`}
            >
              ${Math.abs(summary.netCostPerShare).toFixed(2)}
            </span>
            <span className="text-xs text-slate-400">
              (${summary.totalCashflow} total)
            </span>
          </div>
        </div>

        {/* Max Profit */}
        <div className="rounded-xl border border-slate-800 bg-[#0c1424] p-4 shadow-lg">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Max Potential Profit
          </div>
          <div className="mt-1 text-2xl font-black font-mono text-emerald-400">
            {summary.maxProfit}
          </div>
        </div>

        {/* Max Risk / Loss */}
        <div className="rounded-xl border border-slate-800 bg-[#0c1424] p-4 shadow-lg">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Max Potential Loss
          </div>
          <div className="mt-1 text-2xl font-black font-mono text-rose-400">
            {summary.maxLoss}
          </div>
        </div>

        {/* Net Delta & Breakevens */}
        <div className="rounded-xl border border-slate-800 bg-[#0c1424] p-4 shadow-lg">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Net Delta & Breakeven
          </div>
          <div className="mt-1 flex items-baseline justify-between">
            <span className="text-lg font-bold font-mono text-indigo-300">
              {summary.netDelta > 0 ? "+" : ""}{summary.netDelta}&Delta;
            </span>
            <span className="text-xs font-mono text-amber-300">
              {summary.breakevens.length > 0
                ? `BE: $${summary.breakevens.join(", $")}`
                : "No BE in range"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
