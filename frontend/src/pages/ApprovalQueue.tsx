import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { api } from "../api/client";
import StatusBadge from "../components/StatusBadge";

export default function ApprovalQueue() {
  const { data: approvals, isLoading } = useQuery({
    queryKey: ["approvals"],
    queryFn: () => api.listApprovals(),
  });

  return (
    <div>
      <h1 className="mb-1 text-xl font-semibold">Approval queue</h1>
      <p className="mb-6 text-sm text-slate-500">
        High-risk actions (refunds, cancellations) always pass through here before executing.{" "}
        <span className="font-medium">Phase-1 note:</span> approvals currently auto-resolve
        synchronously (see <code className="rounded bg-slate-100 px-1">app/agent/nodes/hitl.py</code>) so
        the eval pipeline runs unattended — this view is read-only until Phase 2 wires up a real
        interrupt/resume decision endpoint.
      </p>

      {isLoading && <p className="text-sm text-slate-500">Loading…</p>}

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-2">Action</th>
              <th className="px-4 py-2">Ticket</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">Reviewer</th>
              <th className="px-4 py-2">Reviewed</th>
            </tr>
          </thead>
          <tbody>
            {approvals?.map((a) => (
              <tr key={a.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                <td className="max-w-md truncate px-4 py-2 font-mono text-xs">{a.action_summary}</td>
                <td className="px-4 py-2">
                  <Link to={`/tickets/${a.ticket_id}`} className="text-slate-600 hover:underline">
                    {a.ticket_id.slice(0, 8)}…
                  </Link>
                </td>
                <td className="px-4 py-2">
                  <StatusBadge status={a.status} />
                </td>
                <td className="px-4 py-2 text-slate-600">{a.reviewer ?? "—"}</td>
                <td className="px-4 py-2 text-slate-500">
                  {a.reviewed_at ? new Date(a.reviewed_at).toLocaleString() : "—"}
                </td>
              </tr>
            ))}
            {approvals?.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                  No approval requests yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
