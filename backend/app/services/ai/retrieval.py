"""
RAG retrieval: embed query → search Qdrant → return ranked chunks.
"""
from uuid import UUID
import structlog

from app.services.ai.embeddings import embed_single
from app.core.vector_store import search_chunks

logger = structlog.get_logger(__name__)


def retrieve_context(
    query: str,
    startup_id: str | UUID,
    top_k: int = 6,
    score_threshold: float = 0.30,
) -> str:
    """Retrieve relevant document chunks and format as context string."""
    query_vector = embed_single(query)
    chunks = search_chunks(
        query_vector=query_vector,
        startup_id=startup_id,
        top_k=top_k,
        score_threshold=score_threshold,
    )

    if not chunks:
        return "No relevant context found in uploaded documents."

    lines: list[str] = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("source_type", "document")
        page = chunk.get("page_number")
        page_ref = f" (page {page})" if page else ""
        lines.append(f"[{i}] [{source}{page_ref}]\n{chunk['text']}")

    logger.debug("context_retrieved", startup_id=str(startup_id), chunks=len(chunks), query=query[:60])
    return "\n\n---\n\n".join(lines)


def retrieve_multi(
    queries: list[str],
    startup_id: str | UUID,
    top_k_per_query: int = 4,
) -> str:
    """Retrieve context for multiple queries, deduplicate by text."""
    seen: set[str] = set()
    all_chunks: list[str] = []

    for query in queries:
        query_vector = embed_single(query)
        chunks = search_chunks(
            query_vector=query_vector,
            startup_id=startup_id,
            top_k=top_k_per_query,
        )
        for chunk in chunks:
            text = chunk["text"]
            if text not in seen:
                seen.add(text)
                all_chunks.append(text)

    if not all_chunks:
        return "No relevant context found."

    return "\n\n---\n\n".join(f"[{i+1}] {t}" for i, t in enumerate(all_chunks))
