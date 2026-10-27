"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Zap,
  Flame,
  Sparkles,
  Shield,
  Layers,
  BarChart3,
  Target,
  ArrowRight,
  Filter,
  Search,
  RefreshCw,
  SlidersHorizontal,
  Wallet,
  LayoutGrid,
  Table as TableIcon,
  Star,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Percent,
  DollarSign,
  ChevronRight,
  Info,
  LineChart,
} from "lucide-react";

import OptionPayoffModal, {
  getSpreadAlternative,
  getThetaCliffInfo,
  SpreadData,
} from "./OptionPayoffModal";

export interface OptionRecommendation {
  id: string;
  symbol: string;
  name: string;
  stock_price: number;
  change_pct: number;
  bias: "BULLISH" | "BEARISH";
  confidence_pct: number;
  strategy_label: string;
  strategy_category: "DIRECTIONAL" | "MOONSHOT" | "ZERO_DTE" | "COMMODITIES" | "AI";
  contract: string;
  contract_name: string;
  option_type: "CALL" | "PUT";
  strike: number;
  expiration: string;
  dte: number;
  delta: number;
  gamma: number;
  theta: number;
  vega: number;
  iv: number;
  bid: number;
  ask: number;
  price: number;
  volume: number;
  open_interest: number;
  breakeven: number;
  pop_pct: number;
  risk_reward_ratio: number;
  tp1_price: number;
  tp1_gain_pct: number;
  stop_loss_price: number;
  stop_loss_loss_pct: number;
  suggested_contracts: number;
  total_capital: number;
  max_risk: number;
  sector: string;
  sector_label: string;
  rationale: string[];
  vertical_spread?: SpreadData;
}

interface BestOptionsHomeProps {
  onSelectTicker: (symbol: string) => void;
  onOpenChain: (symbol: string) => void;
  onPaperBuy: (rec: any) => void;
  starredTickers: string[];
  onToggleStar: (symbol: string) => void;
}

export default function BestOptionsHome({
  onSelectTicker,
  onOpenChain,
  onPaperBuy,
  starredTickers,
  onToggleStar,
}: BestOptionsHomeProps) {
  const [recommendations, setRecommendations] = useState<OptionRecommendation[]>([]);
  const [marketRegime, setMarketRegime] = useState<{
    vix: number;
    regime: string;
    headline: string;
    updated_at: string;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & Controls
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [selectedBias, setSelectedBias] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [sortBy, setSortBy] = useState<string>("score");
  const [viewMode, setViewMode] = useState<"grid" | "table">("grid");
  const [boughtMap, setBoughtMap] = useState<Record<string, boolean>>({});

  // Card view state: Single Leg vs Spread toggle per card
  const [cardModes, setCardModes] = useState<Record<string, "SINGLE" | "SPREAD">>({});

  // Interactive Payoff Modal state
  const [selectedPayoffRec, setSelectedPayoffRec] = useState<OptionRecommendation | null>(null);
  const [payoffInitialMode, setPayoffInitialMode] = useState<"SINGLE" | "SPREAD">("SINGLE");

  // Active Paper Trading Positions sync
  const [activePaperPositions, setActivePaperPositions] = useState<any[]>([]);

  const syncPaperPositions = () => {
    try {
      if (typeof window === "undefined") return;
      const raw = localStorage.getItem("options_paper_positions");
      if (!raw) {
        setActivePaperPositions([]);
        return;
      }
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        setActivePaperPositions(parsed.filter((p: any) => p.status === "OPEN"));
      }
    } catch (e) {
      console.error("Failed to parse options_paper_positions:", e);
    }
  };

  useEffect(() => {
    syncPaperPositions();
    const handleStorage = (e: StorageEvent) => {
      if (e.key === "options_paper_positions") {
        syncPaperPositions();
      }
    };
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  const isPositionInPaper = (rec: OptionRecommendation) => {
    return activePaperPositions.some((p: any) => {
      if (p.contract && rec.contract && p.contract === rec.contract) return true;
      if (
        p.ticker === rec.symbol &&
        p.strike === rec.strike &&
        p.optionType === rec.option_type
      )
        return true;
      return false;
    });
  };

  const openPayoffModal = (rec: OptionRecommendation, mode: "SINGLE" | "SPREAD" = "SINGLE") => {
    setSelectedPayoffRec(rec);
    setPayoffInitialMode(mode);
  };

  const fetchRecommendations = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (selectedCategory !== "ALL") params.append("category", selectedCategory);
      if (selectedBias !== "ALL") params.append("bias", selectedBias);
      if (searchQuery.trim()) params.append("search", searchQuery.trim());
      if (sortBy) params.append("sort_by", sortBy);

      const res = await fetch(`/api/options/recommendations?${params.toString()}`);
      if (!res.ok) {
        throw new Error(`Failed to load recommendations: status ${res.status}`);
      }
      const data = await res.json();
      setRecommendations(data.items || []);
      if (data.market_regime) {
        setMarketRegime(data.market_regime);
      }
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to fetch options recommendations");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, [selectedCategory, selectedBias, sortBy]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchRecommendations();
  };

  const handlePaperBuyClick = (rec: OptionRecommendation, spread?: SpreadData | null) => {
    const isSpreadMode = (cardModes[rec.id] || "SINGLE") === "SPREAD";
    const contracts = isSpreadMode ? (spread?.suggested_contracts ?? 0) : (rec.suggested_contracts ?? 0);
    if (contracts <= 0) {
      alert("Position exceeds capital risk budget (0 contracts qualified).");
      return;
    }
    if (isSpreadMode && spread) {
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
        suggested_contracts: contracts,
        strategy_label: spread.spread_label,
        notes: `Defined-Risk Vertical Spread (${spread.spread_label}): Long $${spread.long_strike} / Short $${spread.short_strike}`,
      });
    } else {
      onPaperBuy(rec);
    }

    setBoughtMap((prev) => ({ ...prev, [rec.id]: true }));
    syncPaperPositions();
    setTimeout(() => {
      syncPaperPositions();
    }, 250);
    setTimeout(() => {
      setBoughtMap((prev) => ({ ...prev, [rec.id]: false }));
    }, 3000);
  };

  // Quick summary metrics
  const summaryMetrics = useMemo(() => {
    if (!recommendations.length) return null;
    const avgPop = recommendations.reduce((acc, r) => acc + (r.pop_pct || 0), 0) / recommendations.length;
    const maxRr = Math.max(...recommendations.map((r) => r.risk_reward_ratio || 0));
    const callCount = recommendations.filter((r) => r.option_type === "CALL").length;
    const putCount = recommendations.filter((r) => r.option_type === "PUT").length;
    return {
      total: recommendations.length,
      avgPop: avgPop.toFixed(1),
      maxRr: maxRr.toFixed(2),
      callCount,
      putCount,
    };
  }, [recommendations]);

  const categories = [
    { id: "ALL", label: "All Top Picks", icon: Target, count: recommendations.length },
    { id: "DIRECTIONAL", label: "High-Conviction Directional", icon: Zap, color: "text-cyan-400" },
    { id: "MOONSHOT", label: "Asymmetric Moonshots", icon: Flame, color: "text-rose-400" },
    { id: "ZERO_DTE", label: "0DTE Flash Scalps", icon: Sparkles, color: "text-amber-400" },
    { id: "AI", label: "AI & Tech Ecosystem", icon: Layers, color: "text-indigo-400" },
    { id: "COMMODITIES", label: "Commodities & Uranium", icon: Shield, color: "text-emerald-400" },
  ];

  const getCategoryBadge = (cat: string) => {
    switch (cat) {
      case "DIRECTIONAL":
        return <span className="rounded-md border border-cyan-500/40 bg-cyan-500/10 px-2 py-0.5 text-[10px] font-bold text-cyan-300">HIGH CONVICTION</span>;
      case "MOONSHOT":
        return <span className="rounded-md border border-rose-500/40 bg-rose-500/10 px-2 py-0.5 text-[10px] font-bold text-rose-300">MOONSHOT LOTTO</span>;
      case "ZERO_DTE":
        return <span className="rounded-md border border-amber-500/40 bg-amber-500/10 px-2 py-0.5 text-[10px] font-bold text-amber-300">0DTE FLASH</span>;
      case "COMMODITIES":
        return <span className="rounded-md border border-emerald-500/40 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold text-emerald-300">COMMODITY PLAY</span>;
      case "AI":
      default:
        return <span className="rounded-md border border-indigo-500/40 bg-indigo-500/10 px-2 py-0.5 text-[10px] font-bold text-indigo-300">AI ECOSYSTEM</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* ========================================================= */}
      {/* 0. MARKET DATA QUALITY & EXECUTION REALITY HEADER         */}
      {/* ========================================================= */}
      <div className="flex flex-wrap items-center justify-between gap-2.5 rounded-xl border border-slate-800 bg-[#070b14] px-4 py-2.5 text-[11px] text-slate-400">
        <div className="flex flex-wrap items-center gap-3">
          <span className="flex items-center space-x-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-400 inline-block animate-pulse" />
            <strong className="text-slate-200">Data Source:</strong>
            <span className="text-slate-300">yfinance (~15m delay standard feeds)</span>
          </span>
          <span className="text-slate-700">|</span>
          <span>
            <strong className="text-slate-200">Retrieval:</strong> {marketRegime?.updated_at || "Recent UTC"}
          </span>
          <span className="text-slate-700">|</span>
          <span>
            <strong className="text-slate-200">Bid/Ask Size:</strong> <span className="text-amber-400/90 font-mono">unavailable</span>
          </span>
        </div>
        <div className="flex items-center space-x-1 text-slate-400 text-[10px]">
          <Info className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
          <span>Fills modeled at Ask (entry) & Bid (exit). Midpoint not guaranteed. Broker fees excluded.</span>
        </div>
      </div>

      {/* ========================================================= */}
      {/* 1. HERO BANNER: MARKET REGIME & RECOMMENDATIONS COCKPIT   */}
      {/* ========================================================= */}
      <div className="relative overflow-hidden rounded-2xl border border-cyan-500/30 bg-gradient-to-br from-[#0c162c] via-[#091020] to-[#060a14] p-6 shadow-2xl">
        <div className="absolute -right-16 -top-16 h-64 w-64 rounded-full bg-cyan-500/10 blur-3xl" />
        <div className="absolute -bottom-16 right-1/3 h-64 w-64 rounded-full bg-indigo-500/10 blur-3xl" />

        <div className="relative z-10 flex flex-col justify-between gap-6 lg:flex-row lg:items-center">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center space-x-2 rounded-full border border-cyan-500/30 bg-cyan-950/60 px-3 py-1 text-xs font-semibold text-cyan-300 shadow-sm">
              <Sparkles className="h-3.5 w-3.5 text-cyan-400" />
              <span>Quantitative Options Signal Engine • Real-Time Picks</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white">
              Best Options to Buy <span className="bg-gradient-to-r from-cyan-400 to-indigo-400 bg-clip-text text-transparent">Currently</span>
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              Algorithmic options recommendations screened across 1,000+ US equities. Ranked by Delta-targeting (0.40–0.50), high Probability of Profit (POP), multi-timeframe momentum, and strict asymmetric risk-to-reward ratios.
            </p>
          </div>

          {/* Market Regime Badge Box */}
          {marketRegime && (
            <div className="shrink-0 rounded-xl border border-slate-700/80 bg-[#0d172a]/90 p-4 shadow-lg backdrop-blur-md lg:w-80">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1.5">
                <span className="font-semibold uppercase tracking-wider text-slate-400 flex items-center space-x-1">
                  <Activity className="h-3.5 w-3.5 text-cyan-400 inline mr-1" />
                  Market Regime
                </span>
                <span className="font-mono text-cyan-300 font-bold">VIX {marketRegime.vix.toFixed(1)}</span>
              </div>
              <div className="text-sm font-bold text-white mb-1">
                {marketRegime.regime}
              </div>
              <p className="text-[11px] leading-snug text-slate-300">
                {marketRegime.headline}
              </p>
            </div>
          )}
        </div>

        {/* Quick KPI Strip */}
        {summaryMetrics && (
          <div className="relative z-10 mt-6 grid grid-cols-2 gap-3 border-t border-slate-800/80 pt-5 sm:grid-cols-4">
            <div className="flex items-center space-x-3 rounded-lg bg-[#0b1222]/80 p-3 border border-slate-800/80">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-500/20 text-cyan-400">
                <Target className="h-4 w-4" />
              </div>
              <div>
                <div className="text-[11px] font-medium text-slate-400">Active Picks</div>
                <div className="text-lg font-bold text-white">{summaryMetrics.total} Contracts</div>
              </div>
            </div>

            <div className="flex items-center space-x-3 rounded-lg bg-[#0b1222]/80 p-3 border border-slate-800/80">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-500/20 text-emerald-400">
                <Percent className="h-4 w-4" />
              </div>
              <div>
                <div className="text-[11px] font-medium text-slate-400">Model PoP (BS Est.)</div>
                <div className="text-lg font-bold text-emerald-400">{summaryMetrics.avgPop}%</div>
              </div>
            </div>

            <div className="flex items-center space-x-3 rounded-lg bg-[#0b1222]/80 p-3 border border-slate-800/80">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-purple-500/20 text-purple-400">
                <TrendingUp className="h-4 w-4" />
              </div>
              <div>
                <div className="text-[11px] font-medium text-slate-400">Top R:R Ratio</div>
                <div className="text-lg font-bold text-purple-300">{summaryMetrics.maxRr}:1</div>
              </div>
            </div>

            <div className="flex items-center space-x-3 rounded-lg bg-[#0b1222]/80 p-3 border border-slate-800/80">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-500/20 text-amber-400">
                <Zap className="h-4 w-4" />
              </div>
              <div>
                <div className="text-[11px] font-medium text-slate-400">Call / Put Balance</div>
                <div className="text-lg font-bold text-white">
                  <span className="text-emerald-400">{summaryMetrics.callCount}C</span> / <span className="text-rose-400">{summaryMetrics.putCount}P</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ========================================================= */}
      {/* 2. FILTER & STRATEGY SELECTION TOOLBAR                    */}
      {/* ========================================================= */}
      <div className="rounded-xl border border-slate-800 bg-[#0a1120] p-4 shadow-lg space-y-4">
        {/* Top: Category Chips */}
        <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 scrollbar-none">
          {categories.map((cat) => {
            const Icon = cat.icon;
            const isSelected = selectedCategory === cat.id;
            return (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`flex shrink-0 items-center space-x-2 rounded-xl px-3.5 py-2 text-xs font-semibold transition ${
                  isSelected
                    ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
                    : "bg-[#0f172a] text-slate-300 hover:bg-slate-800 hover:text-white border border-slate-800"
                }`}
              >
                <Icon className={`h-3.5 w-3.5 ${isSelected ? "text-slate-950" : cat.color || "text-slate-400"}`} />
                <span>{cat.label}</span>
              </button>
            );
          })}
        </div>

        {/* Bottom: Search, Bias Filter, Sorting, View Toggle */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-800/80 pt-3 text-xs">
          {/* Left: Search input & Bias Filter */}
          <div className="flex flex-wrap items-center gap-2.5">
            <form onSubmit={handleSearchSubmit} className="relative w-48 sm:w-60">
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
              <input
                type="text"
                placeholder="Search Ticker, Company..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-lg border border-slate-800 bg-[#0d1424] py-1.5 pl-8 pr-3 text-xs text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none uppercase"
              />
            </form>

            {/* Bias toggle */}
            <div className="flex items-center rounded-lg border border-slate-800 bg-[#0d1424] p-0.5">
              {[
                { id: "ALL", label: "All Bias" },
                { id: "CALL", label: "Calls (Bullish)" },
                { id: "PUT", label: "Puts (Bearish)" },
              ].map((b) => (
                <button
                  key={b.id}
                  onClick={() => setSelectedBias(b.id)}
                  className={`rounded-md px-2.5 py-1 font-medium transition ${
                    selectedBias === b.id
                      ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {b.label}
                </button>
              ))}
            </div>
          </div>

          {/* Right: Sort & Layout Mode */}
          <div className="flex items-center space-x-2.5">
            <div className="flex items-center space-x-1.5 text-slate-400">
              <SlidersHorizontal className="h-3.5 w-3.5" />
              <span>Sort:</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="rounded-lg border border-slate-800 bg-[#0d1424] px-2.5 py-1 text-xs text-white focus:border-cyan-500 focus:outline-none"
              >
                <option value="score">Highest Confidence</option>
                <option value="win_rate">Probability of Profit (POP)</option>
                <option value="rr_ratio">Best Risk / Reward (R:R)</option>
                <option value="price">Lowest Contract Cost</option>
                <option value="dte">Shortest Expiration (DTE)</option>
                <option value="delta">Highest Delta Exposure</option>
              </select>
            </div>

            <div className="flex items-center rounded-lg border border-slate-800 bg-[#0d1424] p-0.5">
              <button
                onClick={() => setViewMode("grid")}
                title="Grid Cards View"
                className={`rounded p-1.5 transition ${
                  viewMode === "grid" ? "bg-cyan-500/20 text-cyan-300" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <LayoutGrid className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => setViewMode("table")}
                title="Table Matrix View"
                className={`rounded p-1.5 transition ${
                  viewMode === "table" ? "bg-cyan-500/20 text-cyan-300" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <TableIcon className="h-3.5 w-3.5" />
              </button>
            </div>

            <button
              onClick={fetchRecommendations}
              title="Refresh Recommendations"
              className="flex h-7 w-7 items-center justify-center rounded-lg border border-slate-800 bg-[#0d1424] text-slate-400 hover:text-cyan-300 hover:border-slate-700 transition"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-cyan-400" : ""}`} />
            </button>
          </div>
        </div>
      </div>

      {/* ========================================================= */}
      {/* 3. ERROR & LOADING STATES                                 */}
      {/* ========================================================= */}
      {error && (
        <div className="flex items-center justify-between rounded-xl border border-red-500/40 bg-red-950/30 p-4 text-xs text-red-200">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-4 w-4 text-red-400 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={fetchRecommendations}
            className="rounded bg-red-800/50 px-2.5 py-1 font-bold text-white hover:bg-red-700/60"
          >
            Retry
          </button>
        </div>
      )}

      {loading && (
        <div className="flex h-72 w-full flex-col items-center justify-center rounded-2xl border border-slate-800 bg-[#090e1a] text-slate-400">
          <RefreshCw className="mb-3 h-8 w-8 animate-spin text-cyan-400" />
          <p className="text-sm font-semibold text-slate-200">Scanning Options Chains & Calculating Greeks...</p>
          <p className="text-xs text-slate-500 mt-1">Evaluating Delta targeting, expected moves, and profit targets</p>
        </div>
      )}

      {!loading && recommendations.length === 0 && !error && (
        <div className="flex h-64 flex-col items-center justify-center rounded-2xl border border-slate-800 bg-[#090e1a] p-8 text-center text-slate-400">
          <Info className="mb-2 h-8 w-8 text-slate-500" />
          <p className="text-sm font-medium text-slate-300">No options match your current filter parameters.</p>
          <p className="text-xs text-slate-500 mt-1">Try switching categories or clearing search query.</p>
          <button
            onClick={() => {
              setSelectedCategory("ALL");
              setSelectedBias("ALL");
              setSearchQuery("");
            }}
            className="mt-3 rounded-lg border border-cyan-500/40 bg-cyan-500/10 px-3.5 py-1.5 text-xs font-semibold text-cyan-300 hover:bg-cyan-500/20"
          >
            Reset Filters
          </button>
        </div>
      )}

      {/* ========================================================= */}
      {/* 4. GRID VIEW: RICH RECOMMENDATION CARDS                   */}
      {/* ========================================================= */}
      {!loading && recommendations.length > 0 && viewMode === "grid" && (
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
          {recommendations.map((rec) => {
            const isCall = rec.option_type === "CALL";
            const isBull = rec.bias === "BULLISH";
            const isStar = starredTickers.includes(rec.symbol);
            const isBought = boughtMap[rec.id];

            const currentMode = cardModes[rec.id] || "SINGLE";
            const spread = getSpreadAlternative(rec);
            const thetaInfo = getThetaCliffInfo(rec.dte, rec.theta);
            const isPaperActive = isPositionInPaper(rec);

            return (
              <div
                key={rec.id}
                className="group relative flex flex-col justify-between rounded-2xl border border-slate-800 bg-[#0a1120] p-5 shadow-lg transition-all duration-200 hover:border-cyan-500/40 hover:shadow-[0_0_20px_rgba(6,182,212,0.15)]"
              >
                <div>
                  {/* Card Header: Stock info & Category badge & Paper Active Badge */}
                  <div className="flex items-start justify-between gap-2 mb-2.5">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => onSelectTicker(rec.symbol)}
                        className="text-lg font-black text-white hover:text-cyan-400 transition"
                      >
                        {rec.symbol}
                      </button>
                      <button
                        type="button"
                        onClick={() => onToggleStar(rec.symbol)}
                        className="text-slate-500 hover:text-amber-400 transition"
                        title={isStar ? "Remove from watchlist" : "Add to watchlist"}
                      >
                        <Star className={`h-4 w-4 ${isStar ? "fill-amber-400 text-amber-400" : ""}`} />
                      </button>
                      <span className="text-xs text-slate-400 truncate max-w-[100px] sm:max-w-[130px]">
                        {rec.name}
                      </span>
                    </div>

                    <div className="flex items-center space-x-1.5 shrink-0">
                      {isPaperActive && (
                        <span className="inline-flex items-center space-x-1 rounded-full border border-emerald-500/50 bg-emerald-950/80 px-2 py-0.5 text-[9px] font-bold text-emerald-300 shadow-sm shadow-emerald-900/40">
                          <span className="relative flex h-1.5 w-1.5 mr-0.5">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500"></span>
                          </span>
                          <span>Active in Paper</span>
                        </span>
                      )}
                      {getCategoryBadge(rec.strategy_category)}
                    </div>
                  </div>

                  {/* Stock price row */}
                  <div className="flex items-center justify-between text-xs text-slate-400 mb-3 border-b border-slate-800/80 pb-2.5">
                    <div className="flex items-baseline space-x-1.5">
                      <span className="text-sm font-bold text-white">${rec.stock_price.toFixed(2)}</span>
                      <span
                        className={`font-semibold ${
                          rec.change_pct >= 0 ? "text-emerald-400" : "text-rose-400"
                        }`}
                      >
                        {rec.change_pct >= 0 ? "+" : ""}
                        {rec.change_pct.toFixed(2)}%
                      </span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <span
                        className={`inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-bold ${
                          isBull
                            ? "bg-emerald-950/60 text-emerald-400 border border-emerald-800/40"
                            : "bg-rose-950/60 text-rose-400 border border-rose-800/40"
                        }`}
                      >
                        {isBull ? <TrendingUp className="mr-0.5 h-3 w-3" /> : <TrendingDown className="mr-0.5 h-3 w-3" />}
                        {rec.bias}
                      </span>
                      <span className="rounded bg-cyan-950/60 px-1.5 py-0.5 text-[10px] font-semibold text-cyan-300 border border-cyan-800/40">
                        {rec.confidence_pct.toFixed(0)}% Conf
                      </span>
                    </div>
                  </div>

                  {/* STRUCTURE TOGGLE: SINGLE-LEG VS DEFINED-RISK SPREAD */}
                  <div className="mb-3 flex items-center justify-between rounded-lg border border-slate-800/80 bg-[#0d1424] p-1 text-[11px]">
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 pl-1.5">
                      Strategy Structure:
                    </span>
                    <div className="flex items-center space-x-1">
                      <button
                        type="button"
                        onClick={() =>
                          setCardModes((prev) => ({ ...prev, [rec.id]: "SINGLE" }))
                        }
                        className={`rounded px-2.5 py-1 font-bold transition ${
                          currentMode === "SINGLE"
                            ? "bg-cyan-500/25 text-cyan-300 border border-cyan-500/50 shadow-sm"
                            : "text-slate-400 hover:text-slate-200"
                        }`}
                      >
                        Single Leg
                      </button>
                      <button
                        type="button"
                        onClick={() =>
                          setCardModes((prev) => ({ ...prev, [rec.id]: "SPREAD" }))
                        }
                        className={`rounded px-2.5 py-1 font-bold transition ${
                          currentMode === "SPREAD"
                            ? "bg-indigo-500/25 text-indigo-300 border border-indigo-500/50 shadow-sm"
                            : "text-slate-400 hover:text-slate-200"
                        }`}
                      >
                        Vertical Spread
                      </button>
                    </div>
                  </div>

                  {/* CONTRACT SPOTLIGHT BOX */}
                  {currentMode === "SINGLE" ? (
                    <div className="rounded-xl border border-slate-800 bg-[#0c1424] p-3.5 mb-3">
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center space-x-2">
                            <span
                              className={`rounded px-1.5 py-0.5 text-xs font-black ${
                                isCall
                                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                                  : "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                              }`}
                            >
                              {rec.option_type}
                            </span>
                            <span className="text-sm font-black text-white">
                              ${rec.strike.toFixed(2)} STRIKE
                            </span>
                          </div>
                          <div className="mt-1 flex items-center space-x-1.5 text-[11px] text-slate-400 font-medium">
                            <Clock className="h-3 w-3 text-slate-500" />
                            <span>Exp: {rec.expiration}</span>
                            <span className="text-cyan-400 font-bold">({rec.dte}d DTE)</span>
                          </div>
                        </div>

                        <div className="text-right">
                          <div className="text-base font-black text-emerald-400">
                            ${rec.ask.toFixed(2)} <span className="text-[10px] text-slate-400 font-normal">Ask</span>
                          </div>
                          <div className="text-[10px] text-slate-400 font-mono">
                            Bid: ${rec.bid.toFixed(2)} | Mid: ${((rec.ask + rec.bid) / 2).toFixed(2)}
                          </div>
                          <div className="text-[9px] text-amber-400/90 font-mono">
                            Spread: ${(rec.ask - rec.bid).toFixed(2)} ({rec.ask > 0 ? (((rec.ask - rec.bid) / rec.ask) * 100).toFixed(1) : 0}%)
                          </div>
                        </div>
                      </div>

                      {/* Greeks & IV Pill Strip */}
                      <div className="mt-3 grid grid-cols-4 gap-1.5 border-t border-slate-800/80 pt-2.5 text-center text-[10px]">
                        <div className="rounded bg-[#101b30] p-1.5">
                          <div className="text-slate-400 font-medium">Delta (Δ)</div>
                          <div className="font-mono font-bold text-cyan-300">
                            {rec.delta > 0 ? "+" : ""}{rec.delta.toFixed(2)}
                          </div>
                        </div>
                        <div className="rounded bg-[#101b30] p-1.5">
                          <div className="text-slate-400 font-medium">Theta (Θ)</div>
                          <div className="font-mono font-bold text-rose-400">
                            {rec.theta.toFixed(2)}/d
                          </div>
                        </div>
                        <div className="rounded bg-[#101b30] p-1.5">
                          <div className="text-slate-400 font-medium">IV %</div>
                          <div className="font-mono font-bold text-amber-300">
                            {rec.iv.toFixed(1)}%
                          </div>
                        </div>
                        <div className="rounded bg-[#101b30] p-1.5">
                          <div className="text-slate-400 font-medium">Breakeven</div>
                          <div className="font-mono font-bold text-slate-200">
                            ${rec.breakeven.toFixed(2)}
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    /* SPREAD SPOTLIGHT BOX */
                    <div className="rounded-xl border border-indigo-500/30 bg-[#0c142b] p-3.5 mb-3">
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="rounded px-1.5 py-0.5 text-xs font-black bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
                              {spread.spread_type === "BULL_CALL" ? "BULL CALL SPREAD" : "BEAR PUT SPREAD"}
                            </span>
                            <span className="text-sm font-black text-white">
                              ${spread.long_strike} / ${spread.short_strike}
                            </span>
                          </div>
                          <div className="mt-1 flex items-center space-x-1.5 text-[11px] text-slate-400 font-medium">
                            <Shield className="h-3 w-3 text-indigo-400" />
                            <span>Defined Risk • Capped Loss</span>
                            <span className="text-cyan-400 font-bold">({rec.dte}d DTE)</span>
                          </div>
                        </div>

                        <div className="text-right">
                          <div className="text-base font-black text-emerald-400">
                            ${spread.net_debit.toFixed(2)} <span className="text-[10px] text-slate-400 font-medium">Debit</span>
                          </div>
                          <div className="text-[10px] text-rose-400 font-semibold">
                            Max Loss: ${spread.max_loss.toFixed(0)}
                          </div>
                        </div>
                      </div>

                      {/* Spread Metrics Strip */}
                      <div className="mt-3 grid grid-cols-4 gap-1.5 border-t border-slate-800/80 pt-2.5 text-center text-[10px]">
                        <div className="rounded bg-[#101b30] p-1.5">
                          <div className="text-slate-400 font-medium">Long Strike</div>
                          <div className="font-mono font-bold text-emerald-300">
                            ${spread.long_strike}
                          </div>
                        </div>
                        <div className="rounded bg-[#101b30] p-1.5">
                          <div className="text-slate-400 font-medium">Short Strike</div>
                          <div className="font-mono font-bold text-indigo-300">
                            ${spread.short_strike}
                          </div>
                        </div>
                        <div className="rounded bg-[#101b30] p-1.5">
                          <div className="text-slate-400 font-medium">Spread Width</div>
                          <div className="font-mono font-bold text-slate-200">
                            ${spread.width.toFixed(2)}
                          </div>
                        </div>
                        <div className="rounded bg-[#101b30] p-1.5">
                          <div className="text-slate-400 font-medium">Breakeven</div>
                          <div className="font-mono font-bold text-amber-300">
                            ${spread.breakeven.toFixed(2)}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* THETA CLIFF & OPTIMAL HOLDING WINDOW BANNER */}
                  <div
                    className={`mb-3 flex items-center justify-between rounded-xl border px-3 py-2 text-xs transition ${
                      thetaInfo.severity === "URGENT" || thetaInfo.severity === "DANGER"
                        ? "border-rose-500/30 bg-rose-950/20 text-rose-300"
                        : thetaInfo.severity === "WARNING"
                        ? "border-amber-500/30 bg-amber-950/20 text-amber-300"
                        : "border-cyan-500/30 bg-cyan-950/20 text-cyan-300"
                    }`}
                  >
                    <div className="flex items-center space-x-2 min-w-0 pr-2">
                      <Clock className="h-3.5 w-3.5 shrink-0" />
                      <span className="text-[11px] font-medium leading-snug truncate">
                        {thetaInfo.headline}
                      </span>
                    </div>
                    <span className="shrink-0 rounded-md bg-[#0a1120] px-2 py-0.5 font-mono text-[10px] font-bold border border-slate-700/60 text-white">
                      {thetaInfo.optimalWindow}
                    </span>
                  </div>

                  {/* Profit Target vs Stop Loss metrics */}
                  {currentMode === "SINGLE" ? (
                    <div className="mb-3 grid grid-cols-2 gap-2 text-xs">
                      <div className="rounded-lg border border-emerald-950/60 bg-emerald-950/20 p-2.5">
                        <div className="flex items-center justify-between text-[10px] text-emerald-400 font-bold uppercase">
                          <span>Target 1 (TP1)</span>
                          <span className="font-mono">+{rec.tp1_gain_pct.toFixed(0)}%</span>
                        </div>
                        <div className="mt-1 text-sm font-extrabold text-white">
                          ${rec.tp1_price.toFixed(2)}
                        </div>
                      </div>

                      <div className="rounded-lg border border-rose-950/60 bg-rose-950/20 p-2.5">
                        <div className="flex items-center justify-between text-[10px] text-rose-400 font-bold uppercase">
                          <span>Stop Loss</span>
                          <span className="font-mono">-{rec.stop_loss_loss_pct.toFixed(0)}%</span>
                        </div>
                        <div className="mt-1 text-sm font-extrabold text-white">
                          ${rec.stop_loss_price.toFixed(2)}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="mb-3 grid grid-cols-2 gap-2 text-xs">
                      <div className="rounded-lg border border-emerald-950/60 bg-emerald-950/20 p-2.5">
                        <div className="flex items-center justify-between text-[10px] text-emerald-400 font-bold uppercase">
                          <span>Max Profit Cap</span>
                          <span className="font-mono">
                            +{((spread.max_profit / spread.max_loss) * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className="mt-1 text-sm font-extrabold text-white">
                          +${spread.max_profit.toFixed(0)}
                        </div>
                      </div>

                      <div className="rounded-lg border border-rose-950/60 bg-rose-950/20 p-2.5">
                        <div className="flex items-center justify-between text-[10px] text-rose-400 font-bold uppercase">
                          <span>Defined Max Risk</span>
                          <span className="font-mono">-100%</span>
                        </div>
                        <div className="mt-1 text-sm font-extrabold text-white">
                          -${spread.max_loss.toFixed(0)}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Win Probability & Risk/Reward */}
                  <div className="mb-3 flex items-center justify-between rounded-lg bg-[#0e1628] px-3 py-2 text-xs">
                    <div className="flex items-center space-x-1.5" title="Theoretical Black-Scholes estimate, not proven historical win rate">
                      <span className="text-[11px] text-slate-400">Model PoP:</span>
                      <span className="font-bold text-emerald-400 font-mono">{rec.pop_pct.toFixed(1)}%</span>
                    </div>
                    <div className="flex items-center space-x-1.5">
                      <span className="text-[11px] text-slate-400">R:R:</span>
                      <span className="font-bold text-cyan-300 font-mono">
                        {currentMode === "SPREAD" ? `${spread.rr_ratio}:1` : `${rec.risk_reward_ratio.toFixed(2)}:1`}
                      </span>
                    </div>
                    <div className="flex items-center space-x-1 text-[11px] text-slate-400">
                      <span>Size:</span>
                      <span className="font-bold text-white font-mono">
                        {currentMode === "SPREAD"
                          ? `${spread.suggested_contracts}x ($${(spread.net_debit * 100 * spread.suggested_contracts).toFixed(0)})`
                          : `${rec.suggested_contracts}x ($${rec.total_capital.toFixed(0)})`}
                      </span>
                    </div>
                  </div>

                  {/* Zero-Contract Risk Safeguard Notice */}
                  {rec.suggested_contracts === 0 && (
                    <div className="mb-3 rounded-lg border border-rose-500/40 bg-rose-950/30 p-2 text-[10px] text-rose-300">
                      <span className="font-bold">⚠️ Exceeds Risk Budget:</span> Contract premium exceeds max risk budget for this account. 0 contracts qualified (paper execution blocked).
                    </div>
                  )}

                  {/* Why this contract? Rationale & Screening Breakdown */}
                  <div className="mb-4 space-y-1.5">
                    <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-800/60 pb-1">
                      <span>Why This Setup Passed:</span>
                      <span className="font-mono text-cyan-300">Vol: {rec.volume.toLocaleString()} | OI: {rec.open_interest.toLocaleString()}</span>
                    </div>
                    {rec.rationale.slice(0, 2).map((r, idx) => (
                      <div key={idx} className="flex items-start space-x-1.5 text-[11px] text-slate-300 leading-snug">
                        <CheckCircle2 className="h-3 w-3 text-cyan-400 shrink-0 mt-0.5" />
                        <span>{r}</span>
                      </div>
                    ))}
                    <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 pt-1">
                      <span>Invalidation: Stop ${rec.stop_loss_price.toFixed(2)} (-{rec.stop_loss_loss_pct.toFixed(0)}%)</span>
                      <span>Max Loss: ${rec.suggested_contracts > 0 ? (rec.ask * 100 * rec.suggested_contracts).toFixed(0) : "0"}</span>
                    </div>
                  </div>
                </div>

                {/* Card Action Buttons */}
                <div className="border-t border-slate-800/80 pt-3 flex items-center space-x-2">
                  <button
                    type="button"
                    onClick={() => handlePaperBuyClick(rec, spread)}
                    disabled={(currentMode === "SPREAD" ? (spread.suggested_contracts ?? 0) : rec.suggested_contracts) <= 0}
                    className={`flex-1 flex items-center justify-center space-x-1.5 rounded-lg py-2 px-3 text-xs font-black transition active:scale-95 shadow-md ${
                      (currentMode === "SPREAD" ? (spread.suggested_contracts ?? 0) : rec.suggested_contracts) <= 0
                        ? "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700"
                        : isBought
                        ? "bg-emerald-400 text-slate-950"
                        : "bg-emerald-500 hover:bg-emerald-400 text-slate-950 shadow-emerald-500/20"
                    }`}
                  >
                    <Wallet className="h-3.5 w-3.5 text-slate-950" />
                    <span>
                      {(currentMode === "SPREAD" ? (spread.suggested_contracts ?? 0) : rec.suggested_contracts) <= 0
                        ? "Exceeds Risk Budget (0x)"
                        : isBought
                        ? "Filled in Paper!"
                        : currentMode === "SPREAD"
                        ? `Paper Spread (${spread.suggested_contracts}x)`
                        : `Paper Buy (${rec.suggested_contracts}x)`}
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={() => openPayoffModal(rec, currentMode)}
                    title="Interactive Payoff Curve & Profit Diagrams"
                    className="flex items-center space-x-1 rounded-lg border border-cyan-500/40 bg-cyan-950/40 px-2.5 py-2 text-xs font-bold text-cyan-300 hover:bg-cyan-500/20 hover:border-cyan-400 transition"
                  >
                    <LineChart className="h-3.5 w-3.5 text-cyan-400" />
                    <span className="hidden sm:inline">Payoff</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => onSelectTicker(rec.symbol)}
                    title="Analyze in TradingView Terminal"
                    className="flex items-center justify-center rounded-lg border border-slate-700/80 bg-[#101b30] p-2 text-xs font-medium text-cyan-300 hover:bg-cyan-500/10 hover:border-cyan-500/50 transition"
                  >
                    <BarChart3 className="h-4 w-4" />
                  </button>

                  <button
                    type="button"
                    onClick={() => onOpenChain(rec.symbol)}
                    title="Open Options Chain Matrix"
                    className="flex items-center justify-center rounded-lg border border-slate-700/80 bg-[#101b30] p-2 text-xs font-medium text-indigo-300 hover:bg-indigo-500/10 hover:border-indigo-500/50 transition"
                  >
                    <Layers className="h-4 w-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ========================================================= */}
      {/* 5. TABLE VIEW: INSTITUTIONAL MATRIX                       */}
      {/* ========================================================= */}
      {!loading && recommendations.length > 0 && viewMode === "table" && (
        <div className="overflow-hidden rounded-2xl border border-slate-800 bg-[#0a1120] shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="border-b border-slate-800 bg-[#0d1629] text-[11px] font-bold uppercase tracking-wider text-slate-400">
                <tr>
                  <th className="px-4 py-3">Ticker / Company</th>
                  <th className="px-3 py-3">Category</th>
                  <th className="px-3 py-3">Option Contract</th>
                  <th className="px-3 py-3 text-center">Bias</th>
                  <th className="px-3 py-3 text-right">Stock Price</th>
                  <th className="px-3 py-3 text-right">Option Ask</th>
                  <th className="px-3 py-3 text-center">Delta (Δ)</th>
                  <th className="px-3 py-3 text-center">IV %</th>
                  <th className="px-3 py-3 text-center">DTE</th>
                  <th className="px-3 py-3 text-center">Model PoP (BS Est.)</th>
                  <th className="px-3 py-3 text-center">R:R</th>
                  <th className="px-3 py-3 text-right">TP1 Target</th>
                  <th className="px-4 py-3 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {recommendations.map((rec) => {
                  const isCall = rec.option_type === "CALL";
                  const isBull = rec.bias === "BULLISH";
                  const isBought = boughtMap[rec.id];
                  const isPaperActive = isPositionInPaper(rec);

                  return (
                    <tr key={rec.id} className="hover:bg-slate-800/40 transition">
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => onSelectTicker(rec.symbol)}
                            className="font-black text-white hover:text-cyan-400 transition"
                          >
                            {rec.symbol}
                          </button>
                          {isPaperActive && (
                            <span className="rounded bg-emerald-950/80 px-1.5 py-0.2 text-[9px] font-bold text-emerald-400 border border-emerald-800/50">
                              IN PAPER
                            </span>
                          )}
                          <span className="text-[11px] text-slate-400 truncate max-w-[120px]">
                            {rec.name}
                          </span>
                        </div>
                      </td>

                      <td className="px-3 py-3 whitespace-nowrap">
                        {getCategoryBadge(rec.strategy_category)}
                      </td>

                      <td className="px-3 py-3 whitespace-nowrap font-mono">
                        <span className="font-bold text-white">${rec.strike.toFixed(2)}</span>{" "}
                        <span className={isCall ? "text-emerald-400 font-bold" : "text-rose-400 font-bold"}>
                          {rec.option_type}
                        </span>{" "}
                        <span className="text-[10px] text-slate-500">({rec.expiration})</span>
                      </td>

                      <td className="px-3 py-3 whitespace-nowrap text-center">
                        <span
                          className={`inline-flex items-center rounded px-2 py-0.5 text-[10px] font-bold ${
                            isBull
                              ? "bg-emerald-950/60 text-emerald-400 border border-emerald-800/40"
                              : "bg-rose-950/60 text-rose-400 border border-rose-800/40"
                          }`}
                        >
                          {rec.bias}
                        </span>
                      </td>

                      <td className="px-3 py-3 whitespace-nowrap text-right font-mono">
                        <div className="font-bold text-white">${rec.stock_price.toFixed(2)}</div>
                        <div className={`text-[10px] ${rec.change_pct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          {rec.change_pct >= 0 ? "+" : ""}{rec.change_pct.toFixed(2)}%
                        </div>
                      </td>

                      <td className="px-3 py-3 whitespace-nowrap text-right font-mono font-bold text-emerald-400">
                        ${rec.ask.toFixed(2)}
                      </td>

                      <td className="px-3 py-3 whitespace-nowrap text-center font-mono font-semibold text-cyan-300">
                        {rec.delta > 0 ? "+" : ""}{rec.delta.toFixed(2)}
                      </td>

                      <td className="px-3 py-3 whitespace-nowrap text-center font-mono text-amber-300">
                        {rec.iv.toFixed(1)}%
                      </td>

                      <td className="px-3 py-3 whitespace-nowrap text-center font-mono text-slate-300">
                        {rec.dte}d
                      </td>

                      <td className="px-3 py-3 whitespace-nowrap text-center font-mono font-bold text-emerald-400">
                        {rec.pop_pct.toFixed(1)}%
                      </td>

                      <td className="px-3 py-3 whitespace-nowrap text-center font-mono font-bold text-cyan-300">
                        {rec.risk_reward_ratio.toFixed(2)}:1
                      </td>

                      <td className="px-3 py-3 whitespace-nowrap text-right font-mono">
                        <div className="font-bold text-white">${rec.tp1_price.toFixed(2)}</div>
                        <div className="text-[10px] text-emerald-400">+{rec.tp1_gain_pct.toFixed(0)}%</div>
                      </td>

                      <td className="px-4 py-3 whitespace-nowrap text-center">
                        <div className="flex items-center justify-center space-x-1.5">
                          <button
                            type="button"
                            onClick={() => handlePaperBuyClick(rec)}
                            disabled={rec.suggested_contracts <= 0}
                            className={`rounded-lg px-2.5 py-1 text-[11px] font-black transition active:scale-95 ${
                              rec.suggested_contracts <= 0
                                ? "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700"
                                : isBought
                                ? "bg-emerald-400 text-slate-950"
                                : "bg-emerald-500 hover:bg-emerald-400 text-slate-950 shadow-sm"
                            }`}
                          >
                            {rec.suggested_contracts <= 0 ? "0x (Budget)" : isBought ? "Filled" : `Buy ${rec.suggested_contracts}x`}
                          </button>
                          <button
                            type="button"
                            onClick={() => openPayoffModal(rec, "SINGLE")}
                            title="Interactive Payoff Diagram"
                            className="rounded-lg border border-cyan-500/40 bg-[#0c182c] p-1 text-cyan-300 hover:bg-cyan-500/20 hover:border-cyan-400 transition"
                          >
                            <LineChart className="h-3.5 w-3.5" />
                          </button>
                          <button
                            type="button"
                            onClick={() => onSelectTicker(rec.symbol)}
                            title="Terminal Deep Dive"
                            className="rounded-lg border border-slate-700 bg-[#101b30] p-1 text-slate-300 hover:text-cyan-300 hover:border-cyan-500/40"
                          >
                            <BarChart3 className="h-3.5 w-3.5" />
                          </button>
                          <button
                            type="button"
                            onClick={() => onOpenChain(rec.symbol)}
                            title="Chain Matrix"
                            className="rounded-lg border border-slate-700 bg-[#101b30] p-1 text-slate-300 hover:text-indigo-300 hover:border-indigo-500/40"
                          >
                            <Layers className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* 6. INTERACTIVE OPTION PAYOFF MODAL                        */}
      {/* ========================================================= */}
      {selectedPayoffRec && (
        <OptionPayoffModal
          isOpen={selectedPayoffRec !== null}
          onClose={() => setSelectedPayoffRec(null)}
          rec={selectedPayoffRec}
          initialMode={payoffInitialMode}
          onPaperBuy={(order: any) => {
            onPaperBuy(order);
            setTimeout(() => {
              syncPaperPositions();
            }, 250);
          }}
        />
      )}
    </div>
  );
}
