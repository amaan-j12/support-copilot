"""Episodic memory (past ticket outcomes) and active-playbook retrieval over
pgvector. Both are read together in the `retrieve_memory` node so the agent
sees "what happened last time" and "what we've learned" side by side.
"""

import uuid

from sqlalchemy.orm import Session

from app.db.models import EpisodicMemory, PlaybookEntry


def retrieve_similar_memories(
    db: Session, query_embedding: list[float], limit: int = 5
) -> list[EpisodicMemory]:
    return (
        db.query(EpisodicMemory)
        .order_by(EpisodicMemory.embedding.cosine_distance(query_embedding))
        .limit(limit)
        .all()
    )


def retrieve_active_playbook(
    db: Session,
    query_embedding: list[float],
    limit: int = 5,
    *,
    candidate_agent_version_id: uuid.UUID | None = None,
) -> list[PlaybookEntry]:
    """Active (already-promoted) entries, plus — when evaluating a not-yet-
    promoted candidate generation — that candidate's own proposed entries, so
    its eval run judges the playbook it would actually run with if promoted.
    """
    filters = [PlaybookEntry.status == "active"]
    if candidate_agent_version_id is not None:
        filters.append(
            (PlaybookEntry.status == "candidate")
            & (PlaybookEntry.version_introduced == candidate_agent_version_id)
        )
    from sqlalchemy import or_

    return (
        db.query(PlaybookEntry)
        .filter(or_(*filters))
        .order_by(PlaybookEntry.embedding.cosine_distance(query_embedding))
        .limit(limit)
        .all()
    )


def write_episodic_memory(
    db: Session,
    *,
    ticket_id: uuid.UUID,
    summary: str,
    embedding: list[float],
    outcome: str,
    tags: list[str] | None = None,
) -> EpisodicMemory:
    mem = EpisodicMemory(
        ticket_id=ticket_id,
        summary=summary,
        embedding=embedding,
        outcome=outcome,
        tags=tags or [],
    )
    db.add(mem)
    db.flush()
    return mem
