"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";

interface Bucket {
  bucket: string;
  n: number;
  avg_predicted_pct?: number;
  realized_win_rate_pct: number;
  avg_directional_ret_10d_pct?: number | null;
  reliable: boolean;
}

interface CalibrationReport {
  total_recorded: number;
  pending: number;
  scored: number;
  min_bucket_samples: number;
  win_rate_pct: number | null;
  avg_pnl_per_contract?: number;
  brier_score: number | null;
  avg_predicted_prob_pct?: number | null;
  outcomes?: Record<string, number>;
  by_predicted_probability: Bucket[];
  by_signal_confidence: Bucket[];
}

const fmtPct = (v: number | null | undefined) => (v === null || v === undefined ? "–" : `${v.toFixed(1)}%`);

/**
 * Track record of past recommendations: predicted probability vs what actually happened.
 * Data comes from the backend recommendation journal (/api/calibration).
 */
export default function CalibrationPanel() {
  const [report, setReport] = useState<CalibrationReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const requestId = useRef(0);

  const load = useCallback(async (evaluate: boolean) => {
    const id = ++requestId.current;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/calibration${evaluate ? "?evaluate=true" : ""}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      if (id === requestId.current) setReport(json);
    } catch (err: any) {
      if (id === requestId.current) setError(err.message || "Failed to load track record");
    } finally {
      if (id === requestId.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(false);
  }, [load]);

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0b1220] p-4 text-xs text-slate-300">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-bold text-white">Recommendation Track Record</h3>
          <p className="text-[11px] text-slate-400">
            Every idea is recorded and later scored against real option prices: +50% target, −50% stop, or time exit.
          </p>
        </div>
        <button
          onClick={() => load(true)}
          disabled={loading}
          className="rounded-lg border border-slate-700 px-3 py-1 text-[11px] font-semibold text-cyan-300 hover:border-cyan-500 disabled:opacity-50"
        >
          {loading ? "Scoring…" : "Score pending ideas"}
        </button>
      </div>

      {error && <div className="text-rose-300">{error}</div>}

      {report && (
        <>
          <div className="mb-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
            <Stat label="Recorded" value={String(report.total_recorded)} />
            <Stat label="Scored" value={`${report.scored} (${report.pending} pending)`} />
            <Stat label="Realized win rate" value={fmtPct(report.win_rate_pct)} />
            <Stat
              label="Predicted (avg)"
              value={fmtPct(report.avg_predicted_prob_pct ?? null)}
              hint={report.brier_score !== null ? `Brier ${report.brier_score.toFixed(3)} (lower is better, 0.25 = coin flip)` : undefined}
            />
          </div>

          {report.scored === 0 ? (
            <p className="text-[11px] text-slate-400">
              No scored ideas yet. Outcomes appear once recorded ideas have traded for a few sessions.
            </p>
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              <BucketTable
                title="Predicted probability vs realized"
                rows={report.by_predicted_probability}
                minN={report.min_bucket_samples}
                showPredicted
              />
              <BucketTable
                title="Signal confidence vs realized"
                rows={report.by_signal_confidence}
                minN={report.min_bucket_samples}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
}

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-lg bg-[#0e1628] px-3 py-2" title={hint}>
      <div className="text-[10px] uppercase tracking-wider text-slate-500">{label}</div>
      <div className="font-mono text-sm font-bold text-white">{value}</div>
    </div>
  );
}

function BucketTable({
  title,
  rows,
  minN,
  showPredicted = false,
}: {
  title: string;
  rows: Bucket[];
  minN: number;
  showPredicted?: boolean;
}) {
  return (
    <div>
      <div className="mb-1 text-[10px] font-bold uppercase tracking-wider text-slate-400">{title}</div>
      <div className="overflow-x-auto">
        <table className="w-full text-left font-mono text-[11px]">
          <thead className="text-slate-500">
            <tr>
              <th className="py-1 pr-2">Bucket</th>
              <th className="py-1 pr-2">n</th>
              {showPredicted && <th className="py-1 pr-2">Predicted</th>}
              <th className="py-1 pr-2">Realized</th>
              {!showPredicted && <th className="py-1">10d move</th>}
            </tr>
          </thead>
          <tbody>
            {rows.map((b) => (
              <tr key={b.bucket} className={b.reliable ? "text-slate-200" : "text-slate-500"}>
                <td className="py-0.5 pr-2">{b.bucket}</td>
                <td className="py-0.5 pr-2">{b.n}</td>
                {showPredicted && <td className="py-0.5 pr-2">{fmtPct(b.avg_predicted_pct)}</td>}
                <td className="py-0.5 pr-2">{fmtPct(b.realized_win_rate_pct)}</td>
                {!showPredicted && <td className="py-0.5">{fmtPct(b.avg_directional_ret_10d_pct ?? null)}</td>}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-1 text-[10px] text-slate-500">Greyed rows have fewer than {minN} ideas – not yet reliable.</div>
    </div>
  );
}
