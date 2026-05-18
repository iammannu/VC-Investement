"""
Text chunker: splits text into overlapping chunks for embedding.
Uses token-aware splitting to stay within embedding model limits.
"""
import re
from uuid import uuid4
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

CHUNK_SIZE = settings.CHUNK_SIZE        # ~800 tokens
CHUNK_OVERLAP = settings.CHUNK_OVERLAP  # ~100 token overlap
MAX_CHUNK_CHARS = CHUNK_SIZE * 4        # ~4 chars per token
OVERLAP_CHARS = CHUNK_OVERLAP * 4


def chunk_text(
    text: str,
    source_type: str = "deck",
    page_number: int | None = None,
) -> list[dict]:
    """
    Split text into chunks. Returns list of chunk dicts ready for embedding.
    Each chunk: {id, text, index, source_type, page_number}
    """
    if not text or not text.strip():
        return []

    # Split on paragraph boundaries first
    paragraphs = _split_paragraphs(text)
    chunks = _merge_paragraphs(paragraphs, MAX_CHUNK_CHARS, OVERLAP_CHARS)

    result = []
    for i, chunk_text in enumerate(chunks):
        chunk_text = chunk_text.strip()
        if len(chunk_text) < 50:  # Skip trivially short chunks
            continue
        result.append({
            "id": str(uuid4()).replace("-", ""),  # Qdrant needs str or int point ID
            "text": chunk_text,
            "index": i,
            "source_type": source_type,
            "page_number": page_number,
        })

    logger.debug("text_chunked", chunks=len(result), source=source_type)
    return result


def chunk_pages(pages_text: list[str], source_type: str = "deck") -> list[dict]:
    """Chunk a list of page texts, preserving page number metadata."""
    all_chunks: list[dict] = []
    for page_num, page_text in enumerate(pages_text, 1):
        chunks = chunk_text(page_text, source_type=source_type, page_number=page_num)
        all_chunks.extend(chunks)
    # Re-index
    for i, chunk in enumerate(all_chunks):
        chunk["index"] = i
    return all_chunks


def _split_paragraphs(text: str) -> list[str]:
    paras = re.split(r"\n{2,}|\r\n{2,}", text)
    return [p.strip() for p in paras if p.strip()]


def _merge_paragraphs(paragraphs: list[str], max_chars: int, overlap_chars: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for para in paragraphs:
        para_len = len(para)

        if current_len + para_len > max_chars and current:
            # Flush current chunk
            chunks.append("\n\n".join(current))
            # Add overlap: keep last N chars worth of paragraphs
            overlap_text = ""
            for p in reversed(current):
                if len(overlap_text) + len(p) <= overlap_chars:
                    overlap_text = p + "\n\n" + overlap_text
                else:
                    break
            current = [overlap_text.strip()] if overlap_text.strip() else []
            current_len = len(overlap_text)

        current.append(para)
        current_len += para_len

    if current:
        chunks.append("\n\n".join(current))

    return chunks
