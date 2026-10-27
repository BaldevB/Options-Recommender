"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  Calculator,
  ShieldCheck,
  AlertTriangle,
  TrendingUp,
  DollarSign,
  Percent,
  Zap,
  CheckCircle2,
  Sliders,
  Scale,
} from "lucide-react";
import { StockRecommendationItem } from "./StockCard";
import { addOrConsolidatePosition, PaperTradePosition } from "../utils/paperSettlement";

interface StockPositionCalculatorProps {
  stock: StockRecommendationItem;
  virtualBalance?: number;
  onTradeSimulated?: (trade: {
    symbol: string;
    shares: number;
    price: number;
    totalCost: number;
    tp: number;
    sl: number;
  }) => void;
  onClose?: () => void;
}

const STORAGE_KEY_POSITIONS = "options_paper_positions";
const STORAGE_KEY_BALANCE = "options_paper_balance";
const DEFAULT_BALANCE = 10000.0;

export default function StockPositionCalculator({
  stock,
  virtualBalance,
  onTradeSimulated,
  onClose,
}: StockPositionCalculatorProps) {
  // Read live balance from localStorage if not passed
  const [balance, setBalance] = useState<number>(() => {
    if (typeof virtualBalance === "number" && virtualBalance > 0) return virtualBalance;
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem(STORAGE_KEY_BALANCE);
      if (saved) {
        const parsed = parseFloat(saved);
        if (!isNaN(parsed) && parsed > 0) return parsed;
      }
    }
    return DEFAULT_BALANCE;
  });

  const [riskPct, setRiskPct] = useState<number>(2.0); // 2% account risk
  const [entryPrice, setEntryPrice] = useState<number>(stock.price || stock.trade_plan.current_price || 100);
  const [stopLoss, setStopLoss] = useState<number>(stock.trade_plan.stop_loss || (stock.price * 0.95));
  const [targetPrice, setTargetPrice] = useState<number>(stock.trade_plan.tp1 || (stock.price * 1.15));
  const [manualShares, setManualShares] = useState<number | null>(null);
  const [simulatedSuccess, setSimulatedSuccess] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Sync state if stock prop changes
  useEffect(() => {
    setEntryPrice(stock.price || stock.trade_plan.current_price || 100);
    setStopLoss(stock.trade_plan.stop_loss || (stock.price * 0.95));
    setTargetPrice(stock.trade_plan.tp1 || (stock.price * 1.15));
    setManualShares(null);
    setSimulatedSuccess(false);
    setErrorMessage(null);
  }, [stock]);

  // Calculations
  const calculations = useMemo(() => {
    const dollarRiskAllowed = balance * (riskPct / 100);
    const perShareRisk = Math.max(0.001, entryPrice - stopLoss);
    const isValidStop = stopLoss < entryPrice;

    // Sizing: shares based on risk formula
    const recommendedShares = isValidStop
      ? Math.max(1, Math.floor(dollarRiskAllowed / perShareRisk))
      : 0;

    const actualShares = manualShares !== null ? manualShares : recommendedShares;
    const totalCost = actualShares * entryPrice;
    const maxAffordableShares = entryPrice > 0 ? Math.floor(balance / entryPrice) : 0;
    const isOverBudget = totalCost > balance;

    const potentialDollarProfit = actualShares * Math.max(0, targetPrice - entryPrice);
    const potentialProfitPct = entryPrice > 0 ? ((targetPrice - entryPrice) / entryPrice) * 100 : 0;
    const portfolioAllocationPct = balance > 0 ? (totalCost / balance) * 100 : 0;
    const realizedRR = perShareRisk > 0 ? (targetPrice - entryPrice) / perShareRisk : 0;

    return {
      dollarRiskAllowed,
      perShareRisk,
      isValidStop,
      recommendedShares,
      actualShares,
      totalCost,
      maxAffordableShares,
      isOverBudget,
      potentialDollarProfit,
      potentialProfitPct,
      portfolioAllocationPct,
      realizedRR,
    };
  }, [balance, riskPct, entryPrice, stopLoss, targetPrice, manualShares]);

  // Execute Paper Buy
  const handleSimulateBuy = () => {
    setErrorMessage(null);

    if (!calculations.isValidStop) {
      setErrorMessage("Stop loss must be strictly below Entry Price for long positions.");
      return;
    }

    if (calculations.actualShares <= 0) {
      setErrorMessage("Please specify at least 1 share to buy.");
      return;
    }

    if (calculations.totalCost > balance) {
      setErrorMessage(
        `Insufficient virtual cash ($${balance.toFixed(2)}) for total trade cost of $${calculations.totalCost.toFixed(2)}.`
      );
      return;
    }

    try {
      const savedPositionsStr = localStorage.getItem(STORAGE_KEY_POSITIONS);
      const positions = savedPositionsStr ? JSON.parse(savedPositionsStr) : [];

      const newPos: PaperTradePosition = {
        id: `stock-${Date.now()}`,
        ticker: stock.symbol.toUpperCase(),
        contract: stock.symbol.toUpperCase(),
        assetType: "STOCK",
        optionType: "STOCK",
        strike: 0,
        expiration: "EQUITY",
        dte: 0,
        entryPrice: entryPrice,
        contracts: calculations.actualShares,
        shares: calculations.actualShares,
        multiplier: 1,
        totalCost: calculations.totalCost,
        enteredAt: new Date().toISOString(),
        currentPrice: entryPrice,
        status: "OPEN",
        targetProfitPrice: targetPrice,
        stopLossPrice: stopLoss,
        notes: `Simulated Stock Buy: ${calculations.actualShares} shares @ $${entryPrice.toFixed(2)} (${stock.horizon || "SWING"})`,
      };

      const { updatedPositions, consolidated, totalQty, weightedPrice } = addOrConsolidatePosition(
        positions,
        newPos
      );

      const updatedBalance = Math.max(0, balance - calculations.totalCost);

      localStorage.setItem(STORAGE_KEY_POSITIONS, JSON.stringify(updatedPositions));
      localStorage.setItem(STORAGE_KEY_BALANCE, updatedBalance.toString());

      setBalance(updatedBalance);
      setSimulatedSuccess(true);

      if (onTradeSimulated) {
        onTradeSimulated({
          symbol: stock.symbol,
          shares: calculations.actualShares,
          price: entryPrice,
          totalCost: calculations.totalCost,
          tp: targetPrice,
          sl: stopLoss,
        });
      }

      setTimeout(() => {
        setSimulatedSuccess(false);
      }, 3500);
    } catch (err: any) {
      console.error("Failed to execute paper buy:", err);
      setErrorMessage("Failed to write trade to local storage.");
    }
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-[#080d19]/95 p-5 shadow-2xl backdrop-blur-md">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <Calculator className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              Position Sizing Calculator
              <span className="font-mono text-xs px-2 py-0.5 rounded bg-cyan-950/40 text-cyan-300 border border-cyan-800/40">
                {stock.symbol}
              </span>
            </h3>
            <p className="text-[11px] text-slate-400">
              Risk-based capital allocation &amp; virtual paper execution
            </p>
          </div>
        </div>

        <div className="text-right">
          <span className="text-[10px] uppercase font-semibold text-slate-400 block tracking-wider">
            Virtual Cash Available
          </span>
          <span className="font-mono text-sm font-bold text-emerald-400">
            ${balance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        </div>
      </div>

      {/* Inputs Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-4">
        {/* Entry Price */}
        <div>
          <label className="text-[11px] font-semibold text-slate-300 block mb-1">
            Entry Price ($)
          </label>
          <input
            type="number"
            step="0.01"
            value={entryPrice}
            onChange={(e) => {
              setEntryPrice(parseFloat(e.target.value) || 0);
              setManualShares(null);
            }}
            className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-1.5 text-xs font-mono text-slate-100 focus:border-cyan-500 focus:outline-none"
          />
        </div>

        {/* Stop Loss */}
        <div>
          <label className="text-[11px] font-semibold text-rose-300 block mb-1">
            Stop Loss ($)
          </label>
          <input
            type="number"
            step="0.01"
            value={stopLoss}
            onChange={(e) => {
              setStopLoss(parseFloat(e.target.value) || 0);
              setManualShares(null);
            }}
            className="w-full rounded-lg bg-slate-900 border border-rose-900/40 px-3 py-1.5 text-xs font-mono text-rose-200 focus:border-rose-500 focus:outline-none"
          />
        </div>

        {/* Target 1 */}
        <div>
          <label className="text-[11px] font-semibold text-emerald-300 block mb-1">
            Target Price ($)
          </label>
          <input
            type="number"
            step="0.01"
            value={targetPrice}
            onChange={(e) => {
              setTargetPrice(parseFloat(e.target.value) || 0);
            }}
            className="w-full rounded-lg bg-slate-900 border border-emerald-900/40 px-3 py-1.5 text-xs font-mono text-emerald-200 focus:border-emerald-500 focus:outline-none"
          />
        </div>

        {/* Account Risk % */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-[11px] font-semibold text-slate-300">
              Risk % of Acct
            </label>
            <span className="font-mono text-xs font-bold text-cyan-400">
              {riskPct.toFixed(1)}% (${calculations.dollarRiskAllowed.toFixed(0)})
            </span>
          </div>
          <input
            type="range"
            min="0.5"
            max="10.0"
            step="0.5"
            value={riskPct}
            onChange={(e) => {
              setRiskPct(parseFloat(e.target.value));
              setManualShares(null);
            }}
            className="w-full accent-cyan-400 h-2 bg-slate-800 rounded-lg cursor-pointer"
          />
        </div>
      </div>

      {/* Preset Risk Buttons */}
      <div className="flex items-center gap-1.5 mb-4">
        <span className="text-[10px] text-slate-400 uppercase font-semibold mr-1">
          Risk Presets:
        </span>
        {[1.0, 2.0, 3.0, 5.0].map((preset) => (
          <button
            key={preset}
            type="button"
            onClick={() => {
              setRiskPct(preset);
              setManualShares(null);
            }}
            className={`px-2 py-0.5 rounded text-[11px] font-mono transition-colors ${
              riskPct === preset
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                : "bg-slate-800/60 text-slate-400 hover:text-slate-200 border border-slate-700/50"
            }`}
          >
            {preset}%
          </button>
        ))}
      </div>

      {/* Dynamic Sizing Matrix */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4 p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
        <div>
          <span className="text-[10px] text-slate-400 block uppercase font-medium">
            Shares to Buy
          </span>
          <div className="flex items-center gap-1 mt-0.5">
            <input
              type="number"
              min="1"
              value={calculations.actualShares}
              onChange={(e) => setManualShares(Math.max(1, parseInt(e.target.value) || 1))}
              className="w-20 rounded bg-slate-800 border border-slate-700 px-2 py-0.5 font-mono font-bold text-slate-100 text-xs focus:border-cyan-500 focus:outline-none"
            />
            <span className="text-[10px] text-slate-400">shares</span>
          </div>
        </div>

        <div>
          <span className="text-[10px] text-slate-400 block uppercase font-medium">
            Total Position Cost
          </span>
          <span className="font-mono font-bold text-slate-200 text-sm block mt-0.5">
            ${calculations.totalCost.toFixed(2)}
          </span>
          <span className="text-[10px] text-slate-400">
            ({calculations.portfolioAllocationPct.toFixed(1)}% of acct)
          </span>
        </div>

        <div>
          <span className="text-[10px] text-slate-400 block uppercase font-medium">
            Risk at Invalidation
          </span>
          <span className="font-mono font-bold text-rose-400 text-sm block mt-0.5">
            -${(calculations.actualShares * calculations.perShareRisk).toFixed(2)}
          </span>
          <span className="text-[10px] text-slate-400">
            (${calculations.perShareRisk.toFixed(2)}/sh)
          </span>
        </div>

        <div>
          <span className="text-[10px] text-slate-400 block uppercase font-medium">
            Potential Profit (TP1)
          </span>
          <span className="font-mono font-bold text-emerald-400 text-sm block mt-0.5">
            +${calculations.potentialDollarProfit.toFixed(2)}
          </span>
          <span className="text-[10px] text-emerald-300 font-semibold">
            1:{calculations.realizedRR.toFixed(1)} R:R (+{calculations.potentialProfitPct.toFixed(1)}%)
          </span>
        </div>
      </div>

      {/* Warnings & Alerts */}
      {!calculations.isValidStop && (
        <div className="mb-3 p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <span>Invalid Stop Loss: Stop price must be below entry price for long equity positions.</span>
        </div>
      )}

      {calculations.isOverBudget && (
        <div className="mb-3 p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
            <span>Position cost exceeds available virtual balance (${balance.toFixed(2)}).</span>
          </div>
          <button
            type="button"
            onClick={() => setManualShares(calculations.maxAffordableShares)}
            className="px-2 py-1 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 border border-amber-500/40 font-mono text-[11px]"
          >
            Cap to Max ({calculations.maxAffordableShares} sh)
          </button>
        </div>
      )}

      {errorMessage && (
        <div className="mb-3 p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
          {errorMessage}
        </div>
      )}

      {simulatedSuccess && (
        <div className="mb-3 p-2.5 rounded-lg bg-emerald-500/15 border border-emerald-500/40 text-emerald-300 text-xs flex items-center gap-2 shadow-[0_0_15px_rgba(16,185,129,0.2)]">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          <span>
            Simulated Paper Buy Executed! Bought {calculations.actualShares} shares of {stock.symbol} @ ${entryPrice.toFixed(2)} into your paper portfolio.
          </span>
        </div>
      )}

      {/* Execute Actions */}
      <div className="flex items-center gap-2">
        <button
          type="button"
          disabled={!calculations.isValidStop || calculations.actualShares <= 0 || calculations.isOverBudget}
          onClick={handleSimulateBuy}
          className={`flex-1 inline-flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-xs font-bold transition-all shadow-md ${
            !calculations.isValidStop || calculations.actualShares <= 0 || calculations.isOverBudget
              ? "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700"
              : "bg-emerald-600 hover:bg-emerald-500 text-white shadow-[0_0_20px_rgba(16,185,129,0.3)] border border-emerald-400"
          }`}
        >
          <Zap className="w-4 h-4 fill-white" />
          Simulate Paper Buy ({calculations.actualShares} Shares &bull; ${calculations.totalCost.toFixed(2)})
        </button>

        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition-colors"
          >
            Close
          </button>
        )}
      </div>
    </div>
  );
}
