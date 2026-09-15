const BASE = "/api";

async function request<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} on ${path}`);
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} on ${path}`);
  return res.json() as Promise<T>;
}

export interface Ticket {
  id: string;
  customer_id: string;
  subject: string;
  status: "open" | "pending_approval" | "resolved" | "escalated";
  category: string | null;
  priority: string | null;
  created_at: string;
  resolved_at: string | null;
}

export interface TicketMessage {
  role: string;
  content: string;
  created_at: string;
}

export interface ToolCallRecord {
  tool_name: string;
  input: Record<string, unknown>;
  output: Record<string, unknown> | null;
  risk_level: string;
  status: string;
  created_at: string;
}

export interface TicketDetail {
  ticket: Ticket;
  messages: TicketMessage[];
  tool_calls: ToolCallRecord[];
}

export interface Approval {
  id: string;
  ticket_id: string;
  status: string;
  action_summary: string;
  reviewer: string | null;
  reviewed_at: string | null;
  created_at: string;
}

export interface EvalRunSummary {
  id: string;
  agent_version_generation: number | null;
  agent_version_status: string | null;
  eval_set_version: string;
  status: string;
  triggered_by: string;
  started_at: string;
  n_cases: number;
  resolution_accuracy: number | null;
  escalation_accuracy: number | null;
  avg_tool_call_f1: number | null;
  total_cost_usd: number;
}

export interface EvalResultRow {
  case_id: string;
  category: string | null;
  resolution_correct: boolean;
  escalation_correct: boolean;
  tool_call_f1: number;
  hallucination_score: number | null;
  latency_ms: number | null;
  cost_usd: number;
  rationale: string;
}

export interface PlaybookEntry {
  id: string;
  title: string;
  content: string;
  status: "draft" | "candidate" | "active" | "retired";
  promoted_at: string | null;
  version_introduced: string | null;
  created_at: string;
}

export interface AgentVersion {
  id: string;
  generation_number: number;
  status: "candidate" | "active" | "retired" | "rejected";
  created_by: string;
  notes: string | null;
  activated_at: string | null;
  created_at: string;
}

export const api = {
  listTickets: (status?: string) => request<Ticket[]>(`/tickets${status ? `?status=${status}` : ""}`),
  getTicket: (id: string) => request<TicketDetail>(`/tickets/${id}`),
  createTicket: (body: { customer_id: string; subject: string; message: string }) =>
    post<{ ticket_id: string; outcome: string; final_response: string }>("/tickets", body),
  listApprovals: (status?: string) => request<Approval[]>(`/approvals${status ? `?status=${status}` : ""}`),
  listEvalRuns: () => request<EvalRunSummary[]>("/eval-runs"),
  getEvalResults: (id: string) => request<EvalResultRow[]>(`/eval-runs/${id}/results`),
  listPlaybook: (status?: string) => request<PlaybookEntry[]>(`/playbook${status ? `?status=${status}` : ""}`),
  listAgentVersions: () => request<AgentVersion[]>("/agent-versions"),
};
