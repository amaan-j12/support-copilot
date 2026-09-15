import { NavLink, Route, Routes } from "react-router-dom";

import ApprovalQueue from "./pages/ApprovalQueue";
import EvalScoreboard from "./pages/EvalScoreboard";
import PlaybookBrowser from "./pages/PlaybookBrowser";
import TicketDetail from "./pages/TicketDetail";
import TicketQueue from "./pages/TicketQueue";

const navItems = [
  { to: "/", label: "Tickets", end: true },
  { to: "/approvals", label: "Approvals" },
  { to: "/evals", label: "Eval Scoreboard" },
  { to: "/playbook", label: "Playbook" },
];

export default function App() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center gap-6 px-6 py-4">
          <span className="text-lg font-semibold tracking-tight">Support Copilot</span>
          <nav className="flex gap-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                    isActive ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">
        <Routes>
          <Route path="/" element={<TicketQueue />} />
          <Route path="/tickets/:id" element={<TicketDetail />} />
          <Route path="/approvals" element={<ApprovalQueue />} />
          <Route path="/evals" element={<EvalScoreboard />} />
          <Route path="/playbook" element={<PlaybookBrowser />} />
        </Routes>
      </main>
    </div>
  );
}
