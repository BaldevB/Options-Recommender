"use client";

import React from "react";
import Link from "next/link";
import {
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  TrendingUp,
  TrendingDown,
  Zap,
  Target,
  Sparkles,
  Layers,
  Star,
  ExternalLink,
} from "lucide-react";
import { StockRecommendationItem } from "./StockCard";

interface StockScreenerTableProps {
  stocks: StockRecommendationItem[];
  sortBy: string;
  sortDirection: "asc" | "desc";
  onSort: (column: string) => void;
  onDeepDive: (stock: StockRecommendationItem) => void;
  onPaperBuy: (stock: StockRecommendationItem) => void;
  starredTickers?: string[];
  onToggleStar?: (symbol: string) => void;
}

export default function StockScreenerTable({
  stocks,
  sortBy,
  sortDirection,
  onSort,
  onDeepDive,
  onPaperBuy,
  starredTickers = [],
  onToggleStar,
}: StockScreenerTableProps) {
  const renderSortIcon = (column: string) => {
    if (sortBy !== column) {
      return <ArrowUpDown className="w-3 h-3 text-slate-500 opacity-60 inline ml-1" />;
    }
    return sortDirection === "asc" ? (
      <ArrowUp className="w-3 h-3 text-cyan-400 inline ml-1" />
    ) : (
      <ArrowDown className="w-3 h-3 text-cyan-400 inline ml-1" />
    );
  };

  const getActionBadge = (action: string) => {
    const act = (action || "BUY").toUpperCase();
    if (act.includes("STRONG")) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
          STRONG BUY
        </span>
      );
    }
    if (act.includes("BUY")) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
          BUY
        </span>
      );
    }
    if (act.includes("WATCH")) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">
          WATCH
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-700/50 text-slate-300 border border-slate-600">
        HOLD
      </span>
    );
  };

  const getStrategyBadge = (tag?: string) => {
    if (!tag) return <span className="text-slate-500 text-[11px]">—</span>;
    const t = tag.toUpperCase();
    if (t === "RS_LEADER") {
      return (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 whitespace-nowrap">
          ⚡ RS Leader
        </span>
      );
    }
    if (t === "52W_BREAKOUT") {
      return (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 whitespace-nowrap">
          🚀 Breakout
        </span>
      );
    }
    if (t === "GOLDEN_CROSS") {
      return (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/40 whitespace-nowrap">
          🌟 Cross
        </span>
      );
    }
    if (t === "PULLBACK_DIP") {
      return (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 whitespace-nowrap">
          🎯 Dip Buy
        </span>
      );
    }
    if (t === "VOLUME_SURGE") {
      return (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold bg-orange-500/20 text-orange-300 border border-orange-500/40 whitespace-nowrap">
          🔥 Vol Surge
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-500/15 text-blue-300 border border-blue-500/30 whitespace-nowrap">
        📈 Swing
      </span>
    );
  };

  const getHorizonBadge = (horizon: string) => {
    const h = (horizon || "SWING").toUpperCase();
    if (h.includes("LONG")) {
      return <span className="text-[11px] font-mono text-purple-300">Long-Term</span>;
    }
    if (h.includes("BREAKOUT")) {
      return <span className="text-[11px] font-mono text-rose-300">Breakout</span>;
    }
    return <span className="text-[11px] font-mono text-cyan-300">Swing</span>;
  };

  return (
    <div className="w-full overflow-hidden rounded-xl border border-slate-800 bg-[#0b1220]/90 shadow-xl backdrop-blur-md">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="border-b border-slate-800 bg-[#080d19] text-[11px] uppercase tracking-wider text-slate-400 font-semibold select-none">
            <tr>
              <th scope="col" className="py-3 px-3 w-8"></th>
              <th
                scope="col"
                className="py-3 px-3 cursor-pointer hover:text-cyan-400 transition-colors"
                onClick={() => onSort("symbol")}
              >
                Ticker {renderSortIcon("symbol")}
              </th>
              <th scope="col" className="py-3 px-3">Strategy</th>
              <th scope="col" className="py-3 px-3">Sector</th>
              <th scope="col" className="py-3 px-3">Horizon</th>
              <th scope="col" className="py-3 px-3">Action</th>
              <th
                scope="col"
                className="py-3 px-3 text-right cursor-pointer hover:text-cyan-400 transition-colors"
                onClick={() => onSort("price")}
              >
                Price {renderSortIcon("price")}
              </th>
              <th
                scope="col"
                className="py-3 px-3 text-right cursor-pointer hover:text-cyan-400 transition-colors"
                onClick={() => onSort("change_pct")}
              >
                24h % {renderSortIcon("change_pct")}
              </th>
              <th
                scope="col"
                className="py-3 px-3 text-right cursor-pointer hover:text-cyan-400 transition-colors"
                onClick={() => onSort("rs")}
                title="Relative Strength Percentile vs Market (0-99)"
              >
                RS {renderSortIcon("rs")}
              </th>
              <th
                scope="col"
                className="py-3 px-3 text-right cursor-pointer hover:text-cyan-400 transition-colors"
                onClick={() => onSort("dist_52w")}
                title="Distance from 52-Week High"
              >
                52W Dist {renderSortIcon("dist_52w")}
              </th>
              <th
                scope="col"
                className="py-3 px-3 text-right cursor-pointer hover:text-cyan-400 transition-colors"
                onClick={() => onSort("volume_ratio")}
              >
                Vol {renderSortIcon("volume_ratio")}
              </th>
              <th
                scope="col"
                className="py-3 px-3 text-right cursor-pointer hover:text-cyan-400 transition-colors"
                onClick={() => onSort("rsi")}
              >
                RSI {renderSortIcon("rsi")}
              </th>
              <th
                scope="col"
                className="py-3 px-3 text-right cursor-pointer hover:text-cyan-400 transition-colors"
                onClick={() => onSort("target_pct")}
              >
                Target 1 {renderSortIcon("target_pct")}
              </th>
              <th
                scope="col"
                className="py-3 px-3 text-right cursor-pointer hover:text-cyan-400 transition-colors"
                onClick={() => onSort("risk_reward")}
              >
                R:R {renderSortIcon("risk_reward")}
              </th>
              <th
                scope="col"
                className="py-3 px-3 text-right cursor-pointer hover:text-cyan-400 transition-colors"
                onClick={() => onSort("score")}
              >
                Score {renderSortIcon("score")}
              </th>
              <th scope="col" className="py-3 px-3">Sentiment</th>
              <th scope="col" className="py-3 px-4 text-center">Quick Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-medium">
            {stocks.length === 0 ? (
              <tr>
                <td colSpan={17} className="py-12 text-center text-slate-500 text-sm">
                  No stock recommendations match your filter criteria.
                </td>
              </tr>
            ) : (
              stocks.map((stock) => {
                const isPositive = stock.change_pct >= 0;
                const isStarred = starredTickers.includes(stock.symbol);
                const plan = stock.trade_plan;

                return (
                  <tr
                    key={stock.symbol}
                    className="hover:bg-slate-800/40 transition-colors duration-150 group"
                  >
                    {/* Star Button */}
                    <td className="py-3 px-2 text-center">
                      {onToggleStar && (
                        <button
                          type="button"
                          onClick={() => onToggleStar(stock.symbol)}
                          className={`p-1 rounded transition-colors ${
                            isStarred
                              ? "text-amber-400"
                              : "text-slate-600 hover:text-amber-400"
                          }`}
                          title={isStarred ? "Remove from watchlist" : "Star ticker"}
                        >
                          <Star className={`w-3.5 h-3.5 ${isStarred ? "fill-amber-400" : ""}`} />
                        </button>
                      )}
                    </td>

                    {/* Ticker & Name */}
                    <td className="py-3 px-3">
                      <div className="flex flex-col">
                        <span className="font-mono font-bold text-slate-100 text-sm group-hover:text-cyan-300 transition-colors">
                          {stock.symbol}
                        </span>
                        <span className="text-[11px] text-slate-400 line-clamp-1 max-w-[120px]" title={stock.name}>
                          {stock.name}
                        </span>
                      </div>
                    </td>

                    {/* Strategy Tag */}
                    <td className="py-3 px-3">
                      {getStrategyBadge(stock.strategy_tag)}
                    </td>

                    {/* Sector */}
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded text-[11px] bg-slate-800/80 text-slate-300 border border-slate-700/60 whitespace-nowrap">
                        {stock.sector}
                      </span>
                    </td>

                    {/* Horizon */}
                    <td className="py-3 px-3">{getHorizonBadge(stock.horizon)}</td>

                    {/* Action */}
                    <td className="py-3 px-3">{getActionBadge(stock.action)}</td>

                    {/* Price */}
                    <td className="py-3 px-3 text-right font-mono font-semibold text-slate-100">
                      ${stock.price > 0 ? stock.price.toFixed(2) : "—"}
                    </td>

                    {/* 24h Change */}
                    <td className="py-3 px-3 text-right font-mono font-semibold">
                      <span
                        className={`inline-flex items-center gap-0.5 ${
                          isPositive ? "text-emerald-400" : "text-rose-400"
                        }`}
                      >
                        {isPositive ? (
                          <TrendingUp className="w-3 h-3" />
                        ) : (
                          <TrendingDown className="w-3 h-3" />
                        )}
                        {isPositive ? "+" : ""}
                        {stock.change_pct.toFixed(2)}%
                      </span>
                    </td>

                    {/* RS Rating */}
                    <td className="py-3 px-3 text-right font-mono">
                      {stock.relative_strength_score !== undefined ? (
                        <span
                          className={`font-bold px-1.5 py-0.5 rounded ${
                            stock.relative_strength_score >= 80
                              ? "text-cyan-300 bg-cyan-950/40 border border-cyan-800/40"
                              : stock.relative_strength_score >= 60
                              ? "text-emerald-300 bg-emerald-950/40 border border-emerald-800/40"
                              : "text-slate-400"
                          }`}
                        >
                          {Math.round(stock.relative_strength_score)}
                        </span>
                      ) : (
                        <span className="text-slate-500">—</span>
                      )}
                    </td>

                    {/* 52W High Distance */}
                    <td className="py-3 px-3 text-right font-mono">
                      {stock.distance_from_52w_high_pct !== undefined ? (
                        <span
                          className={`text-[11px] ${
                            stock.distance_from_52w_high_pct >= -3.0
                              ? "text-amber-400 font-bold"
                              : "text-slate-400"
                          }`}
                        >
                          {stock.distance_from_52w_high_pct >= -0.1
                            ? "HIGH"
                            : `${stock.distance_from_52w_high_pct.toFixed(1)}%`}
                        </span>
                      ) : (
                        <span className="text-slate-500">—</span>
                      )}
                    </td>

                    {/* Volume Ratio */}
                    <td className="py-3 px-3 text-right font-mono">
                      <span
                        className={
                          stock.volume_ratio >= 1.25
                            ? "text-amber-400 font-bold"
                            : "text-slate-300"
                        }
                      >
                        {stock.volume_ratio.toFixed(2)}x
                      </span>
                    </td>

                    {/* RSI */}
                    <td className="py-3 px-3 text-right font-mono font-semibold">
                      <span
                        className={
                          stock.rsi > 70
                            ? "text-rose-400"
                            : stock.rsi < 35
                            ? "text-emerald-400"
                            : "text-slate-300"
                        }
                      >
                        {stock.rsi.toFixed(1)}
                      </span>
                    </td>

                    {/* Target 1 */}
                    <td className="py-3 px-3 text-right font-mono">
                      <div className="flex flex-col items-end">
                        <span className="font-bold text-emerald-300">
                          ${plan.tp1 ? plan.tp1.toFixed(2) : "—"}
                        </span>
                        <span className="text-[10px] text-emerald-400/80 font-semibold">
                          +{plan.tp1_pct ? plan.tp1_pct.toFixed(1) : "0.0"}%
                        </span>
                      </div>
                    </td>

                    {/* R:R */}
                    <td className="py-3 px-3 text-right font-mono font-bold text-emerald-400">
                      1:{plan.risk_reward_ratio ? plan.risk_reward_ratio.toFixed(1) : "2.0"}
                    </td>

                    {/* Score */}
                    <td className="py-3 px-3 text-right font-mono">
                      <span className="font-bold text-cyan-300 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-800/40">
                        {stock.score.toFixed(1)}
                      </span>
                    </td>

                    {/* Sentiment */}
                    <td className="py-3 px-3">
                      <span
                        className={`text-[11px] font-mono px-1.5 py-0.5 rounded ${
                          stock.sentiment_score >= 0.15
                            ? "text-emerald-300 bg-emerald-500/10 border border-emerald-500/20"
                            : stock.sentiment_score <= -0.15
                            ? "text-rose-300 bg-rose-500/10 border border-rose-500/20"
                            : "text-slate-400 bg-slate-800"
                        }`}
                      >
                        {stock.sentiment_score > 0 ? "+" : ""}
                        {stock.sentiment_score.toFixed(2)}
                      </span>
                    </td>

                    {/* Actions */}
                    <td className="py-3 px-4 text-center">
                      <div className="flex items-center justify-center gap-1.5">
                        <button
                          type="button"
                          onClick={() => onDeepDive(stock)}
                          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-cyan-500/30 text-[11px] font-semibold transition-colors inline-flex items-center gap-1"
                          title="Deep Dive Trade Plan & Chart"
                        >
                          <Target className="w-3 h-3 text-cyan-400" />
                          Plan
                        </button>

                        <button
                          type="button"
                          onClick={() => onPaperBuy(stock)}
                          className="px-2 py-1 rounded bg-emerald-600/30 hover:bg-emerald-600/50 text-emerald-300 border border-emerald-500/40 text-[11px] font-semibold transition-colors inline-flex items-center gap-1 shadow-sm"
                          title="Execute Paper Buy"
                        >
                          <Zap className="w-3 h-3 text-emerald-400 fill-emerald-400/40" />
                          Buy
                        </button>

                        <Link
                          href={`/?ticker=${encodeURIComponent(stock.symbol)}`}
                          className="p-1 rounded bg-slate-800/60 hover:bg-slate-700 text-slate-400 hover:text-cyan-300 border border-slate-700/60 transition-colors"
                          title="View Options"
                        >
                          <Layers className="w-3 h-3" />
                        </Link>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
