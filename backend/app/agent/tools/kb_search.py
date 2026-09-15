"""RAG-style search over Loopwork's help-center articles: embed the KB once
(cached), embed the query, rank by cosine similarity. Deliberately real
embeddings (not keyword match) so this exercises actual retrieval quality —
and so eval cases can test whether irrelevant/low-similarity results should
have been trusted.
"""

import math

from app.llm.base import LLMAdapter
from app.synthetic_data.loopwork_fixtures import KB_ARTICLES


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb + 1e-8)


_kb_embedding_cache: dict[str, list[list[float]]] = {}


def _get_kb_embeddings(adapter: LLMAdapter) -> list[list[float]]:
    if adapter.name not in _kb_embedding_cache:
        texts = [f"{a['title']}\n{a['body']}" for a in KB_ARTICLES]
        _kb_embedding_cache[adapter.name] = adapter.embed(texts)
    return _kb_embedding_cache[adapter.name]


def kb_search(query: str, adapter: LLMAdapter, top_k: int = 3) -> dict:
    q_emb = adapter.embed([query])[0]
    kb_embs = _get_kb_embeddings(adapter)
    scored = sorted(
        zip(KB_ARTICLES, kb_embs), key=lambda pair: -_cosine(q_emb, pair[1])
    )
    results = [
        {"id": a["id"], "title": a["title"], "body": a["body"], "score": round(_cosine(q_emb, e), 4)}
        for a, e in scored[:top_k]
    ]
    return {"results": results}
