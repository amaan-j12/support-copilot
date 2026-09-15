from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.llm.base import LLMAdapter


@dataclass
class NodeContext:
    """Bound to a single graph run via functools.partial when nodes are
    registered — every node needs the same db session + LLM adapter, but
    neither belongs in the (serializable) TicketState.
    """

    db: Session
    adapter: LLMAdapter
    agent_version_id: str | None = None
    # True while evaluating a not-yet-promoted candidate generation, so
    # retrieve_memory also considers that candidate's own draft playbook
    # entries (not just already-active ones). See memory/episodic.py.
    is_candidate_eval: bool = False
