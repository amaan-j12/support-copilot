import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agent.runner import run_ticket
from app.db.models import AgentVersion, Ticket, TicketMessage, ToolCall
from app.db.session import get_db
from app.llm.factory import get_llm_adapter

router = APIRouter(prefix="/tickets", tags=["tickets"])


class CreateTicketRequest(BaseModel):
    customer_id: str
    subject: str
    message: str
    channel: str = "email"


def _active_agent_version(db: Session) -> AgentVersion:
    version = (
        db.query(AgentVersion)
        .filter_by(status="active")
        .order_by(AgentVersion.generation_number.desc())
        .first()
    )
    if version is None:
        raise HTTPException(500, "No active agent version. Run scripts/run_baseline.py first.")
    return version


def _serialize_ticket(t: Ticket) -> dict:
    return {
        "id": str(t.id),
        "customer_id": t.customer_id,
        "subject": t.subject,
        "status": t.status,
        "category": t.category,
        "priority": t.priority,
        "created_at": t.created_at.isoformat(),
        "resolved_at": t.resolved_at.isoformat() if t.resolved_at else None,
    }


@router.get("")
def list_tickets(db: Session = Depends(get_db), status: str | None = None):
    q = db.query(Ticket)
    if status:
        q = q.filter(Ticket.status == status)
    tickets = q.order_by(Ticket.created_at.desc()).limit(100).all()
    return [_serialize_ticket(t) for t in tickets]


@router.get("/{ticket_id}")
def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.get(Ticket, uuid.UUID(ticket_id))
    if ticket is None:
        raise HTTPException(404, "not found")
    messages = (
        db.query(TicketMessage).filter_by(ticket_id=ticket.id).order_by(TicketMessage.created_at).all()
    )
    tool_calls = db.query(ToolCall).filter_by(ticket_id=ticket.id).order_by(ToolCall.created_at).all()
    return {
        "ticket": _serialize_ticket(ticket),
        "messages": [
            {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()} for m in messages
        ],
        "tool_calls": [
            {
                "tool_name": tc.tool_name,
                "input": tc.input_json,
                "output": tc.output_json,
                "risk_level": tc.risk_level,
                "status": tc.status,
                "created_at": tc.created_at.isoformat(),
            }
            for tc in tool_calls
        ],
    }


@router.post("")
def create_ticket(req: CreateTicketRequest, db: Session = Depends(get_db)):
    agent_version = _active_agent_version(db)
    adapter = get_llm_adapter()

    ticket = Ticket(
        id=uuid.uuid4(),
        customer_id=req.customer_id,
        subject=req.subject,
        channel=req.channel,
        status="open",
    )
    db.add(ticket)
    db.flush()

    final_state = run_ticket(
        db,
        adapter,
        ticket=ticket,
        customer_message=req.message,
        agent_version_id=str(agent_version.id),
    )
    db.commit()

    return {
        "ticket_id": str(ticket.id),
        "outcome": final_state.get("outcome"),
        "final_response": final_state.get("final_response"),
    }
