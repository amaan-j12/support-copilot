"""SQLAlchemy models for the support-copilot data model.

See docs/architecture.md for the entity-relationship overview. Embedding
dimension (384) matches the default local embedding model
(sentence-transformers/all-MiniLM-L6-v2); if the embedding backend changes,
bump EMBEDDING_DIM and add a migration.
"""

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    Boolean,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

EMBEDDING_DIM = 384


class Base(DeclarativeBase):
    pass


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


# --------------------------------------------------------------------------
# Agent versioning — every ticket run and eval run is pinned to one of these.
# --------------------------------------------------------------------------


class AgentVersion(Base, TimestampMixin):
    """A generation of the agent: a specific (playbook snapshot, prompt set) pair."""

    __tablename__ = "agent_versions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    generation_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    parent_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_versions.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        Enum("candidate", "active", "retired", "rejected", name="agent_version_status"),
        nullable=False,
        default="candidate",
    )
    # "baseline" (phase-1 gen-0), "reflection_loop", "prompt_optimizer", "manual"
    created_by: Mapped[str] = mapped_column(String(32), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    activated_at: Mapped[datetime | None] = mapped_column(nullable=True)
    retired_at: Mapped[datetime | None] = mapped_column(nullable=True)

    prompt_versions: Mapped[list["PromptVersion"]] = relationship(back_populates="agent_version")


class PromptVersion(Base, TimestampMixin):
    """A single node's prompt text as of a given agent version."""

    __tablename__ = "prompt_versions"
    __table_args__ = (UniqueConstraint("agent_version_id", "node_name"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    agent_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_versions.id"), nullable=False
    )
    node_name: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    diff_from_parent: Mapped[str | None] = mapped_column(Text, nullable=True)

    agent_version: Mapped[AgentVersion] = relationship(back_populates="prompt_versions")


# --------------------------------------------------------------------------
# Tickets
# --------------------------------------------------------------------------


class Ticket(Base, TimestampMixin):
    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = _uuid_pk()
    customer_id: Mapped[str] = mapped_column(String(64), nullable=False)
    subject: Mapped[str] = mapped_column(String(256), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), default="email")
    status: Mapped[str] = mapped_column(
        Enum(
            "open",
            "pending_approval",
            "resolved",
            "escalated",
            name="ticket_status",
        ),
        default="open",
        nullable=False,
    )
    priority: Mapped[str] = mapped_column(String(16), default="normal")
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    agent_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_versions.id"), nullable=True
    )
    # links back to the eval case this ticket was generated from, if any (eval runs vs live)
    eval_case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("eval_set_cases.id"), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(nullable=True)

    messages: Mapped[list["TicketMessage"]] = relationship(back_populates="ticket")
    tool_calls: Mapped[list["ToolCall"]] = relationship(back_populates="ticket")


class TicketMessage(Base, TimestampMixin):
    __tablename__ = "ticket_messages"

    id: Mapped[uuid.UUID] = _uuid_pk()
    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # customer / agent / system
    content: Mapped[str] = mapped_column(Text, nullable=False)  # PII-redacted canonical text
    redaction_meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    ticket: Mapped[Ticket] = relationship(back_populates="messages")


class ToolCall(Base, TimestampMixin):
    __tablename__ = "tool_calls"

    id: Mapped[uuid.UUID] = _uuid_pk()
    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(64), nullable=False)
    input_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    output_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    risk_level: Mapped[str] = mapped_column(String(16), default="low")  # low / high
    status: Mapped[str] = mapped_column(
        Enum("executed", "pending_approval", "rejected", name="tool_call_status"),
        default="executed",
    )
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)

    ticket: Mapped[Ticket] = relationship(back_populates="tool_calls")
    approval: Mapped["Approval | None"] = relationship(back_populates="tool_call", uselist=False)


class Approval(Base, TimestampMixin):
    __tablename__ = "approvals"

    id: Mapped[uuid.UUID] = _uuid_pk()
    tool_call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tool_calls.id"), nullable=False, unique=True
    )
    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("pending", "approved", "rejected", "expired", name="approval_status"),
        default="pending",
    )
    action_summary: Mapped[str] = mapped_column(Text, nullable=False)
    reviewer: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    tool_call: Mapped[ToolCall] = relationship(back_populates="approval")


# --------------------------------------------------------------------------
# Memory / learning
# --------------------------------------------------------------------------


class EpisodicMemory(Base, TimestampMixin):
    __tablename__ = "episodic_memories"

    id: Mapped[uuid.UUID] = _uuid_pk()
    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)  # resolved / escalated / rejected_action
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)


class Reflection(Base, TimestampMixin):
    __tablename__ = "reflections"

    id: Mapped[uuid.UUID] = _uuid_pk()
    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False)
    critique_text: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_lesson: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    generation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_versions.id"), nullable=True
    )


class PlaybookEntry(Base, TimestampMixin):
    __tablename__ = "playbook_entries"

    id: Mapped[uuid.UUID] = _uuid_pk()
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("draft", "candidate", "active", "retired", name="playbook_status"),
        default="draft",
    )
    source_reflection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reflections.id"), nullable=True
    )
    promoted_at: Mapped[datetime | None] = mapped_column(nullable=True)
    promoted_by_eval_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("eval_runs.id"), nullable=True
    )
    version_introduced: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_versions.id"), nullable=True
    )


# --------------------------------------------------------------------------
# Evaluation harness
# --------------------------------------------------------------------------


class EvalSetCase(Base, TimestampMixin):
    __tablename__ = "eval_set_cases"

    id: Mapped[uuid.UUID] = _uuid_pk()
    eval_set_version: Mapped[str] = mapped_column(String(16), nullable=False)
    scenario_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    expected_outcome_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    expected_tool_calls_json: Mapped[list] = mapped_column(JSON, default=list)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(16), default="medium")
    requires_hitl: Mapped[bool] = mapped_column(Boolean, default=False)


class EvalRun(Base, TimestampMixin):
    __tablename__ = "eval_runs"

    id: Mapped[uuid.UUID] = _uuid_pk()
    agent_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_versions.id"), nullable=False
    )
    eval_set_version: Mapped[str] = mapped_column(String(16), nullable=False)
    triggered_by: Mapped[str] = mapped_column(String(32), default="manual")  # manual/nightly/gate
    started_at: Mapped[datetime] = mapped_column(server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("running", "completed", "failed", name="eval_run_status"), default="running"
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    results: Mapped[list["EvalResult"]] = relationship(back_populates="eval_run")


class EvalResult(Base, TimestampMixin):
    __tablename__ = "eval_results"

    id: Mapped[uuid.UUID] = _uuid_pk()
    eval_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("eval_runs.id"), nullable=False)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("eval_set_cases.id"), nullable=False)
    resolution_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    escalation_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    tool_call_f1: Mapped[float] = mapped_column(Float, default=0.0)
    hallucination_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    judge_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)

    eval_run: Mapped[EvalRun] = relationship(back_populates="results")


# --------------------------------------------------------------------------
# Feedback & cost
# --------------------------------------------------------------------------


class Feedback(Base, TimestampMixin):
    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = _uuid_pk()
    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False)
    source: Mapped[str] = mapped_column(String(32), default="customer")  # customer/reviewer/synthetic
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # -1/0/1
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)


class CostLedgerEntry(Base, TimestampMixin):
    __tablename__ = "cost_ledger"

    id: Mapped[uuid.UUID] = _uuid_pk()
    ticket_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=True)
    eval_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("eval_runs.id"), nullable=True
    )
    tokens_in: Mapped[int] = mapped_column(Integer, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
