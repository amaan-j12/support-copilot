"""Turns accumulated per-ticket reflections into candidate playbook entries.

Deliberately simple for a first pass: one draft playbook entry per
reflection that clears a confidence bar (no cross-reflection clustering —
merging would need to mark every merged reflection as incorporated, not just
one, which the current one-entry-per-reflection schema can't represent
cleanly; near-duplicate entries are harmless for retrieval, which only takes
the top-k anyway). The eval gate in playbook_promote.py — not this module —
decides whether these candidates are trustworthy enough to go live; this
module only proposes them.
"""

import uuid

from sqlalchemy.orm import Session

from app.db.models import PlaybookEntry, Reflection
from app.llm.base import LLMAdapter

MIN_CONFIDENCE = 0.5


def unincorporated_reflections(db: Session) -> list[Reflection]:
    incorporated_ids = {
        row[0]
        for row in db.query(PlaybookEntry.source_reflection_id)
        .filter(PlaybookEntry.source_reflection_id.isnot(None))
        .all()
    }
    reflections = (
        db.query(Reflection)
        .filter(Reflection.proposed_lesson.isnot(None))
        .filter(Reflection.confidence >= MIN_CONFIDENCE)
        .all()
    )
    return [r for r in reflections if r.id not in incorporated_ids]


def build_candidate_playbook_entries(
    db: Session, adapter: LLMAdapter, *, agent_version_id: uuid.UUID
) -> list[PlaybookEntry]:
    reflections = unincorporated_reflections(db)
    if not reflections:
        return []

    lessons = [r.proposed_lesson for r in reflections]
    embeddings = adapter.embed(lessons)

    entries = []
    for reflection, lesson, emb in zip(reflections, lessons, embeddings):
        title = lesson[:80] + ("..." if len(lesson) > 80 else "")
        entry = PlaybookEntry(
            title=title,
            content=lesson,
            embedding=emb,
            status="candidate",
            source_reflection_id=reflection.id,
            version_introduced=agent_version_id,
        )
        db.add(entry)
        entries.append(entry)
    db.flush()
    return entries
