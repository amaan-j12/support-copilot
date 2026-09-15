"""Runs one reflection/playbook learning cycle: turns unincorporated
reflections into a candidate agent generation, evaluates it against the
frozen eval set, and promotes or rejects it. Run scripts/simulate_traffic.py
first so there's something to learn from.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.learning.playbook_promote import run_reflection_learning_cycle
from app.llm.factory import get_llm_adapter


def main() -> None:
    db = SessionLocal()
    adapter = get_llm_adapter()
    run_reflection_learning_cycle(db, adapter, eval_set_version="v1")


if __name__ == "__main__":
    main()
