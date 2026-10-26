"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import {
  Wallet,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Plus,
  Trash2,
  RefreshCw,
  RotateCcw,
  AlertCircle,
  CheckCircle2,
  Clock,
  Layers,
  ArrowRight,
  ShieldCheck,
  Zap,
  Activity,
  History,
  Target,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Search,
  Sliders,
  Check,
} from "lucide-react";

import {
  PaperTradePosition,
  isOptionExpired,
  calculateOptionSettlement,
  settleExpiredPositions,
  settleSinglePosition,
} from "../utils/paperSettlement";

export type { PaperTradePosition };

interface PaperTradingTrackerProps {
  onSelectTicker?: (ticker: string) => void;
  onOpenChain?: (ticker: string) => void;
  defaultTicker?: string;
}

const STORAGE_KEY_POSITIONS = "options_paper_positions";
const STORAGE_KEY_BALANCE = "options_paper_balance";
const DEFAULT_STARTING_CASH = 10000.0;

// Curated list of popular tickers by sector for the quick dropdown
const POPULAR_TICKER_GROUPS = [
  {
    category: "Mega-Cap Tech",
    tickers: ["NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA"],
  },
  {
    category: "AI Ecosystem & Chips",
    tickers: ["AMD", "AVGO", "TSM", "ARM", "PLTR", "MRVL", "MU", "CRWD", "SMCI"],
  },
  {
    category: "Index & Market ETFs",
    tickers: ["SPY", "QQQ", "IWM", "DIA", "SMH", "XLF", "XLE"],
  },
  {
    category: "Commodities & Energy",
    tickers: ["GLD", "SLV", "GDX", "USO", "UNG", "FCX", "CCJ"],
  },
  {
    category: "High-Beta & Crypto Miners",
    tickers: ["MSTR", "COIN", "MARA", "ASTS", "IONQ", "CVNA", "HOOD", "SOFI"],
  },
];

export default function PaperTradingTracker({
  onSelectTicker,
  onOpenChain,
  defaultTicker = "NVDA",
}: PaperTradingTrackerProps) {
  const [cashBalance, setCashBalance] = useState<number>(DEFAULT_STARTING_CASH);
  const [positions, setPositions] = useState<PaperTradePosition[]>([]);
  const [loadingQuotes, setLoadingQuotes] = useState<boolean>(false);
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);
  const [activeSubTab, setActiveSubTab] = useState<"open" | "closed" | "new_trade">("open");

  // Order Ticket Form State
  const [selectedDropdownTicker, setSelectedDropdownTicker] = useState<string>(defaultTicker.toUpperCase());
  const [customTickerInput, setCustomTickerInput] = useState<string>("");
  const [isCustomTicker, setIsCustomTicker] = useState<boolean>(false);
  const [formTicker, setFormTicker] = useState<string>(defaultTicker.toUpperCase());
  const [formType, setFormType] = useState<"CALL" | "PUT">("CALL");
  const [formStrike, setFormStrike] = useState<number>(230);
  const [formExpiration, setFormExpiration] = useState<string>("2026-10-16");
  const [formEntryPrice, setFormEntryPrice] = useState<number>(4.5);
  const [formContracts, setFormContracts] = useState<number>(1);
  const [formTarget, setFormTarget] = useState<number>(9.0);
  const [formStop, setFormStop] = useState<number>(2.25);
  const [formNotes, setFormNotes] = useState<string>("Simulated directional options trade");

  // Live Options Chain & Live Option Quote State
  const [chainLoading, setChainLoading] = useState<boolean>(false);
  const [chainData, setChainData] = useState<any>(null);
  const [availableExpirations, setAvailableExpirations] = useState<{ expiration: string; dte: number }[]>([]);
  const [availableStrikes, setAvailableStrikes] = useState<any[]>([]);
  const [selectedOptionQuote, setSelectedOptionQuote] = useState<{
    ask: number;
    bid: number;
    mid: number;
    last: number;
    delta: number;
    iv_pct: number;
    spread: number;
    spread_pct: number;
    contract: string;
    inTheMoney: boolean;
    volume: number;
    open_interest: number;
  } | null>(null);
  const [quoteFeedback, setQuoteFeedback] = useState<string | null>(null);
  const [expiryNotice, setExpiryNotice] = useState<string | null>(null);

  // Load from localStorage on mount and auto-settle any expired positions
  useEffect(() => {
    if (typeof window !== "undefined") {
      try {
        let initialCash = DEFAULT_STARTING_CASH;
        const savedBalance = localStorage.getItem(STORAGE_KEY_BALANCE);
        if (savedBalance) {
          initialCash = parseFloat(savedBalance);
          setCashBalance(initialCash);
        }

        const savedPositions = localStorage.getItem(STORAGE_KEY_POSITIONS);
        if (savedPositions) {
          const parsed = JSON.parse(savedPositions);
          if (Array.isArray(parsed)) {
            const autoSettle = settleExpiredPositions(parsed, initialCash);
            if (autoSettle.settledCount > 0) {
              setPositions(autoSettle.updatedPositions);
              setCashBalance(autoSettle.newCashBalance);
              localStorage.setItem(STORAGE_KEY_POSITIONS, JSON.stringify(autoSettle.updatedPositions));
              localStorage.setItem(STORAGE_KEY_BALANCE, autoSettle.newCashBalance.toString());
              setExpiryNotice(autoSettle.summaryMessage);
            } else {
              setPositions(parsed);
            }
          }
        }
      } catch (err) {
        console.error("Failed to load paper trading storage:", err);
      }
    }
  }, []);

  // Update default ticker if prop changes
  useEffect(() => {
    if (defaultTicker && !isCustomTicker) {
      const sym = defaultTicker.trim().toUpperCase();
      setSelectedDropdownTicker(sym);
      setFormTicker(sym);
    }
  }, [defaultTicker, isCustomTicker]);

  // Save to localStorage whenever state changes
  const savePositions = (updated: PaperTradePosition[]) => {
    setPositions(updated);
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem(STORAGE_KEY_POSITIONS, JSON.stringify(updated));
      } catch (err) {
        console.error("Failed to save paper positions:", err);
      }
    }
  };

  const saveBalance = (newBalance: number) => {
    setCashBalance(newBalance);
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem(STORAGE_KEY_BALANCE, newBalance.toString());
      } catch (err) {
        console.error("Failed to save paper balance:", err);
      }
    }
  };

  // Sync live market quotes for open positions and auto-settle expired contracts
  const refreshLiveQuotes = useCallback(async () => {
    const openPos = positions.filter((p) => p.status === "OPEN");
    if (openPos.length === 0) return;

    setLoadingQuotes(true);
    try {
      const itemsPayload = openPos.map((p) => ({
        contract: p.contract,
        symbol: p.ticker,
        ticker: p.ticker,
        asset_type: "OPTION",
        expiration: p.expiration,
        strike: p.strike,
        option_type: p.optionType,
      }));

      const res = await fetch("/api/paper-quotes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items: itemsPayload }),
      });

      if (res.ok) {
        const json = await res.json();
        const quotes = json.quotes || {};

        const updated = positions.map((p) => {
          if (p.status === "OPEN") {
            const q = quotes[p.contract] || quotes[p.ticker];
            if (q && q.valid) {
              return {
                ...p,
                currentPrice: q.current_price,
              };
            }
          }
          return p;
        });

        const autoSettle = settleExpiredPositions(updated, cashBalance, quotes);
        if (autoSettle.settledCount > 0) {
          savePositions(autoSettle.updatedPositions);
          saveBalance(autoSettle.newCashBalance);
          setExpiryNotice(autoSettle.summaryMessage);
        } else {
          savePositions(updated);
        }
        setLastRefreshed(new Date());
      }
    } catch (err) {
      console.error("Error refreshing paper quotes:", err);
    } finally {
      setLoadingQuotes(false);
    }
  }, [positions, cashBalance]);

  useEffect(() => {
    if (positions.some((p) => p.status === "OPEN")) {
      refreshLiveQuotes();
    }
  }, []);

  // Fetch options chain & live quotes for the current ticker and expiration
  const fetchChainForTicker = useCallback(async (targetTicker: string, targetExp?: string) => {
    const sym = targetTicker.trim().toUpperCase();
    if (!sym) return;

    setChainLoading(true);
    setQuoteFeedback(null);
    try {
      const url = `/api/options-chain?ticker=${encodeURIComponent(sym)}${
        targetExp ? `&expiration=${encodeURIComponent(targetExp)}` : ""
      }`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setChainData(data);

        // Update available expirations
        if (data.available_expirations && Array.isArray(data.available_expirations) && data.available_expirations.length > 0) {
          setAvailableExpirations(data.available_expirations);
          if (!targetExp && data.selected_expiration) {
            setFormExpiration(data.selected_expiration);
          }
        }

        // Update available strikes
        if (data.strikes && Array.isArray(data.strikes) && data.strikes.length > 0) {
          setAvailableStrikes(data.strikes);

          // Select closest strike to spot price if not already set or not found
          const spot = data.current_price || 100;
          let bestStrike = data.strikes[0].strike;
          let minDiff = 999999;
          data.strikes.forEach((s: any) => {
            const diff = Math.abs(s.strike - spot);
            if (diff < minDiff) {
              minDiff = diff;
              bestStrike = s.strike;
            }
          });
          setFormStrike(bestStrike);
        }
      }
    } catch (err) {
      console.error("Failed to load options chain matrix for paper ticket:", err);
    } finally {
      setChainLoading(false);
    }
  }, []);

  // Fetch chain when switching to new_trade tab or changing ticker
  useEffect(() => {
    if (activeSubTab === "new_trade") {
      fetchChainForTicker(formTicker);
    }
  }, [activeSubTab, formTicker, fetchChainForTicker]);

  // Sync selectedOptionQuote and auto-fill formEntryPrice whenever strike, type, or strikes list change
  useEffect(() => {
    if (!availableStrikes || availableStrikes.length === 0) {
      setSelectedOptionQuote(null);
      return;
    }

    const strikeObj = availableStrikes.find((s: any) => Math.abs(s.strike - formStrike) < 0.001);
    if (strikeObj) {
      const leg = formType === "CALL" ? strikeObj.call : strikeObj.put;
      if (leg) {
        const ask = leg.ask || 0;
        const bid = leg.bid || 0;
        const mid = leg.mid || (ask > 0 && bid > 0 ? (ask + bid) / 2 : ask || leg.last || 0);
        const last = leg.last || 0;

        const quoteInfo = {
          ask,
          bid,
          mid,
          last,
          delta: leg.delta || 0,
          iv_pct: leg.iv_pct || 0,
          spread: leg.spread || 0,
          spread_pct: leg.spread_pct || 0,
          contract: leg.contract || "",
          inTheMoney: !!leg.inTheMoney,
          volume: leg.volume || 0,
          open_interest: leg.open_interest || 0,
        };
        setSelectedOptionQuote(quoteInfo);

        // Auto-fill price with current live Ask (or Mid if ask is 0)
        const fillPrice = ask > 0 ? ask : mid > 0 ? mid : last;
        if (fillPrice > 0) {
          const formatted = Number(fillPrice.toFixed(2));
          setFormEntryPrice(formatted);
          setFormTarget(Number((formatted * 1.5).toFixed(2))); // +50% target default
          setFormStop(Number((formatted * 0.5).toFixed(2)));   // -50% stop default
          setQuoteFeedback(`Live option price ($${formatted.toFixed(2)}) auto-synced`);
        }
      } else {
        setSelectedOptionQuote(null);
      }
    } else {
      setSelectedOptionQuote(null);
    }
  }, [availableStrikes, formStrike, formType]);

  // Handle ticker selection from dropdown
  const handleDropdownTickerChange = (value: string) => {
    if (value === "CUSTOM") {
      setIsCustomTicker(true);
      setSelectedDropdownTicker("CUSTOM");
    } else {
      setIsCustomTicker(false);
      setSelectedDropdownTicker(value);
      setFormTicker(value);
      fetchChainForTicker(value);
    }
  };

  // Handle custom ticker input commit
  const handleCustomTickerSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (customTickerInput.trim()) {
      const sym = customTickerInput.trim().toUpperCase();
      setFormTicker(sym);
      fetchChainForTicker(sym);
    }
  };

  // Handle expiration dropdown change
  const handleExpirationChange = (newExp: string) => {
    setFormExpiration(newExp);
    fetchChainForTicker(formTicker, newExp);
  };

  // Buy new option position
  const handleOpenPosition = (e: React.FormEvent) => {
    e.preventDefault();
    const cost = formEntryPrice * 100 * formContracts;
    if (cost > cashBalance) {
      alert(
        `Insufficient virtual funds. Cost is $${cost.toFixed(2)}, but available balance is $${cashBalance.toFixed(2)}.`
      );
      return;
    }

    const expClean = formExpiration.replace(/-/g, "").slice(2); // e.g. 261016
    const strikeFormatted = String(Math.round(formStrike * 1000)).padStart(8, "0");
    const generatedContract =
      selectedOptionQuote?.contract ||
      `${formTicker.trim().toUpperCase()}${expClean}${formType[0]}${strikeFormatted}`;

    const newPosition: PaperTradePosition = {
      id: `pos-${Date.now()}`,
      ticker: formTicker.trim().toUpperCase(),
      contract: generatedContract,
      optionType: formType,
      strike: formStrike,
      expiration: formExpiration,
      dte: chainData?.dte || 30,
      entryPrice: formEntryPrice,
      contracts: formContracts,
      totalCost: cost,
      enteredAt: new Date().toISOString(),
      currentPrice: formEntryPrice,
      status: "OPEN",
      targetProfitPrice: formTarget > 0 ? formTarget : undefined,
      stopLossPrice: formStop > 0 ? formStop : undefined,
      notes: formNotes,
    };

    const nextPositions = [newPosition, ...positions];
    savePositions(nextPositions);
    saveBalance(cashBalance - cost);
    setActiveSubTab("open");
  };

  // Close / Sell position to take profit or cut loss
  const handleClosePosition = (posId: string, exitPriceOverride?: number) => {
    const pos = positions.find((p) => p.id === posId);
    if (!pos || pos.status !== "OPEN") return;

    const exitPx = exitPriceOverride !== undefined ? exitPriceOverride : pos.currentPrice;
    const exitProceeds = exitPx * 100 * pos.contracts;
    const realizedPnl = exitProceeds - pos.totalCost;

    const updated = positions.map((p) => {
      if (p.id === posId) {
        return {
          ...p,
          status: "CLOSED" as const,
          closedAt: new Date().toISOString(),
          exitPrice: exitPx,
          realizedPnl,
        };
      }
      return p;
    });

    savePositions(updated);
    saveBalance(cashBalance + exitProceeds);
  };

  // Settle all expired positions explicitly
  const handleSettleExpiredPositions = () => {
    const settlement = settleExpiredPositions(positions, cashBalance);
    if (settlement.settledCount > 0) {
      savePositions(settlement.updatedPositions);
      saveBalance(settlement.newCashBalance);
      setExpiryNotice(settlement.summaryMessage);
    } else {
      setExpiryNotice("No open positions currently require expiration settlement.");
      setTimeout(() => setExpiryNotice(null), 3500);
    }
  };

  // Immediate expiration or simulation of a specific position
  const handleExpirePositionNow = (posId: string) => {
    const pos = positions.find((p) => p.id === posId);
    if (!pos) return;
    const spot = chainData?.current_price || pos.currentPrice || pos.strike;
    const settlement = settleSinglePosition(posId, positions, cashBalance, spot);
    if (settlement.settledCount > 0) {
      savePositions(settlement.updatedPositions);
      saveBalance(settlement.newCashBalance);
      setExpiryNotice(settlement.summaryMessage);
    }
  };

  // Reset entire paper account to default
  const handleResetAccount = () => {
    if (confirm("Reset paper trading account? This will clear all positions and reset cash to $10,000.")) {
      savePositions([]);
      saveBalance(DEFAULT_STARTING_CASH);
    }
  };

  // Summary Metrics
  const openPositions = useMemo(() => positions.filter((p) => p.status === "OPEN"), [positions]);
  const closedPositions = useMemo(() => positions.filter((p) => p.status === "CLOSED"), [positions]);

  const portfolioStats = useMemo(() => {
    let openPositionsValue = 0;
    let totalInvestedCost = 0;
    let unrealizedDollarPnl = 0;

    for (const p of openPositions) {
      const currentVal = p.currentPrice * 100 * p.contracts;
      openPositionsValue += currentVal;
      totalInvestedCost += p.totalCost;
      unrealizedDollarPnl += currentVal - p.totalCost;
    }

    const unrealizedRoiPct = totalInvestedCost > 0 ? (unrealizedDollarPnl / totalInvestedCost) * 100 : 0;
    const totalRealizedPnl = closedPositions.reduce((acc, p) => acc + (p.realizedPnl || 0), 0);
    const totalPortfolioValue = cashBalance + openPositionsValue;
    const allTimePnl = totalPortfolioValue - DEFAULT_STARTING_CASH;
    const allTimeRoiPct = (allTimePnl / DEFAULT_STARTING_CASH) * 100;

    const winTrades = closedPositions.filter((p) => (p.realizedPnl || 0) > 0).length;
    const totalClosed = closedPositions.length;
    const winRate = totalClosed > 0 ? (winTrades / totalClosed) * 100 : 0;

    return {
      openPositionsValue,
      totalInvestedCost,
      unrealizedDollarPnl,
      unrealizedRoiPct,
      totalRealizedPnl,
      totalPortfolioValue,
      allTimePnl,
      allTimeRoiPct,
      winRate,
      totalClosed,
    };
  }, [openPositions, closedPositions, cashBalance]);

  // Derived current option live display values
  const liveAsk = selectedOptionQuote?.ask || 0;
  const liveBid = selectedOptionQuote?.bid || 0;
  const liveMid = selectedOptionQuote?.mid || 0;
  const liveDelta = selectedOptionQuote?.delta || 0;
  const liveIv = selectedOptionQuote?.iv_pct || 0;

  // Breakeven price calculation
  const breakevenPrice =
    formType === "CALL" ? formStrike + formEntryPrice : Math.max(0, formStrike - formEntryPrice);
  const stockSpotPrice = chainData?.current_price || formStrike;
  const reqMovePct =
    stockSpotPrice > 0
      ? formType === "CALL"
        ? ((breakevenPrice - stockSpotPrice) / stockSpotPrice) * 100
        : ((stockSpotPrice - breakevenPrice) / stockSpotPrice) * 100
      : 0;

  const expiredOpenPositions = useMemo(
    () => openPositions.filter((p) => isOptionExpired(p.expiration)),
    [openPositions]
  );

  return (
    <div className="space-y-6">
      {/* Expiration Settlement Notice Banner */}
      {expiryNotice && (
        <div className="flex items-center justify-between rounded-xl border border-cyan-500/40 bg-gradient-to-r from-cyan-950/40 to-slate-900/60 p-4 text-xs text-cyan-200 shadow-xl">
          <div className="flex items-center space-x-2.5">
            <Sparkles className="h-4 w-4 text-cyan-400 shrink-0" />
            <span>{expiryNotice}</span>
          </div>
          <button
            onClick={() => setExpiryNotice(null)}
            className="text-cyan-400 hover:text-white ml-3 font-bold px-1.5 py-0.5 rounded hover:bg-slate-800"
          >
            ✕
          </button>
        </div>
      )}

      {/* ---------------- 1. PORTFOLIO OVERVIEW HERO BANNER ---------------- */}
      <div className="rounded-2xl border border-slate-800 bg-gradient-to-r from-[#0c1626] via-[#0b1220] to-[#0a101b] p-6 shadow-2xl">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
          <div className="flex items-center space-x-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-500 to-cyan-500 text-slate-950 font-black shadow-lg shadow-emerald-500/20">
              <Wallet className="h-6 w-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-xl font-black text-white">Paper Options Portfolio</h2>
                <span className="rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-bold text-emerald-400 border border-emerald-500/20">
                  Virtual Cash Account
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Risk-free options simulation. Execute live options setups, monitor mark-to-market P&amp;L, and test holding horizons.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={refreshLiveQuotes}
              disabled={loadingQuotes || openPositions.length === 0}
              className="flex items-center space-x-1.5 rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-1.5 text-xs font-semibold text-slate-200 hover:text-white transition disabled:opacity-40"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loadingQuotes ? "animate-spin text-cyan-400" : ""}`} />
              <span>Refresh P&amp;L</span>
            </button>
            <button
              onClick={handleResetAccount}
              title="Reset Virtual Account"
              className="flex items-center space-x-1 rounded-lg border border-slate-800 bg-slate-900 px-2.5 py-1.5 text-xs font-medium text-slate-400 hover:text-rose-400 hover:border-rose-900 transition"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              <span>Reset</span>
            </button>
          </div>
        </div>

        {/* Portfolio KPI Bar */}
        <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-xl border border-slate-800 bg-[#090f1d] p-3.5">
            <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
              Total Account Value
            </div>
            <div className="mt-1 flex items-baseline space-x-2">
              <span className="text-2xl font-black font-mono text-white">
                ${portfolioStats.totalPortfolioValue.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </div>
            <div className="mt-1 flex items-center text-xs font-semibold">
              <span className={portfolioStats.allTimePnl >= 0 ? "text-emerald-400" : "text-rose-400"}>
                {portfolioStats.allTimePnl >= 0 ? "+" : ""}${portfolioStats.allTimePnl.toFixed(2)} ({portfolioStats.allTimeRoiPct >= 0 ? "+" : ""}{portfolioStats.allTimeRoiPct.toFixed(2)}%)
              </span>
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-[#090f1d] p-3.5">
            <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
              Available Cash
            </div>
            <div className="mt-1 text-2xl font-black font-mono text-cyan-300">
              ${cashBalance.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div className="mt-1 text-xs text-slate-400">
              Initial Capital: $10,000.00
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-[#090f1d] p-3.5">
            <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
              Open Positions P&amp;L
            </div>
            <div className="mt-1 text-2xl font-black font-mono">
              <span className={portfolioStats.unrealizedDollarPnl >= 0 ? "text-emerald-400" : "text-rose-400"}>
                {portfolioStats.unrealizedDollarPnl >= 0 ? "+" : ""}${portfolioStats.unrealizedDollarPnl.toFixed(2)}
              </span>
            </div>
            <div className="mt-1 text-xs font-semibold">
              <span className={portfolioStats.unrealizedRoiPct >= 0 ? "text-emerald-400" : "text-rose-400"}>
                {portfolioStats.unrealizedRoiPct >= 0 ? "+" : ""}{portfolioStats.unrealizedRoiPct.toFixed(2)}% ROI
              </span>
              <span className="ml-1 text-slate-500 font-normal">({openPositions.length} active)</span>
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-[#090f1d] p-3.5">
            <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
              Realized P&amp;L (Closed)
            </div>
            <div className="mt-1 text-2xl font-black font-mono">
              <span className={portfolioStats.totalRealizedPnl >= 0 ? "text-emerald-400" : "text-rose-400"}>
                {portfolioStats.totalRealizedPnl >= 0 ? "+" : ""}${portfolioStats.totalRealizedPnl.toFixed(2)}
              </span>
            </div>
            <div className="mt-1 text-xs text-slate-400">
              Win Rate: <strong className="text-white">{portfolioStats.winRate.toFixed(1)}%</strong> ({portfolioStats.totalClosed} closed)
            </div>
          </div>
        </div>
      </div>

      {/* ---------------- 2. TAB CONTROLS (OPEN / CLOSED / NEW ORDER) ---------------- */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-2">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setActiveSubTab("open")}
            className={`flex items-center space-x-1.5 rounded-lg px-3.5 py-1.5 text-xs font-bold transition ${
              activeSubTab === "open"
                ? "bg-cyan-500 text-black shadow-md font-black"
                : "text-slate-400 hover:text-white bg-slate-900 border border-slate-800"
            }`}
          >
            <Activity className="h-3.5 w-3.5" />
            <span>Open Positions ({openPositions.length})</span>
          </button>

          <button
            onClick={() => setActiveSubTab("closed")}
            className={`flex items-center space-x-1.5 rounded-lg px-3.5 py-1.5 text-xs font-bold transition ${
              activeSubTab === "closed"
                ? "bg-cyan-500 text-black shadow-md font-black"
                : "text-slate-400 hover:text-white bg-slate-900 border border-slate-800"
            }`}
          >
            <History className="h-3.5 w-3.5" />
            <span>Trade Log / Closed ({closedPositions.length})</span>
          </button>

          <button
            onClick={() => setActiveSubTab("new_trade")}
            className={`flex items-center space-x-1.5 rounded-lg px-3.5 py-1.5 text-xs font-bold transition ${
              activeSubTab === "new_trade"
                ? "bg-emerald-500 text-black shadow-md font-black"
                : "text-emerald-400 hover:text-white bg-emerald-950/30 border border-emerald-800/40"
            }`}
          >
            <Plus className="h-3.5 w-3.5" />
            <span>+ Buy New Option</span>
          </button>
        </div>

        {lastRefreshed && (
          <span className="text-[11px] text-slate-500">
            Last mark-to-market sync: {lastRefreshed.toLocaleTimeString()}
          </span>
        )}
      </div>

      {/* ---------------- 3. VIEW: OPEN POSITIONS ---------------- */}
      {activeSubTab === "open" && (
        <div>
          {expiredOpenPositions.length > 0 && (
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-500/40 bg-amber-950/25 p-4 text-xs text-amber-200 shadow-lg">
              <div className="flex items-center space-x-2.5">
                <AlertCircle className="h-5 w-5 text-amber-400 shrink-0" />
                <div>
                  <strong>{expiredOpenPositions.length} position(s) have reached expiration.</strong>
                  <p className="text-[11px] text-amber-300/80 mt-0.5">
                    In-The-Money options will be cash-settled for intrinsic value and credited to your virtual cash balance.
                  </p>
                </div>
              </div>
              <button
                onClick={handleSettleExpiredPositions}
                className="flex items-center space-x-1.5 rounded-lg bg-amber-500 px-3.5 py-2 text-xs font-black text-slate-950 hover:bg-amber-400 transition shadow-md"
              >
                <Zap className="h-3.5 w-3.5" />
                <span>Settle Expired Positions Now</span>
              </button>
            </div>
          )}
          {openPositions.length === 0 ? (
            <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-800 bg-[#090e1b] py-16 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 mb-4">
                <Activity className="h-7 w-7" />
              </div>
              <h3 className="text-lg font-bold text-white">No Open Paper Positions</h3>
              <p className="mt-1 max-w-md text-xs text-slate-400">
                You have no active options trades. Click &quot;Buy New Option&quot; above to simulate buying calls or puts, or execute ideas directly from the Chain Matrix or Signal Cards.
              </p>
              <button
                onClick={() => setActiveSubTab("new_trade")}
                className="mt-5 rounded-lg border border-emerald-500/40 bg-emerald-500/20 px-4 py-2 text-xs font-bold text-emerald-300 hover:bg-emerald-500/30 transition shadow-sm"
              >
                + Place First Paper Trade
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              {openPositions.map((pos) => {
                const currentVal = pos.currentPrice * 100 * pos.contracts;
                const dollarPnl = currentVal - pos.totalCost;
                const roiPct = (dollarPnl / pos.totalCost) * 100;
                const isProfit = dollarPnl >= 0;

                return (
                  <div
                    key={pos.id}
                    className="flex flex-col justify-between rounded-xl border border-slate-800 bg-[#0b1220] p-5 shadow-lg hover:border-slate-700 transition"
                  >
                    <div>
                      {/* Card Header */}
                      <div className="flex items-start justify-between border-b border-slate-800/80 pb-3">
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="text-lg font-black text-white">{pos.ticker}</span>
                            <span
                              className={`rounded px-2 py-0.5 text-xs font-black ${
                                pos.optionType === "CALL"
                                  ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                                  : "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                              }`}
                            >
                              {pos.strike} {pos.optionType}
                            </span>
                            <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-400 font-mono">
                              {pos.contracts}x ({pos.contracts * 100} shares)
                            </span>
                            {isOptionExpired(pos.expiration) && (
                              <span className="rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 px-2 py-0.5 text-[10px] font-bold">
                                ⚠️ EXPIRED
                              </span>
                            )}
                          </div>
                          <p className="mt-1 font-mono text-[11px] text-slate-400">
                            {pos.contract} &bull; Exp: {pos.expiration}
                          </p>
                        </div>

                        {/* Live P&L Pill */}
                        <div className="text-right">
                          <div
                            className={`flex items-center justify-end font-mono text-lg font-black ${
                              isProfit ? "text-emerald-400" : "text-rose-400"
                            }`}
                          >
                            {isProfit ? <TrendingUp className="mr-1 h-4 w-4" /> : <TrendingDown className="mr-1 h-4 w-4" />}
                            {isProfit ? "+" : ""}${dollarPnl.toFixed(2)}
                          </div>
                          <span
                            className={`rounded px-1.5 py-0.2 text-[10px] font-bold ${
                              isProfit
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                            }`}
                          >
                            {isProfit ? "+" : ""}{roiPct.toFixed(2)}% ROI
                          </span>
                        </div>
                      </div>

                      {/* Financial Detail Grid */}
                      <div className="mt-3 grid grid-cols-2 gap-3 text-xs sm:grid-cols-4">
                        <div className="rounded bg-slate-900/60 p-2 border border-slate-800/60">
                          <span className="text-[10px] text-slate-400 block">Buy Premium:</span>
                          <span className="font-mono font-bold text-slate-200">${pos.entryPrice.toFixed(2)}</span>
                        </div>
                        <div className="rounded bg-slate-900/60 p-2 border border-slate-800/60">
                          <span className="text-[10px] text-slate-400 block">Current Premium:</span>
                          <span className="font-mono font-bold text-cyan-300">${pos.currentPrice.toFixed(2)}</span>
                        </div>
                        <div className="rounded bg-slate-900/60 p-2 border border-slate-800/60">
                          <span className="text-[10px] text-slate-400 block">Total Invested:</span>
                          <span className="font-mono font-bold text-slate-200">${pos.totalCost.toFixed(2)}</span>
                        </div>
                        <div className="rounded bg-slate-900/60 p-2 border border-slate-800/60">
                          <span className="text-[10px] text-slate-400 block">Current Value:</span>
                          <span className="font-mono font-bold text-white">${currentVal.toFixed(2)}</span>
                        </div>
                      </div>

                      {/* Trade Targets / Stops */}
                      {(pos.targetProfitPrice || pos.stopLossPrice) && (
                        <div className="mt-3 flex items-center justify-between rounded-lg bg-[#070d18] px-3 py-1.5 text-[11px] text-slate-400 border border-slate-800">
                          {pos.targetProfitPrice && (
                            <span>
                              🎯 Profit Target: <strong className="text-emerald-400">${pos.targetProfitPrice.toFixed(2)}</strong>
                            </span>
                          )}
                          {pos.stopLossPrice && (
                            <span>
                              🛑 Stop Loss: <strong className="text-rose-400">${pos.stopLossPrice.toFixed(2)}</strong>
                            </span>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Action Bar */}
                    <div className="mt-4 flex items-center justify-between border-t border-slate-800/80 pt-3">
                      <div className="text-[10px] text-slate-500">
                        Entered {new Date(pos.enteredAt).toLocaleDateString()}
                      </div>

                      <div className="flex items-center space-x-2">
                        {onSelectTicker && (
                          <button
                            onClick={() => onSelectTicker(pos.ticker)}
                            className="rounded px-2.5 py-1 text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 transition"
                          >
                            Chart &rarr;
                          </button>
                        )}
                        {isOptionExpired(pos.expiration) ? (
                          <button
                            onClick={() => handleExpirePositionNow(pos.id)}
                            className="flex items-center space-x-1.5 rounded-lg border border-amber-500/50 bg-amber-500/20 px-3 py-1 text-xs font-bold text-amber-300 hover:bg-amber-500/30 transition shadow-sm"
                          >
                            <Zap className="h-3.5 w-3.5" />
                            <span>Cash Settle Expired</span>
                          </button>
                        ) : (
                          <div className="flex items-center space-x-1.5">
                            <button
                              onClick={() => handleExpirePositionNow(pos.id)}
                              title="Simulate expiration against current market spot price"
                              className="rounded-lg border border-slate-700 bg-slate-800/60 px-2 py-1 text-[11px] font-medium text-slate-400 hover:text-amber-300 hover:border-amber-500/30 transition"
                            >
                              Simulate Expiry
                            </button>
                            <button
                              onClick={() => handleClosePosition(pos.id)}
                              className="flex items-center space-x-1 rounded-lg border border-cyan-500/40 bg-cyan-600/80 px-3 py-1 text-xs font-bold text-white hover:bg-cyan-500 transition shadow-sm"
                            >
                              <DollarSign className="h-3.5 w-3.5" />
                              <span>Close / Sell</span>
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ---------------- 4. VIEW: TRADE LOG / CLOSED POSITIONS ---------------- */}
      {activeSubTab === "closed" && (
        <div className="rounded-2xl border border-slate-800 bg-[#090e1a] shadow-xl overflow-hidden">
          {closedPositions.length === 0 ? (
            <div className="py-16 text-center text-xs text-slate-400">
              No closed trades recorded yet. Close active positions to see realized win/loss performance here.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 bg-[#0c1424] text-[11px] text-slate-400 uppercase font-semibold">
                    <th className="p-3">Ticker / Contract</th>
                    <th className="p-3">Side</th>
                    <th className="p-3">Settlement</th>
                    <th className="p-3">Contracts</th>
                    <th className="p-3">Entry Price</th>
                    <th className="p-3">Exit Price</th>
                    <th className="p-3">Total Cost</th>
                    <th className="p-3">Realized P&amp;L</th>
                    <th className="p-3">ROI %</th>
                    <th className="p-3">Closed Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {closedPositions.map((pos) => {
                    const pnl = pos.realizedPnl || 0;
                    const roi = pos.totalCost > 0 ? (pnl / pos.totalCost) * 100 : 0;
                    const isWin = pnl >= 0;

                    return (
                      <tr key={pos.id} className="hover:bg-slate-800/20">
                        <td className="p-3 font-sans font-bold text-white">
                          <span>{pos.ticker}</span>{" "}
                          <span className="text-[11px] text-slate-400 font-mono">
                            ${pos.strike} {pos.optionType}
                          </span>
                        </td>
                        <td className="p-3">
                          <span
                            className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${
                              pos.optionType === "CALL" ? "text-emerald-400 bg-emerald-950/40" : "text-rose-400 bg-rose-950/40"
                            }`}
                          >
                            {pos.optionType}
                          </span>
                        </td>
                        <td className="p-3 font-sans">
                          {pos.settlementType === "EXPIRED_ITM" ? (
                            <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-[10px] font-bold text-emerald-300 border border-emerald-500/30 inline-flex items-center gap-1">
                              💎 Expired ITM
                            </span>
                          ) : pos.settlementType === "EXPIRED_WORTHLESS" ? (
                            <span className="rounded bg-rose-500/20 px-2 py-0.5 text-[10px] font-bold text-rose-300 border border-rose-500/30 inline-flex items-center gap-1">
                              💀 Expired Worthless
                            </span>
                          ) : (
                            <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-medium text-slate-300 border border-slate-700">
                              Manual Close
                            </span>
                          )}
                        </td>
                        <td className="p-3 text-slate-300">{pos.contracts}x</td>
                        <td className="p-3 text-slate-300">${pos.entryPrice.toFixed(2)}</td>
                        <td className="p-3 text-cyan-300">${(pos.exitPrice || 0).toFixed(2)}</td>
                        <td className="p-3 text-slate-400">${pos.totalCost.toFixed(2)}</td>
                        <td className={`p-3 font-bold ${isWin ? "text-emerald-400" : "text-rose-400"}`}>\
                          {isWin ? "+" : ""}${pnl.toFixed(2)}
                        </td>
                        <td className={`p-3 font-bold ${isWin ? "text-emerald-400" : "text-rose-400"}`}>\
                          {isWin ? "+" : ""}{roi.toFixed(1)}%
                        </td>
                        <td className="p-3 text-[11px] font-sans text-slate-400">
                          {pos.closedAt ? new Date(pos.closedAt).toLocaleDateString() : "--"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ---------------- 5. VIEW: NEW PAPER ORDER FORM (WITH TICKER DROPDOWN & LIVE OPTION PRICE) ---------------- */}
      {activeSubTab === "new_trade" && (
        <div className="rounded-2xl border border-slate-800 bg-[#0a1120] p-6 shadow-2xl max-w-2xl mx-auto">
          {/* Header */}
          <div className="border-b border-slate-800 pb-4 mb-5 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="text-base font-bold text-white flex items-center space-x-2">
                <Plus className="h-4 w-4 text-emerald-400" />
                <span>Simulated Option Order Ticket</span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Select your ticker from the dropdown to automatically stream real-time option chains and live contract prices.
              </p>
            </div>
            <div className="text-right">
              <span className="text-[10px] text-slate-400 block uppercase">Virtual Cash Available</span>
              <span className="font-mono text-base font-black text-cyan-300">${cashBalance.toFixed(2)}</span>
            </div>
          </div>

          <form onSubmit={handleOpenPosition} className="space-y-4 text-xs">
            {/* ROW 1: TICKER SELECTION DROPDOWN & OPTION TYPE */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-slate-300 font-semibold flex items-center space-x-1.5">
                    <span>Underlying Ticker:</span>
                    {chainLoading && <RefreshCw className="h-3 w-3 animate-spin text-cyan-400" />}
                  </label>
                  {chainData?.current_price && (
                    <span className="text-[11px] font-mono font-bold text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-500/30">
                      {formTicker}: ${chainData.current_price.toFixed(2)}{" "}
                      {chainData.change_pct !== undefined && (
                        <span>({chainData.change_pct >= 0 ? "+" : ""}{chainData.change_pct.toFixed(2)}%)</span>
                      )}
                    </span>
                  )}
                </div>

                {/* Dropdown Menu for Selecting Ticker */}
                <div className="relative">
                  <select
                    value={isCustomTicker ? "CUSTOM" : selectedDropdownTicker}
                    onChange={(e) => handleDropdownTickerChange(e.target.value)}
                    className="w-full appearance-none rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 pr-8 font-mono font-bold text-white focus:border-cyan-500 focus:outline-none cursor-pointer"
                  >
                    {POPULAR_TICKER_GROUPS.map((group) => (
                      <optgroup key={group.category} label={`── ${group.category} ──`} className="bg-slate-900 text-cyan-400 font-bold">
                        {group.tickers.map((sym) => (
                          <option key={sym} value={sym} className="text-white font-mono bg-slate-900">
                            {sym}
                          </option>
                        ))}
                      </optgroup>
                    ))}
                    <optgroup label="── Custom Entry ──" className="bg-slate-900 text-indigo-400 font-bold">
                      <option value="CUSTOM" className="text-amber-300 font-mono bg-slate-900">
                        ✍️ Other / Custom Ticker...
                      </option>
                    </optgroup>
                  </select>
                  <ChevronDown className="absolute right-2.5 top-2.5 h-4 w-4 text-slate-400 pointer-events-none" />
                </div>

                {/* Custom Ticker Write-in if selected */}
                {isCustomTicker && (
                  <div className="mt-2 flex items-center space-x-1.5">
                    <input
                      type="text"
                      placeholder="Enter custom ticker (e.g. TSLA)"
                      value={customTickerInput}
                      onChange={(e) => setCustomTickerInput(e.target.value.toUpperCase())}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          handleCustomTickerSubmit();
                        }
                      }}
                      className="w-full rounded-lg border border-cyan-500/50 bg-slate-950 px-3 py-1.5 font-mono font-bold text-white uppercase focus:border-cyan-400 focus:outline-none"
                    />
                    <button
                      type="button"
                      onClick={() => handleCustomTickerSubmit()}
                      className="rounded-lg bg-cyan-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-cyan-500 transition"
                    >
                      Load
                    </button>
                  </div>
                )}
              </div>

              {/* Option Type Selector (CALL / PUT) */}
              <div>
                <label className="text-slate-300 block mb-1 font-semibold">Option Contract Type:</label>
                <div className="grid grid-cols-2 gap-1 rounded-lg border border-slate-700 bg-slate-900 p-1">
                  <button
                    type="button"
                    onClick={() => setFormType("CALL")}
                    className={`rounded py-1.5 font-black text-xs transition ${
                      formType === "CALL"
                        ? "bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/20"
                        : "text-slate-400 hover:text-white"
                    }`}
                  >
                    CALL (Bullish)
                  </button>
                  <button
                    type="button"
                    onClick={() => setFormType("PUT")}
                    className={`rounded py-1.5 font-black text-xs transition ${
                      formType === "PUT"
                        ? "bg-rose-500 text-white shadow-md shadow-rose-500/20"
                        : "text-slate-400 hover:text-white"
                    }`}
                  >
                    PUT (Bearish)
                  </button>
                </div>
              </div>
            </div>

            {/* ROW 2: EXPIRATION DATE & STRIKE PRICE DROPDOWNS */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Expiration Dropdown */}
              <div>
                <label className="text-slate-300 block mb-1 font-semibold">
                  Expiration Cycle (DTE):
                </label>
                {availableExpirations.length > 0 ? (
                  <div className="relative">
                    <select
                      value={formExpiration}
                      onChange={(e) => handleExpirationChange(e.target.value)}
                      className="w-full appearance-none rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 pr-8 font-mono text-white focus:border-cyan-500 focus:outline-none cursor-pointer"
                    >
                      {availableExpirations.map((exp) => (
                        <option key={exp.expiration} value={exp.expiration} className="bg-slate-900">
                          {exp.expiration} ({exp.dte}d DTE)
                        </option>
                      ))}
                    </select>
                    <ChevronDown className="absolute right-2.5 top-2.5 h-4 w-4 text-slate-400 pointer-events-none" />
                  </div>
                ) : (
                  <input
                    type="date"
                    value={formExpiration}
                    onChange={(e) => handleExpirationChange(e.target.value)}
                    required
                    className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 font-mono text-white focus:border-cyan-500 focus:outline-none"
                  />
                )}
              </div>

              {/* Strike Price Dropdown */}
              <div>
                <label className="text-slate-300 block mb-1 font-semibold flex items-center justify-between">
                  <span>Strike Price ($):</span>
                  {selectedOptionQuote?.inTheMoney !== undefined && (
                    <span
                      className={`text-[10px] px-1.5 py-0.2 rounded font-bold ${
                        selectedOptionQuote.inTheMoney
                          ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                          : "bg-slate-800 text-slate-400"
                      }`}
                    >
                      {selectedOptionQuote.inTheMoney ? "ITM (In The Money)" : "OTM (Out of Money)"}
                    </span>
                  )}
                </label>

                {availableStrikes.length > 0 ? (
                  <div className="relative">
                    <select
                      value={formStrike}
                      onChange={(e) => setFormStrike(parseFloat(e.target.value))}
                      className="w-full appearance-none rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 pr-8 font-mono font-bold text-white focus:border-cyan-500 focus:outline-none cursor-pointer"
                    >
                      {availableStrikes.map((s: any) => {
                        const isAtm = s.is_atm;
                        const itmCall = s.is_itm_call;
                        const itmPut = s.is_itm_put;
                        const isItm = formType === "CALL" ? itmCall : itmPut;
                        const relTag = isAtm ? "★ ATM" : isItm ? "ITM" : "OTM";
                        const askPrice = formType === "CALL" ? s.call?.ask : s.put?.ask;
                        const priceStr = askPrice && askPrice > 0 ? `$${askPrice.toFixed(2)}` : "--";

                        return (
                          <option key={s.strike} value={s.strike} className="bg-slate-900">
                            ${s.strike.toFixed(2)} [{relTag}] - Ask: {priceStr}
                          </option>
                        );
                      })}
                    </select>
                    <ChevronDown className="absolute right-2.5 top-2.5 h-4 w-4 text-slate-400 pointer-events-none" />
                  </div>
                ) : (
                  <input
                    type="number"
                    step="0.5"
                    value={formStrike}
                    onChange={(e) => setFormStrike(parseFloat(e.target.value))}
                    required
                    className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 font-mono font-bold text-white focus:border-cyan-500 focus:outline-none"
                  />
                )}
              </div>
            </div>

            {/* ---------------- 🌟 LIVE CURRENT OPTION PRICE DISPLAY CARD ---------------- */}
            <div className="rounded-xl border border-cyan-500/30 bg-gradient-to-r from-[#0d172a] to-[#091122] p-4 shadow-xl">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-[11px] font-bold text-cyan-400 uppercase tracking-wider flex items-center space-x-1">
                      <Sparkles className="h-3.5 w-3.5 text-cyan-400" />
                      <span>Live Option Market Quote</span>
                    </span>
                    {chainLoading && <RefreshCw className="h-3 w-3 animate-spin text-cyan-400" />}
                  </div>
                  <div className="mt-1 flex items-baseline space-x-3">
                    <span className="font-mono text-2xl font-black text-cyan-300">
                      ${liveAsk > 0 ? liveAsk.toFixed(2) : liveMid > 0 ? liveMid.toFixed(2) : formEntryPrice.toFixed(2)}
                    </span>
                    <span className="text-xs text-slate-400">
                      (Current Ask / Buying Price)
                    </span>
                  </div>
                </div>

                {/* Quick 1-Click Price Application Buttons */}
                <div className="flex items-center space-x-2">
                  <button
                    type="button"
                    onClick={() => {
                      if (liveAsk > 0) {
                        setFormEntryPrice(Number(liveAsk.toFixed(2)));
                        setQuoteFeedback(`Filled with Live Ask ($${liveAsk.toFixed(2)})`);
                      }
                    }}
                    className="rounded-lg border border-cyan-500/40 bg-cyan-500/20 px-2.5 py-1 text-xs font-bold text-cyan-300 hover:bg-cyan-500/30 transition shadow-sm"
                  >
                    Use Ask (${liveAsk > 0 ? liveAsk.toFixed(2) : formEntryPrice.toFixed(2)})
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      if (liveMid > 0) {
                        setFormEntryPrice(Number(liveMid.toFixed(2)));
                        setQuoteFeedback(`Filled with Mid-Market ($${liveMid.toFixed(2)})`);
                      }
                    }}
                    className="rounded-lg border border-slate-700 bg-slate-800/80 px-2.5 py-1 text-xs font-semibold text-slate-300 hover:text-white hover:bg-slate-700 transition"
                  >
                    Use Mid (${liveMid > 0 ? liveMid.toFixed(2) : formEntryPrice.toFixed(2)})
                  </button>
                </div>
              </div>

              {/* Real-time Bid / Ask / Greeks Ladder */}
              <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
                <div className="rounded-lg bg-slate-900/80 p-2 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block">Bid Price:</span>
                  <span className="font-mono font-bold text-slate-200">${liveBid.toFixed(2)}</span>
                </div>
                <div className="rounded-lg bg-slate-900/80 p-2 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block">Mid Price:</span>
                  <span className="font-mono font-bold text-cyan-300">${liveMid.toFixed(2)}</span>
                </div>
                <div className="rounded-lg bg-slate-900/80 p-2 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block">Delta (Δ):</span>
                  <span className="font-mono font-bold text-emerald-400">
                    {liveDelta > 0 ? "+" : ""}{liveDelta.toFixed(3)}
                  </span>
                </div>
                <div className="rounded-lg bg-slate-900/80 p-2 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block">Implied Vol (IV):</span>
                  <span className="font-mono font-bold text-amber-300">{liveIv.toFixed(1)}%</span>
                </div>
              </div>

              {/* OCC Contract ID & Feedback */}
              <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-400">
                <span className="font-mono text-slate-300">
                  Contract: <strong className="text-white">{selectedOptionQuote?.contract || `${formTicker}${formExpiration.replace(/-/g,"").slice(2)}${formType[0]}`}</strong>
                </span>
                {quoteFeedback && (
                  <span className="text-emerald-400 font-semibold flex items-center space-x-1 animate-pulse">
                    <Check className="h-3 w-3" />
                    <span>{quoteFeedback}</span>
                  </span>
                )}
              </div>
            </div>

            {/* ROW 3: ENTRY PRICE & CONTRACT QUANTITY STEPPER */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-slate-300 block mb-1 font-semibold">
                  Purchase Premium Per Share ($):
                </label>
                <div className="relative">
                  <input
                    type="number"
                    step="0.05"
                    min="0.01"
                    value={formEntryPrice}
                    onChange={(e) => setFormEntryPrice(parseFloat(e.target.value) || 0.01)}
                    required
                    className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 font-mono font-bold text-cyan-300 focus:border-cyan-500 focus:outline-none"
                  />
                  <span className="absolute right-3 top-2 text-xs text-slate-500">/ share</span>
                </div>
                <span className="text-[10px] text-slate-500 mt-1 block">
                  1 contract = 100 shares (${(formEntryPrice * 100).toFixed(2)} premium)
                </span>
              </div>

              <div>
                <label className="text-slate-300 block mb-1 font-semibold">
                  Contracts Quantity:
                </label>
                <div className="flex items-center space-x-2">
                  <div className="flex items-center rounded-lg border border-slate-700 bg-slate-900 p-0.5">
                    <button
                      type="button"
                      onClick={() => setFormContracts((prev) => Math.max(1, prev - 1))}
                      className="flex h-8 w-8 items-center justify-center rounded text-slate-300 hover:bg-slate-800 hover:text-white"
                    >
                      <ChevronDown className="h-4 w-4" />
                    </button>
                    <input
                      type="number"
                      min="1"
                      max="100"
                      value={formContracts}
                      onChange={(e) => setFormContracts(Math.max(1, parseInt(e.target.value) || 1))}
                      className="w-12 bg-transparent text-center font-mono font-bold text-white focus:outline-none"
                    />
                    <button
                      type="button"
                      onClick={() => setFormContracts((prev) => Math.min(100, prev + 1))}
                      className="flex h-8 w-8 items-center justify-center rounded text-slate-300 hover:bg-slate-800 hover:text-white"
                    >
                      <ChevronUp className="h-4 w-4" />
                    </button>
                  </div>

                  {/* Quick Preset Buttons */}
                  <div className="flex items-center space-x-1">
                    {[1, 2, 5, 10].map((qty) => (
                      <button
                        key={qty}
                        type="button"
                        onClick={() => setFormContracts(qty)}
                        className={`rounded px-2 py-1 font-mono text-[11px] font-bold transition ${
                          formContracts === qty
                            ? "bg-cyan-500 text-slate-950 font-black shadow-sm"
                            : "bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700"
                        }`}
                      >
                        {qty}x
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* ROW 4: PROFIT TARGET & STOP LOSS */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-slate-300 font-semibold">Profit Target ($/sh):</label>
                  <button
                    type="button"
                    onClick={() => setFormTarget(Number((formEntryPrice * 1.5).toFixed(2)))}
                    className="text-[10px] text-emerald-400 hover:underline"
                  >
                    +50% (${(formEntryPrice * 1.5).toFixed(2)})
                  </button>
                </div>
                <input
                  type="number"
                  step="0.1"
                  placeholder="Target $"
                  value={formTarget}
                  onChange={(e) => setFormTarget(parseFloat(e.target.value) || 0)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 font-mono text-emerald-300 focus:border-cyan-500 focus:outline-none"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-slate-300 font-semibold">Stop Loss ($/sh):</label>
                  <button
                    type="button"
                    onClick={() => setFormStop(Number((formEntryPrice * 0.5).toFixed(2)))}
                    className="text-[10px] text-rose-400 hover:underline"
                  >
                    -50% (${(formEntryPrice * 0.5).toFixed(2)})
                  </button>
                </div>
                <input
                  type="number"
                  step="0.1"
                  placeholder="Stop $"
                  value={formStop}
                  onChange={(e) => setFormStop(parseFloat(e.target.value) || 0)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 font-mono text-rose-300 focus:border-cyan-500 focus:outline-none"
                />
              </div>
            </div>

            {/* Breakeven Analytics Pill */}
            <div className="flex items-center justify-between rounded-xl bg-slate-900/60 p-3 border border-slate-800 text-[11px] text-slate-400">
              <span>
                🎯 Breakeven: <strong className="font-mono text-white">${breakevenPrice.toFixed(2)}</strong>
              </span>
              <span>
                Move required:{" "}
                <strong className={reqMovePct >= 0 ? "text-cyan-300" : "text-rose-300"}>
                  {reqMovePct >= 0 ? "+" : ""}{reqMovePct.toFixed(1)}%
                </strong>
              </span>
            </div>

            {/* Total Cost Review & Order Execution Box */}
            <div className="rounded-xl bg-[#080e1b] p-4 border border-emerald-500/30 flex items-center justify-between shadow-xl">
              <div>
                <span className="text-slate-400 block text-[11px] uppercase font-semibold">
                  Total Virtual Capital Required:
                </span>
                <span className="text-2xl font-black font-mono text-emerald-400">
                  ${(formEntryPrice * 100 * formContracts).toFixed(2)}
                </span>
                <span className="text-[10px] text-slate-500 block">
                  ({formContracts}x contract &times; 100 shares &times; ${formEntryPrice.toFixed(2)})
                </span>
              </div>

              <button
                type="submit"
                disabled={formEntryPrice * 100 * formContracts > cashBalance}
                className="rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 px-6 py-3 font-black text-slate-950 shadow-lg shadow-emerald-500/25 hover:from-emerald-400 hover:to-teal-400 disabled:opacity-40 transition flex items-center space-x-2"
              >
                <Plus className="h-4 w-4" />
                <span>Execute Paper Buy ({formContracts}x)</span>
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
