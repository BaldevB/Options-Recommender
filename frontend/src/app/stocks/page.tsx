"use client";

import React, { useState, useEffect, useCallback, useMemo, Suspense } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import {
  TrendingUp,
  TrendingDown,
  LayoutGrid,
  Table as TableIcon,
  Search,
  Filter,
  RefreshCw,
  Wallet,
  Zap,
  Target,
  ShieldCheck,
  Activity,
  Layers,
  Sparkles,
  ArrowRight,
  Flame,
  Star,
  Compass,
  AlertCircle,
  X,
  CheckCircle2,
  Sliders,
  DollarSign,
  ChevronDown,
  ExternalLink,
} from "lucide-react";

import MarketRibbon from "@/components/MarketRibbon";
import StockCard, { StockRecommendationItem } from "@/components/StockCard";
import StockScreenerTable from "@/components/StockScreenerTable";
import StockPositionCalculator from "@/components/StockPositionCalculator";
import StockPaperTradingDrawer from "@/components/StockPaperTradingDrawer";

// Dynamically import StockChart with ssr: false for Lightweight Charts canvas support
const StockChart = dynamic(() => import("@/components/StockChart"), {
  ssr: false,
  loading: () => (
    <div className="h-[480px] w-full rounded-xl bg-slate-900/50 border border-slate-800 flex items-center justify-center text-slate-500 font-mono text-xs">
      <RefreshCw className="w-4 h-4 mr-2 animate-spin text-cyan-400" />
      Loading TradingView Candlestick Chart...
    </div>
  ),
});

interface SectorOption {
  key: string;
  name: string;
  count: number;
}

interface ScreenerStatus {
  status: string;
  cached_stocks?: number;
  cached_count?: number;
  total_stocks: number;
  total_universe: number;
  is_refreshing: boolean;
  last_updated: string | null;
  refresh_interval_sec?: number;
}

const STORAGE_KEY_POSITIONS = "options_paper_positions";
const STORAGE_KEY_BALANCE = "options_paper_balance";
const STORAGE_KEY_STARRED = "options_starred_tickers";

function StockRecommendationsContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  // URL Query Params
  const initialSymbol = searchParams.get("symbol") || searchParams.get("ticker") || "";
  const initialHorizon = searchParams.get("horizon") || "ALL";
  const initialStrategy = searchParams.get("strategy") || "ALL";

  // Navigation & View mode
  const [viewMode, setViewMode] = useState<"grid" | "table">("grid");
  const [activeHorizon, setActiveHorizon] = useState<string>(initialHorizon);
  const [activeStrategy, setActiveStrategy] = useState<string>(initialStrategy);
  const [selectedSector, setSelectedSector] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [sortBy, setSortBy] = useState<string>("score");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");

  // Data State
  const [recommendations, setRecommendations] = useState<StockRecommendationItem[]>([]);
  const [sectors, setSectors] = useState<SectorOption[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [cacheStatus, setCacheStatus] = useState<ScreenerStatus | null>(null);

  // Watchlist & Paper Trading
  const [starredTickers, setStarredTickers] = useState<string[]>([]);
  const [paperBalance, setPaperBalance] = useState<number>(10000);
  const [paperPositionsCount, setPaperPositionsCount] = useState<number>(0);
  const [isPaperDrawerOpen, setIsPaperDrawerOpen] = useState<boolean>(false);

  // Deep Dive Modal State
  const [deepDiveStock, setDeepDiveStock] = useState<StockRecommendationItem | null>(null);
  const [deepDiveAnalysis, setDeepDiveAnalysis] = useState<any>(null);
  const [deepDiveCandles, setDeepDiveCandles] = useState<any[]>([]);
  const [deepDiveLoading, setDeepDiveLoading] = useState<boolean>(false);

  // Quick Calculator Modal
  const [calculatorStock, setCalculatorStock] = useState<StockRecommendationItem | null>(null);

  // Toast feedback
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Show Toast
  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage((cur) => (cur === msg ? null : cur));
    }, 4500);
  };

  // Load Starred and Paper state from localStorage
  useEffect(() => {
    if (typeof window !== "undefined") {
      try {
        const savedStarred = localStorage.getItem(STORAGE_KEY_STARRED);
        if (savedStarred) {
          const parsed = JSON.parse(savedStarred);
          if (Array.isArray(parsed)) setStarredTickers(parsed);
        }

        const savedBalance = localStorage.getItem(STORAGE_KEY_BALANCE);
        if (savedBalance) {
          setPaperBalance(parseFloat(savedBalance) || 10000);
        }

        const savedPos = localStorage.getItem(STORAGE_KEY_POSITIONS);
        if (savedPos) {
          const parsedPos = JSON.parse(savedPos);
          if (Array.isArray(parsedPos)) {
            setPaperPositionsCount(parsedPos.filter((p: any) => p.status === "OPEN").length);
          }
        }
      } catch (err) {
        console.error("Error reading localStorage:", err);
      }
    }
  }, [isPaperDrawerOpen]);

  // Toggle Star
  const handleToggleStar = (sym: string) => {
    const symbol = sym.trim().toUpperCase();
    setStarredTickers((prev) => {
      const isAlready = prev.includes(symbol);
      const updated = isAlready ? prev.filter((s) => s !== symbol) : [...prev, symbol];
      try {
        localStorage.setItem(STORAGE_KEY_STARRED, JSON.stringify(updated));
      } catch (e) {
        console.error("Failed saving starred tickers:", e);
      }
      return updated;
    });
  };

  // Fetch Universe Sectors
  useEffect(() => {
    const fetchUniverse = async () => {
      try {
        const res = await fetch("/api/stocks/universe");
        if (res.ok) {
          const json = await res.json();
          if (json.sectors && Array.isArray(json.sectors)) {
            setSectors(json.sectors);
          }
        }
      } catch (err) {
        console.warn("Could not fetch universe sectors:", err);
      }
    };
    fetchUniverse();
  }, []);

  // Fetch Status
  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch("/api/stocks/status");
      if (res.ok) {
        const json = await res.json();
        setCacheStatus(json);
      }
    } catch (err) {
      console.warn("Could not fetch screener status:", err);
    }
  }, []);

  // Fetch Recommendations
  const fetchRecommendations = useCallback(async () => {
    setError(null);
    try {
      const params = new URLSearchParams();
      if (activeHorizon && activeHorizon !== "ALL") {
        params.set("horizon", activeHorizon);
      }
      if (activeStrategy && activeStrategy !== "ALL") {
        params.set("strategy", activeStrategy);
      }
      if (selectedSector && selectedSector !== "ALL") {
        params.set("sector", selectedSector);
      }
      if (searchQuery.trim()) {
        params.set("search", searchQuery.trim());
      }
      params.set("sort_by", sortBy);
      params.set("limit", "100");

      const res = await fetch(`/api/stocks/recommendations?${params.toString()}`);
      if (!res.ok) {
        throw new Error(`Server returned ${res.status}: ${res.statusText}`);
      }

      const json = await res.json();
      if (json && Array.isArray(json.items)) {
        setRecommendations(json.items);
      } else {
        setRecommendations([]);
      }
    } catch (err: any) {
      console.error("Error fetching stock recommendations:", err);
      setError(err.message || "Failed to load stock recommendations.");
    } finally {
      setLoading(false);
      fetchStatus();
    }
  }, [activeHorizon, activeStrategy, selectedSector, searchQuery, sortBy, fetchStatus]);

  useEffect(() => {
    fetchRecommendations();
  }, [fetchRecommendations]);

  // Auto-poll if screener is actively refreshing or if no recommendations yet
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (cacheStatus?.is_refreshing || recommendations.length === 0) {
      interval = setInterval(() => {
        fetchRecommendations();
      }, 3000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [cacheStatus?.is_refreshing, recommendations.length, fetchRecommendations]);

  // Trigger Force Refresh
  const handleForceRefresh = async () => {
    setRefreshing(true);
    try {
      const res = await fetch("/api/stocks/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ force: true }),
      });
      if (res.ok) {
        showToast("Screener scan started in background. Recommendations will update automatically!");
        await fetchRecommendations();
      } else {
        showToast("Refresh queued or already in progress.");
      }
    } catch (err) {
      console.error("Refresh error:", err);
      showToast("Error triggering refresh.");
    } finally {
      setRefreshing(false);
    }
  };

  // Deep Dive fetch
  const openDeepDive = useCallback(async (stock: StockRecommendationItem) => {
    setDeepDiveStock(stock);
    setDeepDiveLoading(true);
    setDeepDiveAnalysis(null);
    setDeepDiveCandles([]);

    try {
      // 1. Fetch analysis
      const analysisPromise = fetch(`/api/stocks/analysis?symbol=${encodeURIComponent(stock.symbol)}`)
        .then((r) => (r.ok ? r.json() : null))
        .catch(() => null);

      // 2. Fetch candles for TradingView chart
      const candlesPromise = fetch(
        `/api/candles?ticker=${encodeURIComponent(stock.symbol)}&interval=1d&period=6mo`
      )
        .then((r) => (r.ok ? r.json() : null))
        .catch(() => null);

      const [analysisRes, candlesRes] = await Promise.all([analysisPromise, candlesPromise]);

      if (analysisRes) setDeepDiveAnalysis(analysisRes);
      if (candlesRes && Array.isArray(candlesRes.candles)) {
        setDeepDiveCandles(candlesRes.candles);
      }
    } catch (err) {
      console.error("Error fetching deep dive:", err);
    } finally {
      setDeepDiveLoading(false);
    }
  }, []);

  // Handle URL ?symbol= query parameter
  useEffect(() => {
    if (initialSymbol && recommendations.length > 0 && !deepDiveStock) {
      const matched = recommendations.find(
        (r) => r.symbol.toUpperCase() === initialSymbol.trim().toUpperCase()
      );
      if (matched) {
        openDeepDive(matched);
      } else {
        // Fetch on-demand analysis
        openDeepDive({
          symbol: initialSymbol.toUpperCase(),
          name: `${initialSymbol.toUpperCase()} Equity`,
          sector: "Selected",
          horizon: "SWING",
          action: "BUY",
          score: 80,
          confidence: 0.8,
          momentum_score: 0.5,
          sentiment_score: 0.2,
          trade_plan: {
            entry_zone: [0, 0],
            current_price: 0,
            tp1: 0,
            tp2: 0,
            stop_loss: 0,
            risk_reward_ratio: 2.0,
            invalidation_pct: 5.0,
            tp1_pct: 15.0,
            tp2_pct: 30.0,
          },
          rationale: [],
          price: 0,
          change: 0,
          change_pct: 0,
          volume_ratio: 1.0,
          rsi: 50,
          target_pct: 15.0,
        });
      }
    }
  }, [initialSymbol, recommendations, deepDiveStock, openDeepDive]);

  // Handle Sort Toggle
  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(column);
      setSortDirection("desc");
    }
  };

  // Filtered & Sorted items for Table/Grid
  const sortedRecommendations = useMemo(() => {
    const list = [...recommendations];
    if (sortDirection === "asc") {
      list.reverse();
    }
    return list;
  }, [recommendations, sortDirection]);

  // Top statistics
  const stats = useMemo(() => {
    const total = recommendations.length;
    if (total === 0) return { total: 0, avgScore: "0.0", strongBuys: 0, avgGain: "0.0" };
    const avgScore = recommendations.reduce((acc, r) => acc + (r.score || 0), 0) / total;
    const strongBuys = recommendations.filter((r) => (r.action || "").includes("STRONG")).length;
    const avgGain = recommendations.reduce((acc, r) => acc + (r.trade_plan?.tp1_pct || 0), 0) / total;
    return {
      total,
      avgScore: avgScore.toFixed(1),
      strongBuys,
      avgGain: avgGain.toFixed(1),
    };
  }, [recommendations]);

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Top Market Ribbon */}
      <MarketRibbon
        onSelectTicker={(ticker) => {
          const matched = recommendations.find((r) => r.symbol === ticker);
          if (matched) openDeepDive(matched);
        }}
        starredTickers={starredTickers}
        onToggleStar={handleToggleStar}
      />

      {/* Main App Navbar Header */}
      <header className="sticky top-0 z-40 border-b border-slate-800/80 bg-[#070b14]/90 backdrop-blur-md px-4 sm:px-6 py-3">
        <div className="flex flex-wrap items-center justify-between gap-3 max-w-7xl mx-auto w-full">
          {/* Logo, Title & Route Switcher */}
          <div className="flex items-center gap-3 sm:gap-4">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-xl bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 border border-emerald-500/40 text-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.25)]">
                <TrendingUp className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-base sm:text-lg font-black tracking-tight text-slate-100 flex items-center gap-2">
                  OPTIONS SUGGESTER <span className="text-emerald-400 font-mono text-xs uppercase px-1.5 py-0.5 rounded bg-emerald-950/40 border border-emerald-800/40">PRO</span>
                </h1>
                <p className="text-[11px] text-slate-400 hidden sm:block">
                  Quantitative Stock Trade Plans &bull; Multi-Factor Momentum &bull; Paper Trading
                </p>
              </div>
            </div>

            {/* Top-Level Route Switcher */}
            <div className="flex items-center gap-1 p-1 rounded-xl bg-slate-900/90 border border-slate-800 shadow-inner ml-2">
              <Link
                href="/"
                className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-400 hover:text-cyan-300 hover:bg-slate-800/60 border border-transparent hover:border-cyan-500/30 transition-all flex items-center gap-1.5"
              >
                <span>⚡</span> Options Pro
              </Link>
              <div className="px-3 py-1.5 rounded-lg text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-[0_0_12px_rgba(16,185,129,0.25)] flex items-center gap-1.5">
                <span>📈</span> Stock Picks Pro
              </div>
            </div>
          </div>

          {/* Quick Header Actions */}
          <div className="flex items-center gap-2">
            {/* Live Screener Scan Indicator */}
            {cacheStatus?.is_refreshing && (
              <span className="hidden md:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-mono text-cyan-300 bg-cyan-950/40 border border-cyan-800/40">
                <RefreshCw className="w-3 h-3 animate-spin text-cyan-400" />
                Scanning Universe ({cacheStatus.cached_stocks || recommendations.length}/{cacheStatus.total_stocks || 1100})
              </span>
            )}

            {/* Paper Portfolio Drawer Toggle */}
            <button
              type="button"
              onClick={() => setIsPaperDrawerOpen(true)}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-900 hover:bg-slate-800 border border-slate-700/80 hover:border-cyan-500/40 text-slate-200 transition-all shadow-sm"
              title="Open Paper Portfolio"
            >
              <Wallet className="w-4 h-4 text-cyan-400" />
              <span className="hidden sm:inline">Paper Portfolio</span>
              {paperPositionsCount > 0 && (
                <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                  {paperPositionsCount}
                </span>
              )}
            </button>

            {/* Refresh Screener */}
            <button
              type="button"
              onClick={handleForceRefresh}
              disabled={refreshing}
              className="p-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700/80 text-slate-300 hover:text-cyan-300 transition-colors"
              title="Refresh Screener Cache"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing || cacheStatus?.is_refreshing ? "animate-spin text-cyan-400" : ""}`} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 space-y-6">
        {/* Horizon Tabs, Strategy Presets & Filter Toolbar */}
        <div className="flex flex-col gap-3.5 bg-[#0a101f] border border-slate-800/80 rounded-2xl p-4 shadow-xl">
          {/* Horizon Tabs */}
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/70 pb-3">
            <div className="flex flex-wrap items-center gap-1 sm:gap-2">
              {[
                { id: "ALL", label: "All Horizons", icon: Compass },
                { id: "SWING", label: "⚡ Swing Momentum (2-6w)", icon: Zap },
                { id: "LONG_TERM", label: "💎 Long-Term Conviction (3-12m)", icon: Sparkles },
                { id: "BREAKOUT", label: "🚀 Breakout Volume (>1.2x)", icon: Flame },
              ].map((tab) => {
                const Icon = tab.icon;
                const isActive = activeHorizon === tab.id;
                return (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => setActiveHorizon(tab.id)}
                    className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                      isActive
                        ? "bg-gradient-to-r from-cyan-500/20 to-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-[0_0_15px_rgba(16,185,129,0.2)] font-bold"
                        : "bg-slate-900/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-slate-800"
                    }`}
                  >
                    <Icon className={`w-3.5 h-3.5 ${isActive ? "text-emerald-400" : "text-slate-400"}`} />
                    {tab.label}
                  </button>
                );
              })}
            </div>

            {/* View Switcher: Card Grid vs Screener Table */}
            <div className="flex items-center gap-1 p-1 rounded-xl bg-slate-900 border border-slate-800">
              <button
                type="button"
                onClick={() => setViewMode("grid")}
                className={`p-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1 ${
                  viewMode === "grid"
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                    : "text-slate-400 hover:text-slate-200"
                }`}
                title="Grid Card View"
              >
                <LayoutGrid className="w-4 h-4" />
                <span className="text-[11px] hidden sm:inline">Cards</span>
              </button>
              <button
                type="button"
                onClick={() => setViewMode("table")}
                className={`p-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1 ${
                  viewMode === "table"
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                    : "text-slate-400 hover:text-slate-200"
                }`}
                title="Pro Screener Table View"
              >
                <TableIcon className="w-4 h-4" />
                <span className="text-[11px] hidden sm:inline">Screener Table</span>
              </button>
            </div>
          </div>

          {/* Strategy Preset Filters */}
          <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
            <span className="text-[11px] font-semibold text-slate-400 mr-1 flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              Strategy:
            </span>
            {[
              { id: "ALL", label: "All Strategies" },
              { id: "rs_leaders", label: "⚡ RS Leaders (RS ≥ 75)", highlight: "cyan" },
              { id: "breakouts", label: "🚀 52W Breakouts (< 5%)", highlight: "amber" },
              { id: "golden_cross", label: "🌟 Golden Cross", highlight: "purple" },
              { id: "pullback", label: "🎯 Pullback Dips", highlight: "emerald" },
            ].map((strat) => {
              const isActive = activeStrategy === strat.id;
              return (
                <button
                  key={strat.id}
                  type="button"
                  onClick={() => setActiveStrategy(strat.id)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
                    isActive
                      ? strat.highlight === "amber"
                        ? "bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-[0_0_12px_rgba(245,158,11,0.25)] font-bold"
                        : strat.highlight === "purple"
                        ? "bg-purple-500/20 text-purple-300 border border-purple-500/40 shadow-[0_0_12px_rgba(168,85,247,0.25)] font-bold"
                        : strat.highlight === "emerald"
                        ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-[0_0_12px_rgba(16,185,129,0.25)] font-bold"
                        : "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_12px_rgba(6,182,212,0.25)] font-bold"
                      : "bg-slate-900/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800/80 border border-slate-800"
                  }`}
                >
                  {strat.label}
                </button>
              );
            })}
          </div>

          {/* Search, Sector, and Sort Controls Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-800/60">
            <div className="flex flex-wrap items-center gap-3 flex-1 min-w-[280px]">
              {/* Search Bar */}
              <div className="relative flex-1 min-w-[220px] max-w-md">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="text"
                  placeholder="Search ticker or company (e.g., NVDA, Copper, CCJ)..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full rounded-xl bg-slate-900 border border-slate-700/80 pl-9 pr-8 py-2 text-xs text-slate-100 placeholder:text-slate-500 focus:border-cyan-500 focus:outline-none transition-colors"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery("")}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>

              {/* Sector Dropdown */}
              <div className="relative">
                <select
                  value={selectedSector}
                  onChange={(e) => setSelectedSector(e.target.value)}
                  className="rounded-xl bg-slate-900 border border-slate-700/80 px-3 py-2 pr-8 text-xs font-medium text-slate-200 focus:border-cyan-500 focus:outline-none appearance-none cursor-pointer"
                >
                  <option value="ALL">All Sectors ({sectors.reduce((acc, s) => acc + s.count, 0) || "1,000+"})</option>
                  {sectors.map((sec) => (
                    <option key={sec.key} value={sec.key}>
                      {sec.name} ({sec.count})
                    </option>
                  ))}
                </select>
                <ChevronDown className="w-3.5 h-3.5 absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
              </div>
            </div>

            {/* Sort Selector */}
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-400 font-medium">Sort By:</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="rounded-xl bg-slate-900 border border-slate-700/80 px-3 py-1.5 text-xs text-slate-200 focus:border-cyan-500 focus:outline-none cursor-pointer"
              >
                <option value="score">Quant Score (Highest)</option>
                <option value="rs">Relative Strength (RS Rating)</option>
                <option value="dist_52w">Distance to 52W High (Closest)</option>
                <option value="change_pct">24h Gain (%)</option>
                <option value="volume_ratio">Volume Breakout</option>
                <option value="target_pct">Target Gain (TP1 %)</option>
                <option value="risk_reward">Risk / Reward Ratio</option>
                <option value="rsi">RSI</option>
                <option value="symbol">Ticker (A-Z)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Screener Stats Summary Banner */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3.5 rounded-xl border border-slate-800 bg-[#090e1b] flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
              <Target className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[10px] uppercase font-semibold text-slate-400 block tracking-wider">
                Stocks Screened
              </span>
              <span className="font-mono text-base font-bold text-slate-100">
                {stats.total} Live Picks
              </span>
            </div>
          </div>

          <div className="p-3.5 rounded-xl border border-slate-800 bg-[#090e1b] flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[10px] uppercase font-semibold text-slate-400 block tracking-wider">
                Strong Buy Signals
              </span>
              <span className="font-mono text-base font-bold text-emerald-400">
                {stats.strongBuys} Top Ranked
              </span>
            </div>
          </div>

          <div className="p-3.5 rounded-xl border border-slate-800 bg-[#090e1b] flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400">
              <Activity className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[10px] uppercase font-semibold text-slate-400 block tracking-wider">
                Avg Quant Score
              </span>
              <span className="font-mono text-base font-bold text-purple-300">
                {stats.avgScore} / 100
              </span>
            </div>
          </div>

          <div className="p-3.5 rounded-xl border border-slate-800 bg-[#090e1b] flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400">
              <TrendingUp className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[10px] uppercase font-semibold text-slate-400 block tracking-wider">
                Avg Target 1 Gain
              </span>
              <span className="font-mono text-base font-bold text-amber-300">
                +{stats.avgGain}%
              </span>
            </div>
          </div>
        </div>

        {/* Content View: Loading, Error, Grid or Table */}
        {loading && recommendations.length === 0 ? (
          <div className="py-20 flex flex-col items-center justify-center space-y-3">
            <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
            <p className="text-sm font-mono text-slate-400">Scanning 1,000+ US stock universe &amp; computing signals...</p>
          </div>
        ) : error && recommendations.length === 0 ? (
          <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-6 h-6 text-rose-400 flex-shrink-0" />
              <div>
                <h4 className="font-bold text-sm">Failed to load recommendations</h4>
                <p className="text-xs text-rose-400">{error}</p>
              </div>
            </div>
            <button
              onClick={fetchRecommendations}
              className="px-4 py-2 rounded-xl bg-rose-600/30 hover:bg-rose-600/50 border border-rose-500/40 text-xs font-semibold transition-colors"
            >
              Retry
            </button>
          </div>
        ) : sortedRecommendations.length === 0 ? (
          <div className="py-20 text-center rounded-2xl border border-slate-800 bg-[#090e1b] p-8">
            {cacheStatus?.is_refreshing ? (
              <div className="flex flex-col items-center justify-center">
                <RefreshCw className="w-10 h-10 text-cyan-400 animate-spin mb-3" />
                <h3 className="text-base font-bold text-slate-200">Scanning US Stock Universe...</h3>
                <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto font-mono">
                  The quantitative screener is calculating multi-factor momentum and moving averages across 1,100+ tickers. Live recommendations will display automatically.
                </p>
              </div>
            ) : (
              <>
                <Compass className="w-12 h-12 mx-auto text-slate-600 mb-3 opacity-60" />
                <h3 className="text-base font-bold text-slate-200">No stock picks found</h3>
                <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
                  No recommendations match the filter criteria. Try resetting your search or selecting &ldquo;All Sectors&rdquo;.
                </p>
                <button
                  type="button"
                  onClick={() => {
                    setActiveHorizon("ALL");
                    setActiveStrategy("ALL");
                    setSelectedSector("ALL");
                    setSearchQuery("");
                  }}
                  className="mt-4 px-4 py-2 rounded-xl bg-cyan-600/25 hover:bg-cyan-600/40 text-cyan-300 border border-cyan-500/40 text-xs font-semibold transition-colors"
                >
                  Reset Filters
                </button>
              </>
            )}
          </div>
        ) : viewMode === "grid" ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {sortedRecommendations.map((stock) => (
              <StockCard
                key={stock.symbol}
                stock={stock}
                onDeepDive={openDeepDive}
                onPaperBuy={(stk) => setCalculatorStock(stk)}
                isStarred={starredTickers.includes(stock.symbol)}
                onToggleStar={handleToggleStar}
              />
            ))}
          </div>
        ) : (
          <StockScreenerTable
            stocks={sortedRecommendations}
            sortBy={sortBy}
            sortDirection={sortDirection}
            onSort={handleSort}
            onDeepDive={openDeepDive}
            onPaperBuy={(stk) => setCalculatorStock(stk)}
            starredTickers={starredTickers}
            onToggleStar={handleToggleStar}
          />
        )}
      </main>

      {/* Deep-Dive Inspection Modal */}
      {deepDiveStock && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-black/75 backdrop-blur-md flex items-center justify-center p-3 sm:p-6 animate-in fade-in duration-200">
          <div className="relative w-full max-w-5xl bg-[#090e1c] border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
            {/* Modal Header */}
            <div className="p-4 sm:p-5 border-b border-slate-800 bg-[#070b14] flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
                  <Target className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <h2 className="text-xl font-black font-mono tracking-wider text-slate-100">
                      {deepDiveStock.symbol}
                    </h2>
                    <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                      {deepDiveStock.action}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-medium">
                      {deepDiveStock.sector}
                    </span>
                    {deepDiveStock.strategy_tag && (
                      <span className="text-xs px-2 py-0.5 rounded font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                        {deepDiveStock.strategy_tag.replace(/_/g, " ")}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">{deepDiveStock.name}</p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Link
                  href={`/?ticker=${encodeURIComponent(deepDiveStock.symbol)}`}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-cyan-500/30 text-xs font-semibold transition-colors inline-flex items-center gap-1.5"
                  title="View Options Chain"
                >
                  <Layers className="w-3.5 h-3.5" />
                  <span>Options Chain</span>
                </Link>
                <button
                  type="button"
                  onClick={() => setDeepDiveStock(null)}
                  className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-100 border border-slate-700 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="overflow-y-auto p-4 sm:p-6 space-y-6 flex-1">
              {/* TradingView Chart */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-xs uppercase font-bold text-slate-400 tracking-wider flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5 text-cyan-400" />
                    TradingView Candlestick Chart &amp; Moving Averages
                  </h3>
                  <span className="text-[11px] text-slate-500 font-mono">Interactive &bull; Multi-Timeframe</span>
                </div>
                <div className="rounded-xl overflow-hidden border border-slate-800 bg-[#0c1322]">
                  <StockChart symbol={deepDiveStock.symbol} data={deepDiveCandles} />
                </div>
              </div>

              {/* Trade Plan Detailed Breakdown */}
              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
                <h3 className="text-xs uppercase font-bold text-emerald-400 tracking-wider flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4" />
                  Quantitative Trade Plan &amp; Risk Parameters
                </h3>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase block">Current Price</span>
                    <span className="font-mono font-bold text-slate-100 text-sm">
                      ${deepDiveStock.price > 0 ? deepDiveStock.price.toFixed(2) : deepDiveStock.trade_plan.current_price.toFixed(2)}
                    </span>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase block">Recommended Entry</span>
                    <span className="font-mono font-bold text-cyan-300 text-sm">
                      ${deepDiveStock.trade_plan.entry_zone ? `${deepDiveStock.trade_plan.entry_zone[0].toFixed(2)} - ${deepDiveStock.trade_plan.entry_zone[1].toFixed(2)}` : deepDiveStock.price.toFixed(2)}
                    </span>
                  </div>

                  <div className="p-3 rounded-lg bg-emerald-950/25 border border-emerald-900/40">
                    <span className="text-[10px] text-emerald-400 uppercase block">Target 1 (TP1)</span>
                    <span className="font-mono font-bold text-emerald-300 text-sm">
                      ${deepDiveStock.trade_plan.tp1.toFixed(2)} (+{deepDiveStock.trade_plan.tp1_pct.toFixed(1)}%)
                    </span>
                  </div>

                  <div className="p-3 rounded-lg bg-rose-950/25 border border-rose-900/40">
                    <span className="text-[10px] text-rose-400 uppercase block">Stop Loss (SL)</span>
                    <span className="font-mono font-bold text-rose-300 text-sm">
                      ${deepDiveStock.trade_plan.stop_loss.toFixed(2)} (-{deepDiveStock.trade_plan.invalidation_pct.toFixed(1)}%)
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs pt-1">
                  <div className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/80">
                    <span className="text-[10px] text-slate-400 uppercase block">Relative Strength</span>
                    <span className="font-mono font-bold text-cyan-300">
                      {deepDiveStock.relative_strength_score !== undefined
                        ? `RS ${Math.round(deepDiveStock.relative_strength_score)}/99`
                        : "—"}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/80">
                    <span className="text-[10px] text-slate-400 uppercase block">52W High Distance</span>
                    <span className="font-mono font-bold text-amber-300">
                      {deepDiveStock.distance_from_52w_high_pct !== undefined
                        ? deepDiveStock.distance_from_52w_high_pct >= -0.1
                          ? "AT HIGH"
                          : `${deepDiveStock.distance_from_52w_high_pct.toFixed(1)}%`
                        : "—"}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/80">
                    <span className="text-[10px] text-slate-400 uppercase block">RSI (14)</span>
                    <span className="font-mono font-bold text-slate-200">
                      {deepDiveStock.rsi.toFixed(1)}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/80">
                    <span className="text-[10px] text-slate-400 uppercase block">Vol Confirmation</span>
                    <span className="font-mono font-bold text-amber-300">
                      {deepDiveStock.volume_ratio.toFixed(2)}x 20d Avg
                    </span>
                  </div>
                </div>
              </div>

              {/* Rationale & News Sentiment */}
              {deepDiveStock.rationale && deepDiveStock.rationale.length > 0 && (
                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                  <h4 className="text-xs uppercase font-bold text-slate-400 tracking-wider">
                    Signal Rationale &amp; Catalyst Breakdown
                  </h4>
                  <ul className="space-y-1.5 text-xs text-slate-300">
                    {deepDiveStock.rationale.map((reason, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0 mt-0.5" />
                        <span>{reason}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Embedded Position Sizing Calculator */}
              <div>
                <StockPositionCalculator
                  stock={deepDiveStock}
                  virtualBalance={paperBalance}
                  onTradeSimulated={(trade) => {
                    showToast(
                      `Paper trade filled: ${trade.shares} shares of ${trade.symbol} @ $${trade.price.toFixed(2)} ($${trade.totalCost.toFixed(2)})`
                    );
                    setPaperBalance((prev) => Math.max(0, prev - trade.totalCost));
                    setPaperPositionsCount((prev) => prev + 1);
                  }}
                  onClose={() => setDeepDiveStock(null)}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Standalone Position Calculator Modal (when clicking Paper Buy from Card/Table) */}
      {calculatorStock && !deepDiveStock && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="relative w-full max-w-2xl">
            <StockPositionCalculator
              stock={calculatorStock}
              virtualBalance={paperBalance}
              onTradeSimulated={(trade) => {
                showToast(
                  `Paper trade filled: ${trade.shares} shares of ${trade.symbol} @ $${trade.price.toFixed(2)} ($${trade.totalCost.toFixed(2)})`
                );
                setPaperBalance((prev) => Math.max(0, prev - trade.totalCost));
                setPaperPositionsCount((prev) => prev + 1);
                setCalculatorStock(null);
              }}
              onClose={() => setCalculatorStock(null)}
            />
          </div>
        </div>
      )}

      {/* Paper Trading Drawer */}
      <StockPaperTradingDrawer
        isOpen={isPaperDrawerOpen}
        onClose={() => setIsPaperDrawerOpen(false)}
        onNavigateToStock={(sym) => {
          const matched = recommendations.find((r) => r.symbol === sym);
          if (matched) openDeepDive(matched);
        }}
        onNavigateToOptions={(sym) => {
          router.push(`/?ticker=${encodeURIComponent(sym)}`);
        }}
      />

      {/* Toast Notification Banner */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 p-4 rounded-xl bg-slate-900 border border-emerald-500/50 text-emerald-300 text-xs font-semibold shadow-[0_0_25px_rgba(16,185,129,0.3)] flex items-center gap-3 animate-in fade-in slide-in-from-bottom-2">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
          <span>{toastMessage}</span>
          <button onClick={() => setToastMessage(null)} className="text-slate-400 hover:text-slate-200">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}

export default function StockRecommendationsPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#070b14] flex items-center justify-center text-cyan-400 font-mono text-sm">
          <RefreshCw className="w-5 h-5 mr-2 animate-spin" />
          Initializing Stock Picks Pro Terminal...
        </div>
      }
    >
      <StockRecommendationsContent />
    </Suspense>
  );
}
