"""
Lightweight OpenAI-compatible LLM client.
Supports OpenAI GPT-4o, Qwen, or any OpenAI-compatible endpoint
by setting OPENAI_BASE_URL in config.
"""
from typing import Any
from openai import OpenAI, AsyncOpenAI
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

# Sync client (for Celery tasks)
_sync_client: OpenAI | None = None
# Async client (for FastAPI routes)
_async_client: AsyncOpenAI | None = None


def get_llm_client() -> OpenAI:
    global _sync_client
    if _sync_client is None:
        _sync_client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
        )
    return _sync_client


def get_async_llm_client() -> AsyncOpenAI:
    global _async_client
    if _async_client is None:
        _async_client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
        )
    return _async_client


def chat_complete(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 3000,
    response_format: dict | None = None,
) -> tuple[str, int]:
    """Returns (content, tokens_used)."""
    client = get_llm_client()
    kwargs: dict[str, Any] = {
        "model": model or settings.OPENAI_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        kwargs["response_format"] = response_format

    try:
        response = client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content or ""
        tokens = response.usage.total_tokens if response.usage else 0
        logger.debug("llm_call", model=kwargs["model"], tokens=tokens)
        return content, tokens
    except Exception as e:
        logger.error("llm_call_failed", error=str(e), model=kwargs["model"])
        raise


def extract_json(
    prompt: str,
    system: str = "You are a precise data extraction assistant. Always respond with valid JSON.",
    model: str | None = None,
) -> tuple[dict | list, int]:
    """Extract structured JSON from a prompt."""
    import json
    content, tokens = chat_complete(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        model=model,
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    try:
        return json.loads(content), tokens
    except json.JSONDecodeError:
        import re
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            return json.loads(match.group()), tokens
        raise ValueError(f"Could not parse JSON from response: {content[:200]}")
