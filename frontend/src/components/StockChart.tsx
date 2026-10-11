"use client";

import React, { useEffect, useRef, useState } from "react";
import { createChart, ColorType, IChartApi, ISeriesApi, LineStyle } from "lightweight-charts";
import { RefreshCw, Maximize2, Activity } from "lucide-react";

export interface CandleData {
  time: string | number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  sma20?: number | null;
  sma50?: number | null;
  vwap?: number | null;
}

interface StockChartProps {
  symbol: string;
  data: CandleData[];
}

interface TimeframeOption {
  id: string;
  label: string;
  name: string;
  period: string;
  isIntraday: boolean;
}

const TIMEFRAMES: TimeframeOption[] = [
  { id: "1m", label: "1m", name: "1m Scalp (1d)", period: "1d", isIntraday: true },
  { id: "5m", label: "5m", name: "5m Intraday (5d)", period: "5d", isIntraday: true },
  { id: "15m", label: "15m", name: "15m Momentum (5d)", period: "5d", isIntraday: true },
  { id: "1h", label: "1h", name: "1h Hourly (1mo)", period: "1mo", isIntraday: true },
  { id: "1d", label: "1D", name: "Daily Swing (6mo)", period: "6mo", isIntraday: false },
  { id: "1wk", label: "1W", name: "Weekly Macro (1y)", period: "1y", isIntraday: false },
];

export default function StockChart({ symbol, data }: StockChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  // Timeframe and data states
  const [activeInterval, setActiveInterval] = useState<string>("1d");
  const [candles, setCandles] = useState<CandleData[]>(data || []);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Indicator overlay toggles
  const [showSma20, setShowSma20] = useState<boolean>(true);
  const [showSma50, setShowSma50] = useState<boolean>(true);
  const [showVwap, setShowVwap] = useState<boolean>(true);

  // Hovered / latest candle for real-time legend
  const [hoveredCandle, setHoveredCandle] = useState<CandleData | null>(null);

  // Sync with incoming parent data when symbol changes
  useEffect(() => {
    setActiveInterval("1d");
    setCandles(data || []);
    setError(null);
  }, [symbol, data]);

  // Fetch smaller or larger timeframes on demand
  const handleTimeframeChange = async (tf: TimeframeOption) => {
    if (activeInterval === tf.id && candles.length > 0) return;
    setActiveInterval(tf.id);
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(
        `/api/candles?ticker=${encodeURIComponent(symbol)}&interval=${tf.id}&period=${tf.period}`
      );
      if (!res.ok) {
        throw new Error(`Failed to fetch ${tf.label} data`);
      }
      const json = await res.json();
      if (json.candles && json.candles.length > 0) {
        setCandles(json.candles);
      } else {
        throw new Error(`No ${tf.label} bars available`);
      }
    } catch (err: any) {
      console.error(err);
      setError(err.message || `Failed to load ${tf.label} timeframe`);
    } finally {
      setLoading(false);
    }
  };

  // Re-render chart on container, data, or indicator changes
  useEffect(() => {
    if (!chartContainerRef.current || !candles || candles.length === 0) return;

    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }

    const container = chartContainerRef.current;
    const currentTf = TIMEFRAMES.find((t) => t.id === activeInterval) || TIMEFRAMES[4];

    const chart = createChart(container, {
      width: container.clientWidth,
      height: 480,
      layout: {
        background: { type: ColorType.Solid, color: "#0c1322" },
        textColor: "#94a3b8",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "rgba(255, 255, 255, 0.04)" },
        horzLines: { color: "rgba(255, 255, 255, 0.04)" },
      },
      crosshair: {
        vertLine: {
          color: "#38bdf8",
          width: 1,
          style: LineStyle.Dashed,
          labelBackgroundColor: "#0284c7",
        },
        horzLine: {
          color: "#38bdf8",
          width: 1,
          style: LineStyle.Dashed,
          labelBackgroundColor: "#0284c7",
        },
      },
      timeScale: {
        borderColor: "rgba(255, 255, 255, 0.08)",
        timeVisible: currentTf.isIntraday,
        secondsVisible: false,
      },
      rightPriceScale: {
        borderColor: "rgba(255, 255, 255, 0.08)",
        scaleMargins: {
          top: 0.1,
          bottom: 0.22,
        },
      },
    });

    chartRef.current = chart;

    // 1. Candlestick Series
    const candleSeries = chart.addCandlestickSeries({
      upColor: "#10b981",
      downColor: "#ef4444",
      borderVisible: false,
      wickUpColor: "#10b981",
      wickDownColor: "#ef4444",
    });

    const candleFormatted = candles.map((d) => ({
      time: d.time as any,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    }));
    candleSeries.setData(candleFormatted);

    // 2. Volume Histogram Series
    const volumeSeries = chart.addHistogramSeries({
      color: "#26a69a",
      priceFormat: {
        type: "volume",
      },
      priceScaleId: "",
    });
    volumeSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

    const volumeFormatted = candles.map((d) => ({
      time: d.time as any,
      value: d.volume,
      color: d.close >= d.open ? "rgba(16, 185, 129, 0.35)" : "rgba(239, 68, 68, 0.35)",
    }));
    volumeSeries.setData(volumeFormatted);

    // 3. SMA 20 Overlay Line
    if (showSma20) {
      const sma20Data = candles
        .filter((d) => d.sma20 !== null && d.sma20 !== undefined)
        .map((d) => ({
          time: d.time as any,
          value: d.sma20 as number,
        }));

      if (sma20Data.length > 0) {
        const sma20Series = chart.addLineSeries({
          color: "#00d2ff",
          lineWidth: 2,
          title: "SMA 20",
        });
        sma20Series.setData(sma20Data);
      }
    }

    // 4. SMA 50 Overlay Line
    if (showSma50) {
      const sma50Data = candles
        .filter((d) => d.sma50 !== null && d.sma50 !== undefined)
        .map((d) => ({
          time: d.time as any,
          value: d.sma50 as number,
        }));

      if (sma50Data.length > 0) {
        const sma50Series = chart.addLineSeries({
          color: "#a855f7",
          lineWidth: 2,
          title: "SMA 50",
        });
        sma50Series.setData(sma50Data);
      }
    }

    // 5. VWAP Overlay Line (for intraday)
    if (showVwap && currentTf.isIntraday) {
      const vwapData = candles
        .filter((d) => d.vwap !== null && d.vwap !== undefined)
        .map((d) => ({
          time: d.time as any,
          value: d.vwap as number,
        }));

      if (vwapData.length > 0) {
        const vwapSeries = chart.addLineSeries({
          color: "#f59e0b",
          lineWidth: 2,
          lineStyle: LineStyle.Dotted,
          title: "VWAP",
        });
        vwapSeries.setData(vwapData);
      }
    }

    chart.timeScale().fitContent();

    // Crosshair hover subscription for real-time legend
    chart.subscribeCrosshairMove((param) => {
      if (param.time) {
        const match = candles.find((c) => String(c.time) === String(param.time));
        if (match) {
          setHoveredCandle(match);
          return;
        }
      }
      setHoveredCandle(null);
    });

    // Resize Handler
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [candles, activeInterval, showSma20, showSma50, showVwap]);

  // Current display candle: either hovered or latest in series
  const activeCandle = hoveredCandle || (candles.length > 0 ? candles[candles.length - 1] : null);
  const activeChange = activeCandle ? activeCandle.close - activeCandle.open : 0;
  const activeChangePct = activeCandle && activeCandle.open > 0 ? (activeChange / activeCandle.open) * 100 : 0;
  const currentTf = TIMEFRAMES.find((t) => t.id === activeInterval) || TIMEFRAMES[4];

  return (
    <div className="relative w-full rounded-xl border border-slate-800 bg-[#0c1322] p-4 shadow-2xl">
      {/* Top Header: Symbol, Timeframe Buttons, and Indicators Bar */}
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
        {/* Left: Symbol & Timeframe Switcher Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center space-x-1.5 mr-2">
            <span className="text-sm font-extrabold tracking-wider text-white">
              {symbol}
            </span>
            <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] font-mono text-slate-400">
              USD
            </span>
          </div>

          {/* Timeframe Buttons: 1m, 5m, 15m, 1h, 1D, 1W */}
          <div className="flex items-center rounded-lg border border-slate-700/80 bg-[#080d18] p-0.5 shadow-inner">
            {TIMEFRAMES.map((tf) => {
              const isActive = activeInterval === tf.id;
              return (
                <button
                  key={tf.id}
                  onClick={() => handleTimeframeChange(tf)}
                  disabled={loading}
                  title={tf.name}
                  className={`rounded px-2.5 py-1 text-xs font-bold transition-all ${
                    isActive
                      ? "bg-cyan-500 text-black shadow-md shadow-cyan-500/30 scale-105"
                      : "text-slate-400 hover:text-white hover:bg-slate-800/60"
                  } disabled:opacity-50`}
                >
                  {tf.label}
                </button>
              );
            })}
          </div>

          {/* Indicator Toggles */}
          <div className="flex items-center space-x-1 ml-1 text-[11px]">
            <button
              onClick={() => setShowSma20(!showSma20)}
              className={`flex items-center space-x-1 rounded px-2 py-0.5 transition ${
                showSma20 ? "bg-[#00d2ff]/20 text-cyan-300 border border-[#00d2ff]/40" : "text-slate-500"
              }`}
            >
              <span className="inline-block h-2 w-2 rounded-full bg-[#00d2ff]" />
              <span>SMA20</span>
            </button>

            <button
              onClick={() => setShowSma50(!showSma50)}
              className={`flex items-center space-x-1 rounded px-2 py-0.5 transition ${
                showSma50 ? "bg-[#a855f7]/20 text-purple-300 border border-[#a855f7]/40" : "text-slate-500"
              }`}
            >
              <span className="inline-block h-2 w-2 rounded-full bg-[#a855f7]" />
              <span>SMA50</span>
            </button>

            {currentTf.isIntraday && (
              <button
                onClick={() => setShowVwap(!showVwap)}
                className={`flex items-center space-x-1 rounded px-2 py-0.5 transition ${
                  showVwap ? "bg-amber-500/20 text-amber-300 border border-amber-500/40" : "text-slate-500"
                }`}
              >
                <span className="inline-block h-2 w-2 rounded-full bg-amber-400" />
                <span>VWAP</span>
              </button>
            )}
          </div>
        </div>

        {/* Right: Controls & Info */}
        <div className="flex items-center space-x-2 text-xs">
          <span className="hidden sm:inline text-[11px] text-slate-400 font-mono">
            {currentTf.name} • {candles.length} bars
          </span>

          <button
            onClick={() => handleTimeframeChange(currentTf)}
            disabled={loading}
            title="Refresh timeframe bars"
            className="rounded p-1.5 text-slate-400 hover:text-cyan-300 hover:bg-slate-800 transition"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-cyan-400" : ""}`} />
          </button>

          <button
            onClick={() => chartRef.current?.timeScale().fitContent()}
            title="Reset Zoom / Fit Content"
            className="rounded p-1.5 text-slate-400 hover:text-cyan-300 hover:bg-slate-800 transition"
          >
            <Maximize2 className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Dynamic Interactive Legend (TradingView Style) */}
      {activeCandle && (
        <div className="mb-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs font-mono">
          <div className="flex items-center space-x-2">
            <span className="text-slate-500">O:</span>
            <span className="text-slate-200 font-semibold">${activeCandle.open.toFixed(2)}</span>
            <span className="text-slate-500">H:</span>
            <span className="text-slate-200 font-semibold">${activeCandle.high.toFixed(2)}</span>
            <span className="text-slate-500">L:</span>
            <span className="text-slate-200 font-semibold">${activeCandle.low.toFixed(2)}</span>
            <span className="text-slate-500">C:</span>
            <span
              className={`font-bold ${
                activeChange >= 0 ? "text-emerald-400" : "text-red-400"
              }`}
            >
              ${activeCandle.close.toFixed(2)}
            </span>
          </div>

          <div
            className={`font-semibold ${
              activeChange >= 0 ? "text-emerald-400" : "text-red-400"
            }`}
          >
            {activeChange >= 0 ? "+" : ""}
            {activeChange.toFixed(2)} ({activeChange >= 0 ? "+" : ""}
            {activeChangePct.toFixed(2)}%)
          </div>

          <div className="text-slate-400">
            Vol: <span className="text-slate-300 font-semibold">{activeCandle.volume.toLocaleString()}</span>
          </div>

          {showSma20 && activeCandle.sma20 && (
            <div className="text-cyan-400">
              SMA20: <span className="font-semibold">${activeCandle.sma20.toFixed(2)}</span>
            </div>
          )}

          {showSma50 && activeCandle.sma50 && (
            <div className="text-purple-400">
              SMA50: <span className="font-semibold">${activeCandle.sma50.toFixed(2)}</span>
            </div>
          )}

          {showVwap && currentTf.isIntraday && activeCandle.vwap && (
            <div className="text-amber-400">
              VWAP: <span className="font-semibold">${activeCandle.vwap.toFixed(2)}</span>
            </div>
          )}
        </div>
      )}

      {/* Chart Canvas & Loading / Error Overlays */}
      <div className="relative w-full">
        <div ref={chartContainerRef} className="w-full" style={{ minHeight: "480px" }} />

        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-[#0c1322]/70 backdrop-blur-[2px] transition-all">
            <div className="flex items-center space-x-2 rounded-lg border border-cyan-500/40 bg-[#080d1a] px-4 py-2 text-xs font-bold text-cyan-300 shadow-xl">
              <RefreshCw className="h-4 w-4 animate-spin text-cyan-400" />
              <span>Loading {currentTf.name}...</span>
            </div>
          </div>
        )}

        {error && (
          <div className="absolute top-4 right-4 rounded-lg border border-red-500/40 bg-red-950/80 px-3 py-1.5 text-xs text-red-200">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
