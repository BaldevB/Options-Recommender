"use client";

import React, { useMemo } from "react";
import Link from "next/link";
import {
  X,
  TrendingUp,
  TrendingDown,
  Target,
  Wallet,
  Zap,
  Trophy,
  ShieldCheck,
  Flame,
  Activity,
  Sparkles,
  Layers,
  ExternalLink,
  Check,
  Compass,
} from "lucide-react";
import { StockRecommendationItem } from "./StockCard";

interface StockComparisonDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  stocks: StockRecommendationItem[];
  onRemoveStock: (symbol: string) => void;
  onAnalyzeStock: (stock: StockRecommendationItem) => void;
  onPaperBuyStock: (stock: StockRecommendationItem) => void;
}

export default function StockComparisonDrawer({
  isOpen,
  onClose,
  stocks,
  onRemoveStock,
  onAnalyzeStock,
  onPaperBuyStock,
}: StockComparisonDrawerProps) {
  if (!isOpen) return null;

  // Compute head-to-head winners when 2 or more stocks are compared
  const topScoreWinner = useMemo(() => {
    if (stocks.length < 2) return null;
    let maxVal = -Infinity;
    let winner: string | null = null;
    let tie = false;
    for (const s of stocks) {
      const v = s.score;
      if (v > maxVal) {
        maxVal = v;
        winner = s.symbol;
        tie = false;
      } else if (v === maxVal) {
        tie = true;
      }
    }
    return tie ? null : winner;
  }, [stocks]);

  const topRSWinner = useMemo(() => {
    if (stocks.length < 2) return null;
    let maxVal = -Infinity;
    let winner: string | null = null;
    let tie = false;
    for (const s of stocks) {
      const v = s.relative_strength_score ?? 0;
      if (v > maxVal) {
        maxVal = v;
        winner = s.symbol;
        tie = false;
      } else if (v === maxVal) {
        tie = true;
      }
    }
    return tie ? null : winner;
  }, [stocks]);

  const topROCWinner = useMemo(() => {
    if (stocks.length < 2) return null;
    let maxVal = -Infinity;
    let winner: string | null = null;
    let tie = false;
    for (const s of stocks) {
      const v = s.roc_3d ?? -999;
      if (v > maxVal) {
        maxVal = v;
        winner = s.symbol;
        tie = false;
      } else if (v === maxVal) {
        tie = true;
      }
    }
    return tie ? null : winner;
  }, [stocks]);

  const topRRWinner = useMemo(() => {
    if (stocks.length < 2) return null;
    let maxVal = -Infinity;
    let winner: string | null = null;
    let tie = false;
    for (const s of stocks) {
      const v = s.trade_plan?.risk_reward_ratio ?? 0;
      if (v > maxVal) {
        maxVal = v;
        winner = s.symbol;
        tie = false;
      } else if (v === maxVal) {
        tie = true;
      }
    }
    return tie ? null : winner;
  }, [stocks]);

  const topTargetWinner = useMemo(() => {
    if (stocks.length < 2) return null;
    let maxVal = -Infinity;
    let winner: string | null = null;
    let tie = false;
    for (const s of stocks) {
      const v = s.trade_plan?.tp1_pct ?? 0;
      if (v > maxVal) {
        maxVal = v;
        winner = s.symbol;
        tie = false;
      } else if (v === maxVal) {
        tie = true;
      }
    }
    return tie ? null : winner;
  }, [stocks]);

  const topTarget2Winner = useMemo(() => {
    if (stocks.length < 2) return null;
    let maxVal = -Infinity;
    let winner: string | null = null;
    let tie = false;
    for (const s of stocks) {
      const v = s.trade_plan?.tp2_pct ?? 0;
      if (v > maxVal) {
        maxVal = v;
        winner = s.symbol;
        tie = false;
      } else if (v === maxVal) {
        tie = true;
      }
    }
    return tie ? null : winner;
  }, [stocks]);

  const safestRiskWinner = useMemo(() => {
    if (stocks.length < 2) return null;
    let minVal = Infinity;
    let winner: string | null = null;
    let tie = false;
    for (const s of stocks) {
      const v = s.trade_plan?.invalidation_pct ?? 999;
      if (v > 0 && v < minVal) {
        minVal = v;
        winner = s.symbol;
        tie = false;
      } else if (v === minVal) {
        tie = true;
      }
    }
    return tie ? null : winner;
  }, [stocks]);

  const topRVOLWinner = useMemo(() => {
    if (stocks.length < 2) return null;
    let maxVal = -Infinity;
    let winner: string | null = null;
    let tie = false;
    for (const s of stocks) {
      const v = s.short_term_rvol ?? s.volume_ratio ?? 0;
      if (v > maxVal) {
        maxVal = v;
        winner = s.symbol;
        tie = false;
      } else if (v === maxVal) {
        tie = true;
      }
    }
    return tie ? null : winner;
  }, [stocks]);

  const renderWinnerBadge = (label: string = "Best") => (
    <span className="inline-flex items-center gap-0.5 px-1.5 py-0.2 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-[0_0_6px_rgba(245,158,11,0.25)] ml-1">
      <Trophy className="w-2.5 h-2.5 text-amber-400" />
      {label}
    </span>
  );

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/80 backdrop-blur-md flex items-end sm:items-center justify-center p-0 sm:p-4 animate-in fade-in duration-200">
      <div className="relative w-full max-w-5xl bg-[#090e1c] border border-slate-700/80 rounded-t-2xl sm:rounded-2xl shadow-2xl flex flex-col max-h-[92vh] overflow-hidden">
        {/* Drawer Header */}
        <div className="p-4 sm:p-5 border-b border-slate-800 bg-[#070b14] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-gradient-to-br from-cyan-500/20 to-emerald-500/20 border border-cyan-500/40 text-cyan-400 shadow-[0_0_12px_rgba(6,182,212,0.25)]">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base sm:text-lg font-black tracking-tight text-slate-100">
                  Head-to-Head Stock Comparison
                </h2>
                <span className="text-xs px-2 py-0.5 rounded-full font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  {stocks.length} of 3
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Comparing algorithmic trade plans, Minervini stage 2 status, momentum velocity &amp; risk/reward
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-100 border border-slate-700 transition-colors"
              title="Close comparison drawer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="overflow-y-auto p-4 sm:p-6 space-y-6 flex-1">
          {stocks.length === 0 ? (
            <div className="py-16 text-center">
              <Compass className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <h3 className="text-base font-bold text-slate-300">No stocks selected</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
                Select up to 3 stocks using the comparison checkboxes on the cards or screener table to compare head-to-head.
              </p>
            </div>
          ) : (
            <>
              {/* Top Overview Cards Grid */}
              <div
                className={`grid gap-4 ${
                  stocks.length === 1
                    ? "grid-cols-1 max-w-md mx-auto"
                    : stocks.length === 2
                    ? "grid-cols-1 sm:grid-cols-2"
                    : "grid-cols-1 sm:grid-cols-3"
                }`}
              >
                {stocks.map((stock) => {
                  const isPositive = stock.change_pct >= 0;
                  const isTopScore = topScoreWinner === stock.symbol;

                  return (
                    <div
                      key={stock.symbol}
                      className={`relative rounded-xl border p-4 bg-[#0d1527] transition-all flex flex-col justify-between ${
                        isTopScore
                          ? "border-amber-500/50 shadow-[0_0_20px_rgba(245,158,11,0.15)] ring-1 ring-amber-500/30"
                          : "border-slate-800"
                      }`}
                    >
                      {/* Top Header of Card */}
                      <div>
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex flex-col">
                            <div className="flex items-center gap-1.5 flex-wrap">
                              <span className="text-lg font-black font-mono tracking-wider text-slate-100">
                                {stock.symbol}
                              </span>
                              {isTopScore && renderWinnerBadge("Leader")}
                            </div>
                            <span
                              className="text-[11px] text-slate-400 line-clamp-1 max-w-[160px]"
                              title={stock.name}
                            >
                              {stock.name}
                            </span>
                          </div>

                          <button
                            type="button"
                            onClick={() => onRemoveStock(stock.symbol)}
                            className="p-1 rounded-md text-slate-500 hover:text-slate-300 hover:bg-slate-800/80 transition-colors"
                            title="Remove from comparison"
                          >
                            <X className="w-3.5 h-3.5" />
                          </button>
                        </div>

                        {/* Price & Change */}
                        <div className="mt-2.5 flex items-baseline justify-between border-b border-slate-800/80 pb-2.5">
                          <span className="text-xl font-mono font-bold text-slate-100">
                            ${stock.price > 0 ? stock.price.toFixed(2) : stock.trade_plan?.current_price?.toFixed(2) ?? "—"}
                          </span>
                          <span
                            className={`inline-flex items-center text-xs font-mono font-semibold ${
                              isPositive ? "text-emerald-400" : "text-rose-400"
                            }`}
                          >
                            {isPositive ? (
                              <TrendingUp className="w-3.5 h-3.5 mr-0.5 inline" />
                            ) : (
                              <TrendingDown className="w-3.5 h-3.5 mr-0.5 inline" />
                            )}
                            {isPositive ? "+" : ""}
                            {stock.change_pct.toFixed(2)}%
                          </span>
                        </div>

                        {/* Badges strip */}
                        <div className="flex flex-wrap items-center gap-1.5 mt-2.5">
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                            {stock.action}
                          </span>
                          <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 border border-slate-700/80">
                            {stock.sector}
                          </span>
                          {stock.strategy_tag && (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-950/60 text-cyan-300 border border-cyan-800/60">
                              {stock.strategy_tag.replace(/_/g, " ")}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Card Action Buttons Footer */}
                      <div className="mt-4 pt-3 border-t border-slate-800/80 grid grid-cols-3 gap-1.5">
                        <button
                          type="button"
                          onClick={() => {
                            onAnalyzeStock(stock);
                          }}
                          className="inline-flex items-center justify-center gap-1 py-1.5 px-2 rounded-lg text-[11px] font-semibold bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-cyan-500/30 transition-colors"
                          title="View Chart & Deep Dive"
                        >
                          <Target className="w-3 h-3 text-cyan-400" />
                          <span>Analyze</span>
                        </button>

                        <button
                          type="button"
                          onClick={() => {
                            onPaperBuyStock(stock);
                          }}
                          className="inline-flex items-center justify-center gap-1 py-1.5 px-2 rounded-lg text-[11px] font-semibold bg-emerald-600/25 hover:bg-emerald-600/40 text-emerald-300 border border-emerald-500/40 transition-colors shadow-sm"
                          title="Simulate paper buy"
                        >
                          <Wallet className="w-3 h-3 text-emerald-400" />
                          <span>Paper Buy</span>
                        </button>

                        <Link
                          href={`/?ticker=${encodeURIComponent(stock.symbol)}&action=options`}
                          className="inline-flex items-center justify-center gap-1 py-1.5 px-2 rounded-lg text-[11px] font-semibold bg-cyan-600/20 hover:bg-cyan-600/35 text-cyan-300 border border-cyan-500/40 transition-colors"
                          title={`Find options for ${stock.symbol}`}
                        >
                          <Zap className="w-3 h-3 text-cyan-400" />
                          <span>Options</span>
                        </Link>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Comparative Matrix Table */}
              <div className="rounded-xl border border-slate-800 bg-[#0b1222] overflow-hidden shadow-lg">
                <div className="px-4 py-3 bg-[#080d1a] border-b border-slate-800 flex items-center justify-between">
                  <h3 className="text-xs uppercase font-bold text-slate-300 tracking-wider flex items-center gap-2">
                    <Activity className="w-4 h-4 text-cyan-400" />
                    Quantitative &amp; Technical Factor Matrix
                  </h3>
                  <span className="text-[11px] text-slate-500 font-mono">
                    ★ Top metrics highlighted
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs text-slate-300 divide-y divide-slate-800/70">
                    <thead>
                      <tr className="bg-[#080d19]/80 text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
                        <th className="py-2.5 px-4 w-48">Metric</th>
                        {stocks.map((s) => (
                          <th key={s.symbol} className="py-2.5 px-4 font-mono font-bold text-slate-200">
                            {s.symbol}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono">
                      {/* Overall Quant Score */}
                      <tr className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-4 text-slate-400 font-sans font-semibold">
                          Quant Score
                        </td>
                        {stocks.map((s) => (
                          <td key={s.symbol} className="py-2.5 px-4 font-bold text-cyan-300">
                            {s.score.toFixed(1)} / 100
                            {topScoreWinner === s.symbol && renderWinnerBadge("Top")}
                          </td>
                        ))}
                      </tr>

                      {/* Relative Strength (0-99) */}
                      <tr className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-4 text-slate-400 font-sans font-semibold">
                          Relative Strength (RS 0-99)
                        </td>
                        {stocks.map((s) => (
                          <td key={s.symbol} className="py-2.5 px-4 font-bold text-slate-100">
                            {s.relative_strength_score !== undefined
                              ? Math.round(s.relative_strength_score)
                              : "—"}
                            {topRSWinner === s.symbol && renderWinnerBadge("RS Leader")}
                          </td>
                        ))}
                      </tr>

                      {/* Minervini Stage 2 */}
                      <tr className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-4 text-slate-400 font-sans font-semibold">
                          Minervini Stage 2 Template
                        </td>
                        {stocks.map((s) => (
                          <td key={s.symbol} className="py-2.5 px-4">
                            {s.is_stage_2 ? (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
                                🔥 Stage 2 Confirmed
                              </span>
                            ) : (
                              <span className="text-slate-500">Not Aligned</span>
                            )}
                          </td>
                        ))}
                      </tr>

                      {/* VCP Squeeze */}
                      <tr className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-4 text-slate-400 font-sans font-semibold">
                          VCP Squeeze &amp; Tightness
                        </td>
                        {stocks.map((s) => (
                          <td key={s.symbol} className="py-2.5 px-4">
                            {s.is_vcp_squeeze ? (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/40">
                                ⚡ Squeezing ({Math.round(s.consolidation_tightness ?? 50)}/100)
                              </span>
                            ) : (
                              <span className="text-slate-400">
                                Tightness: {Math.round(s.consolidation_tightness ?? 50)}/100
                              </span>
                            )}
                          </td>
                        ))}
                      </tr>

                      {/* 3D Price Velocity (ROC %) */}
                      <tr className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-4 text-slate-400 font-sans font-semibold">
                          3-Day Velocity (ROC %)
                        </td>
                        {stocks.map((s) => {
                          const v = s.roc_3d;
                          return (
                            <td
                              key={s.symbol}
                              className={`py-2.5 px-4 font-bold ${
                                (v ?? 0) >= 3.0
                                  ? "text-cyan-300"
                                  : (v ?? 0) >= 0
                                  ? "text-emerald-400"
                                  : "text-rose-400"
                              }`}
                            >
                              {v !== undefined ? `${v >= 0 ? "+" : ""}${v.toFixed(1)}%` : "—"}
                              {topROCWinner === s.symbol && renderWinnerBadge("Fastest")}
                            </td>
                          );
                        })}
                      </tr>

                      {/* 5-Day Rate of Change */}
                      <tr className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-4 text-slate-400 font-sans font-semibold">
                          5-Day Rate of Change (%)
                        </td>
                        {stocks.map((s) => {
                          const v = s.roc_5d;
                          return (
                            <td
                              key={s.symbol}
                              className={`py-2.5 px-4 font-semibold ${
                                (v ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"
                              }`}
                            >
                              {v !== undefined ? `${v >= 0 ? "+" : ""}${v.toFixed(1)}%` : "—"}
                            </td>
                          );
                        })}
                      </tr>

                      {/* Short-Term RVOL */}
                      <tr className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-4 text-slate-400 font-sans font-semibold">
                          Relative Volume (5D RVOL)
                        </td>
                        {stocks.map((s) => {
                          const rvol = s.short_term_rvol ?? s.volume_ratio;
                          return (
                            <td key={s.symbol} className="py-2.5 px-4 font-bold text-amber-300">
                              {rvol ? `${rvol.toFixed(2)}x` : "—"}
                              {topRVOLWinner === s.symbol && renderWinnerBadge("Top Vol")}
                            </td>
                          );
                        })}
                      </tr>

                      {/* 8/21 EMA Spread % */}
                      <tr className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-4 text-slate-400 font-sans font-semibold">
                          8/21 EMA Ribbon Spread
                        </td>
                        {stocks.map((s) => (
                          <td key={s.symbol} className="py-2.5 px-4 text-purple-300 font-semibold">
                            {s.ema_spread_pct !== undefined
                              ? `${s.ema_spread_pct >= 0 ? "+" : ""}${s.ema_spread_pct.toFixed(1)}%`
                              : "—"}
                          </td>
                        ))}
                      </tr>

                      {/* Institutional Inflow Flow Rating */}
                      <tr className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-4 text-slate-400 font-sans font-semibold">
                          Accumulation / Distribution
                        </td>
                        {stocks.map((s) => (
                          <td key={s.symbol} className="py-2.5 px-4">
                            {s.accumulation_rating ? (
                              <span
                                className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                                  s.accumulation_rating.startsWith("A")
                                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                                    : "bg-slate-800 text-slate-300 border border-slate-700"
                                }`}
                              >
                                {s.accumulation_rating} (Up/Down: {s.up_down_volume_ratio?.toFixed(1) ?? "1.0"}x)
                              </span>
                            ) : (
                              <span className="text-slate-500">—</span>
                            )}
                          </td>
                        ))}
                      </tr>

                      {/* Recommended Entry Zone */}
                      <tr className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-4 text-slate-400 font-sans font-semibold">
                          Entry Zone
                        </td>
                        {stocks.map((s) => (
                          <td key={s.symbol} className="py-2.5 px-4 font-semibold text-slate-200">
                            {s.trade_plan?.entry_zone
                              ? `$${s.trade_plan.entry_zone[0].toFixed(2)} - $${s.trade_plan.entry_zone[1].toFixed(2)}`
                              : `$${s.price.toFixed(2)}`}
                          </td>
                        ))}
                      </tr>

                      {/* Target 1 Gain % */}
                      <tr className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-4 text-slate-400 font-sans font-semibold">
                          Target 1 Upside (TP1)
                        </td>
                        {stocks.map((s) => (
                          <td key={s.symbol} className="py-2.5 px-4 font-bold text-emerald-400">
                            ${s.trade_plan?.tp1?.toFixed(2) ?? "—"} (+{s.trade_plan?.tp1_pct?.toFixed(1) ?? "0.0"}%)
                            {topTargetWinner === s.symbol && renderWinnerBadge("Max Gain")}
                          </td>
                        ))}
                      </tr>

                      {/* Target 2 Gain % (TP2 Runner) */}
                      <tr className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-4 text-slate-400 font-sans font-semibold">
                          Target 2 Runner (TP2)
                        </td>
                        {stocks.map((s) => (
                          <td key={s.symbol} className="py-2.5 px-4 font-bold text-emerald-400/90">
                            ${s.trade_plan?.tp2 ? s.trade_plan.tp2.toFixed(2) : "—"} (+{s.trade_plan?.tp2_pct ? s.trade_plan.tp2_pct.toFixed(1) : "0.0"}%)
                            {topTarget2Winner === s.symbol && renderWinnerBadge("Top Runner")}
                          </td>
                        ))}
                      </tr>

                      {/* Stop Loss & Invalidation Risk % */}
                      <tr className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-4 text-slate-400 font-sans font-semibold">
                          Invalidation Stop Loss
                        </td>
                        {stocks.map((s) => {
                          const currPrice = s.price > 0 ? s.price : s.trade_plan?.current_price ?? 0;
                          const stopPrice = s.trade_plan?.stop_loss ?? 0;
                          const stopDist = currPrice > stopPrice && stopPrice > 0 ? currPrice - stopPrice : null;
                          return (
                            <td key={s.symbol} className="py-2.5 px-4 font-bold text-rose-400">
                              <span>${stopPrice > 0 ? stopPrice.toFixed(2) : "—"}</span>{" "}
                              <span className="text-[11px] font-normal text-rose-300">
                                (-{s.trade_plan?.invalidation_pct ? s.trade_plan.invalidation_pct.toFixed(1) : "0.0"}%
                                {stopDist !== null ? ` | -$${stopDist.toFixed(2)}` : ""})
                              </span>
                              {safestRiskWinner === s.symbol && renderWinnerBadge("Safest")}
                            </td>
                          );
                        })}
                      </tr>

                      {/* Risk : Reward Ratio */}
                      <tr className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-4 text-slate-400 font-sans font-semibold">
                          Risk-Reward Ratio
                        </td>
                        {stocks.map((s) => (
                          <td key={s.symbol} className="py-2.5 px-4 font-bold text-emerald-300">
                            1 : {s.trade_plan?.risk_reward_ratio?.toFixed(2) ?? "2.0"} R:R
                            {topRRWinner === s.symbol && renderWinnerBadge("Best R:R")}
                          </td>
                        ))}
                      </tr>

                      {/* Fast RSI */}
                      <tr className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-4 text-slate-400 font-sans font-semibold">
                          RSI Indicator
                        </td>
                        {stocks.map((s) => (
                          <td key={s.symbol} className="py-2.5 px-4 font-semibold text-slate-300">
                            {s.rsi ? s.rsi.toFixed(1) : "—"}
                          </td>
                        ))}
                      </tr>

                      {/* 52-Week High Distance */}
                      <tr className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-4 text-slate-400 font-sans font-semibold">
                          52-Week High Distance
                        </td>
                        {stocks.map((s) => (
                          <td key={s.symbol} className="py-2.5 px-4 text-amber-300 font-semibold">
                            {s.distance_from_52w_high_pct !== undefined
                              ? s.distance_from_52w_high_pct >= -0.1
                                ? "AT HIGH"
                                : `${s.distance_from_52w_high_pct.toFixed(1)}%`
                              : "—"}
                          </td>
                        ))}
                      </tr>

                      {/* Earnings Blackout / Days Away */}
                      <tr className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-4 text-slate-400 font-sans font-semibold">
                          Upcoming Earnings
                        </td>
                        {stocks.map((s) => (
                          <td key={s.symbol} className="py-2.5 px-4">
                            {s.earnings_days_away !== null && s.earnings_days_away !== undefined ? (
                              <span
                                className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold ${
                                  s.earnings_days_away <= 7
                                    ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                                    : "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                                }`}
                              >
                                ⚠️ {s.earnings_days_away === 0 ? "Today" : `${s.earnings_days_away}d away`}
                              </span>
                            ) : (
                              <span className="text-slate-500">No imminent earnings</span>
                            )}
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
