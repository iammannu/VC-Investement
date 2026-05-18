"""
PDF text extraction with OCR fallback.
1. Try PyMuPDF text extraction
2. If text coverage < 40%, fallback to pytesseract OCR
"""
import io
from pathlib import Path
import structlog
import fitz  # PyMuPDF

from app.config import settings
from app.services.ai.llm_client import extract_json
from app.services.ai.prompts import EXTRACTION_PROMPT

logger = structlog.get_logger(__name__)


def extract_text_from_pdf(pdf_bytes: bytes) -> tuple[str, int, bool]:
    """
    Returns (raw_text, page_count, ocr_used).
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_count = len(doc)

    pages_text: list[str] = []
    for page in doc:
        pages_text.append(page.get_text())

    raw_text = "\n\n".join(pages_text)
    total_chars = sum(len(t) for t in pages_text)
    avg_chars_per_page = total_chars / max(page_count, 1)

    # If less than 100 chars/page on average → likely scanned, use OCR
    if avg_chars_per_page < 100 and settings.USE_OCR_FALLBACK:
        logger.info("ocr_fallback_triggered", avg_chars=avg_chars_per_page, pages=page_count)
        raw_text = _extract_via_ocr(doc)
        return raw_text, page_count, True

    logger.info("pdf_text_extracted", pages=page_count, chars=len(raw_text))
    return raw_text, page_count, False


def _extract_via_ocr(doc: fitz.Document) -> str:
    """Render each page to image, run pytesseract OCR."""
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        logger.warning("ocr_deps_missing", message="pytesseract/Pillow not installed, skipping OCR")
        return ""

    pages_text: list[str] = []
    for page_num, page in enumerate(doc):
        # Render at 200 DPI for good OCR quality
        mat = fitz.Matrix(200 / 72, 200 / 72)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        text = pytesseract.image_to_string(img, lang="eng")
        pages_text.append(text)
        logger.debug("ocr_page", page=page_num + 1, chars=len(text))

    return "\n\n".join(pages_text)


def extract_structured_data(raw_text: str) -> dict:
    """
    Use LLM to extract structured startup data from raw PDF text.
    Returns dict with startup fields.
    """
    # Truncate to ~50K chars to stay within context window
    truncated = raw_text[:50000]
    prompt = EXTRACTION_PROMPT.format(text=truncated)

    try:
        data, tokens = extract_json(prompt)
        logger.info("structured_data_extracted", tokens=tokens, fields=len(data))
        return data if isinstance(data, dict) else {}
    except Exception as e:
        logger.error("extraction_failed", error=str(e))
        return {}
