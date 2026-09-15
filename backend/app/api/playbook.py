from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import PlaybookEntry
from app.db.session import get_db

router = APIRouter(prefix="/playbook", tags=["playbook"])


@router.get("")
def list_playbook(db: Session = Depends(get_db), status: str | None = None):
    q = db.query(PlaybookEntry)
    if status:
        q = q.filter(PlaybookEntry.status == status)
    rows = q.order_by(PlaybookEntry.created_at.desc()).limit(200).all()
    return [
        {
            "id": str(p.id),
            "title": p.title,
            "content": p.content,
            "status": p.status,
            "promoted_at": p.promoted_at.isoformat() if p.promoted_at else None,
            "version_introduced": str(p.version_introduced) if p.version_introduced else None,
            "created_at": p.created_at.isoformat(),
        }
        for p in rows
    ]
