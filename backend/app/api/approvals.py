from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import Approval
from app.db.session import get_db

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("")
def list_approvals(db: Session = Depends(get_db), status: str | None = None):
    q = db.query(Approval)
    if status:
        q = q.filter(Approval.status == status)
    rows = q.order_by(Approval.created_at.desc()).limit(100).all()
    return [
        {
            "id": str(a.id),
            "ticket_id": str(a.ticket_id),
            "status": a.status,
            "action_summary": a.action_summary,
            "reviewer": a.reviewer,
            "reviewed_at": a.reviewed_at.isoformat() if a.reviewed_at else None,
            "created_at": a.created_at.isoformat(),
        }
        for a in rows
    ]
