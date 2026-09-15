import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { api } from "../api/client";
import StatusBadge from "../components/StatusBadge";

export default function TicketDetail() {
  const { id } = useParams<{ id: string }>();
  const { data, isLoading } = useQuery({
    queryKey: ["ticket", id],
    queryFn: () => api.getTicket(id!),
    enabled: !!id,
  });

  if (isLoading) return <p className="text-sm text-slate-500">Loading…</p>;
  if (!data) return <p className="text-sm text-slate-500">Not found.</p>;

  const { ticket, messages, tool_calls } = data;

  return (
    <div>
      <Link to="/" className="text-sm text-slate-500 hover:underline">
        ← Back to queue
      </Link>

      <div className="mt-2 mb-6 flex items-center justify-between">
        <h1 className="text-xl font-semibold">{ticket.subject}</h1>
        <StatusBadge status={ticket.status} />
      </div>

      <div className="mb-6 grid grid-cols-4 gap-4 text-sm">
        <div>
          <div className="text-xs uppercase text-slate-400">Customer</div>
          <div>{ticket.customer_id}</div>
        </div>
        <div>
          <div className="text-xs uppercase text-slate-400">Category</div>
          <div>{ticket.category ?? "—"}</div>
        </div>
        <div>
          <div className="text-xs uppercase text-slate-400">Priority</div>
          <div>{ticket.priority ?? "—"}</div>
        </div>
        <div>
          <div className="text-xs uppercase text-slate-400">Resolved</div>
          <div>{ticket.resolved_at ? new Date(ticket.resolved_at).toLocaleString() : "—"}</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <section>
          <h2 className="mb-2 text-sm font-semibold text-slate-700">Conversation</h2>
          <div className="space-y-2 rounded-lg border border-slate-200 bg-white p-4">
            {messages.map((m, i) => (
              <div key={i} className={`rounded-md p-3 text-sm ${m.role === "customer" ? "bg-slate-50" : "bg-indigo-50"}`}>
                <div className="mb-1 text-xs font-medium uppercase text-slate-400">{m.role}</div>
                <div className="whitespace-pre-wrap text-slate-800">{m.content}</div>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2 className="mb-2 text-sm font-semibold text-slate-700">Reasoning trace (tool calls)</h2>
          <div className="space-y-2">
            {tool_calls.length === 0 && (
              <p className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-400">
                No tool calls — resolved directly from the model's own reply.
              </p>
            )}
            {tool_calls.map((tc, i) => (
              <div key={i} className="rounded-lg border border-slate-200 bg-white p-3 text-sm">
                <div className="mb-1 flex items-center justify-between">
                  <span className="font-mono font-medium">{tc.tool_name}</span>
                  <div className="flex gap-1">
                    <StatusBadge status={tc.risk_level} />
                    <StatusBadge status={tc.status} />
                  </div>
                </div>
                <pre className="overflow-x-auto rounded bg-slate-50 p-2 text-xs text-slate-600">
                  {JSON.stringify(tc.input, null, 2)}
                </pre>
                {tc.output && (
                  <pre className="mt-1 overflow-x-auto rounded bg-slate-50 p-2 text-xs text-slate-600">
                    → {JSON.stringify(tc.output, null, 2)}
                  </pre>
                )}
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
