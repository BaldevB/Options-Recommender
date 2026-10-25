"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Star,
  Plus,
  Trash2,
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
  Layers,
  Zap,
  RefreshCw,
  Search,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  AlertCircle,
} from "lucide-react";

interface WatchlistItem {
  symbol: string;
  name: string;
  price: number;
  previous_close: number;
  change: number;
  change_percent: number;
  day_high?: number;
  day_low?: number;
  volume?: number;
  momentum?: {
    score: number;
    rsi: number;
    trend: string;
    volume_ratio: number;
    volume_confirmed: boolean;
    weekly_trend?: string;
  } | null;
}

interface StarredWatchlistViewProps {
  starredTickers: string[];
  onToggleStar: (ticker: string) => void;
  onSelectTicker: (ticker: string) => void;
  onOpenOptionsChain: (ticker: string) => void;
  onOpenZeroDte: (ticker: string) => void;
}

const POPULAR_SUGGESTIONS = [
  "NVDA",
  "SPY",
  "QQQ",
  "TSLA",
  "AAPL",
  "AMD",
  "PLTR",
  "GLD",
  "COIN",
  "AMZN",
  "MSFT",
];

export default function StarredWatchlistView({
  starredTickers,
  onToggleStar,
  onSelectTicker,
  onOpenOptionsChain,
  onOpenZeroDte,
}: StarredWatchlistViewProps) {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [addInput, setAddInput] = useState<string>("");
  const [filterQuery, setFilterQuery] = useState<string>("");
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchWatchlistData = useCallback(async () => {
    if (!starredTickers || starredTickers.length === 0) {
      setItems([]);
      return;
    }
    setLoading(true);
    try {
      const tickerList = starredTickers.join(",");
      const res = await fetch(`/api/watchlist-summary?tickers=${encodeURIComponent(tickerList)}`);
      if (!res.ok) throw new Error("Failed to load watchlist summary");
      const json = await res.json();
      setItems(json.tickers || []);
      setLastUpdated(new Date());
    } catch (err) {
      console.error("Error fetching watchlist data:", err);
    } finally {
      setLoading(false);
    }
  }, [starredTickers]);

  useEffect(() => {
    fetchWatchlistData();
  }, [fetchWatchlistData]);

  const handleAddTicker = (e: React.FormEvent) => {
    e.preventDefault();
    const clean = addInput.trim().toUpperCase();
    if (clean && !starredTickers.includes(clean)) {
      onToggleStar(clean);
      setAddInput("");
    }
  };

  const filteredItems = items.filter((it) => {
    if (!filterQuery) return true;
    const q = filterQuery.toUpperCase();
    return it.symbol.includes(q) || it.name.toUpperCase().includes(q);
  });

  return (
    <div className="space-y-6">
      {/* ---------------- TOP BANNER & STATS ---------------- */}
      <div className="flex flex-col justify-between gap-4 rounded-2xl border border-slate-800 bg-gradient-to-r from-[#0c1424] via-[#0b1220] to-[#0a101b] p-6 sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center space-x-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400 shadow-md shadow-amber-950/40">
              <Star className="h-5 w-5 fill-amber-400 text-amber-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white flex items-center space-x-2">
                <span>Starred Watchlist</span>
                <span className="rounded-full bg-amber-500/10 px-2.5 py-0.5 text-xs font-semibold text-amber-300 border border-amber-500/20">
                  {starredTickers.length} {starredTickers.length === 1 ? "Ticker" : "Tickers"}
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Bookmarks saved to browser storage. Real-time quotes, technical momentum & quick options execution.
              </p>
            </div>
          </div>
        </div>

        {/* Quick Add Bar & Refresh */}
        <div className="flex flex-wrap items-center gap-2">
          <form onSubmit={handleAddTicker} className="flex items-center">
            <div className="relative">
              <input
                type="text"
                placeholder="Add ticker (e.g. AMD)..."
                value={addInput}
                onChange={(e) => setAddInput(e.target.value)}
                className="w-48 rounded-l-lg border border-slate-700 bg-slate-900/90 px-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 focus:border-cyan-500 focus:outline-none uppercase"
              />
            </div>
            <button
              type="submit"
              disabled={!addInput.trim()}
              className="flex items-center space-x-1 rounded-r-lg border border-l-0 border-cyan-500/40 bg-cyan-600/80 px-3 py-1.5 text-xs font-medium text-white hover:bg-cyan-500 disabled:opacity-40 transition"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Add</span>
            </button>
          </form>

          <button
            onClick={fetchWatchlistData}
            disabled={loading}
            className="flex items-center space-x-1.5 rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-1.5 text-xs font-medium text-slate-300 hover:border-slate-600 hover:text-white transition disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-cyan-400" : ""}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        </div>
      </div>

      {/* ---------------- QUICK SUGGESTION CHIPS ---------------- */}
      <div className="flex flex-wrap items-center gap-1.5 rounded-xl border border-slate-800/80 bg-[#090f1c] px-4 py-2.5 text-xs">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mr-2 flex items-center">
          <Sparkles className="mr-1 h-3 w-3 text-cyan-400" />
          Quick Add:
        </span>
        {POPULAR_SUGGESTIONS.map((sym) => {
          const isAdded = starredTickers.includes(sym);
          return (
            <button
              key={sym}
              onClick={() => onToggleStar(sym)}
              className={`rounded-md px-2 py-0.5 text-[11px] font-medium transition ${
                isAdded
                  ? "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                  : "bg-slate-800/60 text-slate-400 hover:bg-slate-700 hover:text-slate-200 border border-slate-700/50"
              }`}
            >
              {isAdded ? "✓" : "+"} {sym}
            </button>
          );
        })}
      </div>

      {/* ---------------- FILTER INPUT ---------------- */}
      {items.length > 3 && (
        <div className="flex items-center justify-between">
          <div className="relative w-64">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-500" />
            <input
              type="text"
              placeholder="Filter your watchlist..."
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
              className="w-full rounded-lg border border-slate-800 bg-slate-900/60 pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
            />
          </div>
          {lastUpdated && (
            <span className="text-[11px] text-slate-500">
              Synced at {lastUpdated.toLocaleTimeString()}
            </span>
          )}
        </div>
      )}

      {/* ---------------- EMPTY STATE ---------------- */}
      {starredTickers.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-800 bg-[#090e1b] py-16 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-400 mb-4">
            <Star className="h-7 w-7" />
          </div>
          <h3 className="text-lg font-bold text-white">Your Starred Watchlist is Empty</h3>
          <p className="mt-1 max-w-md text-xs text-slate-400">
            Bookmark your favorite stocks and setups by clicking the ⭐ star icon across the Terminal, High-Confidence Picks, or 0DTE Flash Lab.
          </p>
          <div className="mt-5 flex flex-wrap justify-center gap-2">
            {["NVDA", "SPY", "QQQ", "TSLA", "AAPL"].map((t) => (
              <button
                key={t}
                onClick={() => onToggleStar(t)}
                className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-1.5 text-xs font-semibold text-amber-300 hover:bg-amber-500/20 transition"
              >
                + Add {t}
              </button>
            ))}
          </div>
        </div>
      ) : loading && items.length === 0 ? (
        <div className="flex h-64 items-center justify-center rounded-2xl border border-slate-800 bg-[#090e1b] text-slate-400">
          <RefreshCw className="mr-2 h-5 w-5 animate-spin text-cyan-400" />
          Loading Starred Quotes & Momentum...
        </div>
      ) : (
        /* ---------------- WATCHLIST GRID ---------------- */
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredItems.map((item) => {
            const isPos = item.change_percent >= 0;
            const mom = item.momentum;
            const momScore = mom?.score ?? 0;
            const rsi = mom?.rsi ?? 50;
            const isBullish = momScore >= 50;

            return (
              <div
                key={item.symbol}
                className="group relative flex flex-col justify-between rounded-xl border border-slate-800 bg-[#0c1322] p-4 shadow-sm hover:border-slate-700 transition"
              >
                {/* Card Header */}
                <div>
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-lg font-black tracking-tight text-white group-hover:text-cyan-300 transition">
                          {item.symbol}
                        </span>
                        {mom?.weekly_trend && (
                          <span
                            className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${
                              mom.weekly_trend === "BULLISH"
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                            }`}
                          >
                            {mom.weekly_trend}
                          </span>
                        )}
                      </div>
                      <p className="line-clamp-1 text-xs text-slate-400 mt-0.5">
                        {item.name || item.symbol}
                      </p>
                    </div>

                    {/* Star Toggle Button */}
                    <button
                      onClick={() => onToggleStar(item.symbol)}
                      title="Remove from Starred Watchlist"
                      className="rounded-lg p-1 text-amber-400 hover:bg-slate-800/80 transition"
                    >
                      <Star className="h-4 w-4 fill-amber-400" />
                    </button>
                  </div>

                  {/* Price & Change Banner */}
                  <div className="mt-3 flex items-baseline justify-between border-b border-slate-800/70 pb-3">
                    <span className="font-mono text-xl font-bold text-white">
                      ${item.price.toFixed(2)}
                    </span>
                    <div
                      className={`flex items-center rounded-md px-2 py-0.5 text-xs font-bold ${
                        isPos
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                      }`}
                    >
                      {isPos ? (
                        <TrendingUp className="mr-1 h-3 w-3" />
                      ) : (
                        <TrendingDown className="mr-1 h-3 w-3" />
                      )}
                      <span>
                        {isPos ? "+" : ""}
                        {item.change ? item.change.toFixed(2) : "0.00"} ({isPos ? "+" : ""}
                        {item.change_percent ? item.change_percent.toFixed(2) : "0.00"}%)
                      </span>
                    </div>
                  </div>

                  {/* Momentum & Technical Metrics */}
                  <div className="mt-3 space-y-2 text-xs">
                    {mom ? (
                      <>
                        <div className="flex items-center justify-between">
                          <span className="text-slate-400">Momentum Score:</span>
                          <span
                            className={`font-mono font-bold ${
                              isBullish ? "text-emerald-400" : "text-amber-400"
                            }`}
                          >
                            {momScore.toFixed(1)} / 100
                          </span>
                        </div>
                        <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${
                              isBullish ? "bg-emerald-500" : "bg-amber-500"
                            }`}
                            style={{ width: `${Math.min(100, Math.max(5, momScore))}%` }}
                          />
                        </div>

                        <div className="flex items-center justify-between text-[11px] pt-1 text-slate-400">
                          <span>
                            RSI:{" "}
                            <strong
                              className={
                                rsi > 70
                                  ? "text-rose-400"
                                  : rsi < 30
                                  ? "text-emerald-400"
                                  : "text-slate-200"
                              }
                            >
                              {rsi.toFixed(1)}
                            </strong>
                          </span>
                          <span>
                            Vol Ratio:{" "}
                            <strong className="text-slate-200">
                              {mom.volume_ratio ? mom.volume_ratio.toFixed(2) : "1.00"}x
                            </strong>
                          </span>
                          <span
                            className={`rounded px-1 text-[10px] ${
                              mom.volume_confirmed
                                ? "bg-cyan-500/10 text-cyan-300"
                                : "bg-slate-800 text-slate-400"
                            }`}
                          >
                            {mom.volume_confirmed ? "Vol Confirmed" : "Normal Vol"}
                          </span>
                        </div>
                      </>
                    ) : (
                      <div className="text-[11px] text-slate-500 italic py-1">
                        Historical momentum sync pending...
                      </div>
                    )}
                  </div>
                </div>

                {/* Card Action Buttons */}
                <div className="mt-4 flex flex-col gap-1.5 border-t border-slate-800/80 pt-3">
                  <button
                    onClick={() => onSelectTicker(item.symbol)}
                    className="flex w-full items-center justify-center space-x-1.5 rounded-lg border border-cyan-500/30 bg-cyan-950/40 py-1.5 text-xs font-semibold text-cyan-300 hover:bg-cyan-900/40 hover:text-white transition shadow-sm"
                  >
                    <BarChart3 className="h-3.5 w-3.5" />
                    <span>Analyze in Terminal</span>
                    <ArrowRight className="h-3 w-3 ml-1" />
                  </button>

                  <div className="grid grid-cols-2 gap-1.5">
                    <button
                      onClick={() => onOpenOptionsChain(item.symbol)}
                      className="flex items-center justify-center space-x-1 rounded-md border border-slate-700/80 bg-slate-800/60 py-1 text-[11px] font-medium text-slate-300 hover:border-slate-600 hover:text-white transition"
                    >
                      <Layers className="h-3 w-3 text-cyan-400" />
                      <span>Options Chain</span>
                    </button>
                    <button
                      onClick={() => onOpenZeroDte(item.symbol)}
                      className="flex items-center justify-center space-x-1 rounded-md border border-amber-500/30 bg-amber-950/30 py-1 text-[11px] font-medium text-amber-300 hover:bg-amber-900/40 transition"
                    >
                      <Zap className="h-3 w-3 text-amber-400" />
                      <span>0DTE Lab</span>
                    </button>
                  </div>

                  <Link
                    href={`/stocks?symbol=${encodeURIComponent(item.symbol)}`}
                    className="flex w-full items-center justify-center space-x-1.5 rounded-lg border border-emerald-500/30 bg-emerald-950/30 py-1.5 text-xs font-semibold text-emerald-300 hover:bg-emerald-900/40 hover:border-emerald-500/50 hover:text-white hover:shadow-[0_0_12px_rgba(16,185,129,0.25)] transition shadow-sm group"
                  >
                    <TrendingUp className="h-3.5 w-3.5 text-emerald-400 group-hover:scale-110 transition-transform" />
                    <span>Stock Plan</span>
                    <ArrowRight className="h-3 w-3 ml-1 text-emerald-400/80 group-hover:translate-x-0.5 transition-transform" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
