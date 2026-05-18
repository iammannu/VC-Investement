from openai import OpenAI
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL)
    return _client


def embed_texts(texts: list[str], batch_size: int = 100) -> list[list[float]]:
    """Embed a list of texts, returns list of embedding vectors."""
    client = _get_client()
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        # Clean empty strings (API will error)
        batch = [t[:8191] if t else " " for t in batch]
        response = client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=batch,
        )
        all_embeddings.extend([item.embedding for item in response.data])
        logger.debug("embeddings_created", batch=i // batch_size, count=len(batch))

    return all_embeddings


def embed_single(text: str) -> list[float]:
    return embed_texts([text])[0]
