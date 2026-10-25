"use client";

import React from "react";
import Link from "next/link";
import {
  TrendingUp,
  TrendingDown,
  Target,
  ShieldAlert,
  Zap,
  Activity,
  Layers,
  Sparkles,
  ArrowRight,
  Flame,
  Star,
  Compass,
} from "lucide-react";

export interface TradePlan {
  entry_zone: [number, number];
  current_price: number;
  tp1: number;
  tp2: number;
  stop_loss: number;
  risk_reward_ratio: number;
  invalidation_pct: number;
  tp1_pct: number;
  tp2_pct: number;
}

export interface StockRecommendationItem {
  symbol: string;
  name: string;
  sector: string;
  horizon: string;
  action: string;
  score: number;
  confidence: number;
  momentum_score: number;
  sentiment_score: number;
  trade_plan: TradePlan;
  rationale: string[];
  price: number;
  change: number;
  change_pct: number;
  volume_ratio: number;
  rsi: number;
  target_pct: number;
}

interface StockCardProps {
  stock: StockRecommendationItem;
  onDeepDive: (stock: StockRecommendationItem) => void;
  onPaperBuy: (stock: StockRecommendationItem) => void;
  isStarred?: boolean;
  onToggleStar?: (symbol: string) => void;
}

export default function StockCard({
  stock,
  onDeepDive,
  onPaperBuy,
  isStarred = false,
  onToggleStar,
}: StockCardProps) {
  const isPositive = stock.change_pct >= 0;
  const plan = stock.trade_plan;

  // Format action tier badges
  const getActionBadge = (action: string) => {
    const act = (action || "BUY").toUpperCase();
    if (act.includes("STRONG")) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-[0_0_10px_rgba(16,185,129,0.25)]">
          <Sparkles className="w-3 h-3 text-emerald-400" />
          STRONG BUY
        </span>
      );
    }
    if (act.includes("BUY")) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
          <TrendingUp className="w-3 h-3 text-cyan-400" />
          BUY
        </span>
      );
    }
    if (act.includes("WATCH")) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">
          <Compass className="w-3 h-3 text-amber-400" />
          WATCH
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-700/50 text-slate-300 border border-slate-600">
        HOLD
      </span>
    );
  };

  // Format horizon badge
  const getHorizonBadge = (horizon: string) => {
    const h = (horizon || "SWING").toUpperCase();
    if (h.includes("LONG")) {
      return (
        <span className="px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-purple-500/15 text-purple-300 border border-purple-500/30">
          💎 Long-Term (3-12m)
        </span>
      );
    }
    if (h.includes("BREAKOUT")) {
      return (
        <span className="px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-rose-500/15 text-rose-300 border border-rose-500/30">
          🚀 Breakout (1-10d)
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
        ⚡ Swing (2-6w)
      </span>
    );
  };

  // Sentiment badge
  const getSentimentBadge = (sentiment: number) => {
    if (sentiment >= 0.15) {
      return (
        <span className="text-[11px] font-mono text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
          Bullish (+{sentiment.toFixed(2)})
        </span>
      );
    }
    if (sentiment <= -0.15) {
      return (
        <span className="text-[11px] font-mono text-rose-400 bg-rose-500/10 px-1.5 py-0.5 rounded border border-rose-500/20">
          Bearish ({sentiment.toFixed(2)})
        </span>
      );
    }
    return (
      <span className="text-[11px] font-mono text-slate-400 bg-slate-800/60 px-1.5 py-0.5 rounded border border-slate-700">
        Neutral ({sentiment.toFixed(2)})
      </span>
    );
  };

  return (
    <div className="group relative flex flex-col justify-between rounded-xl border border-slate-800 bg-[#0d1424]/90 p-5 shadow-lg backdrop-blur-md transition-all duration-200 hover:border-cyan-500/40 hover:shadow-[0_0_24px_rgba(6,182,212,0.15)]">
      {/* Top Header */}
      <div>
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <span className="text-xl font-black tracking-wider text-slate-100 group-hover:text-cyan-400 transition-colors">
                  {stock.symbol}
                </span>
                {getActionBadge(stock.action)}
              </div>
              <span className="text-xs text-slate-400 line-clamp-1 max-w-[180px] font-medium" title={stock.name}>
                {stock.name}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            {onToggleStar && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onToggleStar(stock.symbol);
                }}
                className={`p-1.5 rounded-lg border transition-colors ${
                  isStarred
                    ? "bg-amber-500/20 border-amber-500/40 text-amber-400"
                    : "bg-slate-800/40 border-slate-700/60 text-slate-400 hover:text-amber-400 hover:border-amber-500/30"
                }`}
                title={isStarred ? "Remove from watchlist" : "Add to watchlist"}
              >
                <Star className={`w-3.5 h-3.5 ${isStarred ? "fill-amber-400" : ""}`} />
              </button>
            )}

            <div className="text-right">
              <div className="text-lg font-mono font-bold text-slate-100">
                ${stock.price > 0 ? stock.price.toFixed(2) : "—"}
              </div>
              <div
                className={`flex items-center justify-end text-xs font-mono font-semibold ${
                  isPositive ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                {isPositive ? (
                  <TrendingUp className="w-3 h-3 mr-0.5 inline" />
                ) : (
                  <TrendingDown className="w-3 h-3 mr-0.5 inline" />
                )}
                {isPositive ? "+" : ""}
                {stock.change_pct.toFixed(2)}%
              </div>
            </div>
          </div>
        </div>

        {/* Sector and Horizon tags */}
        <div className="flex flex-wrap items-center gap-1.5 mt-3">
          <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800 text-slate-300 border border-slate-700">
            {stock.sector}
          </span>
          {getHorizonBadge(stock.horizon)}
          {stock.volume_ratio >= 1.25 && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-amber-500/15 text-amber-300 border border-amber-500/30">
              <Flame className="w-3 h-3 text-amber-400" />
              {stock.volume_ratio.toFixed(2)}x Vol
            </span>
          )}
        </div>

        {/* Score & Confidence Bar */}
        <div className="mt-4 p-2.5 rounded-lg bg-[#080d1a] border border-slate-800/80">
          <div className="flex items-center justify-between text-xs mb-1.5">
            <span className="text-slate-400 font-medium flex items-center gap-1">
              <Activity className="w-3.5 h-3.5 text-cyan-400" />
              Quant Score: <span className="font-mono font-bold text-cyan-300">{stock.score.toFixed(1)}/100</span>
            </span>
            <span className="text-slate-400 font-mono text-[11px]">
              Conf: <span className="text-slate-200 font-semibold">{Math.round(stock.confidence * 100)}%</span>
            </span>
          </div>
          {/* Progress bar */}
          <div className="w-full bg-slate-800/80 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-gradient-to-r from-cyan-500 to-emerald-400 h-1.5 rounded-full transition-all duration-300"
              style={{ width: `${Math.min(100, Math.max(5, stock.score))}%` }}
            />
          </div>
        </div>

        {/* Trade Plan Grid */}
        <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
          <div className="p-2 rounded bg-slate-900/60 border border-slate-800/70">
            <span className="text-[10px] uppercase font-semibold text-slate-400 block tracking-wider">
              Entry Zone
            </span>
            <span className="font-mono font-medium text-slate-200 text-[11px]">
              ${plan.entry_zone ? `${plan.entry_zone[0].toFixed(2)} - ${plan.entry_zone[1].toFixed(2)}` : stock.price.toFixed(2)}
            </span>
          </div>

          <div className="p-2 rounded bg-slate-900/60 border border-slate-800/70">
            <span className="text-[10px] uppercase font-semibold text-slate-400 block tracking-wider">
              Risk : Reward
            </span>
            <span className="font-mono font-bold text-emerald-400 text-[11px]">
              1 : {plan.risk_reward_ratio ? plan.risk_reward_ratio.toFixed(2) : "2.0"} R:R
            </span>
          </div>

          <div className="p-2 rounded bg-emerald-950/20 border border-emerald-900/30">
            <span className="text-[10px] uppercase font-semibold text-emerald-400 block tracking-wider">
              Target 1 (TP1)
            </span>
            <span className="font-mono font-bold text-emerald-300 text-[11px]">
              ${plan.tp1.toFixed(2)} (+{plan.tp1_pct.toFixed(1)}%)
            </span>
          </div>

          <div className="p-2 rounded bg-rose-950/20 border border-rose-900/30">
            <span className="text-[10px] uppercase font-semibold text-rose-400 block tracking-wider">
              Stop Loss (SL)
            </span>
            <span className="font-mono font-bold text-rose-300 text-[11px]">
              ${plan.stop_loss.toFixed(2)} (-{plan.invalidation_pct.toFixed(1)}%)
            </span>
          </div>
        </div>

        {/* Technical & Sentiment Indicators */}
        <div className="mt-3 flex items-center justify-between gap-1 text-[11px] text-slate-400 pt-2 border-t border-slate-800/60">
          <div className="flex items-center gap-1.5">
            <span>RSI:</span>
            <span
              className={`font-mono font-semibold ${
                stock.rsi > 70
                  ? "text-rose-400"
                  : stock.rsi < 35
                  ? "text-emerald-400"
                  : "text-slate-200"
              }`}
            >
              {stock.rsi.toFixed(1)}
            </span>
          </div>

          <div className="flex items-center gap-1">
            <span>Sent:</span>
            {getSentimentBadge(stock.sentiment_score)}
          </div>
        </div>

        {/* Primary Rationale preview */}
        {stock.rationale && stock.rationale.length > 0 && (
          <div className="mt-2.5 text-[11px] text-slate-400/90 italic bg-slate-900/40 px-2.5 py-1.5 rounded border border-slate-800/50 line-clamp-2">
            &ldquo;{stock.rationale[0]}&rdquo;
          </div>
        )}
      </div>

      {/* Action Buttons Footer */}
      <div className="mt-4 pt-3 border-t border-slate-800 flex items-center gap-2">
        <button
          type="button"
          onClick={() => onDeepDive(stock)}
          className="flex-1 inline-flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold bg-slate-800/80 hover:bg-slate-700/80 text-cyan-300 border border-cyan-500/30 hover:border-cyan-400/60 transition-all shadow-sm"
        >
          <Target className="w-3.5 h-3.5 text-cyan-400" />
          Deep Dive
        </button>

        <button
          type="button"
          onClick={() => onPaperBuy(stock)}
          className="flex-1 inline-flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold bg-emerald-600/25 hover:bg-emerald-600/40 text-emerald-300 border border-emerald-500/40 hover:border-emerald-400 transition-all shadow-[0_0_12px_rgba(16,185,129,0.2)]"
        >
          <Zap className="w-3.5 h-3.5 text-emerald-400 fill-emerald-400/30" />
          Paper Buy
        </button>

        <Link
          href={`/?ticker=${encodeURIComponent(stock.symbol)}`}
          className="p-2 rounded-lg bg-slate-800/50 hover:bg-slate-700/70 border border-slate-700/60 text-slate-400 hover:text-cyan-300 transition-colors"
          title={`View Options for ${stock.symbol}`}
        >
          <Layers className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
}
