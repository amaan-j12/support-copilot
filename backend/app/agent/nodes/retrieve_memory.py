import uuid

from app.agent.context import NodeContext
from app.agent.state import TicketState
from app.agent.tools.kb_search import kb_search
from app.memory.episodic import retrieve_active_playbook, retrieve_similar_memories


def retrieve_memory_node(state: TicketState, ctx: NodeContext) -> dict:
    query_text = f"{state['subject']} {state.get('intent_summary') or state['sanitized_message']}"
    embedding = ctx.adapter.embed([query_text])[0]

    candidate_id = (
        uuid.UUID(ctx.agent_version_id) if ctx.is_candidate_eval and ctx.agent_version_id else None
    )
    memories = retrieve_similar_memories(ctx.db, embedding, limit=3)
    playbook = retrieve_active_playbook(ctx.db, embedding, limit=3, candidate_agent_version_id=candidate_id)
    kb = kb_search(query_text, ctx.adapter, top_k=3)["results"]

    return {
        "retrieved_memories": [
            {"summary": m.summary, "outcome": m.outcome} for m in memories
        ],
        "retrieved_playbook": [
            {"title": p.title, "content": p.content} for p in playbook
        ],
        "retrieved_kb": kb,
    }
