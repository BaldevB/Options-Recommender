"use client";

import React, { useState, useMemo, useEffect, useRef } from "react";
import {
  X,
  TrendingUp,
  TrendingDown,
  Activity,
  Layers,
  Zap,
  Target,
  DollarSign,
  Percent,
  Wallet,
  Clock,
  Shield,
  Sliders,
  ChevronRight,
  Info,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";

export interface SpreadData {
  spread_type: "BULL_CALL" | "BEAR_PUT" | string;
  spread_label: string;
  long_strike: number;
  short_strike: number;
  long_ask: number;
  short_bid: number;
  net_debit: number;
  max_loss: number;
  max_profit: number;
  breakeven: number;
  pop_pct?: number;
  risk_reward_ratio?: number;
  rr_ratio: number;
  width: number;
  suggested_contracts: number;
}

export interface PayoffModalRec {
  id?: string;
  symbol: string;
  name: string;
  stock_price: number;
  option_type: "CALL" | "PUT";
  strike: number;
  expiration: string;
  dte: number;
  delta: number;
  theta: number;
  iv: number;
  ask: number;
  bid: number;
  breakeven: number;
  pop_pct?: number;
  risk_reward_ratio?: number;
  tp1_price?: number;
  tp1_gain_pct?: number;
  stop_loss_price?: number;
  stop_loss_loss_pct?: number;
  suggested_contracts?: number;
  strategy_label?: string;
  strategy_category?: string;
  contract?: string;
  vertical_spread?: SpreadData;
}

export interface OptionPayoffModalProps {
  isOpen: boolean;
  onClose: () => void;
  rec: PayoffModalRec | null;
  spreadData?: SpreadData | null;
  initialMode?: "SINGLE" | "SPREAD";
  onPaperBuy?: (order: any) => void;
}

export function getSpreadAlternative(rec: PayoffModalRec): SpreadData {
  const isCall = rec.option_type === "CALL";
  const stock = rec.stock_price;
  const longStrike = rec.strike;
  const longAsk = rec.ask;

  let step = 5;
  if (stock < 35) step = 1;
  else if (stock < 80) step = 2.5;
  else if (stock < 250) step = 5;
  else if (stock < 500) step = 10;
  else step = 20;

  let shortStrike: number;
  let shortBid: number;

  if (isCall) {
    shortStrike = +(longStrike + step).toFixed(2);
    const discount = Math.max(0.35, Math.min(0.55, (rec.delta || 0.45) * 0.95));
    shortBid = +(longAsk * discount).toFixed(2);
    if (shortBid >= longAsk) shortBid = +(longAsk * 0.45).toFixed(2);
  } else {
    const rawShort = +(longStrike - step).toFixed(2);
    shortStrike = rawShort > 0 ? rawShort : +(longStrike * 0.5).toFixed(2);
    const discount = Math.max(0.35, Math.min(0.55, Math.abs(rec.delta || -0.45) * 0.95));
    shortBid = +(longAsk * discount).toFixed(2);
    if (shortBid >= longAsk) shortBid = +(longAsk * 0.45).toFixed(2);
  }

  const netDebit = Math.max(0.15, +(longAsk - shortBid).toFixed(2));
  const width = Math.abs(shortStrike - longStrike);
  const maxLoss = +(netDebit * 100).toFixed(2);
  const maxProfit = Math.max(10, +((width - netDebit) * 100).toFixed(2));
  const breakeven = isCall ? +(longStrike + netDebit).toFixed(2) : +(longStrike - netDebit).toFixed(2);
  const rr_ratio = +(maxProfit / maxLoss).toFixed(2);

  return {
    spread_type: isCall ? "BULL_CALL" : "BEAR_PUT",
    spread_label: isCall ? "Bull Call Debit Spread" : "Bear Put Debit Spread",
    long_strike: longStrike,
    short_strike: shortStrike,
    long_ask: longAsk,
    short_bid: shortBid,
    net_debit: netDebit,
    max_loss: maxLoss,
    max_profit: maxProfit,
    breakeven: breakeven,
    rr_ratio: rr_ratio,
    width: width,
    suggested_contracts: rec.suggested_contracts ?? 0,
  };
}

export function getThetaCliffInfo(dte: number, theta: number) {
  const absTheta = Math.abs(theta || 0);
  const dailyDecayStr = absTheta > 0 ? `-$${(absTheta * 100).toFixed(0)}/day` : "-$0/day";

  if (dte === 0) {
    return {
      severity: "URGENT" as const,
      color: "rose",
      badge: "0DTE FLASH",
      timer: "Hourly theta decay active",
      optimalWindow: "Intraday Scalp Only",
      exitRule: "Close position before 3:30 PM ET to prevent total theta collapse.",
      headline: `⚡ 0DTE Flash: Extreme theta burn (${dailyDecayStr}). Exit intraday.`,
    };
  }

  if (dte <= 7) {
    return {
      severity: "DANGER" as const,
      color: "rose",
      badge: "THETA CLIFF",
      timer: `Cliff Active (${dte}d left)`,
      optimalWindow: "Day 1 to 2",
      exitRule: "Exit within 48h to avoid exponential time decay.",
      headline: `🔥 Theta Cliff Active: Exit within 1–2 days. Rapid decay (${dailyDecayStr}).`,
    };
  }

  if (dte <= 21) {
    return {
      severity: "WARNING" as const,
      color: "amber",
      badge: "APPROACHING CLIFF",
      timer: `${Math.max(1, dte - 14)}d to steep decay`,
      optimalWindow: "Day 2 to 5",
      exitRule: "Take profit at +50% to +80% or exit before 14 DTE.",
      headline: `⏳ Approaching Theta Cliff: Optimal exit: Day 2–5. Exit before 14 DTE (${dailyDecayStr}).`,
    };
  }

  if (dte <= 45) {
    return {
      severity: "OPTIMAL" as const,
      color: "cyan",
      badge: "OPTIMAL WINDOW",
      timer: `${dte - 21}d until cliff`,
      optimalWindow: "Day 3 to 12",
      exitRule: "Exit before 21 DTE to avoid accelerated theta decay.",
      headline: `🛡️ Optimal Theta Window: Day 3 to 12. Exit before 21 DTE to avoid accelerated decay (${dailyDecayStr}).`,
    };
  }

  return {
    severity: "BENIGN" as const,
    color: "emerald",
    badge: "LOW THETA DRAG",
    timer: `${dte - 21}d until cliff`,
    optimalWindow: "Day 5 to 20",
    exitRule: "Low daily decay. Hold through multi-week momentum swing.",
    headline: `🌿 Low Theta Drag: Hold Day 5–20. ${dte - 21} days before theta cliff begins (${dailyDecayStr}).`,
  };
}

export default function OptionPayoffModal({
  isOpen,
  onClose,
  rec,
  spreadData: propSpreadData,
  initialMode = "SINGLE",
  onPaperBuy,
}: OptionPayoffModalProps) {
  const [mode, setMode] = useState<"SINGLE" | "SPREAD">(initialMode);
  const [sliderPrice, setSliderPrice] = useState<number | null>(null);
  const [hoverPrice, setHoverPrice] = useState<number | null>(null);
  const [boughtToast, setBoughtToast] = useState(false);

  // Sync mode when initialMode changes or modal opens
  useEffect(() => {
    if (isOpen) {
      setMode(initialMode);
      setSliderPrice(null);
      setHoverPrice(null);
      setBoughtToast(false);
    }
  }, [isOpen, initialMode]);

  // Handle ESC key to close
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // Compute or fallback spread data
  const spread = useMemo<SpreadData | null>(() => {
    if (!rec) return null;
    if (propSpreadData) return propSpreadData;
    if (rec.vertical_spread) return rec.vertical_spread;
    return getSpreadAlternative(rec);
  }, [rec, propSpreadData]);

  // Calculations for Single Leg vs Spread
  const calculations = useMemo(() => {
    if (!rec) return null;
    const isCall = rec.option_type === "CALL";
    const contracts = rec.suggested_contracts ?? 0;
    const spot = rec.stock_price;

    if (mode === "SPREAD" && spread) {
      const netDebit = spread.net_debit;
      const totalCost = netDebit * 100 * contracts;
      const maxLoss = spread.max_loss * contracts;
      const maxProfit = spread.max_profit * contracts;
      const breakeven = spread.breakeven;

      const tp1Stock = isCall
        ? +(breakeven + spread.width * 0.4).toFixed(2)
        : +(breakeven - spread.width * 0.4).toFixed(2);
      const tp2Stock = spread.short_strike;

      return {
        isCall,
        contracts,
        spot,
        costPerUnit: netDebit,
        totalInvested: totalCost,
        maxLoss,
        maxProfit,
        isCappedProfit: true,
        breakeven,
        longStrike: spread.long_strike,
        shortStrike: spread.short_strike,
        tp1Stock,
        tp2Stock,
        tp1GainPct: 50,
        tp2GainPct: 100,
        rrRatio: spread.rr_ratio,
        label: spread.spread_label,
      };
    } else {
      const ask = rec.ask;
      const totalCost = ask * 100 * contracts;
      const maxLoss = totalCost;
      const breakeven = isCall ? +(rec.strike + ask).toFixed(2) : +(rec.strike - ask).toFixed(2);

      // TP1 = +75% gain on option contract, TP2 = +150% gain on option contract
      const tp1Stock = isCall
        ? +(rec.strike + ask * 1.75).toFixed(2)
        : +(rec.strike - ask * 1.75).toFixed(2);
      const tp2Stock = isCall
        ? +(rec.strike + ask * 2.50).toFixed(2)
        : +(rec.strike - ask * 2.50).toFixed(2);

      return {
        isCall,
        contracts,
        spot,
        costPerUnit: ask,
        totalInvested: totalCost,
        maxLoss,
        maxProfit: Infinity,
        isCappedProfit: false,
        breakeven,
        longStrike: rec.strike,
        shortStrike: null,
        tp1Stock,
        tp2Stock,
        tp1GainPct: 75,
        tp2GainPct: 150,
        rrRatio: rec.risk_reward_ratio || 2.0,
        label: `${rec.symbol} $${rec.strike} ${rec.option_type} (Single Leg)`,
      };
    }
  }, [rec, mode, spread]);

  // Compute payoff function at expiration for any underlying price S
  const calcPnlAtExp = (price: number) => {
    if (!calculations || !rec) return { dollar: 0, pct: 0 };
    const { isCall, contracts, costPerUnit, totalInvested } = calculations;

    let contractValue = 0;
    if (mode === "SPREAD" && spread) {
      if (isCall) {
        const longVal = Math.max(0, price - spread.long_strike);
        const shortVal = Math.max(0, price - spread.short_strike);
        contractValue = longVal - shortVal;
      } else {
        const longVal = Math.max(0, spread.long_strike - price);
        const shortVal = Math.max(0, spread.short_strike - price);
        contractValue = longVal - shortVal;
      }
    } else {
      if (isCall) {
        contractValue = Math.max(0, price - rec.strike);
      } else {
        contractValue = Math.max(0, rec.strike - price);
      }
    }

    const totalValue = contractValue * 100 * contracts;
    const dollarPnl = totalValue - totalInvested;
    const pctPnl = totalInvested > 0 ? (dollarPnl / totalInvested) * 100 : 0;
    return { dollar: dollarPnl, pct: pctPnl, unitValue: contractValue };
  };

  // SVG Chart Geometry & Points
  const chartData = useMemo(() => {
    if (!calculations || !rec) return null;
    const { spot, breakeven, longStrike, shortStrike, tp1Stock, tp2Stock, maxLoss } = calculations;

    // Determine X-axis min and max
    const keyPrices = [spot, breakeven, longStrike, tp1Stock, tp2Stock];
    if (shortStrike) keyPrices.push(shortStrike);

    const minKey = Math.min(...keyPrices);
    const maxKey = Math.max(...keyPrices);
    const span = Math.max(10, maxKey - minKey);

    const minX = Math.max(0.5, +(minKey - span * 0.35).toFixed(2));
    const maxX = +(maxKey + span * 0.35).toFixed(2);

    const steps = 90;
    const stepSize = (maxX - minX) / steps;
    const points: { price: number; pnl: number; pct: number }[] = [];

    for (let i = 0; i <= steps; i++) {
      const p = +(minX + i * stepSize).toFixed(2);
      const res = calcPnlAtExp(p);
      points.push({ price: p, pnl: res.dollar, pct: res.pct });
    }

    const allPnls = points.map((pt) => pt.pnl);
    let rawMinPnl = Math.min(...allPnls);
    let rawMaxPnl = Math.max(...allPnls);

    // Single leg upside can be huge; clamp display scale so visual is well balanced
    const maxClamp = Math.max(maxLoss * 2.5, 300);
    const displayMaxPnl = Math.min(rawMaxPnl, maxClamp);
    const displayMinPnl = Math.min(-maxLoss * 1.1, rawMinPnl);

    const pnlPadding = (displayMaxPnl - displayMinPnl) * 0.12;
    const minY = displayMinPnl - pnlPadding;
    const maxY = displayMaxPnl + pnlPadding;

    return {
      minX,
      maxX,
      minY,
      maxY,
      points,
      zeroY: 0,
    };
  }, [calculations, rec, mode, spread]);

  // Dimensions
  const svgWidth = 680;
  const svgHeight = 290;
  const padding = { top: 28, right: 30, bottom: 35, left: 62 };
  const plotWidth = svgWidth - padding.left - padding.right;
  const plotHeight = svgHeight - padding.top - padding.bottom;

  const scaleX = (price: number) => {
    if (!chartData) return 0;
    const ratio = (price - chartData.minX) / (chartData.maxX - chartData.minX);
    return padding.left + Math.max(0, Math.min(plotWidth, ratio * plotWidth));
  };

  const scaleY = (pnl: number) => {
    if (!chartData) return 0;
    const ratio = (pnl - chartData.minY) / (chartData.maxY - chartData.minY);
    return padding.top + plotHeight - Math.max(0, Math.min(plotHeight, ratio * plotHeight));
  };

  const activePrice = hoverPrice ?? sliderPrice ?? rec?.stock_price ?? 0;
  const activePnl = calcPnlAtExp(activePrice);
  const spotPrice = rec?.stock_price ?? 0;
  const priceMovePct = spotPrice > 0 ? ((activePrice - spotPrice) / spotPrice) * 100 : 0;

  // Build SVG Paths
  const { pathD, profitPoly, lossPoly, zeroLineY } = useMemo(() => {
    if (!chartData) return { pathD: "", profitPoly: "", lossPoly: "", zeroLineY: 0 };

    const zeroY = scaleY(0);
    const pts = chartData.points.map((pt) => ({
      x: scaleX(pt.price),
      y: scaleY(Math.min(chartData.maxY, Math.max(chartData.minY, pt.pnl))),
      pnl: pt.pnl,
    }));

    let d = "";
    pts.forEach((p, idx) => {
      d += idx === 0 ? `M ${p.x.toFixed(1)} ${p.y.toFixed(1)}` : ` L ${p.x.toFixed(1)} ${p.y.toFixed(1)}`;
    });

    // Profit area: from line to zeroY where pnl >= 0
    let profitD = `M ${pts[0].x.toFixed(1)} ${zeroY.toFixed(1)}`;
    pts.forEach((p) => {
      const yClamped = p.pnl >= 0 ? p.y : zeroY;
      profitD += ` L ${p.x.toFixed(1)} ${yClamped.toFixed(1)}`;
    });
    profitD += ` L ${pts[pts.length - 1].x.toFixed(1)} ${zeroY.toFixed(1)} Z`;

    // Loss area: from line to zeroY where pnl < 0
    let lossD = `M ${pts[0].x.toFixed(1)} ${zeroY.toFixed(1)}`;
    pts.forEach((p) => {
      const yClamped = p.pnl < 0 ? p.y : zeroY;
      lossD += ` L ${p.x.toFixed(1)} ${yClamped.toFixed(1)}`;
    });
    lossD += ` L ${pts[pts.length - 1].x.toFixed(1)} ${zeroY.toFixed(1)} Z`;

    return { pathD: d, profitPoly: profitD, lossPoly: lossD, zeroLineY: zeroY };
  }, [chartData]);

  // Handle Paper Buy within modal
  const handlePaperBuySubmit = () => {
    if (!rec || !calculations || !onPaperBuy) return;
    if (calculations.contracts <= 0) {
      alert("Cannot execute paper order: 0 contracts qualified (trade cost exceeds risk budget).");
      return;
    }
    if (mode === "SPREAD" && spread) {
      onPaperBuy({
        symbol: rec.symbol,
        contract: `${rec.symbol} ${spread.spread_type} ${spread.long_strike}/${spread.short_strike}`,
        strike: spread.long_strike,
        option_type: rec.option_type,
        expiration: rec.expiration,
        dte: rec.dte,
        ask: spread.net_debit,
        net_debit: spread.net_debit,
        isSpread: true,
        spread_type: spread.spread_type,
        suggested_contracts: calculations.contracts,
        strategy_label: spread.spread_label,
        notes: `Defined-Risk Vertical Spread (${spread.spread_label}): Long $${spread.long_strike} / Short $${spread.short_strike}`,
      });
    } else {
      onPaperBuy(rec);
    }
    setBoughtToast(true);
    setTimeout(() => setBoughtToast(false), 2500);
  };

  if (!isOpen || !rec || !calculations || !chartData) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      {/* Modal Dialog Card */}
      <div
        className="relative flex flex-col w-full max-w-4xl max-h-[92vh] overflow-hidden rounded-2xl border border-slate-800 bg-[#080d19] shadow-2xl text-slate-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* ========================================================= */}
        {/* 1. MODAL HEADER                                           */}
        {/* ========================================================= */}
        <div className="flex items-center justify-between border-b border-slate-800/80 bg-[#0a1120] px-5 py-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center space-x-2">
              <span className="text-xl font-black text-white">{rec.symbol}</span>
              <span className="text-xs text-slate-400 font-medium truncate max-w-[140px] sm:max-w-[200px]">
                {rec.name}
              </span>
            </div>

            <div className="flex items-center space-x-1.5">
              <span
                className={`rounded px-2 py-0.5 text-xs font-black ${
                  calculations.isCall
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                    : "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                }`}
              >
                {rec.option_type}
              </span>
              <span className="text-xs font-mono font-bold text-slate-300">
                Spot: ${rec.stock_price.toFixed(2)}
              </span>
              <span className="rounded bg-slate-800/80 px-2 py-0.5 text-[11px] font-mono text-cyan-300 border border-slate-700/60">
                Exp: {rec.expiration} ({rec.dte}d DTE)
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {/* Mode Switcher inside modal: Single vs Spread */}
            <div className="flex items-center rounded-lg border border-slate-700/80 bg-[#0d1629] p-0.5 text-xs">
              <button
                type="button"
                onClick={() => setMode("SINGLE")}
                className={`rounded-md px-2.5 py-1 font-semibold transition ${
                  mode === "SINGLE"
                    ? "bg-cyan-500 text-slate-950 shadow-sm"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                Single Leg
              </button>
              <button
                type="button"
                onClick={() => setMode("SPREAD")}
                className={`rounded-md px-2.5 py-1 font-semibold transition ${
                  mode === "SPREAD"
                    ? "bg-cyan-500 text-slate-950 shadow-sm"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                Vertical Spread
              </button>
            </div>

            <button
              onClick={onClose}
              className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition"
              title="Close modal (Esc)"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Modal Scrollable Body */}
        <div className="overflow-y-auto px-5 py-4 space-y-4 scrollbar-thin">
          {/* ========================================================= */}
          {/* 2. STRATEGY SUMMARY KPI BAR                               */}
          {/* ========================================================= */}
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 md:grid-cols-6 rounded-xl border border-slate-800 bg-[#0c1424] p-3 text-xs">
            <div>
              <div className="text-[10px] uppercase font-semibold text-slate-400">Entry Strike(s)</div>
              <div className="mt-0.5 text-sm font-bold text-white font-mono">
                {mode === "SPREAD" && spread ? (
                  <span>
                    ${spread.long_strike} / ${spread.short_strike}
                  </span>
                ) : (
                  <span>${rec.strike.toFixed(2)}</span>
                )}
              </div>
            </div>

            <div>
              <div className="text-[10px] uppercase font-semibold text-slate-400">
                {mode === "SPREAD" ? "Net Debit" : "Contract Cost"}
              </div>
              <div className="mt-0.5 text-sm font-bold text-emerald-400 font-mono">
                ${calculations.costPerUnit.toFixed(2)}{" "}
                <span className="text-[10px] text-slate-500">(${calculations.totalInvested.toFixed(0)})</span>
              </div>
            </div>

            <div>
              <div className="text-[10px] uppercase font-semibold text-slate-400">Breakeven</div>
              <div className="mt-0.5 text-sm font-bold text-amber-300 font-mono">
                ${calculations.breakeven.toFixed(2)}
              </div>
            </div>

            <div>
              <div className="text-[10px] uppercase font-semibold text-slate-400">Max Loss</div>
              <div className="mt-0.5 text-sm font-bold text-rose-400 font-mono">
                -${calculations.maxLoss.toFixed(0)} <span className="text-[10px] text-slate-500">(-100%)</span>
              </div>
            </div>

            <div>
              <div className="text-[10px] uppercase font-semibold text-slate-400">Max Upside</div>
              <div className="mt-0.5 text-sm font-bold text-emerald-300 font-mono">
                {calculations.isCappedProfit ? `+$${calculations.maxProfit.toFixed(0)}` : "Unlimited ∞"}
              </div>
            </div>

            <div>
              <div className="text-[10px] uppercase font-semibold text-slate-400">Risk/Reward</div>
              <div className="mt-0.5 text-sm font-bold text-cyan-300 font-mono">
                {calculations.rrRatio}:1
              </div>
            </div>
          </div>

          {/* ========================================================= */}
          {/* 3. DYNAMIC INSPECT CALLOUT STRIP                          */}
          {/* ========================================================= */}
          <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-800/80 bg-[#0e1628] px-3.5 py-2 text-xs">
            <div className="flex items-center space-x-2">
              <span className="text-slate-400 font-medium">Underlying Price at Exp:</span>
              <span className="text-base font-black text-white font-mono">
                ${activePrice.toFixed(2)}
              </span>
              <span
                className={`font-mono text-xs font-bold ${
                  priceMovePct >= 0 ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                ({priceMovePct >= 0 ? "+" : ""}{priceMovePct.toFixed(2)}% from spot)
              </span>
            </div>

            <div className="flex items-center space-x-3 font-mono">
              <div className="flex items-center space-x-1.5">
                <span className="text-slate-400">Theoretical P&L:</span>
                <span
                  className={`text-base font-black ${
                    activePnl.dollar > 0
                      ? "text-emerald-400"
                      : activePnl.dollar < 0
                      ? "text-rose-400"
                      : "text-amber-300"
                  }`}
                >
                  {activePnl.dollar >= 0 ? "+" : ""}${activePnl.dollar.toFixed(0)} ({activePnl.pct >= 0 ? "+" : ""}
                  {activePnl.pct.toFixed(1)}%)
                </span>
              </div>

              <span
                className={`rounded px-2 py-0.5 text-[10px] font-black uppercase ${
                  activePnl.dollar > 0
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                    : activePnl.dollar < 0
                    ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                    : "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                }`}
              >
                {activePnl.dollar > 0 ? "PROFIT ZONE" : activePnl.dollar < 0 ? "LOSS ZONE" : "BREAKEVEN"}
              </span>
            </div>
          </div>

          {/* ========================================================= */}
          {/* 4. INTERACTIVE SVG PAYOFF CURVE                           */}
          {/* ========================================================= */}
          <div className="relative rounded-xl border border-slate-800 bg-[#070b14] p-2 sm:p-3 overflow-hidden shadow-inner">
            <svg
              viewBox={`0 0 ${svgWidth} ${svgHeight}`}
              className="w-full h-auto cursor-crosshair select-none"
              onMouseMove={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                const xInSvg = ((e.clientX - rect.left) / rect.width) * svgWidth;
                if (xInSvg >= padding.left && xInSvg <= padding.left + plotWidth) {
                  const ratio = (xInSvg - padding.left) / plotWidth;
                  const price = chartData.minX + ratio * (chartData.maxX - chartData.minX);
                  setHoverPrice(+price.toFixed(2));
                }
              }}
              onMouseLeave={() => setHoverPrice(null)}
            >
              <defs>
                <linearGradient id="profitGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#10b981" stopOpacity="0.30" />
                  <stop offset="100%" stopColor="#10b981" stopOpacity="0.02" />
                </linearGradient>
                <linearGradient id="lossGrad" x1="0%" y1="100%" x2="0%" y2="0%">
                  <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.25" />
                  <stop offset="100%" stopColor="#f43f5e" stopOpacity="0.02" />
                </linearGradient>
              </defs>

              {/* Grid Lines */}
              <line
                x1={padding.left}
                y1={zeroLineY}
                x2={padding.left + plotWidth}
                y2={zeroLineY}
                stroke="#334155"
                strokeWidth="1.2"
                strokeDasharray="4 4"
              />

              {/* Shaded Profit and Loss Polygons */}
              <path d={profitPoly} fill="url(#profitGrad)" />
              <path d={lossPoly} fill="url(#lossGrad)" />

              {/* Zero P&L reference text */}
              <text
                x={padding.left - 8}
                y={zeroLineY + 3.5}
                textAnchor="end"
                className="fill-slate-400 font-mono text-[9px] font-bold"
              >
                $0
              </text>

              {/* Max Loss reference line */}
              <line
                x1={padding.left}
                y1={scaleY(-calculations.maxLoss)}
                x2={padding.left + plotWidth}
                y2={scaleY(-calculations.maxLoss)}
                stroke="#f43f5e"
                strokeOpacity="0.35"
                strokeWidth="1"
                strokeDasharray="2 2"
              />
              <text
                x={padding.left - 8}
                y={scaleY(-calculations.maxLoss) + 3.5}
                textAnchor="end"
                className="fill-rose-400 font-mono text-[9px] font-bold"
              >
                -${calculations.maxLoss.toFixed(0)}
              </text>

              {/* Main Payoff Line Curve */}
              <path
                d={pathD}
                fill="none"
                stroke="#06b6d4"
                strokeWidth="2.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              />

              {/* Current Spot Line */}
              <line
                x1={scaleX(calculations.spot)}
                y1={padding.top}
                x2={scaleX(calculations.spot)}
                y2={padding.top + plotHeight}
                stroke="#38bdf8"
                strokeWidth="1.5"
                strokeDasharray="3 3"
              />
              <text
                x={scaleX(calculations.spot)}
                y={padding.top - 8}
                textAnchor="middle"
                className="fill-sky-400 font-mono text-[9px] font-black"
              >
                Spot ${calculations.spot.toFixed(2)}
              </text>

              {/* Breakeven Line */}
              <line
                x1={scaleX(calculations.breakeven)}
                y1={padding.top}
                x2={scaleX(calculations.breakeven)}
                y2={padding.top + plotHeight}
                stroke="#f59e0b"
                strokeWidth="1.5"
                strokeDasharray="2 3"
              />
              <text
                x={scaleX(calculations.breakeven)}
                y={padding.top - 8}
                textAnchor="middle"
                className="fill-amber-400 font-mono text-[9px] font-black"
              >
                BE ${calculations.breakeven.toFixed(2)}
              </text>

              {/* Target 1 Marker Line */}
              <line
                x1={scaleX(calculations.tp1Stock)}
                y1={padding.top}
                x2={scaleX(calculations.tp1Stock)}
                y2={padding.top + plotHeight}
                stroke="#10b981"
                strokeWidth="1.2"
                strokeDasharray="2 2"
                strokeOpacity="0.6"
              />
              <text
                x={scaleX(calculations.tp1Stock)}
                y={padding.top - 8}
                textAnchor="middle"
                className="fill-emerald-400 font-mono text-[8px] font-bold"
              >
                TP1 (+{calculations.tp1GainPct}%)
              </text>

              {/* Target 2 Marker Line */}
              <line
                x1={scaleX(calculations.tp2Stock)}
                y1={padding.top}
                x2={scaleX(calculations.tp2Stock)}
                y2={padding.top + plotHeight}
                stroke="#10b981"
                strokeWidth="1.2"
                strokeDasharray="2 2"
                strokeOpacity="0.6"
              />
              <text
                x={scaleX(calculations.tp2Stock)}
                y={padding.top - 8}
                textAnchor="middle"
                className="fill-emerald-400 font-mono text-[8px] font-bold"
              >
                TP2 (+{calculations.tp2GainPct}%)
              </text>

              {/* Active Hover / Slider Cursor Indicator */}
              {activePrice >= chartData.minX && activePrice <= chartData.maxX && (
                <g>
                  <line
                    x1={scaleX(activePrice)}
                    y1={padding.top}
                    x2={scaleX(activePrice)}
                    y2={padding.top + plotHeight}
                    stroke="#ffffff"
                    strokeWidth="1.2"
                    strokeDasharray="2 2"
                  />
                  <circle
                    cx={scaleX(activePrice)}
                    cy={scaleY(activePnl.dollar)}
                    r="5"
                    fill={activePnl.dollar >= 0 ? "#10b981" : "#f43f5e"}
                    stroke="#ffffff"
                    strokeWidth="2"
                    className="drop-shadow-md"
                  />
                </g>
              )}

              {/* X-axis Ticks & Labels */}
              <line
                x1={padding.left}
                y1={padding.top + plotHeight}
                x2={padding.left + plotWidth}
                y2={padding.top + plotHeight}
                stroke="#334155"
                strokeWidth="1"
              />
              {[chartData.minX, calculations.spot, calculations.breakeven, chartData.maxX].map(
                (val, idx) => (
                  <text
                    key={idx}
                    x={scaleX(val)}
                    y={padding.top + plotHeight + 15}
                    textAnchor="middle"
                    className="fill-slate-400 font-mono text-[9px]"
                  >
                    ${val.toFixed(1)}
                  </text>
                )
              )}
            </svg>
          </div>

          {/* ========================================================= */}
          {/* 5. INTERACTIVE PRICE SLIDER & QUICK SCENARIOS            */}
          {/* ========================================================= */}
          <div className="space-y-2 rounded-xl border border-slate-800/80 bg-[#0a1120] p-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-slate-400 font-medium flex items-center space-x-1.5">
                <Sliders className="h-3.5 w-3.5 text-cyan-400" />
                <span>Simulate Underlying Stock Price:</span>
              </span>
              <span className="font-mono font-bold text-white">${activePrice.toFixed(2)}</span>
            </div>

            <input
              type="range"
              min={chartData.minX}
              max={chartData.maxX}
              step={0.1}
              value={activePrice}
              onChange={(e) => {
                setSliderPrice(parseFloat(e.target.value));
                setHoverPrice(null);
              }}
              className="w-full accent-cyan-400 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
            />

            {/* Quick Scenario Preset Buttons */}
            <div className="flex flex-wrap items-center gap-1.5 pt-1">
              <span className="text-[10px] text-slate-500 font-semibold mr-1 uppercase">
                Jump to:
              </span>
              <button
                type="button"
                onClick={() => setSliderPrice(calculations.spot)}
                className="rounded-md border border-slate-800 bg-[#0d1424] px-2 py-0.5 text-[11px] font-mono text-sky-300 hover:border-sky-500/40"
              >
                Current Spot (${calculations.spot.toFixed(2)})
              </button>
              <button
                type="button"
                onClick={() => setSliderPrice(calculations.breakeven)}
                className="rounded-md border border-slate-800 bg-[#0d1424] px-2 py-0.5 text-[11px] font-mono text-amber-300 hover:border-amber-500/40"
              >
                Breakeven (${calculations.breakeven.toFixed(2)})
              </button>
              <button
                type="button"
                onClick={() => setSliderPrice(calculations.tp1Stock)}
                className="rounded-md border border-slate-800 bg-[#0d1424] px-2 py-0.5 text-[11px] font-mono text-emerald-300 hover:border-emerald-500/40"
              >
                Target 1 (${calculations.tp1Stock.toFixed(2)})
              </button>
              <button
                type="button"
                onClick={() => setSliderPrice(calculations.tp2Stock)}
                className="rounded-md border border-slate-800 bg-[#0d1424] px-2 py-0.5 text-[11px] font-mono text-emerald-300 hover:border-emerald-500/40"
              >
                Target 2 (${calculations.tp2Stock.toFixed(2)})
              </button>
              <button
                type="button"
                onClick={() => setSliderPrice(+(calculations.spot * 1.05).toFixed(2))}
                className="rounded-md border border-slate-800 bg-[#0d1424] px-2 py-0.5 text-[11px] font-mono text-cyan-300 hover:border-cyan-500/40"
              >
                +5% Move
              </button>
              <button
                type="button"
                onClick={() => setSliderPrice(+(calculations.spot * 0.95).toFixed(2))}
                className="rounded-md border border-slate-800 bg-[#0d1424] px-2 py-0.5 text-[11px] font-mono text-rose-300 hover:border-rose-500/40"
              >
                -5% Move
              </button>
            </div>
          </div>

          {/* Execution Reality & Theoretical Model Disclaimer */}
          <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-slate-800 bg-[#070b14] px-4 py-2 text-[11px] text-slate-400">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-slate-300 font-bold">Execution Modeling:</span>
              <span>Ask Entry: ${rec.ask.toFixed(2)} | Bid Exit: ${rec.bid.toFixed(2)} | Spread Friction: -${(rec.ask - rec.bid).toFixed(2)} (-{rec.ask > 0 ? (((rec.ask - rec.bid) / rec.ask) * 100).toFixed(1) : 0}%)</span>
            </div>
            <div className="text-amber-400/90 text-[10px] font-medium">
              Midpoint fills not guaranteed. Broker fees/slippage excluded. Win POP is a Black-Scholes theoretical estimate.
            </div>
          </div>

          {/* ========================================================= */}
          {/* 6. TARGET MILESTONES TABLE                                */}
          {/* ========================================================= */}
          <div className="overflow-hidden rounded-xl border border-slate-800 bg-[#0a1120]">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-800/80 bg-[#0d1629] text-[10px] font-bold uppercase tracking-wider text-slate-400">
                <tr>
                  <th className="px-3.5 py-2">Milestone Level</th>
                  <th className="px-3 py-2 text-right">Stock Price</th>
                  <th className="px-3 py-2 text-right">Contract Value</th>
                  <th className="px-3 py-2 text-right">Expiration P&L</th>
                  <th className="px-3.5 py-2 text-right">Return %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                <tr className="hover:bg-slate-800/30">
                  <td className="px-3.5 py-2 text-rose-400 font-semibold">Max Loss (Zero Value)</td>
                  <td className="px-3 py-2 text-right text-slate-400">
                    {calculations.isCall ? `< $${calculations.longStrike}` : `> $${calculations.longStrike}`}
                  </td>
                  <td className="px-3 py-2 text-right text-slate-400">$0.00</td>
                  <td className="px-3 py-2 text-right text-rose-400">-${calculations.maxLoss.toFixed(0)}</td>
                  <td className="px-3.5 py-2 text-right text-rose-400">-100.0%</td>
                </tr>
                <tr className="hover:bg-slate-800/30">
                  <td className="px-3.5 py-2 text-amber-300 font-semibold">Breakeven Price</td>
                  <td className="px-3 py-2 text-right text-white">${calculations.breakeven.toFixed(2)}</td>
                  <td className="px-3 py-2 text-right text-slate-300">${calculations.costPerUnit.toFixed(2)}</td>
                  <td className="px-3 py-2 text-right text-amber-300">$0.00</td>
                  <td className="px-3.5 py-2 text-right text-amber-300">0.0%</td>
                </tr>
                <tr className="hover:bg-slate-800/30">
                  <td className="px-3.5 py-2 text-emerald-400 font-semibold">Target 1 (+{calculations.tp1GainPct}%)</td>
                  <td className="px-3 py-2 text-right text-white">${calculations.tp1Stock.toFixed(2)}</td>
                  <td className="px-3 py-2 text-right text-emerald-300">
                    ${(calculations.costPerUnit * (1 + calculations.tp1GainPct / 100)).toFixed(2)}
                  </td>
                  <td className="px-3 py-2 text-right text-emerald-400">
                    +${(calculations.totalInvested * (calculations.tp1GainPct / 100)).toFixed(0)}
                  </td>
                  <td className="px-3.5 py-2 text-right text-emerald-400">+{calculations.tp1GainPct}%</td>
                </tr>
                <tr className="hover:bg-slate-800/30">
                  <td className="px-3.5 py-2 text-emerald-300 font-semibold">Target 2 (+{calculations.tp2GainPct}%)</td>
                  <td className="px-3 py-2 text-right text-white">${calculations.tp2Stock.toFixed(2)}</td>
                  <td className="px-3 py-2 text-right text-emerald-300">
                    ${(calculations.costPerUnit * (1 + calculations.tp2GainPct / 100)).toFixed(2)}
                  </td>
                  <td className="px-3 py-2 text-right text-emerald-300">
                    +${(calculations.totalInvested * (calculations.tp2GainPct / 100)).toFixed(0)}
                  </td>
                  <td className="px-3.5 py-2 text-right text-emerald-300">+{calculations.tp2GainPct}%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* ========================================================= */}
        {/* 7. MODAL FOOTER & PAPER TRADING CTA                       */}
        {/* ========================================================= */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-800/80 bg-[#0a1120] px-5 py-3.5">
          <div className="flex items-center space-x-2 text-xs text-slate-400">
            <Info className="h-4 w-4 text-cyan-400 shrink-0" />
            <span>
              {mode === "SPREAD"
                ? "Defined-Risk Spread caps both max profit and max loss to provide high risk-adjusted efficiency."
                : "Single-leg option offers uncapped upside with strict capital risk bounded to premium paid."}
            </span>
          </div>

          <div className="flex items-center space-x-2.5">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-slate-700 bg-[#0f172a] px-3.5 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-800 hover:text-white transition"
            >
              Close
            </button>

            {onPaperBuy && (
              <button
                type="button"
                onClick={handlePaperBuySubmit}
                disabled={calculations.contracts <= 0}
                className={`flex items-center space-x-1.5 rounded-lg px-4 py-2 text-xs font-black shadow-md transition active:scale-95 ${
                  calculations.contracts <= 0
                    ? "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700"
                    : boughtToast
                    ? "bg-emerald-400 text-slate-950"
                    : "bg-emerald-500 hover:bg-emerald-400 text-slate-950 shadow-emerald-500/20"
                }`}
              >
                <Wallet className="h-4 w-4 text-slate-950" />
                <span>
                  {calculations.contracts <= 0
                    ? "Exceeds Risk Budget (0x)"
                    : boughtToast
                    ? "Added to Paper Portfolio!"
                    : `Paper Buy (${calculations.contracts}x @ $${calculations.costPerUnit.toFixed(2)})`}
                </span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
