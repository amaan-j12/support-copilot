import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../api/client";

const SAMPLE_CUSTOMERS = [
  "cust_1001",
  "cust_1002",
  "cust_1003",
  "cust_1004",
  "cust_1005",
  "cust_1006",
  "cust_1007",
  "cust_1008",
  "cust_1009",
];

export default function NewTicketModal({ onClose }: { onClose: () => void }) {
  const [customerId, setCustomerId] = useState(SAMPLE_CUSTOMERS[0]);
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => api.createTicket({ customer_id: customerId, subject, message }),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
      onClose();
      navigate(`/tickets/${result.ticket_id}`);
    },
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 px-4">
      <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Raise a ticket</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600" aria-label="Close">
            ✕
          </button>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            mutation.mutate();
          }}
          className="space-y-4"
        >
          <div>
            <label className="mb-1 block text-xs font-medium uppercase text-slate-500">Customer</label>
            <select
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={customerId}
              onChange={(e) => setCustomerId(e.target.value)}
            >
              {SAMPLE_CUSTOMERS.map((id) => (
                <option key={id} value={id}>
                  {id}
                </option>
              ))}
            </select>
            <p className="mt-1 text-xs text-slate-400">
              Synthetic Loopwork accounts seeded in the fixture data (see
              app/synthetic_data/loopwork_fixtures.py).
            </p>
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium uppercase text-slate-500">Subject</label>
            <input
              required
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="e.g. Charged twice this month"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium uppercase text-slate-500">Message</label>
            <textarea
              required
              rows={5}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Describe the issue as the customer would..."
            />
          </div>

          {mutation.isError && (
            <p className="text-sm text-rose-600">
              {(mutation.error as Error)?.message ?? "Something went wrong."}
            </p>
          )}

          <div className="flex items-center justify-between gap-3 pt-2">
            <p className="text-xs text-slate-400">
              {mutation.isPending ? "Running the agent — this takes 15-40s (several LLM calls)..." : " "}
            </p>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={onClose}
                className="rounded-md px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100"
                disabled={mutation.isPending}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={mutation.isPending}
                className="rounded-md bg-slate-900 px-4 py-1.5 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
              >
                {mutation.isPending ? "Submitting…" : "Submit"}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
