from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import AgentVersion
from app.db.session import get_db

router = APIRouter(prefix="/agent-versions", tags=["agent-versions"])


@router.get("")
def list_agent_versions(db: Session = Depends(get_db)):
    rows = db.query(AgentVersion).order_by(AgentVersion.generation_number).all()
    return [
        {
            "id": str(v.id),
            "generation_number": v.generation_number,
            "status": v.status,
            "created_by": v.created_by,
            "notes": v.notes,
            "activated_at": v.activated_at.isoformat() if v.activated_at else None,
            "created_at": v.created_at.isoformat(),
        }
        for v in rows
    ]
