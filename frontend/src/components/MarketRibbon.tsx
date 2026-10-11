"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  TrendingUp,
  TrendingDown,
  Clock,
  RefreshCw,
  Activity,
  Globe,
  Radio,
  Sparkles,
} from "lucide-react";

interface BenchmarkItem {
  symbol: string;
  name: string;
  price: number;
  previous_close: number;
  change: number;
  change_percent: number;
  day_high?: number;
  day_low?: number;
  valid?: boolean;
}

interface MarketSession {
  status: "REGULAR" | "PRE_MARKET" | "AFTER_HOURS" | "CLOSED";
  label: string;
  et_time: string;
  is_open: boolean;
}

interface MarketRibbonProps {
  onSelectTicker?: (ticker: string) => void;
  activeTicker?: string;
  starredTickers?: string[];
  onToggleStar?: (ticker: string) => void;
}

export default function MarketRibbon({
  onSelectTicker,
  activeTicker,
  starredTickers = [],
  onToggleStar,
}: MarketRibbonProps) {
  const [session, setSession] = useState<MarketSession | null>(null);
  const [benchmarks, setBenchmarks] = useState<BenchmarkItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);

  const fetchRibbonData = useCallback(async () => {
    try {
      const res = await fetch("/api/market-ribbon");
      if (!res.ok) throw new Error("Failed fetching market ribbon");
      const json = await res.json();
      if (json.session) setSession(json.session);
      if (json.benchmarks) setBenchmarks(json.benchmarks);
      setLastRefreshed(new Date());
    } catch (err) {
      console.error("Error loading market ribbon:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRibbonData();
    // Auto-refresh market ribbon every 45 seconds
    const interval = setInterval(fetchRibbonData, 45000);
    return () => clearInterval(interval);
  }, [fetchRibbonData]);

  // Session pill style mapper
  const getSessionBadge = () => {
    if (!session) {
      return (
        <span className="flex items-center space-x-1.5 rounded-full bg-slate-800/80 px-2.5 py-0.5 text-[11px] font-medium text-slate-400 border border-slate-700/60">
          <Clock className="h-3 w-3" />
          <span>Syncing...</span>
        </span>
      );
    }

    switch (session.status) {
      case "REGULAR":
        return (
          <span className="flex items-center space-x-1.5 rounded-full bg-emerald-950/80 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-300 border border-emerald-700/50 shadow-sm shadow-emerald-950">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
            </span>
            <span>Market Open</span>
            <span className="text-[10px] text-emerald-400/70 font-normal">({session.et_time})</span>
          </span>
        );
      case "PRE_MARKET":
        return (
          <span className="flex items-center space-x-1.5 rounded-full bg-amber-950/80 px-2.5 py-0.5 text-[11px] font-semibold text-amber-300 border border-amber-700/50">
            <span className="relative flex h-2 w-2">
              <span className="inline-flex h-2 w-2 rounded-full bg-amber-400"></span>
            </span>
            <span>Pre-Market</span>
            <span className="text-[10px] text-amber-400/70 font-normal">({session.et_time})</span>
          </span>
        );
      case "AFTER_HOURS":
        return (
          <span className="flex items-center space-x-1.5 rounded-full bg-indigo-950/80 px-2.5 py-0.5 text-[11px] font-semibold text-indigo-300 border border-indigo-700/50">
            <span className="relative flex h-2 w-2">
              <span className="inline-flex h-2 w-2 rounded-full bg-indigo-400"></span>
            </span>
            <span>After-Hours</span>
            <span className="text-[10px] text-indigo-400/70 font-normal">({session.et_time})</span>
          </span>
        );
      default:
        return (
          <span className="flex items-center space-x-1.5 rounded-full bg-slate-900/90 px-2.5 py-0.5 text-[11px] font-medium text-slate-400 border border-slate-800">
            <span className="h-1.5 w-1.5 rounded-full bg-slate-500"></span>
            <span>{session.label}</span>
            <span className="text-[10px] text-slate-500 font-normal">({session.et_time})</span>
          </span>
        );
    }
  };

  const formatPrice = (sym: string, val: number) => {
    if (!val || val <= 0) return "--";
    if (sym === "BTC-USD") {
      return `$${val.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
    }
    if (sym === "^VIX") {
      return val.toFixed(2);
    }
    return `$${val.toFixed(2)}`;
  };

  return (
    <div className="w-full border-b border-slate-800/80 bg-[#060a12]/95 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-3 py-1.5 text-xs">
        {/* Left: Market Session Status Pill */}
        <div className="flex shrink-0 items-center space-x-2.5 pr-4 border-r border-slate-800/80">
          <div className="flex items-center space-x-1.5 text-slate-400">
            <Radio className="h-3.5 w-3.5 text-cyan-400 animate-pulse" />
            <span className="hidden text-[11px] font-medium uppercase tracking-wider text-slate-400 sm:inline">
              US Market
            </span>
          </div>
          {getSessionBadge()}
        </div>

        {/* Center: Scrollable Ticker Tape */}
        <div className="flex flex-1 items-center space-x-2 overflow-x-auto px-3 scrollbar-none">
          {benchmarks.map((item) => {
            const isPos = item.change_percent >= 0;
            const isVix = item.symbol === "^VIX";
            // For VIX, green/red interpretation: higher VIX usually red for market, but standard quote shows change
            const colorClass = isPos ? "text-emerald-400" : "text-rose-400";
            const bgClass = isPos ? "bg-emerald-500/10 hover:bg-emerald-500/20 border-emerald-500/20" : "bg-rose-500/10 hover:bg-rose-500/20 border-rose-500/20";
            const isActive = activeTicker?.toUpperCase() === item.symbol.toUpperCase();

            return (
              <button
                key={item.symbol}
                onClick={() => onSelectTicker && onSelectTicker(item.symbol.replace("^", ""))}
                title={`Click to analyze ${item.name} (${item.symbol})`}
                className={`group flex shrink-0 items-center space-x-2 rounded-md border px-2.5 py-1 text-left transition-all ${
                  isActive
                    ? "border-cyan-500/60 bg-cyan-950/40 shadow-sm shadow-cyan-900/30 ring-1 ring-cyan-500/40"
                    : "border-slate-800/80 bg-slate-900/40 hover:border-slate-700 hover:bg-slate-800/60"
                }`}
              >
                <div className="flex items-center space-x-1.5">
                  <span className="font-bold tracking-tight text-slate-200 group-hover:text-cyan-300">
                    {item.symbol.replace("^", "")}
                  </span>
                  <span className="hidden text-[10px] text-slate-400 md:inline">
                    {item.name}
                  </span>
                </div>

                <div className="flex items-center space-x-1.5 font-mono">
                  <span className="font-semibold text-slate-100">
                    {formatPrice(item.symbol, item.price)}
                  </span>

                  <span
                    className={`flex items-center rounded px-1 py-0.5 text-[10px] font-bold ${colorClass} ${bgClass}`}
                  >
                    {isPos ? (
                      <TrendingUp className="mr-0.5 h-2.5 w-2.5" />
                    ) : (
                      <TrendingDown className="mr-0.5 h-2.5 w-2.5" />
                    )}
                    {isPos ? "+" : ""}
                    {item.change_percent ? item.change_percent.toFixed(2) : "0.00"}%
                  </span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Right: Manual Refresh & Pulse */}
        <div className="flex shrink-0 items-center pl-2">
          <button
            onClick={() => {
              setLoading(true);
              fetchRibbonData();
            }}
            disabled={loading}
            title={lastRefreshed ? `Last refreshed: ${lastRefreshed.toLocaleTimeString()}` : "Refresh ribbon"}
            className="flex h-7 w-7 items-center justify-center rounded-md border border-slate-800 bg-slate-900/60 text-slate-400 hover:border-slate-700 hover:text-slate-200 transition"
          >
            <RefreshCw className={`h-3 w-3 ${loading ? "animate-spin text-cyan-400" : ""}`} />
          </button>
        </div>
      </div>
    </div>
  );
}
