import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client";
import StatusBadge from "../components/StatusBadge";

export default function TicketQueue() {
  const [statusFilter, setStatusFilter] = useState<string>("");
  const { data: tickets, isLoading } = useQuery({
    queryKey: ["tickets", statusFilter],
    queryFn: () => api.listTickets(statusFilter || undefined),
  });

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Ticket queue</h1>
        <select
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="pending_approval">Pending approval</option>
          <option value="resolved">Resolved</option>
          <option value="escalated">Escalated</option>
        </select>
      </div>

      {isLoading && <p className="text-sm text-slate-500">Loading…</p>}

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-2">Subject</th>
              <th className="px-4 py-2">Customer</th>
              <th className="px-4 py-2">Category</th>
              <th className="px-4 py-2">Priority</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">Created</th>
            </tr>
          </thead>
          <tbody>
            {tickets?.map((t) => (
              <tr key={t.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                <td className="px-4 py-2">
                  <Link to={`/tickets/${t.id}`} className="font-medium text-slate-900 hover:underline">
                    {t.subject}
                  </Link>
                </td>
                <td className="px-4 py-2 text-slate-600">{t.customer_id}</td>
                <td className="px-4 py-2 text-slate-600">{t.category ?? "—"}</td>
                <td className="px-4 py-2 text-slate-600">{t.priority ?? "—"}</td>
                <td className="px-4 py-2">
                  <StatusBadge status={t.status} />
                </td>
                <td className="px-4 py-2 text-slate-500">{new Date(t.created_at).toLocaleString()}</td>
              </tr>
            ))}
            {tickets?.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                  No tickets yet — POST to /tickets or run a script to create some.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
