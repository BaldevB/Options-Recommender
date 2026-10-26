"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import {
  X,
  Wallet,
  TrendingUp,
  TrendingDown,
  DollarSign,
  RefreshCw,
  Trash2,
  ExternalLink,
  Layers,
  Zap,
  CheckCircle2,
  AlertCircle,
  Clock,
  ArrowRight,
  ShieldCheck,
  RotateCcw,
} from "lucide-react";

import {
  PaperTradePosition,
  isOptionExpired,
  settleExpiredPositions,
  settleSinglePosition,
} from "../utils/paperSettlement";

export type { PaperTradePosition };

interface StockPaperTradingDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigateToStock?: (symbol: string) => void;
  onNavigateToOptions?: (symbol: string) => void;
}

const STORAGE_KEY_POSITIONS = "options_paper_positions";
const STORAGE_KEY_BALANCE = "options_paper_balance";
const DEFAULT_STARTING_CASH = 10000.0;

export default function StockPaperTradingDrawer({
  isOpen,
  onClose,
  onNavigateToStock,
  onNavigateToOptions,
}: StockPaperTradingDrawerProps) {
  const [cashBalance, setCashBalance] = useState<number>(DEFAULT_STARTING_CASH);
  const [positions, setPositions] = useState<PaperTradePosition[]>([]);
  const [loadingQuotes, setLoadingQuotes] = useState<boolean>(false);
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);
  const [activeFilterTab, setActiveFilterTab] = useState<"all" | "stocks" | "options" | "closed">("all");
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  // Load from localStorage
  const loadPortfolioData = useCallback(() => {
    if (typeof window === "undefined") return;
    try {
      const savedBalance = localStorage.getItem(STORAGE_KEY_BALANCE);
      if (savedBalance) {
        setCashBalance(parseFloat(savedBalance));
      } else {
        localStorage.setItem(STORAGE_KEY_BALANCE, DEFAULT_STARTING_CASH.toString());
      }

      const savedPositions = localStorage.getItem(STORAGE_KEY_POSITIONS);
      if (savedPositions) {
        const parsed = JSON.parse(savedPositions);
        if (Array.isArray(parsed)) {
          let curCash = savedBalance ? parseFloat(savedBalance) : DEFAULT_STARTING_CASH;
          const autoSettle = settleExpiredPositions(parsed, curCash);
          if (autoSettle.settledCount > 0) {
            setPositions(autoSettle.updatedPositions);
            setCashBalance(autoSettle.newCashBalance);
            localStorage.setItem(STORAGE_KEY_POSITIONS, JSON.stringify(autoSettle.updatedPositions));
            localStorage.setItem(STORAGE_KEY_BALANCE, autoSettle.newCashBalance.toString());
            setFeedbackMessage(autoSettle.summaryMessage);
          } else {
            setPositions(parsed);
          }
        }
      }
    } catch (err) {
      console.error("Failed loading paper portfolio storage:", err);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      loadPortfolioData();
    }
  }, [isOpen, loadPortfolioData]);

  // Save helper
  const savePositions = (updated: PaperTradePosition[]) => {
    setPositions(updated);
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem(STORAGE_KEY_POSITIONS, JSON.stringify(updated));
      } catch (err) {
        console.error("Failed saving positions:", err);
      }
    }
  };

  const saveBalance = (newBalance: number) => {
    setCashBalance(newBalance);
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem(STORAGE_KEY_BALANCE, newBalance.toString());
      } catch (err) {
        console.error("Failed saving balance:", err);
      }
    }
  };

  // Live Quote Refresh via POST /api/paper-quotes
  const refreshLiveQuotes = useCallback(async () => {
    const openPos = positions.filter((p) => p.status === "OPEN");
    if (openPos.length === 0) return;

    setLoadingQuotes(true);
    try {
      const itemsPayload = openPos.map((p) => {
        const isStock = p.assetType === "STOCK" || p.optionType === "STOCK" || p.multiplier === 1;
        return {
          symbol: p.ticker,
          ticker: p.ticker,
          contract: p.contract || p.ticker,
          asset_type: isStock ? "STOCK" : "OPTION",
          expiration: p.expiration,
          strike: p.strike,
          option_type: p.optionType,
        };
      });

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
            const lookupKey = p.contract || p.ticker;
            const quoteData = quotes[lookupKey] || quotes[p.ticker];
            if (quoteData && quoteData.valid && quoteData.current_price > 0) {
              return {
                ...p,
                currentPrice: quoteData.current_price,
              };
            }
          }
          return p;
        });

        const autoSettle = settleExpiredPositions(updated, cashBalance, quotes);
        if (autoSettle.settledCount > 0) {
          savePositions(autoSettle.updatedPositions);
          saveBalance(autoSettle.newCashBalance);
          setFeedbackMessage(autoSettle.summaryMessage);
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
  }, [positions]);

  // Initial quote refresh on open if positions exist
  useEffect(() => {
    if (isOpen && positions.some((p) => p.status === "OPEN") && !lastRefreshed) {
      refreshLiveQuotes();
    }
  }, [isOpen, positions, lastRefreshed, refreshLiveQuotes]);

  // Settle all expired positions in drawer
  const handleSettleAllExpired = () => {
    const settlement = settleExpiredPositions(positions, cashBalance);
    if (settlement.settledCount > 0) {
      savePositions(settlement.updatedPositions);
      saveBalance(settlement.newCashBalance);
      setFeedbackMessage(settlement.summaryMessage);
    } else {
      setFeedbackMessage("No open positions currently require expiration settlement.");
      setTimeout(() => setFeedbackMessage(null), 3500);
    }
  };

  // Immediate expiration or simulation of a specific position
  const handleExpirePositionNow = (posId: string) => {
    const pos = positions.find((p) => p.id === posId);
    if (!pos) return;
    const spot = pos.currentPrice || pos.strike || 0;
    const settlement = settleSinglePosition(posId, positions, cashBalance, spot);
    if (settlement.settledCount > 0) {
      savePositions(settlement.updatedPositions);
      saveBalance(settlement.newCashBalance);
      setFeedbackMessage(settlement.summaryMessage);
    }
  };

  // Close Position
  const handleClosePosition = (positionId: string) => {
    const pos = positions.find((p) => p.id === positionId);
    if (!pos || pos.status !== "OPEN") return;

    const isStock = pos.assetType === "STOCK" || pos.optionType === "STOCK" || pos.multiplier === 1;
    const qty = pos.shares || pos.contracts || 1;
    const currentPrice = pos.currentPrice || pos.entryPrice;
    const proceeds = isStock ? currentPrice * qty : currentPrice * 100 * qty;
    const realizedPnl = proceeds - pos.totalCost;

    const updated = positions.map((p) => {
      if (p.id === positionId) {
        return {
          ...p,
          status: "CLOSED" as const,
          closedAt: new Date().toISOString(),
          exitPrice: currentPrice,
          realizedPnl: realizedPnl,
        };
      }
      return p;
    });

    const newBalance = cashBalance + proceeds;
    savePositions(updated);
    saveBalance(newBalance);

    setFeedbackMessage(
      `Closed ${pos.ticker} (${isStock ? `${qty} shares` : `${qty}x options`}) at $${currentPrice.toFixed(2)}. Realized P&L: ${
        realizedPnl >= 0 ? "+" : ""
      }$${realizedPnl.toFixed(2)}.`
    );
    setTimeout(() => setFeedbackMessage(null), 4000);
  };

  // Reset Portfolio
  const handleResetPortfolio = () => {
    if (typeof window !== "undefined" && window.confirm("Reset entire paper portfolio and balance to $10,000 cash?")) {
      savePositions([]);
      saveBalance(DEFAULT_STARTING_CASH);
      setFeedbackMessage("Paper portfolio successfully reset to $10,000 virtual cash.");
      setTimeout(() => setFeedbackMessage(null), 3500);
    }
  };

  // Portfolio calculations
  const portfolioStats = useMemo(() => {
    const openPositions = positions.filter((p) => p.status === "OPEN");
    const closedPositions = positions.filter((p) => p.status === "CLOSED");

    let openMarketValue = 0;
    let totalInvestedCost = 0;
    let unrealizedDollarPnl = 0;

    for (const p of openPositions) {
      const isStock = p.assetType === "STOCK" || p.optionType === "STOCK" || p.multiplier === 1;
      const qty = p.shares || p.contracts || 1;
      const currentVal = isStock ? p.currentPrice * qty : p.currentPrice * 100 * qty;
      openMarketValue += currentVal;
      totalInvestedCost += p.totalCost;
      unrealizedDollarPnl += currentVal - p.totalCost;
    }

    const unrealizedRoiPct = totalInvestedCost > 0 ? (unrealizedDollarPnl / totalInvestedCost) * 100 : 0;
    const totalRealizedPnl = closedPositions.reduce((acc, p) => acc + (p.realizedPnl || 0), 0);
    const totalPortfolioValue = cashBalance + openMarketValue;
    const allTimePnl = totalPortfolioValue - DEFAULT_STARTING_CASH;
    const allTimeRoiPct = (allTimePnl / DEFAULT_STARTING_CASH) * 100;

    return {
      openCount: openPositions.length,
      closedCount: closedPositions.length,
      openMarketValue,
      totalInvestedCost,
      unrealizedDollarPnl,
      unrealizedRoiPct,
      totalRealizedPnl,
      totalPortfolioValue,
      allTimePnl,
      allTimeRoiPct,
    };
  }, [positions, cashBalance]);

  // Filter positions
  const filteredPositions = useMemo(() => {
    if (activeFilterTab === "closed") {
      return positions.filter((p) => p.status === "CLOSED");
    }
    const openPositions = positions.filter((p) => p.status === "OPEN");
    if (activeFilterTab === "stocks") {
      return openPositions.filter((p) => p.assetType === "STOCK" || p.optionType === "STOCK" || p.multiplier === 1);
    }
    if (activeFilterTab === "options") {
      return openPositions.filter((p) => p.assetType !== "STOCK" && p.optionType !== "STOCK" && p.multiplier !== 1);
    }
    return openPositions;
  }, [positions, activeFilterTab]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-sm transition-opacity">
      <div className="absolute inset-y-0 right-0 flex max-w-full pl-10">
        <div className="relative w-screen max-w-2xl bg-[#090e1a] border-l border-slate-800 shadow-2xl flex flex-col text-slate-200">
          {/* Header */}
          <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-[#070b14]">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
                <Wallet className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                  Paper Portfolio Simulator
                  <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    Live Mark-to-Market
                  </span>
                </h2>
                <p className="text-xs text-slate-400">
                  Track stock shares &amp; option positions with zero real risk
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={refreshLiveQuotes}
                disabled={loadingQuotes}
                className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-cyan-300 border border-slate-700 transition-colors"
                title="Refresh Live Quotes"
              >
                <RefreshCw className={`w-4 h-4 ${loadingQuotes ? "animate-spin text-cyan-400" : ""}`} />
              </button>
              <button
                type="button"
                onClick={onClose}
                className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-100 border border-slate-700 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Portfolio Stats Banner */}
          <div className="p-4 bg-[#0c1322] border-b border-slate-800 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div>
              <span className="text-[10px] uppercase font-semibold text-slate-400 block tracking-wider">
                Total Acct Value
              </span>
              <span className="font-mono font-black text-slate-100 text-base block mt-0.5">
                ${portfolioStats.totalPortfolioValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
              <span
                className={`text-[11px] font-mono font-bold ${
                  portfolioStats.allTimePnl >= 0 ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                {portfolioStats.allTimePnl >= 0 ? "+" : ""}
                ${portfolioStats.allTimePnl.toFixed(2)} ({portfolioStats.allTimeRoiPct.toFixed(1)}%)
              </span>
            </div>

            <div>
              <span className="text-[10px] uppercase font-semibold text-slate-400 block tracking-wider">
                Virtual Cash Available
              </span>
              <span className="font-mono font-bold text-emerald-400 text-base block mt-0.5">
                ${cashBalance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
              <span className="text-[10px] text-slate-400">Liquid buying power</span>
            </div>

            <div>
              <span className="text-[10px] uppercase font-semibold text-slate-400 block tracking-wider">
                Invested Capital
              </span>
              <span className="font-mono font-bold text-slate-200 text-base block mt-0.5">
                ${portfolioStats.totalInvestedCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
              <span className="text-[10px] text-slate-400">{portfolioStats.openCount} open position(s)</span>
            </div>

            <div>
              <span className="text-[10px] uppercase font-semibold text-slate-400 block tracking-wider">
                Unrealized P&amp;L
              </span>
              <span
                className={`font-mono font-black text-base block mt-0.5 ${
                  portfolioStats.unrealizedDollarPnl >= 0 ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                {portfolioStats.unrealizedDollarPnl >= 0 ? "+" : ""}
                ${portfolioStats.unrealizedDollarPnl.toFixed(2)}
              </span>
              <span
                className={`text-[11px] font-mono font-bold ${
                  portfolioStats.unrealizedRoiPct >= 0 ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                {portfolioStats.unrealizedRoiPct >= 0 ? "+" : ""}
                {portfolioStats.unrealizedRoiPct.toFixed(2)}% ROI
              </span>
            </div>
          </div>

          {/* Feedback banner */}
          {feedbackMessage && (
            <div className="p-3 mx-4 mt-3 rounded-lg bg-emerald-500/15 border border-emerald-500/40 text-emerald-300 text-xs flex items-center justify-between">
              <span>{feedbackMessage}</span>
              <button onClick={() => setFeedbackMessage(null)} className="text-emerald-400 hover:text-emerald-200">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* Filter Tabs & Reset Action */}
          <div className="px-4 pt-3 flex items-center justify-between border-b border-slate-800">
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => setActiveFilterTab("all")}
                className={`px-3 py-2 text-xs font-semibold border-b-2 transition-colors ${
                  activeFilterTab === "all"
                    ? "border-cyan-400 text-cyan-300"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                All Open ({portfolioStats.openCount})
              </button>
              <button
                type="button"
                onClick={() => setActiveFilterTab("stocks")}
                className={`px-3 py-2 text-xs font-semibold border-b-2 transition-colors ${
                  activeFilterTab === "stocks"
                    ? "border-cyan-400 text-cyan-300"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                Stocks (Shares)
              </button>
              <button
                type="button"
                onClick={() => setActiveFilterTab("options")}
                className={`px-3 py-2 text-xs font-semibold border-b-2 transition-colors ${
                  activeFilterTab === "options"
                    ? "border-cyan-400 text-cyan-300"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                Options Contracts
              </button>
              <button
                type="button"
                onClick={() => setActiveFilterTab("closed")}
                className={`px-3 py-2 text-xs font-semibold border-b-2 transition-colors ${
                  activeFilterTab === "closed"
                    ? "border-cyan-400 text-cyan-300"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                Closed History ({portfolioStats.closedCount})
              </button>
            </div>

            <button
              type="button"
              onClick={handleResetPortfolio}
              className="text-[11px] text-slate-400 hover:text-rose-400 transition-colors inline-flex items-center gap-1"
              title="Reset to $10,000 starting cash"
            >
              <RotateCcw className="w-3 h-3" />
              Reset Portfolio
            </button>
          </div>

          {/* Positions List */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {positions.some((p) => p.status === "OPEN" && p.assetType !== "STOCK" && p.optionType !== "STOCK" && isOptionExpired(p.expiration)) && (
              <div className="p-3 rounded-xl border border-amber-500/40 bg-amber-950/20 text-xs text-amber-200 flex items-center justify-between gap-3 shadow-md">
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
                  <span>One or more options contracts have reached expiration date.</span>
                </div>
                <button
                  onClick={handleSettleAllExpired}
                  className="px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs inline-flex items-center gap-1 shadow-sm"
                >
                  <Zap className="w-3.5 h-3.5" />
                  Settle Expired
                </button>
              </div>
            )}
            {filteredPositions.length === 0 ? (
              <div className="py-16 text-center text-slate-500">
                <Wallet className="w-10 h-10 mx-auto text-slate-600 mb-2 opacity-50" />
                <p className="text-sm font-semibold text-slate-400">No positions found</p>
                <p className="text-xs text-slate-500 mt-1">
                  {activeFilterTab === "closed"
                    ? "No closed trades recorded yet."
                    : "Use 'Paper Buy' on any stock or option pick to start paper trading."}
                </p>
              </div>
            ) : (
              filteredPositions.map((pos) => {
                const isStock = pos.assetType === "STOCK" || pos.optionType === "STOCK" || pos.multiplier === 1;
                const qty = pos.shares || pos.contracts || 1;
                const currentPrice = pos.currentPrice || pos.entryPrice;
                const currentMarketVal = isStock ? currentPrice * qty : currentPrice * 100 * qty;
                const dollarPnl = pos.status === "CLOSED" ? (pos.realizedPnl || 0) : (currentMarketVal - pos.totalCost);
                const roiPct = pos.totalCost > 0 ? (dollarPnl / pos.totalCost) * 100 : 0;
                const isProfitable = dollarPnl >= 0;

                return (
                  <div
                    key={pos.id}
                    className="p-4 rounded-xl border border-slate-800 bg-[#0d1424] hover:border-slate-700 transition-all shadow-md"
                  >
                    {/* Top Row: Symbol, Asset Tag, Status & PnL */}
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-black text-base text-slate-100">
                          {pos.ticker}
                        </span>
                        {isStock ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                            EQUITY ({qty} Shares)
                          </span>
                        ) : (
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              pos.optionType === "PUT"
                                ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                                : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                            }`}
                          >
                            ${pos.strike} {pos.optionType} ({qty}x)
                          </span>
                        )}
                        {pos.status === "CLOSED" && (
                          <>
                            {pos.settlementType === "EXPIRED_ITM" ? (
                              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                                💎 Expired ITM
                              </span>
                            ) : pos.settlementType === "EXPIRED_WORTHLESS" ? (
                              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                                💀 Expired Worthless
                              </span>
                            ) : (
                              <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-400 border border-slate-700">
                                CLOSED
                              </span>
                            )}
                          </>
                        )}
                        {pos.status === "OPEN" && !isStock && isOptionExpired(pos.expiration) && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                            ⏳ EXPIRED
                          </span>
                        )}
                      </div>

                      <div className="text-right">
                        <div
                          className={`font-mono font-bold text-sm ${
                            isProfitable ? "text-emerald-400" : "text-rose-400"
                          }`}
                        >
                          {isProfitable ? "+" : ""}${dollarPnl.toFixed(2)}
                        </div>
                        <div
                          className={`text-xs font-mono font-semibold ${
                            isProfitable ? "text-emerald-400" : "text-rose-400"
                          }`}
                        >
                          {isProfitable ? "+" : ""}{roiPct.toFixed(2)}%
                        </div>
                      </div>
                    </div>

                    {/* Middle Row: Price comparison */}
                    <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-2 p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80 text-xs">
                      <div>
                        <span className="text-[10px] text-slate-400 uppercase block">Entry Price</span>
                        <span className="font-mono font-semibold text-slate-200">
                          ${pos.entryPrice.toFixed(2)}
                        </span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-400 uppercase block">
                          {pos.status === "CLOSED" ? "Exit Price" : "Live Price"}
                        </span>
                        <span className="font-mono font-semibold text-slate-100">
                          ${pos.status === "CLOSED" && pos.exitPrice ? pos.exitPrice.toFixed(2) : currentPrice.toFixed(2)}
                        </span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-400 uppercase block">Total Cost</span>
                        <span className="font-mono font-semibold text-slate-300">
                          ${pos.totalCost.toFixed(2)}
                        </span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-400 uppercase block">
                          {pos.status === "CLOSED" ? "Exit Proceeds" : "Current Value"}
                        </span>
                        <span className="font-mono font-semibold text-slate-100">
                          ${currentMarketVal.toFixed(2)}
                        </span>
                      </div>
                    </div>

                    {/* Trade Targets & Notes */}
                    <div className="mt-2.5 flex flex-wrap items-center justify-between text-[11px] text-slate-400">
                      <div className="flex items-center gap-3">
                        {pos.targetProfitPrice && (
                          <span>
                            Target: <span className="font-mono text-emerald-400 font-semibold">${pos.targetProfitPrice.toFixed(2)}</span>
                          </span>
                        )}
                        {pos.stopLossPrice && (
                          <span>
                            Stop: <span className="font-mono text-rose-400 font-semibold">${pos.stopLossPrice.toFixed(2)}</span>
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-slate-500 font-mono">
                        {new Date(pos.enteredAt).toLocaleDateString()}
                      </span>
                    </div>

                    {/* Actions */}
                    {pos.status === "OPEN" && (
                      <div className="mt-3 pt-2.5 border-t border-slate-800 flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          {onNavigateToStock && (
                            <button
                              type="button"
                              onClick={() => {
                                onNavigateToStock(pos.ticker);
                                onClose();
                              }}
                              className="text-[11px] font-semibold text-cyan-400 hover:text-cyan-300 transition-colors inline-flex items-center gap-1"
                            >
                              View Stock Plan <ArrowRight className="w-3 h-3" />
                            </button>
                          )}
                          {onNavigateToOptions && (
                            <button
                              type="button"
                              onClick={() => {
                                onNavigateToOptions(pos.ticker);
                                onClose();
                              }}
                              className="text-[11px] font-semibold text-slate-400 hover:text-slate-200 transition-colors inline-flex items-center gap-1"
                            >
                              Options <ExternalLink className="w-3 h-3" />
                            </button>
                          )}
                        </div>

                        {!isStock && isOptionExpired(pos.expiration) ? (
                          <button
                            type="button"
                            onClick={() => handleExpirePositionNow(pos.id)}
                            className="px-3 py-1 rounded-lg text-xs font-bold bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 transition-colors inline-flex items-center gap-1 shadow-sm"
                          >
                            <Zap className="w-3.5 h-3.5" />
                            Cash Settle
                          </button>
                        ) : (
                          <div className="flex items-center gap-1.5">
                            {!isStock && (
                              <button
                                type="button"
                                onClick={() => handleExpirePositionNow(pos.id)}
                                title="Simulate expiration at current market price"
                                className="px-2 py-1 rounded-lg text-[11px] font-medium bg-slate-800/60 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
                              >
                                Simulate Expiry
                              </button>
                            )}
                            <button
                              type="button"
                              onClick={() => handleClosePosition(pos.id)}
                              className="px-3 py-1 rounded-lg text-xs font-semibold bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 border border-rose-800/50 transition-colors"
                            >
                              Close Position
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
