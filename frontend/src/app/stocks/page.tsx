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
  Download,
} from "lucide-react";

import MarketRibbon from "@/components/MarketRibbon";
import StockCard, { StockRecommendationItem } from "@/components/StockCard";
import StockScreenerTable from "@/components/StockScreenerTable";
import StockPositionCalculator from "@/components/StockPositionCalculator";
import StockPaperTradingDrawer from "@/components/StockPaperTradingDrawer";
import { StockMonteCarlo } from "@/components/StockMonteCarlo";

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

const STRATEGY_PRESETS = [
  { id: "ALL", label: "⚡ All Setups" },
  { id: "STAGE_2_LEADERS", label: "🏆 Minervini Stage 2", highlight: "amber" },
  { id: "VCP_SQUEEZES", label: "🗜️ VCP Squeezes", highlight: "purple" },
  { id: "INSTITUTIONAL_INFLOW", label: "🏦 Institutional Inflow A+", highlight: "emerald" },
  { id: "VELOCITY_BREAKOUT", label: "🚀 Velocity Breakouts", highlight: "cyan" },
  { id: "PULLBACK_DIP", label: "📉 Pullback Dips", highlight: "emerald" },
];

const PRICE_RANGE_OPTIONS = [
  { id: "ALL", label: "All Prices" },
  { id: "UNDER_25", label: "Under $25" },
  { id: "25_TO_100", label: "$25 - $100" },
  { id: "100_TO_250", label: "$100 - $250" },
  { id: "ABOVE_250", label: "$250+" },
];

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
  const initialPreset = searchParams.get("strategy_preset") || searchParams.get("preset") || "ALL";
  const initialPriceRange = searchParams.get("price_range") || "ALL";

  // Navigation & View mode
  const [viewMode, setViewMode] = useState<"grid" | "table">("grid");
  const [activeHorizon, setActiveHorizon] = useState<string>(initialHorizon);
  const [activeStrategy, setActiveStrategy] = useState<string>(initialStrategy);
  const [activePreset, setActivePreset] = useState<string>(initialPreset);
  const [priceRange, setPriceRange] = useState<string>(initialPriceRange);
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
  const [deepDiveTab, setDeepDiveTab] = useState<"overview" | "monte_carlo">("overview");

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

  // Price Bounds mapping
  const priceBounds = useMemo(() => {
    switch (priceRange) {
      case "UNDER_25":
        return { min: undefined, max: 25 };
      case "25_TO_100":
        return { min: 25, max: 100 };
      case "100_TO_250":
        return { min: 100, max: 250 };
      case "ABOVE_250":
        return { min: 250, max: undefined };
      default:
        return { min: undefined, max: undefined };
    }
  }, [priceRange]);

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
      if (activePreset && activePreset !== "ALL") {
        params.set("strategy_preset", activePreset);
      } else if (activeStrategy && activeStrategy !== "ALL") {
        params.set("strategy", activeStrategy);
      }
      if (selectedSector && selectedSector !== "ALL") {
        params.set("sector", selectedSector);
      }
      if (searchQuery.trim()) {
        params.set("search", searchQuery.trim());
      }
      if (priceBounds.min !== undefined) {
        params.set("min_price", priceBounds.min.toString());
      }
      if (priceBounds.max !== undefined) {
        params.set("max_price", priceBounds.max.toString());
      }
      params.set("sort_by", sortBy);
      params.set("limit", "100");

      const res = await fetch(`/api/stocks/recommendations?${params.toString()}`);
      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}`);
      }
      const data = await res.json();
      if (data && Array.isArray(data.items)) {
        setRecommendations(data.items);
      } else {
        setRecommendations([]);
      }
    } catch (err: any) {
      console.error("Error fetching stock recommendations:", err);
      setError(err.message || "Failed to load stock recommendations");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [activeHorizon, activeStrategy, activePreset, priceBounds, selectedSector, searchQuery, sortBy]);

  // Initial and reactive fetch
  useEffect(() => {
    fetchRecommendations();
    fetchStatus();
  }, [fetchRecommendations, fetchStatus]);

  // Periodic poll of status to monitor background universe scanner
  useEffect(() => {
    const timer = setInterval(() => {
      fetchStatus();
    }, 15000);
    return () => clearInterval(timer);
  }, [fetchStatus]);

  // Manual Trigger Refresh
  const handleManualRefresh = async () => {
    setRefreshing(true);
    await fetchRecommendations();
    await fetchStatus();
  };

  // Open Deep Dive Modal for a stock
  const openDeepDive = useCallback(
    async (stk: StockRecommendationItem) => {
      setDeepDiveStock(stk);
      setDeepDiveTab("overview");
      setDeepDiveLoading(true);
      setDeepDiveAnalysis(null);
      setDeepDiveCandles([]);

      try {
        // Fetch OHLCV candles for TradingView chart
        const candleRes = await fetch(
          `/api/candles?ticker=${encodeURIComponent(stk.symbol)}&timeframe=daily`
        );
        if (candleRes.ok) {
          const cData = await candleRes.json();
          if (cData && Array.isArray(cData.candles)) {
            setDeepDiveCandles(cData.candles);
          }
        }

        // Fetch deep dive analysis if needed
        const deepRes = await fetch(
          `/api/stocks/analysis?symbol=${encodeURIComponent(stk.symbol)}`
        );
        if (deepRes.ok) {
          const aData = await deepRes.json();
          setDeepDiveAnalysis(aData);
        }
      } catch (err) {
        console.error("Error loading deep dive modal data:", err);
      } finally {
        setDeepDiveLoading(false);
      }
    },
    []
  );

  // Auto-open deep-dive if ticker passed via query param
  useEffect(() => {
    if (initialSymbol && recommendations.length > 0 && !deepDiveStock) {
      const match = recommendations.find(
        (r) => r.symbol.toUpperCase() === initialSymbol.toUpperCase()
      );
      if (match) {
        openDeepDive(match);
      } else {
        // If not in current page, load on-demand deep dive
        openDeepDive({
          symbol: initialSymbol.toUpperCase(),
          name: initialSymbol.toUpperCase(),
          sector: "Equities",
          horizon: "SWING",
          action: "BUY ACCUMULATE",
          score: 80.0,
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
            tp1_pct: 10.0,
            tp2_pct: 18.0,
          },
          rationale: ["On-demand ticker deep dive requested."],
          price: 0,
          change: 0,
          change_pct: 0,
          volume_ratio: 1.0,
          rsi: 50.0,
          target_pct: 10.0,
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
    if (total === 0) return { total: 0, avgScore: "0.0", strongBuys: 0, avgGain: "0.0", stage2Count: 0 };
    const avgScore = recommendations.reduce((acc, r) => acc + (r.score || 0), 0) / total;
    const strongBuys = recommendations.filter((r) => (r.action || "").includes("STRONG")).length;
    const avgGain = recommendations.reduce((acc, r) => acc + (r.trade_plan?.tp1_pct || 0), 0) / total;
    const stage2Count = recommendations.filter((r) => r.is_stage_2).length;
    return {
      total,
      avgScore: avgScore.toFixed(1),
      strongBuys,
      avgGain: avgGain.toFixed(1),
      stage2Count,
    };
  }, [recommendations]);

  // Export current filtered recommendations to CSV
  const handleExportCSV = useCallback(() => {
    if (!sortedRecommendations.length) return;

    const headers = [
      "Symbol",
      "Name",
      "Sector",
      "Score",
      "Action",
      "Price",
      "3D ROC %",
      "5D RVOL",
      "RS Rating",
      "Stage 2",
      "VCP Squeeze",
      "Flow Rating",
      "TP1",
      "Stop Loss",
      "R:R Ratio",
      "Earnings Days Away",
    ];

    const escapeCSV = (val: any): string => {
      if (val === null || val === undefined) return "";
      const str = String(val);
      if (str.includes(",") || str.includes('"') || str.includes("\n")) {
        return `"${str.replace(/"/g, '""')}"`;
      }
      return str;
    };

    const rows = sortedRecommendations.map((stock) => {
      const priceVal = stock.price > 0 ? stock.price : stock.trade_plan?.current_price ?? 0;
      const rvolVal =
        stock.short_term_rvol !== undefined
          ? stock.short_term_rvol
          : stock.volume_ratio !== undefined
          ? stock.volume_ratio
          : "";
      const rsVal =
        stock.relative_strength_score !== undefined
          ? Math.round(stock.relative_strength_score)
          : "";
      const earningsAway =
        stock.earnings_days_away !== null && stock.earnings_days_away !== undefined
          ? stock.earnings_days_away
          : "";

      return [
        escapeCSV(stock.symbol),
        escapeCSV(stock.name),
        escapeCSV(stock.sector),
        escapeCSV(stock.score?.toFixed(1)),
        escapeCSV(stock.action),
        escapeCSV(priceVal ? priceVal.toFixed(2) : ""),
        escapeCSV(stock.roc_3d !== undefined ? stock.roc_3d.toFixed(1) : ""),
        escapeCSV(typeof rvolVal === "number" ? rvolVal.toFixed(2) : rvolVal),
        escapeCSV(rsVal),
        escapeCSV(stock.is_stage_2 ? "YES" : "NO"),
        escapeCSV(stock.is_vcp_squeeze ? "YES" : "NO"),
        escapeCSV(stock.accumulation_rating || ""),
        escapeCSV(stock.trade_plan?.tp1 ? stock.trade_plan.tp1.toFixed(2) : ""),
        escapeCSV(stock.trade_plan?.stop_loss ? stock.trade_plan.stop_loss.toFixed(2) : ""),
        escapeCSV(stock.trade_plan?.risk_reward_ratio ? stock.trade_plan.risk_reward_ratio.toFixed(2) : ""),
        escapeCSV(earningsAway),
      ].join(",");
    });

    const csvContent = [headers.join(","), ...rows].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const dateStr = new Date().toISOString().split("T")[0];
    const a = document.createElement("a");
    a.href = url;
    a.download = `stocks_screener_export_${dateStr}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast(`Exported ${sortedRecommendations.length} picks to CSV`);
  }, [sortedRecommendations]);

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
              <Wallet className="w-4 h-4 text-emerald-400" />
              <span className="hidden sm:inline">Paper Portfolio</span>
              <span className="font-mono font-bold text-emerald-300">
                ${paperBalance.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
              </span>
              {paperPositionsCount > 0 && (
                <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-bold">
                  {paperPositionsCount}
                </span>
              )}
            </button>

            {/* Refresh Button */}
            <button
              type="button"
              onClick={handleManualRefresh}
              disabled={refreshing}
              className="p-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700/80 hover:border-cyan-500/40 text-slate-300 hover:text-cyan-300 transition-colors"
              title="Refresh recommendations"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin text-cyan-400" : ""}`} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Body Container */}
      <main className="max-w-7xl mx-auto w-full px-4 sm:px-6 py-6 flex-1 space-y-6">
        {/* Controls Container */}
        <div className="space-y-4 rounded-2xl border border-slate-800 bg-[#0b1220]/80 p-4 sm:p-5 backdrop-blur-md shadow-xl">
          {/* Horizon & View Switcher Row */}
          <div className="flex flex-wrap items-center justify-between gap-3">
            {/* Horizon Filter Tabs */}
            <div className="flex flex-wrap items-center gap-1.5 p-1 rounded-xl bg-slate-900 border border-slate-800">
              {[
                { id: "ALL", label: "All Horizons", icon: Layers },
                { id: "SWING", label: "⚡ Swing (2-6w)", icon: Zap },
                { id: "LONG_TERM", label: "💎 Long-Term (3-12m)", icon: ShieldCheck },
                { id: "BREAKOUT", label: "🚀 Breakouts", icon: Flame },
              ].map((tab) => {
                const Icon = tab.icon;
                const isActive = activeHorizon === tab.id;
                return (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => setActiveHorizon(tab.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                      isActive
                        ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-[0_0_12px_rgba(16,185,129,0.25)] font-bold"
                        : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                    }`}
                  >
                    <Icon className={`w-3.5 h-3.5 ${isActive ? "text-emerald-400" : "text-slate-400"}`} />
                    {tab.label}
                  </button>
                );
              })}
            </div>

            {/* Right Header Actions: CSV Export + View Switcher */}
            <div className="flex items-center gap-2">
              {/* CSV Export Button */}
              <button
                type="button"
                onClick={handleExportCSV}
                disabled={sortedRecommendations.length === 0}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-900 hover:bg-slate-800 border border-slate-700/80 hover:border-cyan-500/40 text-slate-200 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm"
                title="Export current filtered recommendations to CSV"
              >
                <Download className="w-3.5 h-3.5 text-cyan-400" />
                <span className="hidden sm:inline">Export CSV</span>
              </button>

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
          </div>

          {/* Strategy Preset Chips Bar */}
          <div className="flex flex-wrap items-center gap-1.5 sm:gap-2 pt-1 border-t border-slate-800/50">
            <span className="text-[11px] font-semibold text-slate-400 mr-1 flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              Presets:
            </span>
            {STRATEGY_PRESETS.map((preset) => {
              const isActive = activePreset === preset.id;
              return (
                <button
                  key={preset.id}
                  type="button"
                  onClick={() => {
                    setActivePreset(preset.id);
                    setActiveStrategy("ALL");
                  }}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    isActive
                      ? preset.highlight === "amber"
                        ? "bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-[0_0_12px_rgba(245,158,11,0.25)] font-bold"
                        : preset.highlight === "purple"
                        ? "bg-purple-500/20 text-purple-300 border border-purple-500/40 shadow-[0_0_12px_rgba(168,85,247,0.25)] font-bold"
                        : preset.highlight === "emerald"
                        ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-[0_0_12px_rgba(16,185,129,0.25)] font-bold"
                        : "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_12px_rgba(6,182,212,0.25)] font-bold"
                      : "bg-slate-900/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800/80 border border-slate-800"
                  }`}
                >
                  {preset.label}
                </button>
              );
            })}
          </div>

          {/* Secondary Technical Strategy Filters */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            <span className="text-[10px] uppercase font-semibold text-slate-500 mr-1 flex items-center gap-1">
              <Activity className="w-3 h-3 text-slate-500" />
              Technicals:
            </span>
            {[
              { id: "ALL", label: "All Technicals" },
              { id: "stage_2", label: "🔥 Stage 2" },
              { id: "vcp_squeeze", label: "⚡ VCP" },
              { id: "accumulation", label: "💎 Flow" },
              { id: "rs_leaders", label: "⚡ RS ≥ 75" },
              { id: "breakouts", label: "🚀 52W High" },
              { id: "golden_cross", label: "🌟 Cross" },
              { id: "pullback", label: "🎯 Dip" },
              { id: "velocity", label: "⚡ Velocity" },
              { id: "rvol", label: "💥 RVOL > 1.35x" },
              { id: "ema_momentum", label: "🚀 8/21 EMA" },
            ].map((strat) => {
              const isActive = activeStrategy === strat.id && activePreset === "ALL";
              return (
                <button
                  key={strat.id}
                  type="button"
                  onClick={() => {
                    setActiveStrategy(strat.id);
                    setActivePreset("ALL");
                  }}
                  className={`px-2 py-0.5 rounded text-[11px] font-medium transition-all ${
                    isActive
                      ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_8px_rgba(6,182,212,0.2)] font-bold"
                      : "bg-slate-900/40 text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-slate-800/60"
                  }`}
                >
                  {strat.label}
                </button>
              );
            })}
          </div>

          {/* Search, Sector, Price Range, and Sort Controls Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-800/60">
            <div className="flex flex-wrap items-center gap-3 flex-1 min-w-[280px]">
              {/* Search Bar */}
              <div className="relative flex-1 min-w-[200px] max-w-sm">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="text"
                  placeholder="Search ticker or company (e.g., NVDA, CCJ)..."
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

              {/* Price Range Dropdown Selector */}
              <div className="relative">
                <select
                  value={priceRange}
                  onChange={(e) => setPriceRange(e.target.value)}
                  className="rounded-xl bg-slate-900 border border-slate-700/80 px-3 py-2 pr-8 text-xs font-medium text-slate-200 focus:border-cyan-500 focus:outline-none appearance-none cursor-pointer"
                  title="Filter by stock price range"
                >
                  {PRICE_RANGE_OPTIONS.map((opt) => (
                    <option key={opt.id} value={opt.id}>
                      {opt.label}
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
                <option value="short_term_momentum">⚡ Short-Term Momentum Score (0-100)</option>
                <option value="roc_3d">🚀 3-Day Velocity (ROC %)</option>
                <option value="rvol">💥 5-Day Relative Volume (RVOL)</option>
                <option value="ema_spread">📈 8/21 EMA Spread (%)</option>
                <option value="stage_2">🔥 Minervini Stage 2 (Leaders First)</option>
                <option value="accumulation">💎 Institutional Inflow (A/D Ratio)</option>
                <option value="vcp">⚡ VCP Squeeze Tightness</option>
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
                {stats.strongBuys} Strong {stats.stage2Count > 0 ? `(${stats.stage2Count} Stage 2)` : ""}
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
                    setActivePreset("ALL");
                    setPriceRange("ALL");
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
                  href={`/?ticker=${encodeURIComponent(deepDiveStock.symbol)}&action=options`}
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

            {/* Modal Tabs Bar */}
            <div className="flex items-center gap-2 px-4 sm:px-6 py-2.5 bg-slate-950 border-b border-slate-800">
              <button
                type="button"
                onClick={() => setDeepDiveTab("overview")}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
                  deepDiveTab === "overview"
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_12px_rgba(6,182,212,0.25)] font-bold"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent"
                }`}
              >
                <Activity className="w-3.5 h-3.5" />
                <span>Overview &amp; Technicals</span>
              </button>

              <button
                type="button"
                onClick={() => setDeepDiveTab("monte_carlo")}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
                  deepDiveTab === "monte_carlo"
                    ? "bg-purple-500/20 text-purple-300 border border-purple-500/40 shadow-[0_0_12px_rgba(168,85,247,0.25)] font-bold"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent"
                }`}
              >
                <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                <span>Monte Carlo Simulation (GBM)</span>
              </button>
            </div>

            {/* Modal Body */}
            <div className="overflow-y-auto p-4 sm:p-6 space-y-6 flex-1">
              {deepDiveTab === "monte_carlo" ? (
                <StockMonteCarlo
                  symbol={deepDiveStock.symbol}
                  currentPrice={
                    deepDiveStock.price > 0
                      ? deepDiveStock.price
                      : deepDiveStock.trade_plan.current_price
                  }
                  initialTp1={deepDiveStock.trade_plan.tp1}
                  initialStopLoss={deepDiveStock.trade_plan.stop_loss}
                />
              ) : (
                <>
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
                    <span className="text-[10px] text-slate-400 uppercase block">Stage 2 Template</span>
                    <span className="font-mono font-bold text-amber-300">
                      {deepDiveStock.is_stage_2 ? "🔥 Confirmed" : "Not Aligned"}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/80">
                    <span className="text-[10px] text-slate-400 uppercase block">A/D Inflow Rating</span>
                    <span className="font-mono font-bold text-emerald-400">
                      {deepDiveStock.accumulation_rating
                        ? `${deepDiveStock.accumulation_rating} (${deepDiveStock.up_down_volume_ratio ? deepDiveStock.up_down_volume_ratio.toFixed(1) + "x" : "—"})`
                        : "—"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Short-Term Momentum Impulse Panel */}
              {(deepDiveStock.roc_3d !== undefined || deepDiveStock.short_term_momentum_score !== undefined) && (
                <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs uppercase font-bold text-cyan-400 tracking-wider flex items-center gap-1.5">
                      <Zap className="w-4 h-4 text-cyan-400" />
                      Short-Term Momentum &amp; Velocity Impulse
                    </h3>
                    {deepDiveStock.short_term_setup && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                        ⚡ {deepDiveStock.short_term_setup.replace(/_/g, " ")}
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                    <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                      <span className="text-[10px] text-slate-400 uppercase block">3-Day Velocity (ROC)</span>
                      <span className={`font-mono font-bold text-sm ${
                        (deepDiveStock.roc_3d ?? 0) >= 2.5
                          ? "text-cyan-300"
                          : (deepDiveStock.roc_3d ?? 0) >= 0
                          ? "text-emerald-400"
                          : "text-rose-400"
                      }`}>
                        {(deepDiveStock.roc_3d ?? 0) >= 0 ? "+" : ""}{(deepDiveStock.roc_3d ?? 0).toFixed(2)}%
                      </span>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                      <span className="text-[10px] text-slate-400 uppercase block">5-Day Rate of Change</span>
                      <span className={`font-mono font-bold text-sm ${
                        (deepDiveStock.roc_5d ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"
                      }`}>
                        {(deepDiveStock.roc_5d ?? 0) >= 0 ? "+" : ""}{(deepDiveStock.roc_5d ?? 0).toFixed(2)}%
                      </span>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                      <span className="text-[10px] text-slate-400 uppercase block">5-Day Relative Volume</span>
                      <span className="font-mono font-bold text-amber-300 text-sm">
                        {(deepDiveStock.short_term_rvol ?? deepDiveStock.volume_ratio).toFixed(2)}x
                      </span>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                      <span className="text-[10px] text-slate-400 uppercase block">8/21 EMA Spread</span>
                      <span className="font-mono font-bold text-purple-300 text-sm">
                        {(deepDiveStock.ema_spread_pct ?? 0) >= 0 ? "+" : ""}{(deepDiveStock.ema_spread_pct ?? 0).toFixed(2)}%
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs pt-1">
                    <div className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/80">
                      <span className="text-[10px] text-slate-400 uppercase block">Short-Term Score</span>
                      <span className="font-mono font-bold text-cyan-300">
                        {Math.round(deepDiveStock.short_term_momentum_score ?? 50)}/100
                      </span>
                    </div>

                    <div className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/80">
                      <span className="text-[10px] text-slate-400 uppercase block">Fast RSI (5-Period)</span>
                      <span className="font-mono font-bold text-slate-200">
                        {(deepDiveStock.short_term_rsi ?? deepDiveStock.rsi).toFixed(1)}
                      </span>
                    </div>

                    <div className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/80">
                      <span className="text-[10px] text-slate-400 uppercase block">10-Day High Breakout</span>
                      <span className="font-mono font-bold text-emerald-400">
                        {deepDiveStock.is_short_term_breakout ? "🚀 Active Breakout" : "Near Range"}
                      </span>
                    </div>
                  </div>
                </div>
              )}

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
                </>
              )}
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
          router.push(`/?ticker=${encodeURIComponent(sym)}&action=options`);
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
