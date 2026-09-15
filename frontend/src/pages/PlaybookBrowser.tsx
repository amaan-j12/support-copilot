import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client";
import StatusBadge from "../components/StatusBadge";

export default function PlaybookBrowser() {
  const [statusFilter, setStatusFilter] = useState<string>("");
  const { data: entries, isLoading } = useQuery({
    queryKey: ["playbook", statusFilter],
    queryFn: () => api.listPlaybook(statusFilter || undefined),
  });
  const { data: versions } = useQuery({ queryKey: ["agent-versions"], queryFn: api.listAgentVersions });

  return (
    <div>
      <h1 className="mb-1 text-xl font-semibold">Learned playbook</h1>
      <p className="mb-6 text-sm text-slate-500">
        Lessons distilled from ticket reflections. Only entries that passed the eval gate (no
        regression vs. the current active version) are "active" and actually influence live
        tickets — rejected candidates stay visible here too.
      </p>

      <div className="mb-6 flex gap-6">
        <section className="flex-1">
          <div className="mb-2 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-700">Entries</h2>
            <select
              className="rounded-md border border-slate-300 bg-white px-2 py-1 text-xs"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">All</option>
              <option value="active">Active</option>
              <option value="candidate">Candidate</option>
              <option value="retired">Retired</option>
            </select>
          </div>

          {isLoading && <p className="text-sm text-slate-500">Loading…</p>}

          <div className="space-y-2">
            {entries?.map((e) => (
              <div key={e.id} className="rounded-lg border border-slate-200 bg-white p-3 text-sm">
                <div className="mb-1 flex items-center justify-between gap-2">
                  <span className="font-medium">{e.title}</span>
                  <StatusBadge status={e.status} />
                </div>
                <p className="text-slate-600">{e.content}</p>
                <div className="mt-1 text-xs text-slate-400">
                  {e.promoted_at ? `Promoted ${new Date(e.promoted_at).toLocaleString()}` : "Not promoted"}
                </div>
              </div>
            ))}
            {entries?.length === 0 && (
              <p className="rounded-lg border border-slate-200 bg-white p-4 text-center text-slate-400">
                No playbook entries yet — run scripts/simulate_traffic.py then
                scripts/run_learning_cycle.py.
              </p>
            )}
          </div>
        </section>

        <section className="w-80">
          <h2 className="mb-2 text-sm font-semibold text-slate-700">Agent generations</h2>
          <div className="space-y-2">
            {versions?.map((v) => (
              <div key={v.id} className="rounded-lg border border-slate-200 bg-white p-3 text-sm">
                <div className="mb-1 flex items-center justify-between">
                  <span className="font-medium">gen{v.generation_number}</span>
                  <StatusBadge status={v.status} />
                </div>
                <div className="text-xs text-slate-500">{v.created_by}</div>
                {v.notes && <p className="mt-1 text-xs text-slate-600">{v.notes}</p>}
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
