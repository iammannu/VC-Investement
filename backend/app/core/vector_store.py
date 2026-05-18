from typing import Any
from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchRequest,
)
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

_client: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    return _client


async def init_vector_store() -> None:
    client = get_qdrant_client()
    collections = [c.name for c in client.get_collections().collections]

    if settings.QDRANT_COLLECTION not in collections:
        client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=settings.QDRANT_VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )
        logger.info("qdrant_collection_created", collection=settings.QDRANT_COLLECTION)
    else:
        logger.info("qdrant_collection_exists", collection=settings.QDRANT_COLLECTION)


def upsert_chunks(
    chunks: list[dict[str, Any]],
    startup_id: str | UUID,
    document_id: str | UUID,
) -> None:
    client = get_qdrant_client()
    points = [
        PointStruct(
            id=chunk["id"],
            vector=chunk["embedding"],
            payload={
                "text": chunk["text"],
                "startup_id": str(startup_id),
                "document_id": str(document_id),
                "chunk_index": chunk["index"],
                "source_type": chunk.get("source_type", "deck"),
                "page_number": chunk.get("page_number"),
            },
        )
        for chunk in chunks
    ]
    client.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)
    logger.info("chunks_upserted", count=len(points), startup_id=str(startup_id))


def search_chunks(
    query_vector: list[float],
    startup_id: str | UUID,
    top_k: int = 8,
    score_threshold: float = 0.35,
) -> list[dict[str, Any]]:
    client = get_qdrant_client()
    results = client.search(
        collection_name=settings.QDRANT_COLLECTION,
        query_vector=query_vector,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="startup_id",
                    match=MatchValue(value=str(startup_id)),
                )
            ]
        ),
        limit=top_k,
        score_threshold=score_threshold,
        with_payload=True,
    )
    return [
        {
            "text": r.payload["text"],
            "score": r.score,
            "chunk_index": r.payload.get("chunk_index"),
            "source_type": r.payload.get("source_type"),
            "page_number": r.payload.get("page_number"),
        }
        for r in results
    ]


def delete_startup_chunks(startup_id: str | UUID) -> None:
    client = get_qdrant_client()
    client.delete(
        collection_name=settings.QDRANT_COLLECTION,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="startup_id",
                    match=MatchValue(value=str(startup_id)),
                )
            ]
        ),
    )
    logger.info("chunks_deleted", startup_id=str(startup_id))
