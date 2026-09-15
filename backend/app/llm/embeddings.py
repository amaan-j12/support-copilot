"""Local (free, offline) embedding fallback used by ClaudeCLIAdapter.

Lazily loads a small sentence-transformers model on first use so importing
this module (and the rest of the app) doesn't pay the torch import cost
unless embeddings are actually requested.
"""

from functools import lru_cache

from app.core.config import get_settings


@lru_cache
def _model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(get_settings().local_embedding_model)


def embed_local(texts: list[str]) -> list[list[float]]:
    vectors = _model().encode(texts, normalize_embeddings=True)
    return [v.tolist() for v in vectors]
