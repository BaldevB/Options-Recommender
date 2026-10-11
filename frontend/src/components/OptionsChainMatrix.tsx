"use client";

import React, { useState, useEffect, useMemo } from "react";
import dynamic from "next/dynamic";
import {
  RefreshCw,
  Search,
  Crosshair,
  TrendingUp,
  TrendingDown,
  Layers,
  Shield,
  HelpCircle,
  Copy,
  Check,
  Zap,
  Wallet,
  CheckCircle2,
} from "lucide-react";

const PayoffChart = dynamic(() => import("@/components/PayoffChart"), {
  ssr: false,
});

interface OptionsChainMatrixProps {
  ticker: string;
  equity: number;
  riskPct: number;
}

export default function OptionsChainMatrix({
  ticker,
  equity,
  riskPct,
}: OptionsChainMatrixProps) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedExp, setSelectedExp] = useState<string>("");
  const [strikeRange, setStrikeRange] = useState<"near" | "all" | "itm" | "otm">("near");
  const [strikeSearch, setStrikeSearch] = useState<string>("");
  const [inspectedOption, setInspectedOption] = useState<any>(null);
  const [copied, setCopied] = useState(false);
  const [chainContracts, setChainContracts] = useState<number>(1);
  const [chainPaperToast, setChainPaperToast] = useState<string | null>(null);

  // Fetch options chain matrix from API
  const fetchChain = async (exp?: string) => {
    setLoading(true);
    setError(null);
    try {
      const url = `/api/options-chain?ticker=${encodeURIComponent(ticker)}${
        exp ? `&expiration=${encodeURIComponent(exp)}` : ""
      }`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`Failed to load options chain for ${ticker}`);
      const json = await res.json();
      if (json.error && (!json.strikes || json.strikes.length === 0)) {
        throw new Error(json.error);
      }
      setData(json);
      if (json.selected_expiration) {
        setSelectedExp(json.selected_expiration);
      }

      // Default inspected option to ATM Call if none selected or ticker changed
      if (json.strikes && json.strikes.length > 0) {
        const atmRow =
          json.strikes.find((s: any) => s.is_atm) ||
          json.strikes[Math.floor(json.strikes.length / 2)];
        if (atmRow?.call) {
          setInspectedOption({
            ...atmRow.call,
            strike: atmRow.strike,
            type: "CALL",
            dte: json.dte,
            expiration: json.selected_expiration,
            spotPrice: json.current_price,
          });
        }
      }
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to load options chain matrix");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChain();
  }, [ticker]);

  const handleExpirationChange = (newExp: string) => {
    setSelectedExp(newExp);
    fetchChain(newExp);
  };

  // Filter strikes based on user selection
  const filteredStrikes = useMemo(() => {
    if (!data?.strikes) return [];
    let list = [...data.strikes];

    // Search filter
    if (strikeSearch.trim()) {
      const q = parseFloat(strikeSearch.trim());
      if (!isNaN(q)) {
        list = list.filter((s) => Math.abs(s.strike - q) < 10);
      }
    }

    const atmIndex = list.findIndex((s) => s.is_atm);
    const validAtmIndex = atmIndex !== -1 ? atmIndex : Math.floor(list.length / 2);

    if (strikeRange === "near") {
      const start = Math.max(0, validAtmIndex - 10);
      const end = Math.min(list.length, validAtmIndex + 11);
      return list.slice(start, end);
    } else if (strikeRange === "itm") {
      // Calls ITM or Puts ITM
      return list.filter((s) => s.is_itm_call || s.is_itm_put);
    } else if (strikeRange === "otm") {
      return list.filter((s) => !s.is_itm_call || !s.is_itm_put);
    }

    return list;
  }, [data?.strikes, strikeRange, strikeSearch]);

  const analytics = data?.analytics || {};
  const spotPrice = data?.current_price || 0;

  const handleSelectContract = (row: any, type: "CALL" | "PUT") => {
    const contractData = type === "CALL" ? row.call : row.put;
    if (!contractData) return;
    setInspectedOption({
      ...contractData,
      strike: row.strike,
      type,
      dte: data?.dte || 0,
      expiration: data?.selected_expiration,
      spotPrice,
    });
  };

  const handleCopySymbol = (sym: string) => {
    if (!sym) return;
    navigator.clipboard.writeText(sym);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Calculate position sizing for inspected contract
  const sizing = useMemo(() => {
    if (!inspectedOption) return { contracts: 1, totalRisk: 0, stopLoss: 0, breakeven: 0 };
    const ask = inspectedOption.ask || inspectedOption.mid || 1;
    const maxLossOne = ask * 100;
    const budget = equity * (riskPct / 100.0);
    const count = Math.max(1, Math.floor(budget / maxLossOne));
    const totalRisk = count * maxLossOne;
    const stopLoss = Math.max(0.01, ask * 0.5);
    const isCall = inspectedOption.type === "CALL";
    const breakeven = isCall ? inspectedOption.strike + ask : inspectedOption.strike - ask;
    return { contracts: count, totalRisk, stopLoss, breakeven };
  }, [inspectedOption, equity, riskPct]);

useEffect(() => {
    if (sizing.contracts) {
      setChainContracts(sizing.contracts);
    }
  }, [sizing.contracts]);

  const handlePaperTradeInspected = () => {
    if (!inspectedOption) return;
    try {
      const askPx = inspectedOption.ask || inspectedOption.mid || 1;
      const cost = askPx * 100 * chainContracts;
      const balanceStr = localStorage.getItem("options_paper_balance");
      const balance = balanceStr ? parseFloat(balanceStr) : 10000;
      if (cost > balance) {
        alert(`Insufficient virtual funds ($${balance.toFixed(2)}) for total cost of $${cost.toFixed(2)}.`);
        return;
      }
      const savedStr = localStorage.getItem("options_paper_positions");
      const positions = savedStr ? JSON.parse(savedStr) : [];
      const newPos = {
        id: `pos-${Date.now()}`,
        ticker: ticker.toUpperCase(),
        contract: inspectedOption.contract,
        optionType: inspectedOption.type,
        strike: inspectedOption.strike,
        expiration: inspectedOption.expiration,
        dte: inspectedOption.dte || 30,
        entryPrice: askPx,
        contracts: chainContracts,
        totalCost: cost,
        enteredAt: new Date().toISOString(),
        currentPrice: askPx,
        status: "OPEN",
        targetProfitPrice: askPx * 1.5,
        stopLossPrice: askPx * 0.5,
        notes: "Executed from Chain Matrix Inspector",
      };
      localStorage.setItem("options_paper_positions", JSON.stringify([newPos, ...positions]));
      localStorage.setItem("options_paper_balance", (balance - cost).toString());
      setChainPaperToast(`Bought ${chainContracts}x ${ticker} $${inspectedOption.strike} ${inspectedOption.type} for $${cost.toFixed(2)}!`);
      setTimeout(() => setChainPaperToast(null), 4000);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6">
      {/* ----------------- TOP CONTROLS & EXPIRATIONS BAR ----------------- */}
      <div className="rounded-2xl border border-slate-800 bg-gradient-to-r from-[#0d1627] via-[#091120] to-[#0a1426] p-5 shadow-2xl">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
          <div className="flex items-center space-x-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
              <Layers className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-xl font-black text-white">
                  {ticker} <span className="text-cyan-400">Options Chain</span>
                </h2>
                <span className="text-base font-bold text-slate-300">
                  ${spotPrice.toFixed(2)}
                </span>
                <span
                  className={`text-xs font-semibold ${
                    (data?.change_pct || 0) >= 0 ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  {(data?.change_pct || 0) >= 0 ? "+" : ""}
                  {(data?.change_pct || 0).toFixed(2)}%
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Full Strike Ladder &bull; Black-Scholes Greeks (&Delta;, &Gamma;, &Theta;, &nu;) &bull; Max Pain &bull; Expected Move
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => fetchChain(selectedExp)}
              disabled={loading}
              className="flex items-center space-x-1.5 rounded-lg border border-slate-700 bg-[#121c2e] px-3 py-1.5 text-xs font-semibold text-slate-200 hover:bg-slate-800 disabled:opacity-50"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-cyan-400" : ""}`} />
              <span>Refresh Chain</span>
            </button>
          </div>
        </div>

        {/* Expirations Horizontally Scrollable Pills */}
        <div className="mt-4 flex items-center space-x-2 overflow-x-auto pb-1 text-xs">
          <span className="shrink-0 font-semibold text-slate-400 uppercase tracking-wider text-[11px]">
            Expirations:
          </span>
          {data?.available_expirations?.map((expItem: any) => {
            const isSelected = expItem.expiration === selectedExp;
            return (
              <button
                key={expItem.expiration}
                onClick={() => handleExpirationChange(expItem.expiration)}
                className={`shrink-0 rounded-lg px-3 py-1.5 text-xs font-bold transition ${
                  isSelected
                    ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/30"
                    : "bg-[#111a2c] text-slate-300 hover:bg-slate-800 hover:text-white border border-slate-800"
                }`}
              >
                {expItem.expiration}
                <span
                  className={`ml-1.5 text-[10px] ${
                    isSelected ? "text-slate-900" : "text-cyan-400 font-normal"
                  }`}
                >
                  ({expItem.dte}d)
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* ----------------- ANALYTICS STRIP (EXPECTED MOVE, MAX PAIN, PCR) ----------------- */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {/* Expected Move */}
        <div className="rounded-xl border border-cyan-500/30 bg-[#0c1424] p-3.5 shadow-lg">
          <div className="flex items-center justify-between text-[11px] text-cyan-400 font-semibold uppercase tracking-wider">
            <span>🎯 Expected Move</span>
            <span className="rounded bg-cyan-950 px-1.5 py-0.5 text-[10px] text-cyan-300">
              {data?.dte} DTE
            </span>
          </div>
          <div className="mt-1 text-lg font-black text-white">
            &plusmn;${analytics.expected_move?.toFixed(2) || "0.00"}
            <span className="ml-1 text-xs font-semibold text-cyan-300">
              (&plusmn;{analytics.expected_move_pct?.toFixed(1) || "0.0"}%)
            </span>
          </div>
          <div className="mt-1 text-[11px] text-slate-400 font-mono">
            Range: ${analytics.expected_range_low?.toFixed(2)} &ndash; ${analytics.expected_range_high?.toFixed(2)}
          </div>
        </div>

        {/* Max Pain Strike */}
        <div className="rounded-xl border border-purple-500/30 bg-[#140e24] p-3.5 shadow-lg">
          <div className="flex items-center justify-between text-[11px] text-purple-400 font-semibold uppercase tracking-wider">
            <span>📌 Max Pain Strike</span>
            <span className="rounded bg-purple-950 px-1.5 py-0.5 text-[10px] text-purple-300">
              Expiry Pin
            </span>
          </div>
          <div className="mt-1 text-lg font-black text-white">
            ${analytics.max_pain?.toFixed(2) || "0.00"}
          </div>
          <div className="mt-1 text-[11px] text-slate-400">
            {spotPrice > (analytics.max_pain || 0)
              ? `$${(spotPrice - (analytics.max_pain || 0)).toFixed(2)} above Max Pain`
              : `$${((analytics.max_pain || 0) - spotPrice).toFixed(2)} below Max Pain`}
          </div>
        </div>

        {/* Put / Call Ratio */}
        <div className="rounded-xl border border-indigo-500/30 bg-[#0d1226] p-3.5 shadow-lg">
          <div className="flex items-center justify-between text-[11px] text-indigo-400 font-semibold uppercase tracking-wider">
            <span>⚖️ Put / Call Ratio</span>
            <span className="rounded bg-indigo-950 px-1.5 py-0.5 text-[10px] text-indigo-300">
              Sentiment
            </span>
          </div>
          <div className="mt-1 text-lg font-black text-white">
            {analytics.pcr_volume?.toFixed(2) || "1.00"}
            <span className="ml-2 text-xs font-semibold text-slate-400">
              (OI: {analytics.pcr_oi?.toFixed(2) || "1.00"})
            </span>
          </div>
          <div className="mt-1 text-[11px] font-semibold text-indigo-300">
            {analytics.pcr_bias || "Neutral"}
          </div>
        </div>

        {/* Total Volumes */}
        <div className="rounded-xl border border-slate-800 bg-[#0c1322] p-3.5 shadow-lg">
          <div className="flex items-center justify-between text-[11px] text-slate-400 font-semibold uppercase tracking-wider">
            <span>📊 Total Chain Volume</span>
            <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-300">
              Flow
            </span>
          </div>
          <div className="mt-1 flex items-baseline justify-between text-xs">
            <span className="font-bold text-emerald-400">
              Calls: {analytics.total_call_volume?.toLocaleString() || 0}
            </span>
            <span className="font-bold text-rose-400">
              Puts: {analytics.total_put_volume?.toLocaleString() || 0}
            </span>
          </div>
          <div className="mt-1.5 text-[10px] text-slate-400 flex justify-between">
            <span>Call OI: {analytics.total_call_oi?.toLocaleString() || 0}</span>
            <span>Put OI: {analytics.total_put_oi?.toLocaleString() || 0}</span>
          </div>
        </div>
      </div>

      {/* ----------------- FILTER AND SEARCH BAR ----------------- */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-800/80 bg-[#0a101d] px-4 py-2.5 text-xs">
        <div className="flex items-center space-x-2">
          <span className="text-slate-400 font-semibold">Strike Filter:</span>
          {(
            [
              { id: "near", label: "Near ATM (&plusmn;10)" },
              { id: "all", label: "All Strikes" },
              { id: "itm", label: "ITM Only" },
              { id: "otm", label: "OTM Only" },
            ] as const
          ).map((filter) => (
            <button
              key={filter.id}
              onClick={() => setStrikeRange(filter.id)}
              className={`rounded-md px-2.5 py-1 text-xs font-semibold transition ${
                strikeRange === filter.id
                  ? "bg-slate-700 text-white"
                  : "bg-slate-900 text-slate-400 hover:text-white"
              }`}
            >
              {filter.label}
            </button>
          ))}
        </div>

        <div className="flex items-center space-x-4">
          <div className="relative w-44">
            <Search className="absolute left-2.5 top-2 h-3.5 w-3.5 text-slate-500" />
            <input
              type="text"
              placeholder="Search strike..."
              value={strikeSearch}
              onChange={(e) => setStrikeSearch(e.target.value)}
              className="w-full rounded-md border border-slate-800 bg-[#080d18] py-1 pl-8 pr-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>

          {/* Color legend */}
          <div className="hidden items-center space-x-3 text-[11px] text-slate-400 sm:flex">
            <span className="flex items-center space-x-1">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              <span>Call ITM</span>
            </span>
            <span className="flex items-center space-x-1">
              <span className="h-2 w-2 rounded-full bg-rose-500" />
              <span>Put ITM</span>
            </span>
            <span className="flex items-center space-x-1">
              <span className="h-2 w-2 rounded-full bg-amber-400" />
              <span>ATM Strike</span>
            </span>
          </div>
        </div>
      </div>

      {/* ----------------- MAIN OPTIONS CHAIN LADDER TABLE ----------------- */}
      <div className="rounded-2xl border border-slate-800 bg-[#090e1a] shadow-2xl overflow-hidden">
        {loading ? (
          <div className="flex h-72 items-center justify-center">
            <div className="text-center text-slate-400 text-sm">
              <RefreshCw className="mx-auto mb-2 h-6 w-6 animate-spin text-cyan-400" />
              Loading complete option chain matrix for {ticker} ({selectedExp})...
            </div>
          </div>
        ) : error ? (
          <div className="p-12 text-center text-sm text-rose-400">
            {error}
          </div>
        ) : filteredStrikes.length === 0 ? (
          <div className="p-12 text-center text-sm text-slate-400">
            No strikes matching your filter.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-center text-xs border-collapse">
              <thead>
                {/* Top Header Label */}
                <tr className="border-b border-slate-800 bg-[#0c1424] text-[11px] uppercase font-bold tracking-wider">
                  <th colSpan={7} className="py-2 text-emerald-400 bg-emerald-950/20 border-r border-slate-800">
                    CALLS (Click to inspect)
                  </th>
                  <th className="py-2 text-white bg-slate-900 border-r border-l border-slate-800">
                    STRIKE
                  </th>
                  <th colSpan={7} className="py-2 text-rose-400 bg-rose-950/20 border-l border-slate-800">
                    PUTS (Click to inspect)
                  </th>
                </tr>

                {/* Column Headers */}
                <tr className="border-b border-slate-800 bg-[#070c17] text-[10px] text-slate-400 font-mono uppercase">
                  {/* Calls columns */}
                  <th className="py-2 px-1 text-right">Delta</th>
                  <th className="py-2 px-1 text-right">Gamma</th>
                  <th className="py-2 px-1 text-right">Theta</th>
                  <th className="py-2 px-1 text-right">IV%</th>
                  <th className="py-2 px-1 text-right">Vol</th>
                  <th className="py-2 px-1 text-right">OI</th>
                  <th className="py-2 px-2 text-right border-r border-slate-800">Bid / Ask</th>

                  {/* Strike center column */}
                  <th className="py-2 px-3 text-center bg-slate-900/60 text-white font-bold border-r border-l border-slate-800">
                    Strike
                  </th>

                  {/* Puts columns */}
                  <th className="py-2 px-2 text-left border-l border-slate-800">Bid / Ask</th>
                  <th className="py-2 px-1 text-left">OI</th>
                  <th className="py-2 px-1 text-left">Vol</th>
                  <th className="py-2 px-1 text-left">IV%</th>
                  <th className="py-2 px-1 text-left">Theta</th>
                  <th className="py-2 px-1 text-left">Gamma</th>
                  <th className="py-2 px-1 text-left">Delta</th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                {filteredStrikes.map((row: any) => {
                  const isAtm = row.is_atm;
                  const isMaxPain = Math.abs(row.strike - (analytics.max_pain || 0)) < 0.01;
                  const c = row.call;
                  const p = row.put;

                  const isInspectedCall =
                    inspectedOption &&
                    inspectedOption.type === "CALL" &&
                    inspectedOption.strike === row.strike;
                  const isInspectedPut =
                    inspectedOption &&
                    inspectedOption.type === "PUT" &&
                    inspectedOption.strike === row.strike;

                  return (
                    <tr
                      key={row.strike}
                      className={`transition ${
                        isAtm
                          ? "bg-amber-950/20 border-y border-amber-500/40"
                          : "hover:bg-slate-800/40"
                      }`}
                    >
                      {/* CALL SIDE */}
                      {c ? (
                        <>
                          <td
                            onClick={() => handleSelectContract(row, "CALL")}
                            className={`py-2 px-1 text-right font-bold cursor-pointer ${
                              isInspectedCall
                                ? "bg-cyan-500/30 text-cyan-200"
                                : row.is_itm_call
                                ? "bg-emerald-950/25 text-emerald-300"
                                : "text-slate-300"
                            }`}
                          >
                            {c.delta > 0 ? "+" : ""}
                            {c.delta.toFixed(3)}
                          </td>
                          <td
                            onClick={() => handleSelectContract(row, "CALL")}
                            className="py-2 px-1 text-right text-slate-400 cursor-pointer"
                          >
                            {c.gamma.toFixed(3)}
                          </td>
                          <td
                            onClick={() => handleSelectContract(row, "CALL")}
                            className="py-2 px-1 text-right text-rose-300/80 cursor-pointer"
                          >
                            ${c.theta.toFixed(2)}
                          </td>
                          <td
                            onClick={() => handleSelectContract(row, "CALL")}
                            className="py-2 px-1 text-right text-slate-300 cursor-pointer"
                          >
                            {c.iv_pct.toFixed(1)}%
                          </td>
                          <td
                            onClick={() => handleSelectContract(row, "CALL")}
                            className="py-2 px-1 text-right text-slate-400 cursor-pointer"
                          >
                            {c.volume.toLocaleString()}
                          </td>
                          <td
                            onClick={() => handleSelectContract(row, "CALL")}
                            className="py-2 px-1 text-right text-slate-400 cursor-pointer"
                          >
                            {c.open_interest.toLocaleString()}
                          </td>
                          <td
                            onClick={() => handleSelectContract(row, "CALL")}
                            className={`py-2 px-2 text-right border-r border-slate-800 font-semibold cursor-pointer ${
                              isInspectedCall ? "bg-cyan-500/30 text-white" : "text-cyan-300"
                            }`}
                          >
                            ${c.bid.toFixed(2)} / ${c.ask.toFixed(2)}
                          </td>
                        </>
                      ) : (
                        <td colSpan={7} className="border-r border-slate-800 text-slate-600">
                          -
                        </td>
                      )}

                      {/* STRIKE CENTER COLUMN */}
                      <td
                        className={`py-2 px-2 font-bold text-center border-r border-l border-slate-800 ${
                          isAtm
                            ? "bg-amber-500/20 text-amber-300 font-black"
                            : isMaxPain
                            ? "bg-purple-900/30 text-purple-200"
                            : "bg-[#0c1322] text-white"
                        }`}
                      >
                        <div className="flex items-center justify-center space-x-1">
                          <span>${row.strike.toFixed(2)}</span>
                          {isAtm && (
                            <span className="rounded bg-amber-400 px-1 py-0.2 text-[9px] font-black text-slate-950">
                              ATM
                            </span>
                          )}
                          {isMaxPain && (
                            <span className="rounded bg-purple-500 px-1 py-0.2 text-[9px] font-black text-white">
                              PAIN
                            </span>
                          )}
                        </div>
                      </td>

                      {/* PUT SIDE */}
                      {p ? (
                        <>
                          <td
                            onClick={() => handleSelectContract(row, "PUT")}
                            className={`py-2 px-2 text-left border-l border-slate-800 font-semibold cursor-pointer ${
                              isInspectedPut ? "bg-cyan-500/30 text-white" : "text-rose-300"
                            }`}
                          >
                            ${p.bid.toFixed(2)} / ${p.ask.toFixed(2)}
                          </td>
                          <td
                            onClick={() => handleSelectContract(row, "PUT")}
                            className="py-2 px-1 text-left text-slate-400 cursor-pointer"
                          >
                            {p.open_interest.toLocaleString()}
                          </td>
                          <td
                            onClick={() => handleSelectContract(row, "PUT")}
                            className="py-2 px-1 text-left text-slate-400 cursor-pointer"
                          >
                            {p.volume.toLocaleString()}
                          </td>
                          <td
                            onClick={() => handleSelectContract(row, "PUT")}
                            className="py-2 px-1 text-left text-slate-300 cursor-pointer"
                          >
                            {p.iv_pct.toFixed(1)}%
                          </td>
                          <td
                            onClick={() => handleSelectContract(row, "PUT")}
                            className="py-2 px-1 text-left text-rose-300/80 cursor-pointer"
                          >
                            ${p.theta.toFixed(2)}
                          </td>
                          <td
                            onClick={() => handleSelectContract(row, "PUT")}
                            className="py-2 px-1 text-left text-slate-400 cursor-pointer"
                          >
                            {p.gamma.toFixed(3)}
                          </td>
                          <td
                            onClick={() => handleSelectContract(row, "PUT")}
                            className={`py-2 px-1 text-left font-bold cursor-pointer ${
                              isInspectedPut
                                ? "bg-cyan-500/30 text-cyan-200"
                                : row.is_itm_put
                                ? "bg-rose-950/25 text-rose-300"
                                : "text-slate-300"
                            }`}
                          >
                            {p.delta.toFixed(3)}
                          </td>
                        </>
                      ) : (
                        <td colSpan={7} className="border-l border-slate-800 text-slate-600">
                          -
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ----------------- CONTRACT INSPECTOR & PAYOFF PROFILE ----------------- */}
      {inspectedOption && (
        <div className="rounded-2xl border border-cyan-500/40 bg-gradient-to-br from-[#0a1426] via-[#091122] to-[#0d172a] p-6 shadow-2xl">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
            <div>
              <div className="flex items-center space-x-2">
                <span
                  className={`rounded px-2.5 py-0.5 text-xs font-black uppercase tracking-wider ${
                    inspectedOption.type === "CALL"
                      ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                      : "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                  }`}
                >
                  {inspectedOption.type} CONTRACT
                </span>
                <span className="text-sm font-bold text-white font-mono">
                  ${inspectedOption.strike.toFixed(2)} STRIKE
                </span>
                <span className="text-xs text-slate-400">
                  Exp: {inspectedOption.expiration} ({inspectedOption.dte}d DTE)
                </span>
              </div>
              <h3 className="mt-1.5 flex items-center space-x-2 text-base font-bold text-slate-200 font-mono">
                <span>{inspectedOption.contract}</span>
                <button
                  onClick={() => handleCopySymbol(inspectedOption.contract)}
                  className="rounded p-1 text-slate-400 hover:text-white"
                  title="Copy contract symbol"
                >
                  {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                </button>
              </h3>
            </div>

            <div className="flex items-center space-x-4 text-xs">
              <div className="text-right">
                <div className="text-slate-400">Bid / Ask</div>
                <div className="text-base font-bold text-white">
                  ${inspectedOption.bid.toFixed(2)} / ${inspectedOption.ask.toFixed(2)}
                </div>
              </div>
              <div className="text-right">
                <div className="text-slate-400">Mid Price</div>
                <div className="text-base font-bold text-cyan-400">
                  ${inspectedOption.mid.toFixed(2)}
                </div>
              </div>
            </div>
          </div>

          <div className="mt-5 grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Greeks & Risk Breakdown */}
            <div className="space-y-4">
              {/* Greeks Cockpit */}
              <div className="rounded-xl border border-slate-800 bg-[#070d18] p-4">
                <h4 className="mb-3 text-xs font-bold uppercase tracking-wider text-cyan-400">
                  Black-Scholes Greeks Cockpit
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div className="rounded-lg bg-[#0e1628] p-2.5">
                    <span className="text-[10px] text-slate-400 block">Delta (&Delta;)</span>
                    <strong className="text-sm font-mono text-cyan-300">
                      {inspectedOption.delta > 0 ? "+" : ""}
                      {inspectedOption.delta.toFixed(3)}
                    </strong>
                    <span className="text-[10px] text-slate-500 block mt-0.5">
                      ~{Math.round(Math.abs(inspectedOption.delta) * 100)} share equiv
                    </span>
                  </div>

                  <div className="rounded-lg bg-[#0e1628] p-2.5">
                    <span className="text-[10px] text-slate-400 block">Gamma (&Gamma;)</span>
                    <strong className="text-sm font-mono text-indigo-300">
                      {inspectedOption.gamma.toFixed(4)}
                    </strong>
                    <span className="text-[10px] text-slate-500 block mt-0.5">&Delta; per $1 move</span>
                  </div>

                  <div className="rounded-lg bg-[#0e1628] p-2.5">
                    <span className="text-[10px] text-slate-400 block">Theta (&Theta;)</span>
                    <strong className="text-sm font-mono text-rose-400">
                      ${inspectedOption.theta.toFixed(3)}
                    </strong>
                    <span className="text-[10px] text-slate-500 block mt-0.5">Decay per day</span>
                  </div>

                  <div className="rounded-lg bg-[#0e1628] p-2.5">
                    <span className="text-[10px] text-slate-400 block">Vega (&nu;)</span>
                    <strong className="text-sm font-mono text-amber-300">
                      ${inspectedOption.vega.toFixed(3)}
                    </strong>
                    <span className="text-[10px] text-slate-500 block mt-0.5">Per 1% IV shift</span>
                  </div>
                </div>
              </div>

              {/* Sizing & Capital Plan */}
              <div className="rounded-xl border border-slate-800 bg-[#070d18] p-4 text-xs">
                <h4 className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-300">
                  Disciplined Trade Sizing (Equity: ${equity.toLocaleString()} &bull; Risk: {riskPct}%)
                </h4>
                <div className="grid grid-cols-2 gap-2 text-slate-300">
                  <div>
                    Suggested Sizing:{" "}
                    <strong className="text-cyan-400 font-bold">
                      {sizing.contracts} Contract{sizing.contracts > 1 ? "s" : ""}
                    </strong>
                  </div>
                  <div>
                    Max Capital Risk:{" "}
                    <strong className="text-rose-400 font-bold">
                      ${sizing.totalRisk.toFixed(0)}
                    </strong>
                  </div>
                  <div>
                    Breakeven at Expiry:{" "}
                    <strong className="text-amber-400 font-bold">
                      ${sizing.breakeven.toFixed(2)}
                    </strong>
                  </div>
                  <div>
                    50% Stop-Loss:{" "}
                    <strong className="text-white font-bold">
                      ${sizing.stopLoss.toFixed(2)}
                    </strong>
                  </div>
                </div>

                {/* Paper Trade with Amount of Contracts Controls */}
                <div className="mt-3 pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-[11px] font-semibold text-slate-300">Contracts:</span>
                    <div className="flex items-center rounded border border-slate-700 bg-slate-900 px-1 py-0.5">
                      <button
                        type="button"
                        onClick={() => setChainContracts((c) => Math.max(1, c - 1))}
                        className="h-5 w-5 rounded bg-slate-800 text-xs font-bold text-slate-200 hover:text-white"
                      >
                        -
                      </button>
                      <input
                        type="number"
                        min="1"
                        max="500"
                        value={chainContracts}
                        onChange={(e) => setChainContracts(Math.max(1, parseInt(e.target.value) || 1))}
                        className="h-5 w-10 bg-transparent text-center font-mono text-xs font-bold text-cyan-300 focus:outline-none"
                      />
                      <button
                        type="button"
                        onClick={() => setChainContracts((c) => Math.min(500, c + 1))}
                        className="h-5 w-5 rounded bg-slate-800 text-xs font-bold text-slate-200 hover:text-white"
                      >
                        +
                      </button>
                    </div>
                    <span className="text-[11px] font-mono text-slate-400">
                      = ${(chainContracts * 100 * (inspectedOption.ask || inspectedOption.mid || 1)).toFixed(2)}
                    </span>
                  </div>

                  <button
                    type="button"
                    onClick={handlePaperTradeInspected}
                    className="flex items-center space-x-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 active:scale-95 px-3 py-1.5 text-xs font-black text-slate-950 transition shadow-sm"
                  >
                    <Wallet className="h-3.5 w-3.5" />
                    <span>Paper Trade ({chainContracts}x)</span>
                  </button>
                </div>

                {chainPaperToast && (
                  <div className="mt-2 flex items-center space-x-1.5 text-[11px] text-emerald-400 font-bold bg-emerald-950/40 border border-emerald-500/30 rounded-lg p-2">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    <span>{chainPaperToast}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Interactive Expiration Payoff Curve */}
            <div>
              <PayoffChart
                spotPrice={spotPrice}
                strike={inspectedOption.strike}
                askPrice={inspectedOption.ask || inspectedOption.mid || 1}
                optionType={inspectedOption.type}
                breakeven={sizing.breakeven}
                contracts={sizing.contracts}
                dte={inspectedOption.dte || data?.dte || 30}
                iv={inspectedOption.iv_pct || 35.0}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
