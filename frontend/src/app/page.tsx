"use client";

import React, { useState, useEffect, useMemo } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import {
  TrendingUp,
  Target,
  Wallet,
  Activity,
  Scale,
  Command,
  Star,
  TrendingDown,
  Minus,
  ShieldAlert,
  Sliders,
  Search,
  Sparkles,
  Download,
  BarChart3,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Cpu,
  Layers,
  Zap,
  Flame,
  Percent,
  Filter,
  Copy,
  Check,
  ArrowUpDown,
  ExternalLink,
  Shield,
  ArrowRight,
  Lock,
  Terminal,
  RotateCcw,
  FileCode,
} from "lucide-react";

// Dynamically import TradingView chart to avoid SSR window issues
const StockChart = dynamic(() => import("@/components/StockChart"), {
  ssr: false,
  loading: () => (
    <div className="flex h-[480px] w-full items-center justify-center rounded-xl border border-slate-800 bg-[#0c1322] text-slate-400">
      <RefreshCw className="mr-2 h-5 w-5 animate-spin text-cyan-400" />
      Loading TradingView Engine...
    </div>
  ),
});

const PayoffChart = dynamic(() => import("@/components/PayoffChart"), {
  ssr: false,
});

import MarketRibbon from "@/components/MarketRibbon";
import StarredWatchlistView from "@/components/StarredWatchlistView";
import VolatilityCockpit from "@/components/VolatilityCockpit";
import MultiLegStrategyBuilder from "@/components/MultiLegStrategyBuilder";
import { addOrConsolidatePosition, PaperTradePosition } from "@/utils/paperSettlement";

const PaperTradingTracker = dynamic(() => import("@/components/PaperTradingTracker"), {
  ssr: false,
  loading: () => (
    <div className="flex h-72 w-full items-center justify-center rounded-2xl border border-slate-800 bg-[#090e1a] text-slate-400">
      <RefreshCw className="mr-2 h-5 w-5 animate-spin text-cyan-400" />
      Loading Paper Trading Portfolio...
    </div>
  ),
});

const BestOptionsHome = dynamic(() => import("@/components/BestOptionsHome"), {
  ssr: false,
  loading: () => (
    <div className="flex h-72 w-full items-center justify-center rounded-2xl border border-slate-800 bg-[#090e1a] text-slate-400">
      <RefreshCw className="mr-2 h-5 w-5 animate-spin text-cyan-400" />
      Loading Best Options Recommendations...
    </div>
  ),
});

const OptionsChainMatrix = dynamic(() => import("@/components/OptionsChainMatrix"), {
  ssr: false,
  loading: () => (
    <div className="flex h-72 w-full items-center justify-center rounded-2xl border border-slate-800 bg-[#090e1a] text-slate-400">
      <RefreshCw className="mr-2 h-5 w-5 animate-spin text-cyan-400" />
      Loading Interactive Options Chain Matrix...
    </div>
  ),
});

export default function Home() {
  const [primaryContracts, setPrimaryContracts] = useState<number>(1);
  const [highRiskContracts, setHighRiskContracts] = useState<number>(1);
  const [aiPickContracts, setAiPickContracts] = useState<Record<string, number>>({});
  const [paperToast, setPaperToast] = useState<{ message: string; id: number } | null>(null);

  const [activeTab, setActiveTab] = useState<"home" | "terminal" | "chain_matrix" | "volatility" | "builder" | "watchlist" | "ai_picks" | "high_risk" | "zero_dte" | "paper_trading">("home");
  const [starredTickers, setStarredTickers] = useState<string[]>(["NVDA", "AAPL", "SPY", "QQQ", "TSLA"]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      try {
        const saved = localStorage.getItem("options_starred_tickers");
        if (saved) {
          const parsed = JSON.parse(saved);
          if (Array.isArray(parsed) && parsed.length > 0) {
            setStarredTickers(parsed);
          }
        }
      } catch (e) {
        console.error("Failed to load starred tickers:", e);
      }
    }
  }, []);

  const toggleStar = (sym: string) => {
    const clean = sym.trim().toUpperCase().replace("^", "");
    if (!clean) return;
    setStarredTickers((prev) => {
      const next = prev.includes(clean) ? prev.filter((t) => t !== clean) : [...prev, clean];
      if (typeof window !== "undefined") {
        try {
          localStorage.setItem("options_starred_tickers", JSON.stringify(next));
        } catch (e) {
          console.error("Failed to save starred tickers:", e);
        }
      }
      return next;
    });
  };

  const isStarred = (sym: string) => {
    return starredTickers.includes(sym.trim().toUpperCase().replace("^", ""));
  };
  const [ticker, setTicker] = useState("NVDA");
  const [showShortcutsHelp, setShowShortcutsHelp] = useState(false);
  const searchInputRef = React.useRef<HTMLInputElement>(null);
  const [searchInput, setSearchInput] = useState("NVDA");
  const [period, setPeriod] = useState("6mo");
  const [equity, setEquity] = useState(10000);
  const [riskPct, setRiskPct] = useState(1.0);

  // Data states
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // High-confidence picks state
  const [aiSector, setAiSector] = useState("all_ai");
  const [minConf, setMinConf] = useState(35);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiPicks, setAiPicks] = useState<any[]>([]);

  // High-risk speculative state
  const [highRiskCategory, setHighRiskCategory] = useState("all_speculative");
  const [specRiskPct, setSpecRiskPct] = useState(1.0);
  const [highRiskLoading, setHighRiskLoading] = useState(false);
  const [highRiskSetups, setHighRiskSetups] = useState<any[]>([]);

  // 0DTE Flash Lab state
  const [zeroDteTicker, setZeroDteTicker] = useState("SPY");
  const [zeroDteSearchInput, setZeroDteSearchInput] = useState("SPY");
  const [zeroDteLoading, setZeroDteLoading] = useState(false);
  const [zeroDteSetups, setZeroDteSetups] = useState<any[]>([]);
  const [zeroDteSelectedSymbol, setZeroDteSelectedSymbol] = useState("SPY");
  const [zeroDteChainFilter, setZeroDteChainFilter] = useState<"ALL" | "CALL" | "PUT" | "ATM" | "MOONSHOT" | "LIQUID">("ALL");
  const [zeroDteChainQuery, setZeroDteChainQuery] = useState("");
  const [zeroDteSortBy, setZeroDteSortBy] = useState("strike_asc");
  const [copiedContract, setCopiedContract] = useState<string | null>(null);
  const [checkedSteps, setCheckedSteps] = useState<Record<string, boolean>>({});
  const toggleStep = (key: string) => setCheckedSteps((prev) => ({ ...prev, [key]: !prev[key] }));

  // Phase 1 Trade Plan states
  const [selectedBrokerFormat, setSelectedBrokerFormat] = useState<"standard" | "tos" | "ibkr" | "webull">("standard");
  const [activeRollingTab, setActiveRollingTab] = useState<"defensive_time_roll" | "synthetic_spread_conversion" | "profit_lock_roll">("defensive_time_roll");
  const [copiedBracket, setCopiedBracket] = useState(false);

  const copyBracketOrder = (text: string) => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(text);
      setCopiedBracket(true);
      setTimeout(() => setCopiedBracket(false), 2000);
    }
  };

  const copyToClipboard = (text: string) => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(text);
      setCopiedContract(text);
      setTimeout(() => setCopiedContract(null), 2000);
    }
  };

    const buyInPaperPortfolio = (
    opt: any,
    sym: string,
    type: "CALL" | "PUT",
    customContracts?: number,
    notePrefix: string = "Terminal signal"
  ) => {
    try {
      const savedBalanceStr = localStorage.getItem("options_paper_balance");
      const balance = savedBalanceStr ? parseFloat(savedBalanceStr) : 10000;
      const contractsCandidate = customContracts ?? opt.suggested_contracts ?? opt.contracts ?? 0;
      if (contractsCandidate <= 0) {
        alert("Cannot execute paper order: 0 contracts qualified (trade exceeds risk budget).");
        return;
      }
      const qty = contractsCandidate;
      const askPx = opt.net_debit ?? opt.ask ?? opt.price ?? 1;
      const cost = askPx * 100 * qty;
      if (cost > balance) {
        alert(
          `Insufficient virtual cash ($${balance.toFixed(2)}) for total trade cost of $${cost.toFixed(2)} (${qty}x contracts). Available balance: $${balance.toFixed(2)}.`
        );
        return;
      }
      const savedPositionsStr = localStorage.getItem("options_paper_positions");
      const positions = savedPositionsStr ? JSON.parse(savedPositionsStr) : [];

      const expClean = (opt.expiration || "2026-10-16").replace(/-/g, "").slice(2);
      const strikeFormatted = String(Math.round((opt.strike || 100) * 1000)).padStart(8, "0");
      const contractSym = opt.contract || `${sym}${expClean}${type[0]}${strikeFormatted}`;

      const newPos: PaperTradePosition = {
        id: `pos-${Date.now()}`,
        ticker: sym,
        contract: contractSym,
        optionType: type,
        strike: opt.strike,
        expiration: opt.expiration || "2026-10-16",
        dte: opt.dte || 30,
        entryPrice: askPx,
        contracts: qty,
        totalCost: cost,
        enteredAt: new Date().toISOString(),
        currentPrice: askPx,
        status: "OPEN",
        targetProfitPrice: opt.trade_plan?.profit_targets?.[0]?.contract_price,
        stopLossPrice: opt.stop_loss_price,
        notes: opt.notes || `Simulated execution from ${notePrefix}`,
      };

      const { updatedPositions, consolidated, totalQty, weightedPrice } = addOrConsolidatePosition(
        positions,
        newPos
      );

      localStorage.setItem("options_paper_positions", JSON.stringify(updatedPositions));
      localStorage.setItem("options_paper_balance", (balance - cost).toString());
      const toastMessage = consolidated
        ? `Consolidated into existing position: now holding ${totalQty}x ${sym} $${opt.strike} ${type} (avg entry $${weightedPrice.toFixed(2)})!`
        : opt.isSpread
        ? `Filled ${qty}x ${contractSym} @ $${askPx.toFixed(2)} ($${cost.toFixed(2)} total debit). Added to Paper Portfolio!`
        : `Filled ${qty}x ${sym} $${opt.strike} ${type} @ $${askPx.toFixed(2)} ($${cost.toFixed(2)} total cost). Added to Paper Portfolio!`;

      setPaperToast({
        message: toastMessage,
        id: Date.now(),
      });
    } catch (err) {
      console.error("Failed to save paper position:", err);
    }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      const isInput = target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable);

      if (e.key === "Escape") {
        setShowShortcutsHelp(false);
        if (isInput) target.blur();
        return;
      }

      if (isInput) return;

      if (e.key === "0" || e.key === "h" || e.key === "H") {
        setActiveTab("home");
      } else if (e.key === "/") {
        e.preventDefault();
        searchInputRef.current?.focus();
        searchInputRef.current?.select();
      } else if (e.key === "1") {
        setActiveTab("terminal");
      } else if (e.key === "2") {
        setActiveTab("chain_matrix");
      } else if (e.key === "3") {
        setActiveTab("volatility");
      } else if (e.key === "4") {
        setActiveTab("builder");
      } else if (e.key === "5") {
        setActiveTab("watchlist");
      } else if (e.key === "6") {
        setActiveTab("ai_picks");
        if (aiPicks.length === 0) fetchAiPicks();
      } else if (e.key === "7") {
        setActiveTab("high_risk");
        if (highRiskSetups.length === 0) fetchHighRiskSetups();
      } else if (e.key === "8") {
        setActiveTab("zero_dte");
        if (zeroDteSetups.length === 0) fetchZeroDteSetups("SPY");
      } else if (e.key === "9") {
        setActiveTab("paper_trading");
      } else if (e.key === "?") {
        e.preventDefault();
        setShowShortcutsHelp((prev) => !prev);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [aiPicks.length, highRiskSetups.length, zeroDteSetups.length]);

  // Fetch single stock analysis
  const fetchAnalysis = async (symbolToFetch: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `/api/stock-analysis?ticker=${encodeURIComponent(symbolToFetch)}&period=${period}&equity=${equity}&risk_pct=${riskPct}`
      );
      if (!res.ok) {
        const errorText = await res.text();
        let message = `Failed fetching data for ${symbolToFetch}`;
        try {
          const errorJson = JSON.parse(errorText);
          if (errorJson.detail) message = errorJson.detail;
        } catch {
          if (res.status === 404) message = `Ticker symbol '${symbolToFetch}' not found or has no active data.`;
        }
        throw new Error(message);
      }
      const json = await res.json();
      setData(json);
      setTicker(symbolToFetch);
    } catch (err: any) {
      setError(
        err.message ||
          "Connection error. Please ensure the backend is running via start-web.bat or .\\start-web.ps1"
      );
    } finally {
      setLoading(false);
    }
  };

  // Fetch high confidence AI picks
  const fetchAiPicks = async () => {
    setAiLoading(true);
    try {
      const res = await fetch(
        `/api/high-confidence?sector=${aiSector}&min_confidence=${minConf}&equity=${equity}&risk_pct=${riskPct}`
      );
      if (!res.ok) throw new Error("Failed fetching AI picks from backend");
      const json = await res.json();
      setAiPicks(json.picks || []);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed fetching AI picks");
    } finally {
      setAiLoading(false);
    }
  };

  // Fetch 0DTE Flash Lab setups
  const fetchZeroDteSetups = async (customTicker?: string) => {
    setZeroDteLoading(true);
    try {
      const q = (customTicker !== undefined && customTicker !== "") ? `?ticker=${encodeURIComponent(customTicker)}&` : "?";
      const res = await fetch(
        `/api/zero-dte${q}equity=${equity}&risk_pct=${specRiskPct}`
      );
      if (!res.ok) throw new Error("Failed fetching 0DTE setups");
      const json = await res.json();
      const loadedSetups = json.setups || [];
      setZeroDteSetups(loadedSetups);
      if (customTicker) {
        setZeroDteTicker(customTicker);
        setZeroDteSearchInput(customTicker);
        setZeroDteSelectedSymbol(customTicker);
      } else if (loadedSetups.length > 0) {
        setZeroDteSelectedSymbol(loadedSetups[0].symbol);
      }
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed fetching 0DTE setups");
    } finally {
      setZeroDteLoading(false);
    }
  };

  // Active setup and filtered chain calculations for 0DTE options explorer
  const activeZeroDteSetup = useMemo(() => {
    return zeroDteSetups.find((s) => s.symbol === zeroDteSelectedSymbol) || zeroDteSetups[0] || null;
  }, [zeroDteSetups, zeroDteSelectedSymbol]);

  const allZeroDteOptions = useMemo(() => {
    return (activeZeroDteSetup?.all_options || []) as any[];
  }, [activeZeroDteSetup]);

  const filteredZeroDteOptions = useMemo(() => {
    if (!allZeroDteOptions.length) return [];
    let list = [...allZeroDteOptions];

    // Filter by search query
    if (zeroDteChainQuery.trim()) {
      const q = zeroDteChainQuery.trim().toLowerCase();
      list = list.filter((c: any) =>
        (c.contract && c.contract.toLowerCase().includes(q)) ||
        (c.strike !== undefined && c.strike.toString().includes(q)) ||
        (c.type && c.type.toLowerCase().includes(q)) ||
        (c.delta !== undefined && c.delta.toString().includes(q))
      );
    }

    // Filter by category chip
    if (zeroDteChainFilter === "CALL") {
      list = list.filter((c: any) => c.type === "CALL");
    } else if (zeroDteChainFilter === "PUT") {
      list = list.filter((c: any) => c.type === "PUT");
    } else if (zeroDteChainFilter === "ATM") {
      list = list.filter((c: any) => Math.abs(c.moneyness_pct || 0) <= 2.5);
    } else if (zeroDteChainFilter === "MOONSHOT") {
      list = list.filter((c: any) => Math.abs(c.delta || 0) >= 0.15 && Math.abs(c.delta || 0) <= 0.30);
    } else if (zeroDteChainFilter === "LIQUID") {
      list = list.filter((c: any) => (c.volume || 0) >= 500);
    }

    // Sorting
    if (zeroDteSortBy === "strike_asc") {
      list.sort((a: any, b: any) => a.strike - b.strike || (a.type === "CALL" ? -1 : 1));
    } else if (zeroDteSortBy === "strike_desc") {
      list.sort((a: any, b: any) => b.strike - a.strike || (a.type === "CALL" ? -1 : 1));
    } else if (zeroDteSortBy === "volume") {
      list.sort((a: any, b: any) => (b.volume || 0) - (a.volume || 0));
    } else if (zeroDteSortBy === "delta") {
      list.sort((a: any, b: any) => Math.abs(b.delta || 0) - Math.abs(a.delta || 0));
    } else if (zeroDteSortBy === "theta_burn") {
      list.sort((a: any, b: any) => Math.abs(a.theta_per_hour || 0) - Math.abs(b.theta_per_hour || 0));
    } else if (zeroDteSortBy === "spread") {
      list.sort((a: any, b: any) => (a.spread_pct || 0) - (b.spread_pct || 0));
    }

    return list;
  }, [allZeroDteOptions, zeroDteChainQuery, zeroDteChainFilter, zeroDteSortBy]);

  // Fetch high-risk speculative setups
  const fetchHighRiskSetups = async () => {
    setHighRiskLoading(true);
    try {
      const res = await fetch(
        `/api/high-risk-setups?category=${highRiskCategory}&equity=${equity}&risk_pct=${specRiskPct}`
      );
      if (!res.ok) throw new Error("Failed fetching high-risk setups");
      const json = await res.json();
      setHighRiskSetups(json.setups || []);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed fetching high-risk setups");
    } finally {
      setHighRiskLoading(false);
    }
  };

  // Auto-sync contract suggestions and auto-dismiss paper trade toast
  useEffect(() => {
    if (data?.options?.single_leg?.[0]?.suggested_contracts) {
      setPrimaryContracts(data.options.single_leg[0].suggested_contracts);
    } else {
      setPrimaryContracts(1);
    }
    if (data?.options?.high_risk_setup?.suggested_contracts) {
      setHighRiskContracts(data.options.high_risk_setup.suggested_contracts);
    } else {
      setHighRiskContracts(1);
    }
  }, [data]);

  useEffect(() => {
    if (paperToast) {
      const timer = setTimeout(() => setPaperToast(null), 6000);
      return () => clearTimeout(timer);
    }
  }, [paperToast]);

  useEffect(() => {
    fetchAnalysis(ticker);
  }, [period]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim()) {
      fetchAnalysis(searchInput.trim().toUpperCase());
    }
  };

  const quote = data?.quote;
  const signal = data?.signal;
  const momentum = data?.momentum;
  const sentiment = data?.sentiment;
  const options = data?.options;
  const primaryOpt = options?.single_leg?.[0];
  const primarySpread = options?.debit_spreads?.[0];
  const highRiskAlt = options?.high_risk_setup;

  return (
    <div className="min-h-screen bg-[#070b12] text-slate-100">
      {/* Global Market Ticker Ribbon */}
      <MarketRibbon
        activeTicker={ticker}
        starredTickers={starredTickers}
        onToggleStar={toggleStar}
        onSelectTicker={(sym) => {
          setSearchInput(sym);
          setTicker(sym);
          fetchAnalysis(sym);
          setActiveTab("terminal");
        }}
      />
      {/* ----------------- TOP NAVBAR ----------------- */}
      <header className="sticky top-0 z-50 border-b border-slate-800/80 bg-[#070b12]/95 backdrop-blur-md">
        <div className="w-full px-4 py-2.5">
          <div className="flex items-center justify-between gap-3">
            {/* Left: Brand Logo & Title + Route Switcher */}
            <div className="flex shrink-0 items-center space-x-3">
              <div className="flex items-center space-x-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 shadow-md shadow-cyan-500/20">
                  <Zap className="h-4 w-4 text-white" />
                </div>
                <div className="flex items-baseline space-x-2">
                  <span className="text-sm font-bold tracking-tight text-white whitespace-nowrap">
                    Options Suggester <span className="text-cyan-400">Pro</span>
                  </span>
                  <span className="hidden rounded-full bg-cyan-950/80 px-2 py-0.5 text-[9px] font-semibold text-cyan-300 border border-cyan-800/50 xl:inline-block">
                    Next.js • Quantitative
                  </span>
                </div>
              </div>

              {/* Route Switcher: Options Pro ⇄ Stock Picks Pro */}
              <div className="flex items-center space-x-1 rounded-xl border border-slate-800/90 bg-[#0a1120] p-1 text-xs">
                <span
                  title="Current page: Options Terminal"
                  className="flex items-center space-x-1.5 rounded-lg bg-cyan-500/20 px-2.5 py-1 font-semibold text-cyan-300 border border-cyan-500/40 shadow-sm shadow-cyan-500/20 whitespace-nowrap"
                >
                  <span>⚡ Options Pro</span>
                </span>
                <Link
                  href="/stocks"
                  title="Switch to Stock Picks Pro"
                  className="flex items-center space-x-1.5 rounded-lg px-2.5 py-1 font-medium text-slate-400 hover:text-emerald-300 hover:bg-emerald-950/40 border border-transparent hover:border-emerald-500/40 hover:shadow-[0_0_15px_rgba(16,185,129,0.35)] transition-all duration-200 whitespace-nowrap group"
                >
                  <span className="group-hover:text-emerald-300 transition">📈 Stock Picks Pro</span>
                </Link>
              </div>
            </div>

            {/* Center: Mode Switcher Tabs (Scrollable on small screens with clean spacing) */}
            <div className="flex min-w-0 flex-1 justify-center px-1">
              <div className="flex items-center space-x-1 overflow-x-auto rounded-xl border border-slate-800/90 bg-[#0a1120] p-1 text-xs scrollbar-none max-w-full">
                <button
                  onClick={() => setActiveTab("home")}
                  className={`flex shrink-0 items-center space-x-1.5 rounded-lg px-2.5 py-1.5 font-medium transition whitespace-nowrap ${
                    activeTab === "home"
                      ? "bg-cyan-500/20 text-cyan-300 shadow-sm border border-cyan-500/40"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <Target className="h-3.5 w-3.5 text-cyan-400" />
                  <span>?? Best Options</span>
                </button>

                <button
                  onClick={() => setActiveTab("terminal")}
                  className={`flex shrink-0 items-center space-x-1.5 rounded-lg px-2.5 py-1.5 font-medium transition whitespace-nowrap ${
                    activeTab === "terminal"
                      ? "bg-cyan-500/20 text-cyan-300 shadow-sm border border-cyan-500/40"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <BarChart3 className="h-3.5 w-3.5 text-cyan-400" />
                  <span>Terminal</span>
                </button>

                <button
                  onClick={() => setActiveTab("chain_matrix")}
                  className={`flex shrink-0 items-center space-x-1.5 rounded-lg px-2.5 py-1.5 font-medium transition whitespace-nowrap ${
                    activeTab === "chain_matrix"
                      ? "bg-cyan-500/20 text-cyan-300 shadow-sm border border-cyan-500/40"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <Layers className="h-3.5 w-3.5 text-cyan-400" />
                  <span>Chain Matrix</span>
                </button>

                <button
                  onClick={() => setActiveTab("volatility")}
                  className={`flex shrink-0 items-center space-x-1.5 rounded-lg px-2.5 py-1.5 font-medium transition whitespace-nowrap ${
                    activeTab === "volatility"
                      ? "bg-cyan-500/20 text-cyan-300 shadow-sm border border-cyan-500/40"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <Activity className="h-3.5 w-3.5 text-cyan-400" />
                  <span>IV Cockpit</span>
                </button>

                <button
                  onClick={() => setActiveTab("builder")}
                  className={`flex shrink-0 items-center space-x-1.5 rounded-lg px-2.5 py-1.5 font-medium transition whitespace-nowrap ${
                    activeTab === "builder"
                      ? "bg-indigo-500/20 text-indigo-300 shadow-sm border border-indigo-500/40"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <Scale className="h-3.5 w-3.5 text-indigo-400" />
                  <span>Strategy Builder</span>
                </button>

                <button
                  onClick={() => setActiveTab("watchlist")}
                  className={`flex shrink-0 items-center space-x-1.5 rounded-lg px-2.5 py-1.5 font-medium transition whitespace-nowrap ${
                    activeTab === "watchlist"
                      ? "bg-amber-500/20 text-amber-300 shadow-sm border border-amber-500/40"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <Star className={`h-3.5 w-3.5 ${starredTickers.length > 0 ? "fill-amber-400 text-amber-400" : "text-amber-400"}`} />
                  <span>Watchlist</span>
                  {starredTickers.length > 0 && (
                    <span className="rounded-full bg-amber-500/20 px-1.5 py-0.2 text-[10px] font-bold text-amber-300">
                      {starredTickers.length}
                    </span>
                  )}
                </button>

                <button
                  onClick={() => {
                    setActiveTab("ai_picks");
                    if (aiPicks.length === 0) fetchAiPicks();
                  }}
                  className={`flex shrink-0 items-center space-x-1.5 rounded-lg px-2.5 py-1.5 font-medium transition whitespace-nowrap ${
                    activeTab === "ai_picks"
                      ? "bg-indigo-500/20 text-indigo-300 shadow-sm border border-indigo-500/40"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
                  <span>AI Picks</span>
                </button>

                <button
                  onClick={() => {
                    setActiveTab("high_risk");
                    if (highRiskSetups.length === 0) fetchHighRiskSetups();
                  }}
                  className={`flex shrink-0 items-center space-x-1.5 rounded-lg px-2.5 py-1.5 font-medium transition whitespace-nowrap ${
                    activeTab === "high_risk"
                      ? "bg-rose-500/20 text-rose-300 shadow-sm border border-rose-500/40"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <Flame className="h-3.5 w-3.5 text-rose-400" />
                  <span>High-Risk</span>
                </button>

                <button
                  onClick={() => {
                    setActiveTab("zero_dte");
                    if (zeroDteSetups.length === 0) fetchZeroDteSetups("SPY");
                  }}
                  className={`flex shrink-0 items-center space-x-1.5 rounded-lg px-2.5 py-1.5 font-medium transition whitespace-nowrap ${
                    activeTab === "zero_dte"
                      ? "bg-amber-500/20 text-amber-300 shadow-sm border border-amber-500/40"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <Zap className="h-3.5 w-3.5 text-amber-400" />
                  <span>0DTE Flash</span>
                </button>

                <button
                  onClick={() => setActiveTab("paper_trading")}
                  className={`flex shrink-0 items-center space-x-1.5 rounded-lg px-2.5 py-1.5 font-medium transition whitespace-nowrap ${
                    activeTab === "paper_trading"
                      ? "bg-emerald-500/20 text-emerald-300 shadow-sm border border-emerald-500/40"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <Wallet className="h-3.5 w-3.5 text-emerald-400" />
                  <span>Paper Portfolio</span>
                </button>

              </div>
            </div>

            {/* Right: Search Input + Star + Shortcut helper */}
            <div className="flex shrink-0 items-center space-x-2">
              <form onSubmit={handleSearchSubmit} className="relative flex items-center space-x-1.5">
                <div className="relative w-44 md:w-56">
                  <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-500" />
                  <input
                    ref={searchInputRef}
                    type="text"
                    placeholder="Search US Ticker..."
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                    className="w-full rounded-lg border border-slate-800 bg-[#0c1424] py-1.5 pl-8 pr-7 text-xs text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none uppercase"
                  />
                  <kbd className="absolute right-2 top-2 hidden rounded border border-slate-700 bg-slate-800/80 px-1 py-0.2 font-mono text-[9px] text-slate-400 md:inline-block">
                    /
                  </kbd>
                </div>
                <button
                  type="button"
                  onClick={() => toggleStar(ticker)}
                  title={isStarred(ticker) ? `Remove ${ticker} from Watchlist` : `Add ${ticker} to Watchlist`}
                  className={`flex h-7 w-7 items-center justify-center rounded-lg border transition ${
                    isStarred(ticker)
                      ? "border-amber-500/50 bg-amber-500/10 text-amber-400 shadow-sm shadow-amber-950"
                      : "border-slate-800 bg-[#0c1424] text-slate-400 hover:text-amber-400"
                  }`}
                >
                  <Star className={`h-3.5 w-3.5 ${isStarred(ticker) ? "fill-amber-400" : ""}`} />
                </button>
                <button
                  type="button"
                  onClick={() => setShowShortcutsHelp(true)}
                  title="Keyboard Shortcuts (Press ?)"
                  className="hidden h-7 w-7 items-center justify-center rounded-lg border border-slate-800 bg-[#0c1424] text-slate-400 hover:text-cyan-400 hover:border-slate-700 transition lg:flex"
                >
                  <Command className="h-3.5 w-3.5" />
                </button>
              </form>
            </div>
          </div>
        </div>
      </header>

      {/* ----------------- SUB-NAV QUICK CHIPS ----------------- */}
      <div className="border-b border-slate-800/60 bg-[#090e18] px-4 py-2">
        <div className="mx-auto flex max-w-7xl items-center justify-between overflow-x-auto text-xs">
          <div className="flex items-center space-x-2">
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              Best Companies:
            </span>
            {[
              "AAPL", "NVDA", "MSFT", "AMZN", "GOOGL", "META", "TSLA",
              "BRK-B", "LLY", "AVGO", "JPM", "V", "TSM", "WMT", "COST",
              "NFLX", "AMD", "SPY", "QQQ"
            ].map(
              (sym) => (
                <button
                  key={sym}
                  onClick={() => {
                    setSearchInput(sym);
                    setTicker(sym);
                    fetchAnalysis(sym);
                  }}
                  className={`rounded-md px-2.5 py-1 text-xs font-semibold transition ${
                    ticker === sym
                      ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/30"
                      : "bg-[#11192a] text-slate-300 hover:bg-slate-800 hover:text-white border border-slate-800"
                  }`}
                >
                  {sym}
                </button>
              )
            )}
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-slate-500">History:</span>
            {["3mo", "6mo", "1y"].map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`rounded px-2 py-0.5 text-xs font-medium uppercase ${
                  period === p ? "bg-slate-700 text-cyan-300 font-bold" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ----------------- MAIN CONTENT ----------------- */}
      <main className="mx-auto max-w-7xl p-4 sm:p-6">
        {/* Error message */}
        {error && (
          <div className="mb-4 flex items-center space-x-2 rounded-lg border border-red-500/30 bg-red-950/40 p-3 text-sm text-red-300">
            <AlertTriangle className="h-5 w-5 text-red-400" />
            <span>{error}</span>
          </div>
        )}

        {/* ========================================================= */}
        {/* VIEW 0: BEST OPTIONS HOME (DEFAULT VIEW)                  */}
        {/* ========================================================= */}
        {activeTab === "home" && (
          <BestOptionsHome
            onSelectTicker={(sym) => {
              setSearchInput(sym);
              setTicker(sym);
              fetchAnalysis(sym);
              setActiveTab("terminal");
            }}
            onOpenChain={(sym) => {
              setSearchInput(sym);
              setTicker(sym);
              setActiveTab("chain_matrix");
            }}
            onPaperBuy={(rec: any) => {
              buyInPaperPortfolio(
                rec,
                rec.symbol,
                rec.option_type,
                rec.suggested_contracts,
                rec.isSpread ? rec.strategy_label : `Best Options (${rec.strategy_label})`
              );
            }}
            starredTickers={starredTickers}
            onToggleStar={toggleStar}
          />
        )}

        {/* ========================================================= */}
        {/* VIEW 1: TERMINAL DEEP DIVE                                */}
        {/* ========================================================= */}
        {activeTab === "terminal" && (
          <div>
            {/* Header KPI Bar */}
            {quote && (
              <div className="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
                <div className="rounded-xl border border-slate-800 bg-[#0d1424] p-3 shadow-md">
                  <div className="text-[11px] font-medium text-slate-400">Current Price</div>
                  <div className="flex items-baseline space-x-2">
                    <span className="text-xl font-bold text-white">${quote.current_price.toFixed(2)}</span>
                    <span
                      className={`text-xs font-semibold ${
                        quote.change >= 0 ? "text-emerald-400" : "text-red-400"
                      }`}
                    >
                      {quote.change >= 0 ? "+" : ""}
                      {quote.change_percent.toFixed(2)}%
                    </span>
                  </div>
                </div>

                <div className="rounded-xl border border-slate-800 bg-[#0d1424] p-3 shadow-md">
                  <div className="text-[11px] font-medium text-slate-400">Day Range</div>
                  <div className="text-sm font-semibold text-slate-200">
                    ${quote.day_low.toFixed(2)} - ${quote.day_high.toFixed(2)}
                  </div>
                </div>

                <div className="rounded-xl border border-slate-800 bg-[#0d1424] p-3 shadow-md">
                  <div className="text-[11px] font-medium text-slate-400">52W Range</div>
                  <div className="text-sm font-semibold text-slate-200">
                    ${quote.fifty_two_week_low.toFixed(2)} - ${quote.fifty_two_week_high.toFixed(2)}
                  </div>
                </div>

                <div className="rounded-xl border border-slate-800 bg-[#0d1424] p-3 shadow-md">
                  <div className="text-[11px] font-medium text-slate-400">20d Volume Ratio</div>
                  <div className="flex items-center space-x-1.5 text-sm font-semibold">
                    <span className="text-white">{momentum?.volume_ratio.toFixed(2)}x</span>
                    {momentum?.volume_confirmed ? (
                      <span className="rounded bg-emerald-950/60 px-1.5 py-0.2 text-[10px] text-emerald-400 font-bold">
                        CONFIRMED
                      </span>
                    ) : (
                      <span className="rounded bg-amber-950/60 px-1.5 py-0.2 text-[10px] text-amber-400 font-bold">
                        LOW
                      </span>
                    )}
                  </div>
                </div>

                <div className="rounded-xl border border-slate-800 bg-[#0d1424] p-3 shadow-md">
                  <div className="text-[11px] font-medium text-slate-400">MTF Weekly Trend</div>
                  <div className="text-sm font-bold text-cyan-300">
                    {momentum?.weekly_trend}
                  </div>
                </div>

                <div className="rounded-xl border border-slate-800 bg-[#0d1424] p-3 shadow-md">
                  <div className="text-[11px] font-medium text-slate-400">News Sentiment</div>
                  <div className="flex items-center space-x-1.5 text-sm font-semibold">
                    <span
                      className={
                        sentiment?.score > 0
                          ? "text-emerald-400"
                          : sentiment?.score < 0
                          ? "text-red-400"
                          : "text-slate-300"
                      }
                    >
                      {sentiment?.score > 0 ? "+" : ""}
                      {sentiment?.score.toFixed(2)}
                    </span>
                    <span className="text-[10px] text-slate-400">({sentiment?.article_count} news)</span>
                  </div>
                </div>
              </div>
            )}

            {/* Earnings Blackout Alert */}
            {data?.earnings?.is_blackout && (
              <div className="mb-5 flex items-center space-x-3 rounded-xl border border-red-500/40 bg-red-950/30 p-4 text-red-200">
                <ShieldAlert className="h-6 w-6 text-red-400 flex-shrink-0" />
                <div>
                  <h4 className="font-bold text-red-300">EARNINGS BLACKOUT ACTIVE</h4>
                  <p className="text-xs text-red-200/80">{data.earnings.status_message}</p>
                </div>
              </div>
            )}

            {/* Strategic Signal Hero Banner */}
            {signal && (
              <div
                className={`mb-6 rounded-2xl border p-5 shadow-2xl transition ${
                  signal.bias === "BULLISH"
                    ? "border-emerald-500/30 bg-gradient-to-r from-[#0d231e] via-[#0d1b28] to-[#0a1120]"
                    : signal.bias === "BEARISH"
                    ? "border-red-500/30 bg-gradient-to-r from-[#291114] via-[#1a0f1b] to-[#0a1120]"
                    : "border-amber-500/30 bg-gradient-to-r from-[#241a0b] via-[#161722] to-[#0a1120]"
                }`}
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center space-x-3">
                    <span className="text-xl font-extrabold text-white">
                      {quote?.name} ({ticker})
                    </span>
                    <button
                      onClick={() => toggleStar(ticker)}
                      title={isStarred(ticker) ? `Remove ${ticker} from Watchlist` : `Add ${ticker} to Watchlist`}
                      className="rounded-lg p-1 text-amber-400 hover:bg-slate-800/80 transition"
                    >
                      <Star className={`h-5 w-5 ${isStarred(ticker) ? "fill-amber-400 text-amber-400" : "text-slate-500 hover:text-amber-400"}`} />
                    </button>
                    <span
                      className={`inline-flex items-center rounded-full px-3.5 py-1 text-xs font-black tracking-wider uppercase ${
                        signal.bias === "BULLISH"
                          ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 shadow-emerald-500/20 shadow-md"
                          : signal.bias === "BEARISH"
                          ? "bg-red-500/20 text-red-400 border border-red-500/40 shadow-red-500/20 shadow-md"
                          : "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                      }`}
                    >
                      {signal.bias === "BULLISH" && <TrendingUp className="mr-1 h-3.5 w-3.5" />}
                      {signal.bias === "BEARISH" && <TrendingDown className="mr-1 h-3.5 w-3.5" />}
                      {signal.bias === "NEUTRAL" && <Minus className="mr-1 h-3.5 w-3.5" />}
                      {signal.bias}
                    </span>
                    <span className="rounded-md bg-cyan-950/80 px-2.5 py-1 text-xs font-bold text-cyan-300 border border-cyan-800">
                      [{signal.confidence_tier} CONFIDENCE] {signal.confidence_pct}%
                    </span>
                  </div>

                  <div className="text-xs text-slate-400">
                    Combined Score:{" "}
                    <strong className="text-white font-mono text-sm">
                      {signal.combined_score > 0 ? "+" : ""}
                      {signal.combined_score.toFixed(2)}
                    </strong>
                  </div>
                </div>

                <div className="mt-3 text-xs leading-relaxed text-slate-300 sm:text-sm">
                  <strong className="text-cyan-300">Tactical Directive:</strong>{" "}
                  {signal.action_suggestion}
                </div>
              </div>
            )}

            {/* Main Interactive Grid: Chart & Contract Spotlight */}
            <div className="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-12">
              {/* Left Column: TradingView Chart (7 cols) */}
              <div className="lg:col-span-7">
                {data?.candles && <StockChart symbol={ticker} data={data.candles} />}
              </div>

              {/* Right Column: Contract Spotlight & Payoff Diagram (5 cols) */}
              <div className="flex flex-col space-y-4 lg:col-span-5">
                {primaryOpt ? (
                  <div className="rounded-xl border border-cyan-500/30 bg-[#0e172a] p-5 shadow-2xl">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="rounded bg-cyan-500/20 px-2 py-0.5 text-[11px] font-bold text-cyan-300">
                            PRIMARY PICK (DISCIPLINED)
                          </span>
                          <span className="text-xs font-semibold text-slate-400">
                            {primaryOpt.expiration} ({primaryOpt.dte}d DTE)
                          </span>
                        </div>
                        <h3 className="mt-1 text-lg font-bold text-white">
                          ${primaryOpt.strike.toFixed(2)} {primaryOpt.type}
                        </h3>
                        <div className="text-xs text-cyan-300 font-mono">
                          Delta: {primaryOpt.delta > 0 ? "+" : ""}
                          {primaryOpt.delta.toFixed(2)}Δ (Target 0.30–0.55)
                        </div>
                      </div>

                      <div className="text-right">
                        <div className="text-xl font-black text-emerald-400">
                          ${primaryOpt.ask.toFixed(2)}
                        </div>
                        <div className="text-[11px] text-slate-400">
                          Bid: ${primaryOpt.bid.toFixed(2)} | Spread: {primaryOpt.spread_pct.toFixed(1)}%
                        </div>
                      </div>
                    </div>

                    {/* Sizing & Risk Card */}
                    <div className="mt-4 grid grid-cols-3 gap-2 rounded-lg bg-[#080d18] p-3 text-center border border-slate-800">
                      <div>
                        <div className="text-[10px] text-slate-400">Position Sizing</div>
                        <div className="text-xs font-bold text-cyan-300">
                          {primaryOpt.suggested_contracts}x (${primaryOpt.total_dollar_risk.toFixed(0)})
                        </div>
                      </div>
                      <div>
                        <div className="text-[10px] text-slate-400">50% Stop-Loss</div>
                        <div className="text-xs font-bold text-red-400">
                          ${primaryOpt.stop_loss_price.toFixed(2)}
                        </div>
                      </div>
                      <div>
                        <div className="text-[10px] text-slate-400">Breakeven</div>
                        <div className="text-xs font-bold text-amber-400">
                          ${primaryOpt.breakeven.toFixed(2)}
                        </div>
                      </div>
                    </div>

                    {/* Payoff Chart */}
                    <div className="mt-4">
                      <PayoffChart
                        spotPrice={quote.current_price}
                        strike={primaryOpt.strike}
                        askPrice={primaryOpt.ask}
                        optionType={primaryOpt.type}
                        breakeven={primaryOpt.breakeven}
                        contracts={primaryOpt.suggested_contracts}
                        dte={primaryOpt.dte}
                        iv={primaryOpt.iv_pct}
                      />
                    </div>

                    {/* Interactive Paper Trade Order Box with Amount of Contracts */}
                    <div className="mt-4 rounded-xl border border-emerald-500/35 bg-gradient-to-r from-[#0a1e1a] via-[#0b1720] to-[#0d1526] p-3.5 shadow-xl">
                      <div className="flex items-center justify-between border-b border-emerald-500/20 pb-2 mb-2.5">
                        <div className="flex items-center space-x-1.5">
                          <Wallet className="h-4 w-4 text-emerald-400" />
                          <span className="text-xs font-black uppercase tracking-wider text-emerald-300">
                            Paper Trade This Suggestion
                          </span>
                        </div>
                        <span className="rounded-full bg-emerald-950/80 px-2 py-0.5 text-[10px] font-bold text-emerald-400 border border-emerald-800/40">
                          100% Risk-Free
                        </span>
                      </div>

                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                        {/* Amount of contracts control */}
                        <div className="flex items-center space-x-2">
                          <span className="text-[11px] font-semibold text-slate-300 whitespace-nowrap">Contracts:</span>
                          <div className="flex items-center rounded-lg border border-slate-700 bg-slate-900 px-1 py-0.5">
                            <button
                              type="button"
                              onClick={() => setPrimaryContracts((prev) => Math.max(1, prev - 1))}
                              className="h-6 w-6 rounded bg-slate-800 text-xs font-bold text-slate-200 hover:bg-slate-700 hover:text-white transition flex items-center justify-center"
                              title="Decrease contract quantity"
                            >
                              -
                            </button>
                            <input
                              type="number"
                              min="1"
                              max="500"
                              value={primaryContracts}
                              onChange={(e) => setPrimaryContracts(Math.max(1, parseInt(e.target.value) || 1))}
                              className="h-6 w-12 bg-transparent text-center font-mono text-xs font-black text-cyan-300 focus:outline-none"
                            />
                            <button
                              type="button"
                              onClick={() => setPrimaryContracts((prev) => Math.min(500, prev + 1))}
                              className="h-6 w-6 rounded bg-slate-800 text-xs font-bold text-slate-200 hover:bg-slate-700 hover:text-white transition flex items-center justify-center"
                              title="Increase contract quantity"
                            >
                              +
                            </button>
                          </div>

                          {/* Quick Quantity Chips */}
                          <div className="hidden sm:flex items-center space-x-1">
                            {[1, 2, 5, 10].map((qty) => (
                              <button
                                key={qty}
                                type="button"
                                onClick={() => setPrimaryContracts(qty)}
                                className={`rounded px-1.5 py-0.5 text-[10px] font-bold transition ${
                                  primaryContracts === qty
                                    ? "bg-emerald-500 text-slate-950 font-black shadow-sm"
                                    : "bg-slate-800/90 text-slate-400 hover:text-white"
                                }`}
                              >
                                {qty}x
                              </button>
                            ))}
                            {primaryOpt.suggested_contracts > 0 && (
                              <button
                                type="button"
                                onClick={() => setPrimaryContracts(primaryOpt.suggested_contracts)}
                                className={`rounded px-1.5 py-0.5 text-[10px] font-bold border transition ${
                                  primaryContracts === primaryOpt.suggested_contracts
                                    ? "border-cyan-400 bg-cyan-500/20 text-cyan-300 font-bold"
                                    : "border-slate-700 bg-slate-800/80 text-slate-400 hover:text-white"
                                }`}
                              >
                                Sized ({primaryOpt.suggested_contracts}x)
                              </button>
                            )}
                          </div>
                        </div>

                        {/* Live calculated cost + Execute Paper Buy button */}
                        <div className="flex items-center justify-between sm:justify-end space-x-3">
                          <div className="text-right">
                            <span className="text-[10px] text-slate-400 block leading-tight">Total Premium:</span>
                            <span className="font-mono text-xs font-black text-white">
                              ${(primaryContracts * 100 * primaryOpt.ask).toFixed(2)}
                            </span>
                          </div>

                          <button
                            type="button"
                            onClick={() => buyInPaperPortfolio(primaryOpt, ticker, primaryOpt.type, primaryContracts, "Primary Pick")}
                            className="flex items-center space-x-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 active:scale-95 text-slate-950 font-black px-3.5 py-2 text-xs transition shadow-md shadow-emerald-500/20"
                          >
                            <Wallet className="h-3.5 w-3.5 text-slate-950" />
                            <span>Paper Trade ({primaryContracts}x)</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex h-full items-center justify-center rounded-xl border border-slate-800 bg-[#0c1322] p-8 text-center text-slate-400">
                    <div>
                      <Minus className="mx-auto h-8 w-8 text-slate-500 mb-2" />
                      <p className="text-sm">Neutral signal or active blackout.</p>
                      <p className="text-xs text-slate-500">No directional contract recommended.</p>
                    </div>
                  </div>
                )}

                {/* Speculative High-Risk Alternative Card right in Terminal View */}
                {highRiskAlt && (
                  <div className="rounded-xl border border-rose-500/30 bg-gradient-to-br from-[#1a0d18] to-[#0d111d] p-4 shadow-xl">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="rounded bg-rose-500/20 px-2 py-0.5 text-[10px] font-black uppercase text-rose-300 border border-rose-500/40">
                          ⚡ ASYMMETRIC MOONSHOT
                        </span>
                        <span className="text-xs text-rose-200/80">
                          {highRiskAlt.expiration} ({highRiskAlt.dte}d)
                        </span>
                      </div>
                      <span className="rounded bg-rose-950/80 px-2 py-0.5 text-[10px] font-bold text-rose-300">
                        {highRiskAlt.upside_leverage.toFixed(1)}x Est. Leverage
                      </span>
                    </div>

                    <div className="mt-2 flex items-baseline justify-between">
                      <div>
                        <span className="text-base font-black text-white">
                          ${highRiskAlt.strike.toFixed(2)} {highRiskAlt.type}
                        </span>
                        <span className="ml-2 text-xs font-mono text-rose-400">
                          ({highRiskAlt.delta > 0 ? "+" : ""}{highRiskAlt.delta.toFixed(2)}Δ • {highRiskAlt.moneyness_pct > 0 ? "+" : ""}{highRiskAlt.moneyness_pct}% OTM)
                        </span>
                      </div>
                      <div className="text-sm font-black text-rose-400">
                        ${highRiskAlt.ask.toFixed(2)}
                      </div>
                    </div>

                    <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-800/80 pt-2">
                      <span>Sizing (Uncapped): <strong className="text-white">{highRiskAlt.suggested_contracts}x (${highRiskAlt.total_dollar_risk.toFixed(0)})</strong></span>
                      <span>Breakeven: <strong className="text-amber-300">${highRiskAlt.breakeven.toFixed(2)}</strong> ({highRiskAlt.req_move_pct > 0 ? "+" : ""}{highRiskAlt.req_move_pct}%)</span>
                    </div>

                    {/* Interactive Paper Trade Box for Moonshot */}
                    <div className="mt-3 pt-2.5 border-t border-rose-950/80 flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center space-x-2">
                        <span className="text-[10px] text-rose-300 font-semibold">Contracts:</span>
                        <div className="flex items-center rounded border border-rose-900 bg-[#0e0712] p-0.5">
                          <button
                            type="button"
                            onClick={() => setHighRiskContracts((c) => Math.max(1, c - 1))}
                            className="h-5 w-5 text-xs text-rose-300 hover:text-white flex items-center justify-center font-bold"
                          >
                            -
                          </button>
                          <input
                            type="number"
                            min="1"
                            max="500"
                            value={highRiskContracts}
                            onChange={(e) => setHighRiskContracts(Math.max(1, parseInt(e.target.value) || 1))}
                            className="w-10 bg-transparent text-center font-mono text-xs font-bold text-white focus:outline-none"
                          />
                          <button
                            type="button"
                            onClick={() => setHighRiskContracts((c) => Math.min(500, c + 1))}
                            className="h-5 w-5 text-xs text-rose-300 hover:text-white flex items-center justify-center font-bold"
                          >
                            +
                          </button>
                        </div>
                        <span className="font-mono text-[11px] text-slate-300">
                          = ${(highRiskContracts * 100 * highRiskAlt.ask).toFixed(2)}
                        </span>
                      </div>

                      <button
                        type="button"
                        onClick={() => buyInPaperPortfolio(highRiskAlt, ticker, highRiskAlt.type, highRiskContracts, "Moonshot Alt")}
                        className="flex items-center space-x-1.5 rounded-lg bg-rose-500 hover:bg-rose-400 active:scale-95 px-3 py-1.5 text-xs font-black text-slate-950 transition shadow-sm"
                      >
                        <Wallet className="h-3.5 w-3.5" />
                        <span>Paper Trade Moonshot ({highRiskContracts}x)</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* ========================================================= */}
            {/* 🎯 INSTITUTIONAL TRADE PLAN & EXECUTION PLAYBOOK COCKPIT   */}
            {/* ========================================================= */}
            {primaryOpt?.trade_plan && (
              <div className="mb-6 rounded-2xl border border-cyan-500/40 bg-gradient-to-br from-[#0a1426] via-[#091120] to-[#070b14] p-5 shadow-2xl">
                {/* Header */}
                <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="rounded bg-cyan-500/20 px-2.5 py-0.5 text-xs font-black uppercase tracking-wider text-cyan-300 border border-cyan-500/40">
                        🎯 INSTITUTIONAL TRADE PLAN
                      </span>
                      <span className="text-xs font-semibold text-slate-300">
                        {primaryOpt.contract} • Strike ${primaryOpt.strike.toFixed(2)} {primaryOpt.type} ({primaryOpt.delta > 0 ? "+" : ""}{primaryOpt.delta.toFixed(2)}Δ)
                      </span>
                    </div>
                    <h3 className="mt-1 text-base font-black text-white">
                      Rule-Based Scaling & Execution Playbook
                    </h3>
                    <p className="text-xs text-slate-400">
                      Multi-tier scaling, Black-Scholes probability modeling (PoP), and strict theta defense.
                    </p>
                  </div>

                  {/* Edge Analytics Badges */}
                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    <div className="rounded-lg bg-[#0e1c33] px-3 py-1.5 border border-cyan-600/40">
                      <span className="text-[10px] block text-cyan-300/80 uppercase font-semibold">Prob. of Profit</span>
                      <span className="text-sm font-extrabold text-cyan-300">
                        {primaryOpt.trade_plan.metrics?.probability_of_profit_pct?.toFixed(1) || "55.0"}%
                      </span>
                    </div>

                    <div className="rounded-lg bg-[#0e1c33] px-3 py-1.5 border border-emerald-600/40">
                      <span className="text-[10px] block text-emerald-300/80 uppercase font-semibold">Risk / Reward</span>
                      <span className="text-sm font-extrabold text-emerald-400">
                        {primaryOpt.trade_plan.metrics?.risk_reward_ratio?.toFixed(2) || "2.0"}:1
                      </span>
                    </div>

                    <div className="rounded-lg bg-[#0e1c33] px-3 py-1.5 border border-indigo-600/40">
                      <span className="text-[10px] block text-indigo-300/80 uppercase font-semibold">Expected Value</span>
                      <span className="text-sm font-extrabold text-indigo-300">
                        +${primaryOpt.trade_plan.metrics?.expected_value_per_contract?.toFixed(2) || "35.00"}/ct
                      </span>
                    </div>
                  </div>
                </div>

                {/* 3-Card Cockpit Grid */}
                <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-3">
                  {/* Card 1: Entry & Invalidation */}
                  <div className="rounded-xl border border-slate-800 bg-[#080e1a] p-4 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between text-xs font-bold text-slate-300">
                        <span>Entry Order & Chart Levels</span>
                        <span className="text-[10px] text-cyan-400 font-mono">MID-LIMIT</span>
                      </div>
                      <div className="mt-3 space-y-2 text-xs">
                        <div className="flex justify-between items-baseline">
                          <span className="text-slate-400">Recommended Limit:</span>
                          <span className="font-mono text-sm font-bold text-cyan-300">
                            ${primaryOpt.trade_plan.entry_limit_price.toFixed(2)}
                          </span>
                        </div>
                        <div className="flex justify-between items-baseline">
                          <span className="text-slate-400">Favorable Entry Zone:</span>
                          <span className="font-semibold text-slate-200">
                            {primaryOpt.trade_plan.entry_zone}
                          </span>
                        </div>
                        <div className="flex justify-between items-baseline">
                          <span className="text-slate-400">Underlying Spot:</span>
                          <span className="font-semibold text-white">
                            ${primaryOpt.trade_plan.underlying_spot.toFixed(2)}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 rounded-lg bg-red-950/40 border border-red-900/60 p-2.5 text-[11px]">
                      <div className="flex justify-between text-red-300 font-bold">
                        <span>Chart Invalidation:</span>
                        <span className="font-mono">${primaryOpt.trade_plan.underlying_invalidation_price.toFixed(2)}</span>
                      </div>
                      <div className="mt-1 text-[10px] text-red-200/70">
                        Cut position if stock candle closes beyond this level.
                      </div>
                    </div>
                  </div>

                  {/* Card 2: Scaling Profit Plan */}
                  <div className="rounded-xl border border-emerald-900/40 bg-[#08151a] p-4">
                    <div className="flex items-center justify-between text-xs font-bold text-emerald-300">
                      <span>Multi-Tier Profit Targets</span>
                      <span className="text-[10px] text-emerald-400 font-mono">SCALED EXITS</span>
                    </div>
                    <div className="mt-3 space-y-2.5 text-xs">
                      {/* TP1 */}
                      <div className="rounded bg-[#061e1b] p-2 border border-emerald-800/40">
                        <div className="flex justify-between items-baseline font-bold text-emerald-300">
                          <span>TP1 (+50% Trim):</span>
                          <span>${primaryOpt.trade_plan.tp1.option_price.toFixed(2)} (${primaryOpt.trade_plan.tp1.underlying_target.toFixed(2)} stock)</span>
                        </div>
                        <div className="mt-0.5 text-[10px] text-emerald-200/80">
                          {primaryOpt.trade_plan.tp1.action}
                        </div>
                      </div>

                      {/* TP2 */}
                      <div className="rounded bg-[#07241f] p-2 border border-emerald-700/50">
                        <div className="flex justify-between items-baseline font-bold text-emerald-200">
                          <span>TP2 (+100% Core):</span>
                          <span>${primaryOpt.trade_plan.tp2.option_price.toFixed(2)} (${primaryOpt.trade_plan.tp2.underlying_target.toFixed(2)} stock)</span>
                        </div>
                        <div className="mt-0.5 text-[10px] text-emerald-100/80">
                          {primaryOpt.trade_plan.tp2.action}
                        </div>
                      </div>

                      {/* TP3 */}
                      <div className="rounded bg-[#082a23] p-2 border border-emerald-600/60">
                        <div className="flex justify-between items-baseline font-bold text-emerald-100">
                          <span>TP3 (+150% Runner):</span>
                          <span>${primaryOpt.trade_plan.tp3.option_price.toFixed(2)} (${primaryOpt.trade_plan.tp3.underlying_target.toFixed(2)} stock)</span>
                        </div>
                        <div className="mt-0.5 text-[10px] text-emerald-100/70">
                          {primaryOpt.trade_plan.tp3.action}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Card 3: Capital Defense & Time-Stop */}
                  <div className="rounded-xl border border-slate-800 bg-[#080e1a] p-4 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between text-xs font-bold text-slate-300">
                        <span>Capital Defense & Theta Clock</span>
                        <span className="text-[10px] text-amber-400 font-mono">TIME-STOP</span>
                      </div>

                      <div className="mt-3 space-y-2 text-xs">
                        <div className="flex justify-between items-baseline">
                          <span className="text-slate-400">Option Stop-Loss:</span>
                          <span className="font-mono text-sm font-bold text-red-400">
                            ${primaryOpt.trade_plan.stop_loss.option_price.toFixed(2)} (-50%)
                          </span>
                        </div>
                        <div className="flex justify-between items-baseline">
                          <span className="text-slate-400">Max Planned Risk:</span>
                          <span className="font-semibold text-red-300">
                            ${primaryOpt.trade_plan.stop_loss.total_planned_risk.toFixed(0)} total
                          </span>
                        </div>
                        <div className="flex justify-between items-baseline">
                          <span className="text-slate-400">Daily Theta Decay:</span>
                          <span className="font-mono font-bold text-amber-400">
                            -${primaryOpt.trade_plan.time_stop.daily_theta_decay.toFixed(2)}/day
                          </span>
                        </div>
                        <div className="flex justify-between items-baseline">
                          <span className="text-slate-400">Max Holding Period:</span>
                          <span className="font-semibold text-amber-300">
                            {primaryOpt.trade_plan.time_stop.max_holding_period_days} trading days
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 rounded-lg bg-amber-950/40 border border-amber-900/60 p-2 text-[10px] text-amber-200/80">
                      <strong>21-DTE Theta Rule:</strong> {primaryOpt.trade_plan.time_stop.rule}
                    </div>
                  </div>
                </div>

                {/* Execution Checklist Playbook */}
                {primaryOpt.trade_plan.playbook_steps && primaryOpt.trade_plan.playbook_steps.length > 0 && (
                  <div className="mt-5 rounded-xl border border-slate-800 bg-[#060a14] p-4">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-cyan-300 mb-3 flex items-center">
                      <CheckCircle2 className="h-4 w-4 mr-1.5 text-cyan-400" />
                      Disciplined Execution Playbook Checklist
                    </h4>
                    <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3 text-xs">
                      {primaryOpt.trade_plan.playbook_steps.map((step: string, i: number) => {
                        const isChecked = !!checkedSteps[`step_${i}`];
                        return (
                          <div
                            key={i}
                            onClick={() => toggleStep(`step_${i}`)}
                            className={`flex items-start space-x-2.5 rounded-lg p-2.5 cursor-pointer border transition ${
                              isChecked
                                ? "border-emerald-500/50 bg-emerald-950/20 text-emerald-200"
                                : "border-slate-800/80 bg-[#0a101f] text-slate-300 hover:border-slate-700"
                            }`}
                          >
                            <input
                              type="checkbox"
                              checked={isChecked}
                              onChange={() => {}}
                              className="mt-0.5 h-3.5 w-3.5 rounded border-slate-700 bg-slate-900 text-cyan-500 accent-cyan-500 cursor-pointer"
                            />
                            <span className={`text-[11px] leading-relaxed ${isChecked ? "line-through text-slate-400" : ""}`}>
                              {step}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* ========================================================================= */}
                {/* 🛡️ PHASE 1: DYNAMIC RATCHET STOP LADDER (PHASES 1 - 4)                    */}
                {/* ========================================================================= */}
                {primaryOpt.trade_plan.ratchet_ladder && primaryOpt.trade_plan.ratchet_ladder.length > 0 && (
                  <div className="mt-5 rounded-xl border border-slate-800 bg-[#060a14] p-4">
                    <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                      <div className="flex items-center space-x-2">
                        <span className="rounded bg-cyan-500/20 px-2 py-0.5 text-[10px] font-black uppercase text-cyan-300 border border-cyan-500/40">
                          🛡️ Active Trade Management
                        </span>
                        <h4 className="text-xs font-bold uppercase tracking-wider text-white">
                          4-Phase Dynamic Stop Ratchet Ladder
                        </h4>
                      </div>
                      <span className="text-[11px] text-slate-400">
                        Systematic risk elimination: De-risk to Breakeven at TP1 • Lock profit at TP2
                      </span>
                    </div>

                    <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
                      {primaryOpt.trade_plan.ratchet_ladder.map((step: any, idx: number) => (
                        <div
                          key={idx}
                          className="rounded-xl border border-slate-800/80 bg-[#0a1122] p-3.5 flex flex-col justify-between hover:border-cyan-500/40 transition"
                        >
                          <div>
                            <div className="flex items-center justify-between">
                              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                                Phase {step.stage_num}
                              </span>
                              <span className={`rounded px-1.5 py-0.5 text-[9px] font-black border ${step.risk_badge}`}>
                                {step.risk_state}
                              </span>
                            </div>

                            <h5 className="mt-1.5 text-xs font-bold text-white leading-tight">
                              {step.phase.replace(`Phase ${step.stage_num}: `, "")}
                            </h5>

                            <div className="mt-2.5 space-y-1.5 text-[11px]">
                              <div className="flex justify-between items-baseline">
                                <span className="text-slate-400 text-[10px]">Trigger:</span>
                                <span className="font-semibold text-slate-200 text-right">
                                  {step.trigger_condition}
                                </span>
                              </div>
                              <div className="flex justify-between items-baseline">
                                <span className="text-slate-400 text-[10px]">Ratchet Stop:</span>
                                <span className="font-mono font-bold text-amber-300 text-right">
                                  {step.stop_rule_label}
                                </span>
                              </div>
                              <div className="flex justify-between items-baseline">
                                <span className="text-slate-400 text-[10px]">Net Outcome:</span>
                                <span className="font-semibold text-emerald-400 text-right">
                                  {step.locked_profit}
                                </span>
                              </div>
                            </div>
                          </div>

                          <div className="mt-3 rounded-lg bg-[#070d1a] border border-slate-800/80 p-2 text-[10px] text-slate-300 leading-relaxed">
                            {step.action}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* ========================================================================= */}
                {/* 🔄 DEFENSIVE ADJUSTMENT & ROLLING PLAYBOOK                                */}
                {/* ========================================================================= */}
                {primaryOpt.trade_plan.rolling_playbook && Object.keys(primaryOpt.trade_plan.rolling_playbook).length > 0 && (
                  <div className="mt-5 rounded-xl border border-slate-800 bg-[#060a14] p-4">
                    <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
                      <div className="flex items-center space-x-2">
                        <span className="rounded bg-amber-500/20 px-2 py-0.5 text-[10px] font-black uppercase text-amber-300 border border-amber-500/40">
                          🔄 Adjustment Protocols
                        </span>
                        <h4 className="text-xs font-bold uppercase tracking-wider text-white">
                          Defensive Adjustment & Rolling Playbook
                        </h4>
                      </div>
                      <div className="flex items-center space-x-1 rounded-lg border border-slate-800 bg-[#0a101f] p-1 text-xs">
                        <button
                          onClick={() => setActiveRollingTab("defensive_time_roll")}
                          className={`rounded px-2.5 py-1 text-[11px] font-bold transition ${
                            activeRollingTab === "defensive_time_roll"
                              ? "bg-amber-500 text-black shadow"
                              : "text-slate-400 hover:text-white"
                          }`}
                        >
                          🛡️ Roll Down & Out (21 DTE)
                        </button>
                        <button
                          onClick={() => setActiveRollingTab("synthetic_spread_conversion")}
                          className={`rounded px-2.5 py-1 text-[11px] font-bold transition ${
                            activeRollingTab === "synthetic_spread_conversion"
                              ? "bg-cyan-500 text-black shadow"
                              : "text-slate-400 hover:text-white"
                          }`}
                        >
                          ⚡ Synthetic Spread (Theta Freeze)
                        </button>
                        <button
                          onClick={() => setActiveRollingTab("profit_lock_roll")}
                          className={`rounded px-2.5 py-1 text-[11px] font-bold transition ${
                            activeRollingTab === "profit_lock_roll"
                              ? "bg-emerald-500 text-black shadow"
                              : "text-slate-400 hover:text-white"
                          }`}
                        >
                          🚀 Profit Roll (Extract Principal)
                        </button>
                      </div>
                    </div>

                    {/* Active Rolling Strategy Card */}
                    {primaryOpt.trade_plan.rolling_playbook[activeRollingTab] && (
                      <div className="rounded-xl border border-slate-800/90 bg-[#0a1122] p-4 text-xs">
                        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
                          <span className="font-bold text-white text-sm">
                            {primaryOpt.trade_plan.rolling_playbook[activeRollingTab].title}
                          </span>
                          <span className="text-[11px] font-semibold text-amber-300">
                            {primaryOpt.trade_plan.rolling_playbook[activeRollingTab].theta_relief}
                          </span>
                        </div>

                        <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-3">
                          <div className="rounded-lg bg-[#070e1c] p-3 border border-slate-800">
                            <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Trigger Signal</span>
                            <p className="text-[11px] text-slate-200 leading-relaxed">
                              {primaryOpt.trade_plan.rolling_playbook[activeRollingTab].trigger_signal}
                            </p>
                          </div>
                          <div className="rounded-lg bg-[#070e1c] p-3 border border-slate-800">
                            <span className="text-[10px] uppercase font-bold text-cyan-300 block mb-1">Execution Action</span>
                            <p className="text-[11px] text-slate-200 leading-relaxed">
                              {primaryOpt.trade_plan.rolling_playbook[activeRollingTab].action}
                            </p>
                          </div>
                          <div className="rounded-lg bg-[#070e1c] p-3 border border-slate-800">
                            <span className="text-[10px] uppercase font-bold text-amber-300 block mb-1">Institutional Rule</span>
                            <p className="text-[11px] text-slate-200 leading-relaxed">
                              {primaryOpt.trade_plan.rolling_playbook[activeRollingTab].rule}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* ========================================================================= */}
                {/* 📋 GTC BROKER BRACKET ORDER GENERATOR                                    */}
                {/* ========================================================================= */}
                {primaryOpt.trade_plan.broker_bracket_order && (
                  <div className="mt-5 rounded-xl border border-slate-800 bg-[#060a14] p-4">
                    <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
                      <div className="flex items-center space-x-2">
                        <span className="rounded bg-indigo-500/20 px-2 py-0.5 text-[10px] font-black uppercase text-indigo-300 border border-indigo-500/40">
                          📋 Order Syntax Generator
                        </span>
                        <h4 className="text-xs font-bold uppercase tracking-wider text-white">
                          Broker Bracket Order Syntax (OCO)
                        </h4>
                      </div>

                      <div className="flex items-center space-x-2">
                        {/* Format Switcher */}
                        <div className="flex items-center space-x-1 rounded-lg border border-slate-800 bg-[#0a101f] p-1 text-xs">
                          {(["standard", "tos", "ibkr", "webull"] as const).map((fmt) => (
                            <button
                              key={fmt}
                              onClick={() => setSelectedBrokerFormat(fmt)}
                              className={`rounded px-2.5 py-1 text-[11px] font-bold uppercase transition ${
                                selectedBrokerFormat === fmt
                                  ? "bg-indigo-600 text-white shadow"
                                  : "text-slate-400 hover:text-white"
                              }`}
                            >
                              {fmt === "tos" ? "Thinkorswim" : fmt === "ibkr" ? "Interactive Brokers" : fmt === "webull" ? "Webull" : "Standard OCO"}
                            </button>
                          ))}
                        </div>

                        {/* 1-Click Copy Button */}
                        <button
                          onClick={() => {
                            const b = primaryOpt.trade_plan.broker_bracket_order;
                            const text =
                              selectedBrokerFormat === "tos"
                                ? b.tos_syntax
                                : selectedBrokerFormat === "ibkr"
                                ? b.ibkr_syntax
                                : selectedBrokerFormat === "webull"
                                ? b.webull_syntax
                                : b.standard_text;
                            copyBracketOrder(text || "");
                          }}
                          className="flex items-center space-x-1 rounded-lg bg-indigo-600/30 px-3 py-1.5 text-xs font-bold text-indigo-200 border border-indigo-500/40 hover:bg-indigo-600/50 transition"
                        >
                          {copiedBracket ? (
                            <>
                              <Check className="h-3.5 w-3.5 text-emerald-400" />
                              <span className="text-emerald-400">Copied!</span>
                            </>
                          ) : (
                            <>
                              <Copy className="h-3.5 w-3.5" />
                              <span>Copy Bracket</span>
                            </>
                          )}
                        </button>
                      </div>
                    </div>

                    {/* Order Code Box */}
                    <div className="rounded-xl border border-slate-800 bg-[#070b14] p-3 font-mono text-xs text-indigo-200/90 whitespace-pre-wrap leading-relaxed">
                      {selectedBrokerFormat === "tos"
                        ? primaryOpt.trade_plan.broker_bracket_order.tos_syntax
                        : selectedBrokerFormat === "ibkr"
                        ? primaryOpt.trade_plan.broker_bracket_order.ibkr_syntax
                        : selectedBrokerFormat === "webull"
                        ? primaryOpt.trade_plan.broker_bracket_order.webull_syntax
                        : primaryOpt.trade_plan.broker_bracket_order.standard_text}
                    </div>
                    <div className="mt-2 flex items-center justify-between text-[10px] text-slate-500">
                      <span>• Pre-calculated limit order entry + automated OCO take-profit trims & hard stop market protection.</span>
                      <span>Paste directly into order ticket or execute via broker terminal.</span>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Defined-Risk Debit Spread Alternative */}
            {primarySpread && (
              <div className="mb-6 rounded-xl border border-emerald-500/30 bg-[#0c1626] p-5 shadow-lg">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-xs font-bold text-emerald-300">
                      DEFINED-RISK SPREAD
                    </span>
                    <h3 className="mt-1 text-base font-bold text-white">
                      {primarySpread.spread_type} ({primarySpread.expiration})
                    </h3>
                  </div>
                  <div className="flex space-x-4 text-xs font-medium text-slate-300">
                    <div>
                      Net Debit: <strong className="text-cyan-400">${primarySpread.net_debit.toFixed(2)}</strong>
                    </div>
                    <div>
                      Max Profit: <strong className="text-emerald-400">${primarySpread.max_profit.toFixed(0)}</strong>
                    </div>
                    <div>
                      R:R Ratio: <strong className="text-amber-400">{primarySpread.risk_reward_ratio.toFixed(2)}:1</strong>
                    </div>
                  </div>
                </div>

                <div className="mt-3 flex flex-wrap items-center gap-3 rounded-lg bg-[#070c16] p-3 text-xs border border-slate-800">
                  <div className="text-emerald-300 font-semibold">
                    [BUY LONG] {primarySpread.long_contract} (${primarySpread.long_strike}) @ ${primarySpread.long_ask.toFixed(2)}
                  </div>
                  <span className="text-slate-500">➔</span>
                  <div className="text-red-300 font-semibold">
                    [SELL SHORT] {primarySpread.short_contract} (${primarySpread.short_strike}) @ ${primarySpread.short_bid.toFixed(2)}
                  </div>
                </div>
              </div>
            )}

            {/* Filtered Liquid Candidates Table */}
            {options?.single_leg && options.single_leg.length > 0 && (
              <div className="mb-6 rounded-xl border border-slate-800 bg-[#0c1322] p-5">
                <div className="mb-3 flex items-center justify-between">
                  <h4 className="text-sm font-bold tracking-wide text-slate-200 uppercase">
                    Top Liquid Candidates (Delta 0.30–0.55 Range)
                  </h4>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setActiveTab("volatility")}
                      className="flex items-center space-x-1 rounded bg-cyan-950/60 px-2.5 py-1 text-xs font-semibold text-cyan-300 border border-cyan-800 hover:bg-cyan-900/60 transition"
                    >
                      <Activity className="h-3 w-3 mr-1 text-cyan-400" />
                      <span>IV Cockpit & Cones</span>
                    </button>
                    <button
                      onClick={() => setActiveTab("chain_matrix")}
                      className="flex items-center space-x-1 rounded bg-cyan-600/20 px-2.5 py-1 text-xs font-semibold text-cyan-300 border border-cyan-500/30 hover:bg-cyan-600/40 transition"
                    >
                      <Layers className="h-3 w-3 mr-1" />
                      <span>Open Strike Ladder &rarr;</span>
                    </button>
                  </div>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-slate-800 text-[11px] text-slate-400 uppercase">
                        <th className="pb-2">Contract</th>
                        <th className="pb-2">Strike</th>
                        <th className="pb-2">Delta</th>
                        <th className="pb-2">DTE</th>
                        <th className="pb-2">Bid / Ask</th>
                        <th className="pb-2">Spread %</th>
                        <th className="pb-2">Vol / OI</th>
                        <th className="pb-2">IV %</th>
                        <th className="pb-2">Breakeven</th>
                        <th className="pb-2">Position Sizing</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {options.single_leg.map((opt: any) => (
                        <tr key={opt.contract} className="hover:bg-slate-800/30">
                          <td className="py-2.5 font-mono text-cyan-300">{opt.contract}</td>
                          <td className="py-2.5 font-bold text-white">${opt.strike.toFixed(2)}</td>
                          <td className="py-2.5 font-mono text-indigo-300 font-semibold">
                            {opt.delta > 0 ? "+" : ""}
                            {opt.delta.toFixed(2)}Δ
                          </td>
                          <td className="py-2.5 text-slate-300">{opt.dte}d</td>
                          <td className="py-2.5 text-slate-200">
                            ${opt.bid.toFixed(2)} / ${opt.ask.toFixed(2)}
                          </td>
                          <td className="py-2.5 text-slate-300">{opt.spread_pct.toFixed(1)}%</td>
                          <td className="py-2.5 text-slate-400">
                            {opt.volume.toLocaleString()} / {opt.open_interest.toLocaleString()}
                          </td>
                          <td className="py-2.5 text-slate-300">{opt.iv_pct.toFixed(1)}%</td>
                          <td className="py-2.5 text-amber-300 font-semibold">${opt.breakeven.toFixed(2)}</td>
                          <td className="py-2.5 text-cyan-300 font-medium">
                            {opt.suggested_contracts}x (${opt.total_dollar_risk.toFixed(0)})
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ========================================================= */}
        {/* VIEW: ⛓️ INTERACTIVE OPTIONS CHAIN MATRIX                 */}
        {/* ========================================================= */}
        {activeTab === "chain_matrix" && (
          <OptionsChainMatrix
            ticker={ticker}
            equity={equity}
            riskPct={riskPct}
          />
        )}

        {/* ========================================================= */}
        {/* VIEW: ⚡ VOLATILITY COCKPIT & EXPECTED MOVE CONES          */}
        {/* ========================================================= */}
        {activeTab === "volatility" && (
          <VolatilityCockpit
            ticker={ticker}
            onOpenChain={(exp) => {
              setActiveTab("chain_matrix");
            }}
            onOpenZeroDte={() => {
              setZeroDteSelectedSymbol(ticker);
              setZeroDteTicker(ticker);
              setZeroDteSearchInput(ticker);
              fetchZeroDteSetups(ticker);
              setActiveTab("zero_dte");
            }}
          />
        )}

        {/* ========================================================= */}
        {/* VIEW: ⚖️ MULTI-LEG STRATEGY BUILDER                         */}
        {/* ========================================================= */}
        {activeTab === "builder" && (
          <MultiLegStrategyBuilder
            ticker={ticker}
            spotPrice={quote?.current_price || 100}
          />
        )}

        {/* ========================================================= */}
        {/* VIEW: ⭐ STARRED WATCHLIST                                 */}
        {/* ========================================================= */}
        {activeTab === "watchlist" && (
          <StarredWatchlistView
            starredTickers={starredTickers}
            onToggleStar={toggleStar}
            onSelectTicker={(sym) => {
              setSearchInput(sym);
              setTicker(sym);
              fetchAnalysis(sym);
              setActiveTab("terminal");
            }}
            onOpenOptionsChain={(sym) => {
              setTicker(sym);
              setSearchInput(sym);
              setActiveTab("chain_matrix");
            }}
            onOpenZeroDte={(sym) => {
              setZeroDteSelectedSymbol(sym);
              setZeroDteTicker(sym);
              setZeroDteSearchInput(sym);
              fetchZeroDteSetups(sym);
              setActiveTab("zero_dte");
            }}
          />
        )}

        {/* ========================================================= */}
        {/* VIEW 2: 🔥 HIGH-CONFIDENCE AI RECOMMENDATIONS             */}
        {/* ========================================================= */}
        {activeTab === "ai_picks" && (
          <div>
            <div className="mb-6 rounded-2xl border border-indigo-500/30 bg-gradient-to-r from-[#171238] via-[#111a33] to-[#0a1122] p-6 shadow-2xl">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-black text-indigo-300">
                    🔥 High-Confidence Options Recommendations
                  </h2>
                  <p className="mt-1 text-xs text-slate-300">
                    Curated high-conviction directional trade setups with <strong>Delta 0.30–0.55</strong> and
                    volume confirmation — spotlighting the <strong>AI Ecosystem & Liquid Commodities</strong>.
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                  <select
                    value={aiSector}
                    onChange={(e) => setAiSector(e.target.value)}
                    className="rounded-lg border border-slate-700 bg-[#0d1526] px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-400"
                  >
                    <option value="all_ai">All AI Leaders (40+ Tickers)</option>
                    <option value="commodities">🪙 All Commodities & Metals (GLD, SLV, USO, FCX...)</option>
                    <option value="precious_metals">✨ Precious Metals & Miners (GLD, SLV, GDX, NEM...)</option>
                    <option value="energy_commodities">🛢️ Energy, Oil & Gas (USO, UNG, XOM, CVX...)</option>
                    <option value="industrial_metals">🏗️ Industrial Metals & Copper (FCX, COPX, CLF...)</option>
                    <option value="neoclouds">☁️ AI NeoClouds & GPU Compute (NBIS, CORZ, APLD...)</option>
                    <option value="opticals">💡 AI Optical & Photonics (COHR, LITE, AAOI...)</option>
                    <option value="memory">💾 AI Memory & Storage HBM (MU, WDC, STX...)</option>
                    <option value="chips">⚡ AI Chips & Semiconductors (NVDA, AMD...)</option>
                    <option value="software">🛡️ AI Enterprise Software & Cyber (PLTR...)</option>
                    <option value="infra">🏗️ AI Data Center Infra (VRT, DELL...)</option>
                    <option value="mag7">👑 Mega-Cap Tech (Mag 7)</option>
                  </select>

                  <div className="flex items-center space-x-2 text-xs">
                    <span className="text-slate-400">Min Conf:</span>
                    <input
                      type="range"
                      min="25"
                      max="60"
                      step="5"
                      value={minConf}
                      onChange={(e) => setMinConf(Number(e.target.value))}
                      className="h-1.5 w-20 accent-indigo-400"
                    />
                    <span className="font-bold text-indigo-300">{minConf}%</span>
                  </div>

                  <button
                    onClick={fetchAiPicks}
                    disabled={aiLoading}
                    className="flex items-center space-x-1.5 rounded-lg bg-indigo-600 px-4 py-1.5 text-xs font-bold text-white shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 disabled:opacity-50"
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${aiLoading ? "animate-spin" : ""}`} />
                    <span>Run AI Screen</span>
                  </button>
                </div>
              </div>
            </div>

            {aiLoading ? (
              <div className="flex h-64 items-center justify-center rounded-xl border border-slate-800 bg-[#0c1322]">
                <div className="text-center text-slate-400 text-sm">
                  <RefreshCw className="mx-auto mb-2 h-6 w-6 animate-spin text-indigo-400" />
                  Screening AI Ecosystem (Prices, Greeks, Volume Confirmations)...
                </div>
              </div>
            ) : aiPicks.length === 0 ? (
              <div className="rounded-xl border border-slate-800 bg-[#0c1322] p-12 text-center text-slate-400 text-sm">
                No setups currently passed the {minConf}% confidence threshold in this category. Click &quot;Run AI Screen&quot; above.
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>Found {aiPicks.length} High-Confidence Setup(s)</span>
                </div>

                <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                  {aiPicks.map((pick, i) => (
                    <div
                      key={pick.symbol}
                      className="rounded-xl border border-slate-800 bg-[#0e1628] p-5 shadow-xl hover:border-indigo-500/40 transition"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <span className="text-lg font-black text-white">
                            #{i + 1} {pick.symbol}
                          </span>
                          <button
                            onClick={() => toggleStar(pick.symbol)}
                            title={isStarred(pick.symbol) ? "Remove from Watchlist" : "Add to Watchlist"}
                            className="rounded p-0.5 text-amber-400 hover:bg-slate-800 transition"
                          >
                            <Star className={`h-4 w-4 ${isStarred(pick.symbol) ? "fill-amber-400" : "text-slate-500 hover:text-amber-400"}`} />
                          </button>
                          <span
                            className={`rounded px-2 py-0.5 text-[11px] font-bold ${
                              pick.bias === "BULLISH"
                                ? "bg-emerald-500/20 text-emerald-400"
                                : "bg-red-500/20 text-red-400"
                            }`}
                          >
                            {pick.bias}
                          </span>
                          <span className="rounded bg-indigo-500/20 px-2 py-0.5 text-[11px] font-bold text-indigo-300">
                            {pick.confidence_pct}% CONF
                          </span>
                        </div>
                        <div className="text-right">
                          <div className="text-base font-bold text-white">
                            ${pick.price.toFixed(2)}
                          </div>
                          <div
                            className={`text-xs ${
                              pick.change_pct >= 0 ? "text-emerald-400" : "text-red-400"
                            }`}
                          >
                            {pick.change_pct >= 0 ? "+" : ""}
                            {pick.change_pct.toFixed(2)}%
                          </div>
                        </div>
                      </div>

                      <div className="mt-3 rounded-lg bg-[#080d18] p-3 text-xs border border-slate-800/80">
                        <div className="font-semibold text-cyan-300">
                          {pick.top_option.type} ${pick.top_option.strike.toFixed(2)} ({pick.top_option.delta > 0 ? "+" : ""}{pick.top_option.delta.toFixed(2)}Δ)
                        </div>
                        <div className="mt-1 flex flex-wrap justify-between text-[11px] text-slate-400">
                          <span>Expiry: {pick.top_option.expiration} ({pick.top_option.dte}d)</span>
                          <span>Ask: ${pick.top_option.ask.toFixed(2)}</span>
                          <span>Breakeven: ${pick.top_option.breakeven.toFixed(2)}</span>
                        </div>
                        <div className="mt-2 text-[11px] text-indigo-300 font-medium">
                          Sizing: {pick.top_option.contracts} contract(s) (${pick.top_option.total_risk.toFixed(0)} max risk) • Stop: ${pick.top_option.stop_loss.toFixed(2)}
                        </div>
                      </div>

                      <div className="mt-3 flex items-center justify-between">
                        <div className="text-[11px] text-slate-400">
                          Momentum: {pick.momentum_score > 0 ? "+" : ""}{pick.momentum_score.toFixed(2)} | Vol Ratio: {pick.volume_ratio.toFixed(2)}x
                        </div>
                        <button
                          onClick={() => {
                            setSearchInput(pick.symbol);
                            setActiveTab("terminal");
                            fetchAnalysis(pick.symbol);
                          }}
                          className="rounded bg-cyan-600/30 px-3 py-1 text-xs font-semibold text-cyan-200 hover:bg-cyan-600/50"
                        >
                          Deep Dive ➔
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
        {/* ========================================================= */}
        {/* VIEW 4: ⚡ 0DTE HIGH-VELOCITY FLASH LAB (NEW)              */}
        {/* ========================================================= */}
        {activeTab === "zero_dte" && (
          <div>
            {/* Top 0DTE Header & Controls */}
            <div className="mb-6 rounded-2xl border border-amber-500/40 bg-gradient-to-r from-[#2a1b0b] via-[#21151a] to-[#0c1221] p-6 shadow-2xl">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="rounded bg-amber-500/20 px-2.5 py-0.5 text-xs font-black uppercase tracking-wider text-amber-300 border border-amber-500/40">
                      ⚡ 0DTE FLASH SCALPER & OPTIONS CHAIN
                    </span>
                    <span className="text-xs font-bold text-rose-300">
                      Same-Day / Front-Session Intraday Velocity
                    </span>
                  </div>
                  <h2 className="mt-2 text-xl font-black text-amber-200">
                    0DTE High-Velocity Options Lab
                  </h2>
                  <p className="mt-1 text-xs text-amber-100/70 max-w-3xl leading-relaxed">
                    Same-day expiration contracts with extreme gamma convexity and accelerating intraday theta decay.
                    Features <strong>🎯 ATM Scalps (~0.50Δ)</strong>, <strong>🚀 OTM Moonshots (~0.20Δ)</strong>, and an interactive <strong>Search Bar</strong> to explore all available 0DTE calls and puts across any ticker.
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                  {/* Ticker Search Bar */}
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      if (zeroDteSearchInput.trim()) {
                        const sym = zeroDteSearchInput.trim().toUpperCase();
                        setZeroDteTicker(sym);
                        fetchZeroDteSetups(sym);
                      }
                    }}
                    className="flex items-center space-x-1.5"
                  >
                    <div className="relative">
                      <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-amber-400" />
                      <input
                        type="text"
                        value={zeroDteSearchInput}
                        onChange={(e) => setZeroDteSearchInput(e.target.value.toUpperCase())}
                        placeholder="Search Ticker (e.g. SPY, TSLA)..."
                        className="w-44 sm:w-56 rounded-lg border border-amber-800/80 bg-[#160f1b] py-1.5 pl-8 pr-2 text-xs font-semibold text-white placeholder-slate-500 focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={zeroDteLoading}
                      className="rounded-lg bg-amber-500/20 px-3 py-1.5 text-xs font-bold text-amber-300 border border-amber-500/40 hover:bg-amber-500/30 transition disabled:opacity-50"
                    >
                      Search
                    </button>
                  </form>

                  {/* Quick Tickers Pills */}
                  <div className="flex items-center space-x-1 rounded-lg border border-amber-800/80 bg-[#191216] p-1 text-xs">
                    {["SPY", "QQQ", "IWM", "NVDA", "TSLA", "AAPL", "AMD", "MSTR", "PLTR"].map((sym) => (
                      <button
                        key={sym}
                        onClick={() => {
                          setZeroDteTicker(sym);
                          setZeroDteSearchInput(sym);
                          fetchZeroDteSetups(sym);
                        }}
                        className={`rounded px-2.5 py-1 font-bold transition ${
                          zeroDteTicker === sym
                            ? "bg-amber-500 text-black shadow"
                            : "text-slate-300 hover:text-white"
                        }`}
                      >
                        {sym}
                      </button>
                    ))}
                    <button
                      onClick={() => {
                        setZeroDteTicker("ALL");
                        fetchZeroDteSetups("");
                      }}
                      className={`rounded px-2.5 py-1 font-bold transition ${
                        zeroDteTicker === "ALL"
                          ? "bg-amber-500 text-black shadow"
                          : "text-amber-400 hover:text-amber-200"
                      }`}
                    >
                      Scan All
                    </button>
                  </div>

                  {/* Risk Budget Selector */}
                  <div className="flex items-center space-x-2 text-xs">
                    <span className="text-amber-300">Risk Budget:</span>
                    <select
                      value={specRiskPct}
                      onChange={(e) => setSpecRiskPct(Number(e.target.value))}
                      className="rounded-lg border border-amber-800 bg-[#191216] px-2 py-1 text-xs text-white focus:outline-none"
                    >
                      <option value={0.5}>0.5% Equity</option>
                      <option value={1.0}>1.0% Equity (Default)</option>
                      <option value={2.0}>2.0% Equity</option>
                      <option value={3.0}>3.0% Equity (Aggressive)</option>
                      <option value={5.0}>5.0% Equity (Max)</option>
                    </select>
                  </div>

                  <button
                    onClick={() => fetchZeroDteSetups(zeroDteTicker === "ALL" ? "" : zeroDteTicker)}
                    disabled={zeroDteLoading}
                    className="flex items-center space-x-1.5 rounded-lg bg-amber-500 px-4 py-1.5 text-xs font-black text-black shadow-lg shadow-amber-500/30 hover:bg-amber-400 disabled:opacity-50"
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${zeroDteLoading ? "animate-spin" : ""}`} />
                    <span>Scan 0DTE</span>
                  </button>
                </div>
              </div>
            </div>

            {zeroDteLoading ? (
              <div className="flex h-64 items-center justify-center rounded-xl border border-slate-800 bg-[#0c1322]">
                <div className="text-center text-slate-400 text-sm">
                  <RefreshCw className="mx-auto mb-2 h-6 w-6 animate-spin text-amber-400" />
                  Extracting Same-Day 0DTE Option Chains, Gamma Convexity & Intraday Theta Decay...
                </div>
              </div>
            ) : zeroDteSetups.length === 0 ? (
              <div className="rounded-xl border border-slate-800 bg-[#0c1322] p-12 text-center text-slate-400 text-sm">
                No 0DTE setups loaded. Use the search bar above to look up any ticker (e.g. SPY, QQQ, NVDA, TSLA) or click &quot;Scan 0DTE&quot;.
              </div>
            ) : (
              <div className="space-y-6">
                <div className="flex items-center justify-between text-xs text-amber-300">
                  <span>Found {zeroDteSetups.length} 0DTE High-Velocity Setup(s)</span>
                  <span className="text-slate-400">Position Sizing: Uncapped Trade Allocation (${(equity * (specRiskPct / 100)).toFixed(0)} budget)</span>
                </div>

                {/* High-Velocity Scalp & Lotto Setups Cards */}
                <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                  {zeroDteSetups.map((setup, idx) => (
                    <div
                      key={setup.symbol}
                      className={`rounded-xl border p-5 shadow-2xl transition cursor-pointer ${
                        zeroDteSelectedSymbol === setup.symbol
                          ? "border-amber-400 bg-[#16111e] ring-1 ring-amber-500/50"
                          : "border-amber-900/60 bg-[#120e18] hover:border-amber-500/50"
                      }`}
                      onClick={() => setZeroDteSelectedSymbol(setup.symbol)}
                    >
                      {/* Top Header */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <span className="text-xl font-black text-white">
                            #{idx + 1} {setup.symbol}
                          </span>
                          <span
                            className={`rounded px-2 py-0.5 text-[11px] font-bold ${
                              setup.bias === "BULLISH"
                                ? "bg-emerald-500/20 text-emerald-400"
                                : "bg-rose-500/20 text-rose-400"
                            }`}
                          >
                            {setup.bias}
                          </span>
                          <span className="rounded bg-amber-500/20 px-2 py-0.5 text-[11px] font-black text-amber-300 border border-amber-500/40">
                            {setup.expiration} ({setup.dte} DTE)
                          </span>
                          {setup.all_options && setup.all_options.length > 0 && (
                            <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-semibold text-slate-300">
                              {setup.all_options.length} Contracts
                            </span>
                          )}
                        </div>
                        <div className="text-right">
                          <div className="text-base font-bold text-white">
                            ${setup.price.toFixed(2)}
                          </div>
                          <div
                            className={`text-xs ${
                              setup.change_pct >= 0 ? "text-emerald-400" : "text-rose-400"
                            }`}
                          >
                            {setup.change_pct >= 0 ? "+" : ""}
                            {setup.change_pct.toFixed(2)}%
                          </div>
                        </div>
                      </div>

                      {/* Velocity Gauge */}
                      {setup.breakeven_velocity_per_hour > 0 && (
                        <div className="mt-3 flex items-center justify-between rounded-lg bg-[#0b0811] px-3 py-2 text-xs border border-amber-950">
                          <span className="text-slate-400">
                            Intraday Velocity Requirement:
                          </span>
                          <span className="font-mono font-bold text-amber-300">
                            ~{setup.breakeven_velocity_per_hour}% / hr to beat theta
                          </span>
                        </div>
                      )}

                      {/* Setup Comparison Grid: Scalp vs Lotto */}
                      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
                        {/* 🎯 ATM Momentum Scalp */}
                        {setup.scalp_setup ? (
                          <div className="rounded-lg border border-cyan-900/60 bg-[#07131d] p-3">
                            <div className="flex items-center justify-between text-xs">
                              <span className="font-bold text-cyan-300">
                                🎯 ATM Momentum Scalp
                              </span>
                              <span className="font-mono text-[10px] text-cyan-400">
                                {setup.scalp_setup.delta > 0 ? "+" : ""}{setup.scalp_setup.delta.toFixed(2)}Δ
                              </span>
                            </div>
                            <div className="mt-2 flex items-baseline justify-between">
                              <span className="text-sm font-black text-white">
                                ${setup.scalp_setup.strike.toFixed(1)} {setup.scalp_setup.type}
                              </span>
                              <span className="text-sm font-black text-cyan-300">
                                ${setup.scalp_setup.ask.toFixed(2)}
                              </span>
                            </div>
                            <div className="mt-2 text-[10px] space-y-1 text-slate-300">
                              <div className="flex justify-between">
                                <span className="text-slate-400">Theta Burn Rate:</span>
                                <span className="font-bold text-rose-400">-${Math.abs(setup.scalp_setup.theta_per_hour * 100).toFixed(1)}/hr</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-slate-400">Gamma Convexity:</span>
                                <span className="font-mono text-cyan-300">Γ {setup.scalp_setup.gamma.toFixed(4)}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-slate-400">Breakeven:</span>
                                <span className="text-amber-300">${setup.scalp_setup.breakeven.toFixed(2)} ({setup.scalp_setup.req_move_pct > 0 ? "+" : ""}{setup.scalp_setup.req_move_pct}%)</span>
                              </div>
                              <div className="flex justify-between border-t border-slate-800 pt-1">
                                <span className="text-slate-400">Sizing (Uncapped):</span>
                                <span className="font-bold text-white">{setup.scalp_setup.contracts}x (${setup.scalp_setup.total_risk.toFixed(0)})</span>
                              </div>
                            </div>
                          </div>
                        ) : null}

                        {/* 🚀 OTM Gamma Moonshot */}
                        {setup.lotto_setup ? (
                          <div className="rounded-lg border border-rose-900/60 bg-[#1b0a16] p-3">
                            <div className="flex items-center justify-between text-xs">
                              <span className="font-bold text-rose-300">
                                🚀 OTM Gamma Moonshot
                              </span>
                              <span className="font-mono text-[10px] text-rose-400">
                                {setup.lotto_setup.delta > 0 ? "+" : ""}{setup.lotto_setup.delta.toFixed(2)}Δ
                              </span>
                            </div>
                            <div className="mt-2 flex items-baseline justify-between">
                              <span className="text-sm font-black text-white">
                                ${setup.lotto_setup.strike.toFixed(1)} {setup.scalp_setup?.type || "CALL"}
                              </span>
                              <span className="text-sm font-black text-rose-300">
                                ${setup.lotto_setup.ask.toFixed(2)}
                              </span>
                            </div>
                            <div className="mt-2 text-[10px] space-y-1 text-slate-300">
                              <div className="flex justify-between">
                                <span className="text-slate-400">Upside Multiplier:</span>
                                <span className="font-bold text-emerald-400">{setup.lotto_setup.upside_leverage.toFixed(1)}x Multiple</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-slate-400">Gamma Sensitivity:</span>
                                <span className="font-mono text-rose-300">Γ {setup.lotto_setup.gamma.toFixed(4)}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-slate-400">Breakeven:</span>
                                <span className="text-amber-300">${setup.lotto_setup.breakeven.toFixed(2)} ({setup.lotto_setup.req_move_pct > 0 ? "+" : ""}{setup.lotto_setup.req_move_pct}%)</span>
                              </div>
                              <div className="flex justify-between border-t border-slate-800 pt-1">
                                <span className="text-slate-400">Sizing (Uncapped):</span>
                                <span className="font-bold text-white">{setup.lotto_setup.contracts}x (${setup.lotto_setup.total_risk.toFixed(0)})</span>
                              </div>
                            </div>
                          </div>
                        ) : null}

                        {/* Direct options chain indicator if no automated scalp */}
                        {!setup.scalp_setup && !setup.lotto_setup && (
                          <div className="col-span-full rounded-lg border border-amber-900/40 bg-[#17101a] p-4 text-center">
                            <span className="text-amber-300 font-bold text-xs">⚡ Direct 0DTE Chain Mode Loaded</span>
                            <p className="text-slate-400 text-[11px] mt-1">
                              All {setup.all_options?.length || 0} available same-day contracts loaded. Use the search bar below to filter and analyze any strike.
                            </p>
                          </div>
                        )}
                      </div>

                      {/* Asymmetric 0DTE Lotto Debit Spread */}
                      {setup.lotto_spread && (
                        <div className="mt-3 rounded-lg bg-[#071318] p-3 text-xs border border-emerald-900/60">
                          <div className="flex items-center justify-between font-bold text-emerald-300">
                            <span>🛡️ {setup.lotto_spread.type}</span>
                            <span className="rounded bg-emerald-950 px-2 py-0.5 text-[10px] text-emerald-200 border border-emerald-800/40">
                              {setup.lotto_spread.risk_reward_ratio.toFixed(1)}:1 R:R
                            </span>
                          </div>
                          <div className="mt-1 text-[11px] text-slate-300">
                            Buy ${setup.lotto_spread.long_strike.toFixed(1)} / Sell ${setup.lotto_spread.short_strike.toFixed(1)} @ <strong>${setup.lotto_spread.net_debit.toFixed(2)} net debit</strong>
                          </div>
                          <div className="mt-1 flex justify-between text-[10px] text-slate-400">
                            <span>Max Profit: <strong className="text-emerald-400">${setup.lotto_spread.max_profit.toFixed(0)}</strong>/contract</span>
                            <span>Sized: {setup.lotto_spread.contracts}x (${setup.lotto_spread.total_risk.toFixed(0)} risk)</span>
                          </div>
                        </div>
                      )}

                      {/* Bottom actions */}
                      <div className="mt-3 flex items-center justify-between border-t border-slate-800/80 pt-2 text-[11px]">
                        <span className="text-amber-400/80 text-[10px]">
                          ⚡ 0DTE Front Expiration • Click card to inspect all available strikes below
                        </span>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setZeroDteSelectedSymbol(setup.symbol);
                            }}
                            className="rounded bg-amber-500/20 px-2.5 py-1 text-xs font-semibold text-amber-200 border border-amber-500/40 hover:bg-amber-500/40 transition"
                          >
                            Explore Options Ladder ↓
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSearchInput(setup.symbol);
                              setActiveTab("terminal");
                              fetchAnalysis(setup.symbol);
                            }}
                            className="rounded bg-cyan-600/30 px-2.5 py-1 text-xs font-semibold text-cyan-200 border border-cyan-500/40 hover:bg-cyan-600/50 transition"
                          >
                            Deep Dive ➔
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* ========================================================================= */}
                {/* 🔍 SEARCH ALL AVAILABLE 0DTE OPTIONS LADDER MATRIX                        */}
                {/* ========================================================================= */}
                <div className="rounded-2xl border border-amber-500/40 bg-[#0d121f] p-5 shadow-2xl">
                  {/* Explorer Header */}
                  <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
                    <div className="flex items-center space-x-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/20 border border-amber-500/40 text-amber-300">
                        <Search className="h-4 w-4" />
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <h3 className="text-base font-black text-white">
                            Search All Available 0DTE Options
                          </h3>
                          <span className="rounded bg-amber-500/20 px-2 py-0.5 text-xs font-bold text-amber-300 border border-amber-500/30">
                            {activeZeroDteSetup?.symbol || zeroDteTicker}
                          </span>
                          {activeZeroDteSetup?.expiration && (
                            <span className="text-xs text-slate-400">
                              • Exp: {activeZeroDteSetup.expiration} (0 DTE)
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-400 mt-0.5">
                          Real-time strike ladder with Black-Scholes Greeks, Bid/Ask spreads, IV%, Theta burn rates, and risk-sized contracts.
                        </p>
                      </div>
                    </div>

                    {/* Symbol switch pills if multiple tickers loaded */}
                    {zeroDteSetups.length > 1 && (
                      <div className="flex flex-wrap items-center gap-1 rounded-lg border border-slate-800 bg-[#080d18] p-1 text-xs">
                        <span className="px-2 text-slate-400 text-[11px] font-medium">Ticker:</span>
                        {zeroDteSetups.map((s) => (
                          <button
                            key={s.symbol}
                            onClick={() => setZeroDteSelectedSymbol(s.symbol)}
                            className={`rounded px-2.5 py-1 text-xs font-bold transition ${
                              zeroDteSelectedSymbol === s.symbol
                                ? "bg-amber-500 text-black shadow"
                                : "text-slate-400 hover:text-white"
                            }`}
                          >
                            {s.symbol} ({s.all_options?.length || 0})
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Search Bar & Filter Controls */}
                  <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
                    {/* Primary Search Input */}
                    <div className="relative flex-1 min-w-[240px] sm:min-w-[320px]">
                      <Search className="absolute left-3 top-2.5 h-4 w-4 text-amber-400" />
                      <input
                        type="text"
                        value={zeroDteChainQuery}
                        onChange={(e) => setZeroDteChainQuery(e.target.value)}
                        placeholder="Search strike (e.g. 590), CALL / PUT, delta (e.g. 0.25), or contract..."
                        className="w-full rounded-xl border border-slate-700/80 bg-[#121829] py-2 pl-9 pr-9 text-xs text-white placeholder-slate-500 focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
                      />
                      {zeroDteChainQuery && (
                        <button
                          onClick={() => setZeroDteChainQuery("")}
                          className="absolute right-3 top-2.5 text-xs text-slate-400 hover:text-white"
                        >
                          ✕
                        </button>
                      )}
                    </div>

                    {/* Filter Category Chips */}
                    <div className="flex flex-wrap items-center gap-1.5 text-xs">
                      <button
                        onClick={() => setZeroDteChainFilter("ALL")}
                        className={`rounded-lg px-2.5 py-1.5 font-bold transition ${
                          zeroDteChainFilter === "ALL"
                            ? "bg-amber-500 text-black shadow"
                            : "bg-slate-800/80 text-slate-300 hover:bg-slate-700"
                        }`}
                      >
                        All ({allZeroDteOptions.length})
                      </button>
                      <button
                        onClick={() => setZeroDteChainFilter("CALL")}
                        className={`rounded-lg px-2.5 py-1.5 font-bold transition ${
                          zeroDteChainFilter === "CALL"
                            ? "bg-emerald-500 text-black shadow"
                            : "bg-emerald-950/60 text-emerald-300 border border-emerald-800/50 hover:bg-emerald-900/60"
                        }`}
                      >
                        Calls Only
                      </button>
                      <button
                        onClick={() => setZeroDteChainFilter("PUT")}
                        className={`rounded-lg px-2.5 py-1.5 font-bold transition ${
                          zeroDteChainFilter === "PUT"
                            ? "bg-rose-500 text-black shadow"
                            : "bg-rose-950/60 text-rose-300 border border-rose-800/50 hover:bg-rose-900/60"
                        }`}
                      >
                        Puts Only
                      </button>
                      <button
                        onClick={() => setZeroDteChainFilter("ATM")}
                        className={`rounded-lg px-2.5 py-1.5 font-bold transition ${
                          zeroDteChainFilter === "ATM"
                            ? "bg-cyan-500 text-black shadow"
                            : "bg-cyan-950/60 text-cyan-300 border border-cyan-800/50 hover:bg-cyan-900/60"
                        }`}
                      >
                        Near ATM (±2.5%)
                      </button>
                      <button
                        onClick={() => setZeroDteChainFilter("MOONSHOT")}
                        className={`rounded-lg px-2.5 py-1.5 font-bold transition ${
                          zeroDteChainFilter === "MOONSHOT"
                            ? "bg-purple-500 text-black shadow"
                            : "bg-purple-950/60 text-purple-300 border border-purple-800/50 hover:bg-purple-900/60"
                        }`}
                      >
                        🚀 Moonshots (0.15–0.30Δ)
                      </button>
                      <button
                        onClick={() => setZeroDteChainFilter("LIQUID")}
                        className={`rounded-lg px-2.5 py-1.5 font-bold transition ${
                          zeroDteChainFilter === "LIQUID"
                            ? "bg-amber-500 text-black shadow"
                            : "bg-amber-950/60 text-amber-300 border border-amber-800/50 hover:bg-amber-900/60"
                        }`}
                      >
                        🌊 Liquid (&gt; 500 Vol)
                      </button>
                    </div>

                    {/* Sort Options */}
                    <div className="flex items-center space-x-1.5 text-xs">
                      <ArrowUpDown className="h-3.5 w-3.5 text-slate-400" />
                      <select
                        value={zeroDteSortBy}
                        onChange={(e) => setZeroDteSortBy(e.target.value)}
                        className="rounded-lg border border-slate-700 bg-[#121829] px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-amber-400"
                      >
                        <option value="strike_asc">Strike (Low to High)</option>
                        <option value="strike_desc">Strike (High to Low)</option>
                        <option value="volume">Highest Volume First</option>
                        <option value="delta">Highest Delta First</option>
                        <option value="theta_burn">Lowest Theta Burn / hr</option>
                        <option value="spread">Tightest Spread % First</option>
                      </select>
                    </div>
                  </div>

                  {/* Results Count & Spot Summary */}
                  <div className="mt-3 flex flex-wrap items-center justify-between text-[11px] text-slate-400 border-t border-slate-800/80 pt-2.5">
                    <div className="flex items-center space-x-3">
                      <span>
                        Showing <strong className="text-white">{filteredZeroDteOptions.length}</strong> of{" "}
                        <strong className="text-white">{allZeroDteOptions.length}</strong> available contracts
                      </span>
                      {activeZeroDteSetup && (
                        <span>
                          Spot: <strong className="text-amber-300">${activeZeroDteSetup.price.toFixed(2)}</strong>
                        </span>
                      )}
                    </div>
                    {copiedContract && (
                      <span className="flex items-center text-emerald-400 font-bold">
                        <Check className="mr-1 h-3.5 w-3.5" />
                        Copied {copiedContract} to clipboard!
                      </span>
                    )}
                  </div>

                  {/* Options Table */}
                  <div className="mt-3 max-h-[540px] overflow-x-auto overflow-y-auto rounded-xl border border-slate-800 bg-[#080d17]">
                    <table className="w-full text-left text-xs text-slate-300">
                      <thead className="sticky top-0 z-10 bg-[#0e1627] text-[11px] font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
                        <tr>
                          <th className="px-3 py-2.5">Contract</th>
                          <th className="px-3 py-2.5">Type</th>
                          <th className="px-3 py-2.5">Strike / Moneyness</th>
                          <th className="px-3 py-2.5">Bid / Ask (Mid)</th>
                          <th className="px-3 py-2.5">Spread</th>
                          <th className="px-3 py-2.5">Vol / OI</th>
                          <th className="px-3 py-2.5">IV %</th>
                          <th className="px-3 py-2.5">Delta (Δ)</th>
                          <th className="px-3 py-2.5">Gamma (Γ)</th>
                          <th className="px-3 py-2.5">Theta / hr</th>
                          <th className="px-3 py-2.5">Breakeven</th>
                          <th className="px-3 py-2.5">Sized Allocation</th>
                          <th className="px-3 py-2.5 text-right">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                        {filteredZeroDteOptions.length === 0 ? (
                          <tr>
                            <td colSpan={13} className="py-12 text-center text-slate-500 font-sans">
                              No contracts match your search filter &quot;{zeroDteChainQuery}&quot;. Try clearing query or switching filter chips.
                            </td>
                          </tr>
                        ) : (
                          filteredZeroDteOptions.map((opt: any) => {
                            const isCall = opt.type === "CALL";
                            const isCopied = copiedContract === opt.contract;
                            const isNearAtm = Math.abs(opt.moneyness_pct || 0) <= 1.0;
                            return (
                              <tr
                                key={opt.contract}
                                className={`transition hover:bg-slate-800/50 ${
                                  isNearAtm ? "bg-amber-950/10" : ""
                                }`}
                              >
                                {/* Contract Symbol */}
                                <td className="px-3 py-2 whitespace-nowrap">
                                  <div className="flex items-center space-x-1.5 font-sans">
                                    <button
                                      onClick={() => copyToClipboard(opt.contract)}
                                      title="Copy contract symbol"
                                      className="text-slate-400 hover:text-amber-400 transition"
                                    >
                                      {isCopied ? (
                                        <Check className="h-3 w-3 text-emerald-400" />
                                      ) : (
                                        <Copy className="h-3 w-3" />
                                      )}
                                    </button>
                                    <span className="font-mono text-[10px] text-slate-300">
                                      {opt.contract}
                                    </span>
                                  </div>
                                </td>

                                {/* Type */}
                                <td className="px-3 py-2 whitespace-nowrap">
                                  <span
                                    className={`rounded px-1.5 py-0.5 text-[10px] font-black font-sans ${
                                      isCall
                                        ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                                        : "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                                    }`}
                                  >
                                    {opt.type}
                                  </span>
                                </td>

                                {/* Strike */}
                                <td className="px-3 py-2 whitespace-nowrap">
                                  <div className="flex items-baseline space-x-1.5">
                                    <span className="font-bold text-white text-xs">
                                      ${opt.strike.toFixed(1)}
                                    </span>
                                    <span
                                      className={`text-[9px] font-sans ${
                                        opt.in_the_money
                                          ? "text-emerald-400 font-bold"
                                          : isNearAtm
                                          ? "text-amber-300 font-bold"
                                          : "text-slate-400"
                                      }`}
                                    >
                                      {opt.in_the_money
                                        ? "ITM"
                                        : `${opt.moneyness_pct > 0 ? "+" : ""}${opt.moneyness_pct}%`}
                                    </span>
                                  </div>
                                </td>

                                {/* Bid / Ask (Mid) */}
                                <td className="px-3 py-2 whitespace-nowrap">
                                  <span className="text-slate-300">
                                    ${opt.bid.toFixed(2)} / ${opt.ask.toFixed(2)}
                                  </span>{" "}
                                  <span className="text-slate-500 text-[10px]">
                                    (${opt.mid.toFixed(2)})
                                  </span>
                                </td>

                                {/* Spread */}
                                <td className="px-3 py-2 whitespace-nowrap">
                                  <span
                                    className={`rounded px-1 py-0.5 text-[9px] font-sans ${
                                      opt.spread_pct <= 5.0
                                        ? "bg-emerald-950/60 text-emerald-300 border border-emerald-800/40"
                                        : opt.spread_pct <= 15.0
                                        ? "bg-amber-950/60 text-amber-300 border border-amber-800/40"
                                        : "bg-rose-950/60 text-rose-300 border border-rose-800/40"
                                    }`}
                                  >
                                    ${opt.spread.toFixed(2)} ({opt.spread_pct}%)
                                  </span>
                                </td>

                                {/* Volume / OI */}
                                <td className="px-3 py-2 whitespace-nowrap font-sans">
                                  <span
                                    className={`font-mono ${
                                      opt.volume >= 1000
                                        ? "font-bold text-amber-300"
                                        : "text-slate-300"
                                    }`}
                                  >
                                    {opt.volume.toLocaleString()}
                                  </span>{" "}
                                  <span className="text-slate-500 text-[10px]">
                                    / {opt.open_interest.toLocaleString()}
                                  </span>
                                </td>

                                {/* IV % */}
                                <td className="px-3 py-2 whitespace-nowrap text-cyan-300">
                                  {opt.iv_pct}%
                                </td>

                                {/* Delta */}
                                <td className="px-3 py-2 whitespace-nowrap font-bold">
                                  <span
                                    className={
                                      isCall
                                        ? opt.delta >= 0.4
                                          ? "text-emerald-400"
                                          : "text-emerald-300/80"
                                        : opt.delta <= -0.4
                                        ? "text-rose-400"
                                        : "text-rose-300/80"
                                    }
                                  >
                                    {opt.delta > 0 ? "+" : ""}
                                    {opt.delta.toFixed(2)}Δ
                                  </span>
                                </td>

                                {/* Gamma */}
                                <td className="px-3 py-2 whitespace-nowrap text-purple-300 text-[10px]">
                                  Γ {opt.gamma.toFixed(4)}
                                </td>

                                {/* Theta / hr */}
                                <td className="px-3 py-2 whitespace-nowrap text-rose-400">
                                  -${Math.abs(opt.theta_per_hour * 100).toFixed(1)}/hr
                                </td>

                                {/* Breakeven */}
                                <td className="px-3 py-2 whitespace-nowrap font-sans text-[10px]">
                                  <span className="text-amber-300 font-mono">
                                    ${opt.breakeven.toFixed(2)}
                                  </span>{" "}
                                  <span className="text-slate-500">
                                    ({opt.req_move_pct > 0 ? "+" : ""}{opt.req_move_pct}%)
                                  </span>
                                </td>

                                {/* Position Sizing */}
                                <td className="px-3 py-2 whitespace-nowrap font-sans">
                                  <span className="font-bold text-white">
                                    {opt.suggested_contracts}x
                                  </span>{" "}
                                  <span className="text-slate-400 text-[10px]">
                                    (${opt.total_dollar_risk.toFixed(0)})
                                  </span>
                                </td>

                                {/* Action */}
                                <td className="px-3 py-2 whitespace-nowrap text-right font-sans">
                                  <button
                                    onClick={() => {
                                      setSearchInput(activeZeroDteSetup?.symbol || zeroDteTicker);
                                      setActiveTab("terminal");
                                      fetchAnalysis(activeZeroDteSetup?.symbol || zeroDteTicker);
                                    }}
                                    className="rounded bg-slate-800 px-2 py-1 text-[10px] font-semibold text-slate-300 hover:bg-cyan-600 hover:text-white transition"
                                    title="Open ticker analysis in terminal"
                                  >
                                    Terminal ➔
                                  </button>
                                </td>
                              </tr>
                            );
                          })
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}        {/* ========================================================= */}
        {/* VIEW 3: ⚡ HIGH-RISK & ASYMMETRIC SETUPS (NEW SECTION)      */}
        {/* ========================================================= */}
        {activeTab === "high_risk" && (
          <div>
            <div className="mb-6 rounded-2xl border border-rose-500/40 bg-gradient-to-r from-[#2a0b16] via-[#1f1022] to-[#0c1221] p-6 shadow-2xl">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="rounded bg-rose-500/20 px-2.5 py-0.5 text-xs font-black uppercase tracking-wider text-rose-300 border border-rose-500/40">
                      HIGH-RISK SPECULATIVE LAB
                    </span>
                    <span className="text-xs font-bold text-amber-300">
                      ⚡ Asymmetric Moonshots & Lotto Spreads
                    </span>
                  </div>
                  <h2 className="mt-2 text-xl font-black text-rose-200">
                    High-Beta & Asymmetric Options Setups
                  </h2>
                  <p className="mt-1 text-xs text-rose-100/70 max-w-3xl leading-relaxed">
                    Targeting explosive momentum in high-volatility names (Crypto-miners, Quantum, Squeeze plays).
                    Uses <strong>OTM Delta 0.15–0.28 contracts</strong> and <strong>3:1 to 6:1+ Risk/Reward lotto spreads</strong>.
                    Risk caps are removed — position sizing dynamically utilizes your full trade risk allocation.
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                  <select
                    value={highRiskCategory}
                    onChange={(e) => setHighRiskCategory(e.target.value)}
                    className="rounded-lg border border-rose-800 bg-[#160d1b] px-3 py-1.5 text-xs text-white focus:outline-none focus:border-rose-400"
                  >
                    <option value="all_speculative">All Speculative (20+ High-Beta Tickers)</option>
                    <option value="crypto_beta">🪙 Crypto-Beta & AI Miners (MSTR, COIN, MARA...)</option>
                    <option value="spec_tech">🚀 Speculative Tech & Quantum (ASTS, IONQ, SOUN...)</option>
                    <option value="high_vol">🔥 High-Vol Fintech & Squeeze Growth (CVNA, HOOD...)</option>
                    <option value="commodities">🌾 Commodities & Natural Resources (GLD, SLV, USO, FCX...)</option>
                  </select>

                  <div className="flex items-center space-x-2 text-xs">
                    <span className="text-rose-300">Risk Budget:</span>
                    <select
                      value={specRiskPct}
                      onChange={(e) => setSpecRiskPct(Number(e.target.value))}
                      className="rounded-lg border border-rose-800 bg-[#160d1b] px-2 py-1 text-xs text-white focus:outline-none"
                    >
                      <option value={0.5}>0.5% Equity</option>
                      <option value={1.0}>1.0% Equity (Default)</option>
                      <option value={2.0}>2.0% Equity</option>
                      <option value={3.0}>3.0% Equity (Aggressive)</option>
                      <option value={5.0}>5.0% Equity (Max)</option>
                    </select>
                  </div>

                  <button
                    onClick={fetchHighRiskSetups}
                    disabled={highRiskLoading}
                    className="flex items-center space-x-1.5 rounded-lg bg-rose-600 px-4 py-1.5 text-xs font-black text-white shadow-lg shadow-rose-600/30 hover:bg-rose-500 disabled:opacity-50"
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${highRiskLoading ? "animate-spin" : ""}`} />
                    <span>Screen High-Risk Setups</span>
                  </button>
                </div>
              </div>
            </div>

            {highRiskLoading ? (
              <div className="flex h-64 items-center justify-center rounded-xl border border-slate-800 bg-[#0c1322]">
                <div className="text-center text-slate-400 text-sm">
                  <RefreshCw className="mx-auto mb-2 h-6 w-6 animate-spin text-rose-400" />
                  Screening High-Beta Volatility & Asymmetric Delta 0.15–0.28 Chains...
                </div>
              </div>
            ) : highRiskSetups.length === 0 ? (
              <div className="rounded-xl border border-slate-800 bg-[#0c1322] p-12 text-center text-slate-400 text-sm">
                No high-risk setups loaded yet. Click &quot;Screen High-Risk Setups&quot; above to scan the speculative universe.
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between text-xs text-rose-300">
                  <span>Found {highRiskSetups.length} High-Risk Speculative Setup(s)</span>
                  <span className="text-slate-400">Uncapped Trade Risk Budget</span>
                </div>

                <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                  {highRiskSetups.map((setup, idx) => (
                    <div
                      key={setup.symbol}
                      className="rounded-xl border border-rose-900/50 bg-[#110e1c] p-5 shadow-xl hover:border-rose-500/50 transition"
                    >
                      {/* Header */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <span className="text-lg font-black text-white">
                            #{idx + 1} {setup.symbol}
                          </span>
                          <span
                            className={`rounded px-2 py-0.5 text-[11px] font-bold ${
                              setup.bias === "BULLISH"
                                ? "bg-emerald-500/20 text-emerald-400"
                                : "bg-rose-500/20 text-rose-400"
                            }`}
                          >
                            {setup.bias}
                          </span>
                          <span className="rounded bg-rose-500/20 px-2 py-0.5 text-[11px] font-black text-rose-300">
                            {setup.upside_leverage.toFixed(1)}x LEVERAGE
                          </span>
                        </div>
                        <div className="text-right">
                          <div className="text-base font-bold text-white">
                            ${setup.price.toFixed(2)}
                          </div>
                          <div
                            className={`text-xs ${
                              setup.change_pct >= 0 ? "text-emerald-400" : "text-rose-400"
                            }`}
                          >
                            {setup.change_pct >= 0 ? "+" : ""}
                            {setup.change_pct.toFixed(2)}%
                          </div>
                        </div>
                      </div>

                      {/* Setup 1: OTM Moonshot Option */}
                      <div className="mt-3 rounded-lg bg-[#0a0714] p-3 text-xs border border-rose-950">
                        <div className="flex items-center justify-between font-bold text-rose-300">
                          <span>{setup.setup_name}</span>
                          <span className="text-white font-mono">${setup.ask.toFixed(2)}/contract</span>
                        </div>
                        <div className="mt-1 flex flex-wrap justify-between text-[11px] text-slate-400">
                          <span>Expiry: {setup.expiration} ({setup.dte}d DTE)</span>
                          <span>Strike: ${setup.strike.toFixed(2)} ({setup.moneyness_pct > 0 ? "+" : ""}{setup.moneyness_pct}% OTM)</span>
                          <span>Breakeven: ${setup.breakeven.toFixed(2)}</span>
                        </div>
                        <div className="mt-2 text-[11px] text-rose-300 font-semibold">
                          Sizing Budget ({specRiskPct}%): {setup.suggested_contracts}x contract(s) ➔ Max Loss: ${setup.total_dollar_risk.toFixed(0)}
                        </div>
                      </div>

                      {/* Setup 2: Lotto Spread Alternative (if present) */}
                      {setup.lotto_spread && (
                        <div className="mt-3 rounded-lg bg-[#071318] p-3 text-xs border border-cyan-900/60">
                          <div className="flex items-center justify-between font-bold text-cyan-300">
                            <span>🎯 {setup.lotto_spread.type}</span>
                            <span className="rounded bg-cyan-950 px-2 py-0.5 text-[10px] text-cyan-200">
                              {setup.lotto_spread.risk_reward_ratio.toFixed(1)}:1 R:R
                            </span>
                          </div>
                          <div className="mt-1 text-[11px] text-slate-300">
                            Buy ${setup.lotto_spread.long_strike.toFixed(2)} / Sell ${setup.lotto_spread.short_strike.toFixed(2)} @ <strong>${setup.lotto_spread.net_debit.toFixed(2)} net debit</strong>
                          </div>
                          <div className="mt-1 flex justify-between text-[10px] text-slate-400">
                            <span>Max Profit: <strong className="text-emerald-400">${setup.lotto_spread.max_profit.toFixed(0)}</strong>/contract</span>
                            <span>Sized: {setup.lotto_spread.suggested_contracts}x (${setup.lotto_spread.total_dollar_risk.toFixed(0)} risk)</span>
                          </div>
                        </div>
                      )}

                      {/* Warnings and deep dive button */}
                      <div className="mt-3 flex items-center justify-between border-t border-slate-800/80 pt-2 text-[11px]">
                        <span className="text-slate-400">
                          Mom: {setup.momentum_score > 0 ? "+" : ""}{setup.momentum_score.toFixed(2)} | Vol: {setup.volume_ratio.toFixed(2)}x
                        </span>
                        <button
                          onClick={() => {
                            setSearchInput(setup.symbol);
                            setActiveTab("terminal");
                            fetchAnalysis(setup.symbol);
                          }}
                          className="rounded bg-rose-600/30 px-3 py-1 text-xs font-bold text-rose-200 hover:bg-rose-600/50"
                        >
                          Deep Dive ➔
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
              {/* ========================================================= */}
        {/* VIEW 9: PAPER TRADING & VIRTUAL PORTFOLIO SIMULATOR       */}
        {/* ========================================================= */}
        {activeTab === "paper_trading" && (
          <PaperTradingTracker
            defaultTicker={ticker}
            onSelectTicker={(sym) => {
              setSearchInput(sym);
              setTicker(sym);
              fetchAnalysis(sym);
              setActiveTab("terminal");
            }}
            onOpenChain={(sym) => {
              setSearchInput(sym);
              setTicker(sym);
              fetchAnalysis(sym);
              setActiveTab("chain_matrix");
            }}
          />
        )}

      </main>

      {/* ----------------- COMPLIANCE FOOTER ----------------- */}
      <footer className="mt-12 border-t border-slate-800/60 bg-[#070b12] py-6 text-center text-[11px] text-slate-500">
        <p className="max-w-3xl mx-auto px-4">
          ⚠️ DISCLAIMER: This tool is strictly for informational and educational purposes only. It does NOT constitute
          financial or investment advice. Options trading involves substantial risk of loss. Always trade responsibly.
        </p>
      </footer>
      {/* ---------------- KEYBOARD SHORTCUTS MODAL ---------------- */}
      {showShortcutsHelp && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
          onClick={() => setShowShortcutsHelp(false)}
        >
          <div
            className="w-full max-w-md rounded-2xl border border-slate-700 bg-[#0d1527] p-6 shadow-2xl text-xs"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <Command className="h-4 w-4 text-cyan-400" />
                <h3 className="font-bold text-white text-sm">Keyboard Shortcuts</h3>
              </div>
              <button
                onClick={() => setShowShortcutsHelp(false)}
                className="rounded-md px-2 py-0.5 text-slate-400 hover:text-white bg-slate-800"
              >
                ESC
              </button>
            </div>

            <div className="mt-4 space-y-2.5">
              <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                <span className="text-slate-300">Focus Search Bar</span>
                <kbd className="rounded border border-slate-700 bg-slate-800 px-2 py-0.5 font-mono text-[11px] text-cyan-300">/</kbd>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                <span className="text-slate-300">Terminal & Chart</span>
                <kbd className="rounded border border-slate-700 bg-slate-800 px-2 py-0.5 font-mono text-[11px] text-cyan-300">1</kbd>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                <span className="text-slate-300">Options Chain Matrix</span>
                <kbd className="rounded border border-slate-700 bg-slate-800 px-2 py-0.5 font-mono text-[11px] text-cyan-300">2</kbd>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                <span className="text-slate-300">Volatility Cockpit</span>
                <kbd className="rounded border border-slate-700 bg-slate-800 px-2 py-0.5 font-mono text-[11px] text-cyan-300">3</kbd>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                <span className="text-slate-300">Strategy Builder</span>
                <kbd className="rounded border border-slate-700 bg-slate-800 px-2 py-0.5 font-mono text-[11px] text-cyan-300">4</kbd>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                <span className="text-slate-300">Starred Watchlist</span>
                <kbd className="rounded border border-slate-700 bg-slate-800 px-2 py-0.5 font-mono text-[11px] text-cyan-300">5</kbd>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                <span className="text-slate-300">High-Confidence AI</span>
                <kbd className="rounded border border-slate-700 bg-slate-800 px-2 py-0.5 font-mono text-[11px] text-cyan-300">6</kbd>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                <span className="text-slate-300">High-Risk Speculative</span>
                <kbd className="rounded border border-slate-700 bg-slate-800 px-2 py-0.5 font-mono text-[11px] text-cyan-300">7</kbd>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                <span className="text-slate-300">0DTE Flash Lab</span>
                <kbd className="rounded border border-slate-700 bg-slate-800 px-2 py-0.5 font-mono text-[11px] text-cyan-300">8</kbd>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                <span className="text-slate-300">Paper Trading Portfolio</span>
                <kbd className="rounded border border-slate-700 bg-slate-800 px-2 py-0.5 font-mono text-[11px] text-cyan-300">9</kbd>
              </div>
              <div className="flex justify-between items-center py-1">
                <span className="text-slate-300">Open This Help Modal</span>
                <kbd className="rounded border border-slate-700 bg-slate-800 px-2 py-0.5 font-mono text-[11px] text-cyan-300">?</kbd>
              </div>
            </div>
          </div>
        </div>
      )}
      {/* Paper Trade Filled Floating Toast Notification */}
      {paperToast && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center space-x-3 rounded-2xl border border-emerald-500/40 bg-[#071714]/95 p-4 text-xs shadow-2xl text-slate-100 backdrop-blur-md">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-400 shrink-0">
            <CheckCircle2 className="h-5 w-5" />
          </div>
          <div>
            <div className="font-bold text-emerald-300">Paper Trade Executed!</div>
            <p className="text-slate-300 text-[11px] max-w-sm mt-0.5">{paperToast.message}</p>
          </div>
          <button
            onClick={() => {
              setActiveTab("paper_trading");
              setPaperToast(null);
            }}
            className="rounded-lg bg-emerald-500 px-3 py-1.5 text-xs font-black text-slate-950 hover:bg-emerald-400 transition ml-2 whitespace-nowrap"
          >
            Portfolio →
          </button>
          <button
            onClick={() => setPaperToast(null)}
            className="text-slate-400 hover:text-white text-base px-1 ml-1"
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
}
