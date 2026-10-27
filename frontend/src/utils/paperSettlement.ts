/**
 * Options Paper Trading Expiration and Cash Settlement Engine.
 *
 * Implements standard US equity options expiration rules:
 * - Options expire at 4:00 PM Eastern Time on their expiration date.
 * - In-The-Money (ITM) options are exercised/cash-settled for intrinsic value:
 *     Call Intrinsic = Math.max(0, spot - strike)
 *     Put Intrinsic  = Math.max(0, strike - spot)
 *     Payout = Intrinsic * 100 * contracts
 *     Realized P&L = Payout - totalCost
 *     Cash balance is credited by Payout.
 * - Out-of-The-Money (OTM / ATM) options expire worthless:
 *     Intrinsic = 0.00
 *     Payout = $0.00
 *     Realized P&L = -totalCost (100% loss of premium)
 *     Cash balance receives $0.00.
 */

export interface PaperTradePosition {
  id: string;
  ticker: string;
  contract: string;
  assetType?: "STOCK" | "OPTION" | string;
  optionType?: "CALL" | "PUT" | "STOCK" | string;
  strike?: number;
  expiration?: string; // Format: YYYY-MM-DD
  dte?: number;
  entryPrice: number; // premium per share bought
  contracts: number; // for options: contract count (x100 multiplier)
  shares?: number; // for stocks: share count
  multiplier?: number;
  totalCost: number; // initial invested capital
  enteredAt: string; // ISO timestamp
  currentPrice: number; // current market price
  status: "OPEN" | "CLOSED";
  closedAt?: string;
  exitPrice?: number;
  realizedPnl?: number;
  targetProfitPrice?: number;
  stopLossPrice?: number;
  notes?: string;
  // Settlement extensions
  settlementType?: "MANUAL" | "EXPIRED_ITM" | "EXPIRED_WORTHLESS";
  underlyingSpotAtExpiry?: number;
}

export interface SettlementSummary {
  updatedPositions: PaperTradePosition[];
  newCashBalance: number;
  settledCount: number;
  itmCount: number;
  worthlessCount: number;
  totalPayout: number;
  summaryMessage: string | null;
}

export interface ConsolidatePositionResult {
  updatedPositions: PaperTradePosition[];
  consolidated: boolean;
  totalQty: number;
  weightedPrice: number;
  existingId?: string;
}

/**
 * Check whether an expiration date (YYYY-MM-DD) has reached or passed 4:00 PM US Eastern Time.
 */
export function isOptionExpired(expirationStr?: string): boolean {
  if (!expirationStr) return false;
  try {
    const cleanStr = expirationStr.trim().slice(0, 10);
    const parts = cleanStr.split("-").map(Number);
    if (parts.length !== 3 || parts.some(isNaN)) return false;
    const [year, month, day] = parts;

    // Get current time in America/New_York (US Eastern Time)
    const formatter = new Intl.DateTimeFormat("en-US", {
      timeZone: "America/New_York",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });

    const formattedET = formatter.format(new Date());
    // Format is typically "MM/DD/YYYY, HH:mm" or "MM/DD/YYYY HH:mm"
    const match = formattedET.match(/(\d{2})\/(\d{2})\/(\d{4})[,\s]+(\d{2}):(\d{2})/);
    if (!match) {
      // Fallback: compare against UTC-4
      const nowUtc = new Date();
      const nowEtHours = nowUtc.getUTCHours() - 4;
      const nowEtDate = new Date(nowUtc.getTime() - 4 * 3600 * 1000);
      const expDate = new Date(Date.UTC(year, month - 1, day, 20, 0, 0)); // 4 PM ET is 20:00 UTC
      return nowUtc.getTime() >= expDate.getTime();
    }

    const curMonth = Number(match[1]);
    const curDay = Number(match[2]);
    const curYear = Number(match[3]);
    const curHour = Number(match[4]);

    const curDateScore = curYear * 10000 + curMonth * 100 + curDay;
    const expDateScore = year * 10000 + month * 100 + day;

    if (curDateScore > expDateScore) {
      return true;
    }
    if (curDateScore === expDateScore && curHour >= 16) {
      // Market closed at 4:00 PM ET on expiration day
      return true;
    }
    return false;
  } catch (err) {
    console.error("Error evaluating isOptionExpired:", err);
    return false;
  }
}

/**
 * Calculate intrinsic cash settlement for an option position given underlying spot price.
 */
export function calculateOptionSettlement(
  position: PaperTradePosition,
  spotPrice?: number
): {
  intrinsic: number;
  payout: number;
  realizedPnl: number;
  isItm: boolean;
  settlementType: "EXPIRED_ITM" | "EXPIRED_WORTHLESS";
} {
  const isPut = String(position.optionType || "").toUpperCase() === "PUT";
  const strike = position.strike ?? 0;
  const spot = spotPrice !== undefined && spotPrice > 0 ? spotPrice : strike;
  const contracts = position.contracts > 0 ? position.contracts : 1;

  let intrinsic = 0;
  if (isPut) {
    intrinsic = Math.max(0, strike - spot);
  } else {
    intrinsic = Math.max(0, spot - strike);
  }

  intrinsic = Number(intrinsic.toFixed(2));
  const isItm = intrinsic > 0;
  const payout = Number((intrinsic * 100 * contracts).toFixed(2));
  const realizedPnl = Number((payout - position.totalCost).toFixed(2));
  const settlementType: "EXPIRED_ITM" | "EXPIRED_WORTHLESS" = isItm
    ? "EXPIRED_ITM"
    : "EXPIRED_WORTHLESS";

  return {
    intrinsic,
    payout,
    realizedPnl,
    isItm,
    settlementType,
  };
}

/**
 * Scan all open positions, detect expired option contracts, and settle them into cash.
 */
export function settleExpiredPositions(
  positions: PaperTradePosition[],
  currentCash: number,
  quotes?: Record<string, any>
): SettlementSummary {
  let newCash = currentCash;
  let settledCount = 0;
  let itmCount = 0;
  let worthlessCount = 0;
  let totalPayout = 0;
  const settledDetails: string[] = [];

  const updatedPositions = positions.map((p) => {
    // Only open option positions can expire
    const isStock = p.assetType === "STOCK" || p.optionType === "STOCK" || p.multiplier === 1;
    if (p.status !== "OPEN" || isStock) {
      return p;
    }

    const quote = quotes ? (quotes[p.contract] || quotes[p.ticker]) : null;
    const expiredByDate = isOptionExpired(p.expiration);
    const expiredByBackend = !!quote?.is_expired;

    if (!expiredByDate && !expiredByBackend) {
      return p;
    }

    // Determine spot price
    const spot =
      quote?.underlying_spot ||
      (quotes && quotes[p.ticker]?.current_price) ||
      p.currentPrice ||
      p.strike ||
      0;

    // Settlement price from quote if provided, otherwise compute intrinsic
    let settlementPrice = 0;
    let settlementType: "EXPIRED_ITM" | "EXPIRED_WORTHLESS" = "EXPIRED_WORTHLESS";
    let payout = 0;
    let realizedPnl = 0;

    if (quote?.settlement_price !== undefined && quote?.settlement_price !== null) {
      settlementPrice = Number(quote.settlement_price);
      settlementType = (quote.settlement_type as any) || (settlementPrice > 0 ? "EXPIRED_ITM" : "EXPIRED_WORTHLESS");
      payout = Number((settlementPrice * 100 * p.contracts).toFixed(2));
      realizedPnl = Number((payout - p.totalCost).toFixed(2));
    } else {
      const calc = calculateOptionSettlement(p, spot);
      settlementPrice = calc.intrinsic;
      settlementType = calc.settlementType;
      payout = calc.payout;
      realizedPnl = calc.realizedPnl;
    }

    settledCount += 1;
    totalPayout += payout;
    newCash += payout;

    if (settlementType === "EXPIRED_ITM") {
      itmCount += 1;
      settledDetails.push(`${p.ticker} ${p.strike} ${p.optionType} settled ITM (+$${payout.toFixed(2)} cash)`);
    } else {
      worthlessCount += 1;
      settledDetails.push(`${p.ticker} ${p.strike} ${p.optionType} expired worthless (-$${p.totalCost.toFixed(2)})`);
    }

    return {
      ...p,
      status: "CLOSED" as const,
      closedAt: new Date().toISOString(),
      exitPrice: settlementPrice,
      realizedPnl,
      settlementType,
      underlyingSpotAtExpiry: spot,
      notes: `${p.notes ? `${p.notes} | ` : ""}Auto-expired on ${p.expiration || "session close"} at spot $${spot.toFixed(2)}`,
    };
  });

  let summaryMessage: string | null = null;
  if (settledCount > 0) {
    summaryMessage = `Auto-settled ${settledCount} expired option ${
      settledCount === 1 ? "position" : "positions"
    }: ${settledDetails.join("; ")}. Total payout added to cash: $${totalPayout.toFixed(2)}.`;
  }

  return {
    updatedPositions,
    newCashBalance: Number(newCash.toFixed(2)),
    settledCount,
    itmCount,
    worthlessCount,
    totalPayout: Number(totalPayout.toFixed(2)),
    summaryMessage,
  };
}

/**
 * Manually expire and cash-settle a specific position (useful for immediate settlement or simulation).
 */
export function settleSinglePosition(
  posId: string,
  positions: PaperTradePosition[],
  currentCash: number,
  spotOverride?: number
): SettlementSummary {
  const target = positions.find((p) => p.id === posId);
  if (!target || target.status !== "OPEN") {
    return {
      updatedPositions: positions,
      newCashBalance: currentCash,
      settledCount: 0,
      itmCount: 0,
      worthlessCount: 0,
      totalPayout: 0,
      summaryMessage: null,
    };
  }

  const isStock = target.assetType === "STOCK" || target.optionType === "STOCK" || target.multiplier === 1;
  if (isStock) {
    // Regular stock close
    const qty = target.shares || target.contracts || 1;
    const px = spotOverride !== undefined ? spotOverride : target.currentPrice;
    const proceeds = Number((px * qty).toFixed(2));
    const realizedPnl = Number((proceeds - target.totalCost).toFixed(2));
    const updatedPositions = positions.map((p) =>
      p.id === posId
        ? {
            ...p,
            status: "CLOSED" as const,
            closedAt: new Date().toISOString(),
            exitPrice: px,
            realizedPnl,
            settlementType: "MANUAL" as const,
          }
        : p
    );
    return {
      updatedPositions,
      newCashBalance: Number((currentCash + proceeds).toFixed(2)),
      settledCount: 1,
      itmCount: realizedPnl > 0 ? 1 : 0,
      worthlessCount: realizedPnl <= 0 ? 1 : 0,
      totalPayout: proceeds,
      summaryMessage: `Closed stock position in ${target.ticker} at $${px.toFixed(2)}.`,
    };
  }

  // Options Settlement
  const spot = spotOverride !== undefined && spotOverride > 0 ? spotOverride : target.currentPrice || target.strike || 0;
  const calc = calculateOptionSettlement(target, spot);
  const newCash = Number((currentCash + calc.payout).toFixed(2));

  const updatedPositions = positions.map((p) =>
    p.id === posId
      ? {
          ...p,
          status: "CLOSED" as const,
          closedAt: new Date().toISOString(),
          exitPrice: calc.intrinsic,
          realizedPnl: calc.realizedPnl,
          settlementType: calc.settlementType,
          underlyingSpotAtExpiry: spot,
          notes: `${p.notes ? `${p.notes} | ` : ""}Settled at expiry on spot $${spot.toFixed(2)}`,
        }
      : p
  );

  const message =
    calc.settlementType === "EXPIRED_ITM"
      ? `💎 Expired ITM: ${target.ticker} ${target.strike} ${target.optionType} exercised at spot $${spot.toFixed(
          2
        )}. Cash payout: +$${calc.payout.toFixed(2)} (P&L: ${calc.realizedPnl >= 0 ? "+" : ""}$${calc.realizedPnl.toFixed(2)}).`
      : `💀 Expired Worthless: ${target.ticker} ${target.strike} ${target.optionType} expired at spot $${spot.toFixed(
          2
        )}. Loss: -$${target.totalCost.toFixed(2)}.`;

  return {
    updatedPositions,
    newCashBalance: newCash,
    settledCount: 1,
    itmCount: calc.isItm ? 1 : 0,
    worthlessCount: calc.isItm ? 0 : 1,
    totalPayout: calc.payout,
    summaryMessage: message,
  };
}

/**
 * Returns a canonical consolidation key for matching duplicate open positions.
 */
export function getPositionConsolidationKey(p: Partial<PaperTradePosition>): string {
  const ticker = (p.ticker || "").trim().toUpperCase();
  const isStock = p.assetType === "STOCK" || p.optionType === "STOCK" || p.multiplier === 1;
  if (isStock) {
    return `STOCK:${ticker}`;
  }

  let optType = (p.optionType || "").trim().toUpperCase();
  let strikeNum = p.strike !== undefined ? Number(p.strike) : undefined;
  let exp = (p.expiration || "").trim().slice(0, 10);

  // If missing fields, attempt parsing from contract symbol
  if (p.contract) {
    const rawContract = p.contract.trim().toUpperCase();
    if (rawContract.includes("SPREAD") || rawContract.includes("DEBIT") || rawContract.includes("CREDIT")) {
      return `SPREAD:${ticker}:${rawContract}:${exp}`;
    }

    const occMatch = rawContract.match(/^([A-Z]+)(\d{2})(\d{2})(\d{2})([CP])(\d{8})$/);
    if (occMatch) {
      if (!optType) optType = occMatch[5] === "C" ? "CALL" : "PUT";
      if (!exp || exp === "EQUITY") {
        exp = `20${occMatch[2]}-${occMatch[3]}-${occMatch[4]}`;
      }
      if (strikeNum === undefined || isNaN(strikeNum)) {
        strikeNum = parseInt(occMatch[6], 10) / 1000;
      }
    }
  }

  const strikeStr = strikeNum !== undefined && !isNaN(strikeNum) ? strikeNum.toFixed(2) : "0.00";
  return `OPTION:${ticker}:${optType || "CALL"}:${strikeStr}:${exp}`;
}

/**
 * Merges an incoming buy into an existing OPEN position if one matches,
 * accumulating contract/share count and computing the weighted average entry price.
 * If no matching open position is found, prepends the new position.
 */
export function addOrConsolidatePosition(
  existingPositions: PaperTradePosition[],
  newPos: PaperTradePosition
): ConsolidatePositionResult {
  const isStock = newPos.assetType === "STOCK" || newPos.optionType === "STOCK" || newPos.multiplier === 1;
  const newKey = getPositionConsolidationKey(newPos);

  const existingIndex = existingPositions.findIndex(
    (p) => p.status === "OPEN" && getPositionConsolidationKey(p) === newKey
  );

  if (existingIndex === -1) {
    return {
      updatedPositions: [newPos, ...existingPositions],
      consolidated: false,
      totalQty: isStock ? (newPos.shares || newPos.contracts || 1) : newPos.contracts,
      weightedPrice: newPos.entryPrice,
    };
  }

  const existing = existingPositions[existingIndex];
  let totalQty = 0;
  let weightedPrice = 0;
  const newTotalCost = Number((existing.totalCost + newPos.totalCost).toFixed(2));

  let merged: PaperTradePosition;

  if (isStock) {
    const existingShares = existing.shares || existing.contracts || 1;
    const addedShares = newPos.shares || newPos.contracts || 1;
    totalQty = existingShares + addedShares;
    weightedPrice = totalQty > 0 ? Number((newTotalCost / totalQty).toFixed(4)) : newPos.entryPrice;

    merged = {
      ...existing,
      shares: totalQty,
      contracts: totalQty,
      totalCost: newTotalCost,
      entryPrice: weightedPrice,
      currentPrice: newPos.currentPrice || newPos.entryPrice || existing.currentPrice,
      targetProfitPrice: newPos.targetProfitPrice || existing.targetProfitPrice,
      stopLossPrice: newPos.stopLossPrice || existing.stopLossPrice,
      notes: `${existing.notes ? `${existing.notes} | ` : ""}Added ${addedShares} sh @ $${newPos.entryPrice.toFixed(2)}`,
    };
  } else {
    const existingContracts = existing.contracts > 0 ? existing.contracts : 1;
    const addedContracts = newPos.contracts > 0 ? newPos.contracts : 1;
    totalQty = existingContracts + addedContracts;
    weightedPrice = totalQty > 0 ? Number((newTotalCost / (totalQty * 100)).toFixed(4)) : newPos.entryPrice;

    merged = {
      ...existing,
      contracts: totalQty,
      totalCost: newTotalCost,
      entryPrice: weightedPrice,
      currentPrice: newPos.currentPrice || newPos.entryPrice || existing.currentPrice,
      targetProfitPrice: newPos.targetProfitPrice || existing.targetProfitPrice,
      stopLossPrice: newPos.stopLossPrice || existing.stopLossPrice,
      notes: `${existing.notes ? `${existing.notes} | ` : ""}Added ${addedContracts}x @ $${newPos.entryPrice.toFixed(2)}`,
    };
  }

  const updatedPositions = [...existingPositions];
  updatedPositions[existingIndex] = merged;

  return {
    updatedPositions,
    consolidated: true,
    totalQty,
    weightedPrice,
    existingId: existing.id,
  };
}

/**
 * Scans an array of positions and consolidates any duplicate OPEN positions into
 * single rows with weighted average entry price. Preserves CLOSED positions as distinct records.
 */
export function consolidateOpenPositions(
  positions: PaperTradePosition[]
): { consolidatedPositions: PaperTradePosition[]; hasChanges: boolean } {
  let hasChanges = false;
  const result: PaperTradePosition[] = [];
  const openKeyToIndex = new Map<string, number>();

  for (const pos of positions) {
    if (pos.status !== "OPEN") {
      result.push(pos);
      continue;
    }

    const key = getPositionConsolidationKey(pos);
    if (!openKeyToIndex.has(key)) {
      openKeyToIndex.set(key, result.length);
      result.push({ ...pos });
    } else {
      hasChanges = true;
      const targetIdx = openKeyToIndex.get(key)!;
      const existing = result[targetIdx];
      const isStock = pos.assetType === "STOCK" || pos.optionType === "STOCK" || pos.multiplier === 1;

      const combinedCost = Number((existing.totalCost + pos.totalCost).toFixed(2));

      if (isStock) {
        const existingShares = existing.shares || existing.contracts || 1;
        const addShares = pos.shares || pos.contracts || 1;
        const totalShares = existingShares + addShares;
        const avgPrice = totalShares > 0 ? Number((combinedCost / totalShares).toFixed(4)) : pos.entryPrice;

        result[targetIdx] = {
          ...existing,
          shares: totalShares,
          contracts: totalShares,
          totalCost: combinedCost,
          entryPrice: avgPrice,
          currentPrice: pos.currentPrice || existing.currentPrice,
          targetProfitPrice: pos.targetProfitPrice || existing.targetProfitPrice,
          stopLossPrice: pos.stopLossPrice || existing.stopLossPrice,
          notes: `${existing.notes ? `${existing.notes} | ` : ""}Merged ${addShares} sh @ $${pos.entryPrice.toFixed(2)}`,
        };
      } else {
        const existingContracts = existing.contracts > 0 ? existing.contracts : 1;
        const addContracts = pos.contracts > 0 ? pos.contracts : 1;
        const totalContracts = existingContracts + addContracts;
        const avgPrice = totalContracts > 0 ? Number((combinedCost / (totalContracts * 100)).toFixed(4)) : pos.entryPrice;

        result[targetIdx] = {
          ...existing,
          contracts: totalContracts,
          totalCost: combinedCost,
          entryPrice: avgPrice,
          currentPrice: pos.currentPrice || existing.currentPrice,
          targetProfitPrice: pos.targetProfitPrice || existing.targetProfitPrice,
          stopLossPrice: pos.stopLossPrice || existing.stopLossPrice,
          notes: `${existing.notes ? `${existing.notes} | ` : ""}Merged ${addContracts}x @ $${pos.entryPrice.toFixed(2)}`,
        };
      }
    }
  }

  return { consolidatedPositions: result, hasChanges };
}
