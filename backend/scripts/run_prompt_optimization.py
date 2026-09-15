"""Runs one prompt-optimization learning cycle against the current active
agent version's latest eval run.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.learning.prompt_optimizer import run_prompt_optimization_cycle
from app.llm.factory import get_llm_adapter


def main() -> None:
    db = SessionLocal()
    adapter = get_llm_adapter()
    run_prompt_optimization_cycle(db, adapter, eval_set_version="v1")


if __name__ == "__main__":
    main()
