from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agent_versions, approvals, evals, playbook, tickets
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title="Support Copilot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tickets.router)
app.include_router(approvals.router)
app.include_router(evals.router)
app.include_router(playbook.router)
app.include_router(agent_versions.router)


@app.get("/health")
def health():
    return {"status": "ok"}
