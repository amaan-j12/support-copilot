import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { api, EvalRunSummary } from "../api/client";
import StatusBadge from "../components/StatusBadge";

export default function EvalScoreboard() {
  const { data: runs, isLoading } = useQuery({ queryKey: ["eval-runs"], queryFn: api.listEvalRuns });
  const [selected, setSelected] = useState<string | null>(null);
  const { data: results } = useQuery({
    queryKey: ["eval-results", selected],
    queryFn: () => api.getEvalResults(selected!),
    enabled: !!selected,
  });

  const chartData = (runs ?? []).map((r: EvalRunSummary) => ({
    generation: `gen${r.agent_version_generation ?? "?"}`,
    resolution_accuracy: r.resolution_accuracy != null ? Math.round(r.resolution_accuracy * 1000) / 10 : null,
    escalation_accuracy: r.escalation_accuracy != null ? Math.round(r.escalation_accuracy * 1000) / 10 : null,
    status: r.agent_version_status,
  }));

  return (
    <div>
      <h1 className="mb-1 text-xl font-semibold">Eval scoreboard</h1>
      <p className="mb-6 text-sm text-slate-500">
        Every agent generation is scored against the same frozen eval set before it can go live —
        this is the "before/after" evidence that the self-learning loop actually improves the agent.
      </p>

      {isLoading && <p className="text-sm text-slate-500">Loading…</p>}

      {chartData.length > 0 && (
        <div className="mb-8 h-72 rounded-lg border border-slate-200 bg-white p-4">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="generation" tick={{ fontSize: 12 }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} unit="%" />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="resolution_accuracy"
                name="Resolution accuracy"
                stroke="#4f46e5"
                strokeWidth={2}
                dot={{ r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="escalation_accuracy"
                name="Escalation accuracy"
                stroke="#0d9488"
                strokeWidth={2}
                dot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-2">Generation</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">Triggered by</th>
              <th className="px-4 py-2">Cases</th>
              <th className="px-4 py-2">Resolution acc.</th>
              <th className="px-4 py-2">Escalation acc.</th>
              <th className="px-4 py-2">Tool F1</th>
              <th className="px-4 py-2">Cost (metered)</th>
            </tr>
          </thead>
          <tbody>
            {runs?.map((r) => (
              <tr
                key={r.id}
                onClick={() => setSelected(r.id === selected ? null : r.id)}
                className={`cursor-pointer border-b border-slate-100 last:border-0 hover:bg-slate-50 ${
                  selected === r.id ? "bg-indigo-50" : ""
                }`}
              >
                <td className="px-4 py-2 font-medium">gen{r.agent_version_generation}</td>
                <td className="px-4 py-2">
                  {r.agent_version_status && <StatusBadge status={r.agent_version_status} />}
                </td>
                <td className="px-4 py-2 text-slate-600">{r.triggered_by}</td>
                <td className="px-4 py-2 text-slate-600">{r.n_cases}</td>
                <td className="px-4 py-2 font-medium">
                  {r.resolution_accuracy != null ? `${(r.resolution_accuracy * 100).toFixed(0)}%` : "—"}
                </td>
                <td className="px-4 py-2">
                  {r.escalation_accuracy != null ? `${(r.escalation_accuracy * 100).toFixed(0)}%` : "—"}
                </td>
                <td className="px-4 py-2">{r.avg_tool_call_f1?.toFixed(2) ?? "—"}</td>
                <td className="px-4 py-2 text-slate-500">${r.total_cost_usd.toFixed(4)}</td>
              </tr>
            ))}
            {runs?.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-slate-400">
                  No eval runs yet — run scripts/run_baseline.py.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {selected && results && (
        <div className="mt-6">
          <h2 className="mb-2 text-sm font-semibold text-slate-700">Per-case results</h2>
          <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
            <table className="w-full text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-2">Case</th>
                  <th className="px-4 py-2">Category</th>
                  <th className="px-4 py-2">Result</th>
                  <th className="px-4 py-2">Rationale</th>
                </tr>
              </thead>
              <tbody>
                {results.map((r) => (
                  <tr key={r.case_id} className="border-b border-slate-100 last:border-0">
                    <td className="px-4 py-2 font-mono text-xs">{r.case_id}</td>
                    <td className="px-4 py-2 text-slate-600">{r.category}</td>
                    <td className="px-4 py-2">
                      <StatusBadge status={r.resolution_correct ? "resolved" : "escalated"} />
                    </td>
                    <td className="px-4 py-2 text-xs text-slate-500">{r.rationale}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
