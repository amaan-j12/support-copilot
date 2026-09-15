const COLORS: Record<string, string> = {
  open: "bg-blue-100 text-blue-800",
  pending_approval: "bg-amber-100 text-amber-800",
  resolved: "bg-emerald-100 text-emerald-800",
  escalated: "bg-rose-100 text-rose-800",
  pending: "bg-amber-100 text-amber-800",
  approved: "bg-emerald-100 text-emerald-800",
  rejected: "bg-rose-100 text-rose-800",
  expired: "bg-slate-100 text-slate-600",
  active: "bg-emerald-100 text-emerald-800",
  candidate: "bg-indigo-100 text-indigo-800",
  retired: "bg-slate-100 text-slate-600",
  draft: "bg-slate-100 text-slate-600",
  executed: "bg-emerald-100 text-emerald-800",
  executed_after_approval: "bg-emerald-100 text-emerald-800",
  low: "bg-slate-100 text-slate-600",
  high: "bg-amber-100 text-amber-800",
};

export default function StatusBadge({ status }: { status: string }) {
  const cls = COLORS[status] ?? "bg-slate-100 text-slate-600";
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>
      {status.replace(/_/g, " ")}
    </span>
  );
}
