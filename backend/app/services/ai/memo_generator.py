"""
Memo generation orchestrator.
Generates all 8 sections sequentially, each with RAG-retrieved context.
"""
import json
import re
import time
from collections.abc import Callable
from uuid import UUID
from sqlalchemy.orm import Session
import structlog

from app.services.ai.llm_client import chat_complete
from app.services.ai.retrieval import retrieve_context, retrieve_multi
from app.services.ai.prompts import (
    EXECUTIVE_SUMMARY_PROMPT,
    PROBLEM_SOLUTION_PROMPT,
    MARKET_ANALYSIS_PROMPT,
    COMPETITOR_ANALYSIS_PROMPT,
    FOUNDER_ANALYSIS_PROMPT,
    FINANCIAL_ANALYSIS_PROMPT,
    RISK_ANALYSIS_PROMPT,
    RECOMMENDATION_PROMPT,
)

logger = structlog.get_logger(__name__)

SYSTEM_PROMPT = (
    "You are a senior VC analyst at a top-tier investment firm. "
    "Write professional, structured investment memos. Be specific, honest, and decisive. "
    "Do not fabricate numbers or metrics. When data is missing, say so explicitly."
)

SECTIONS_CONFIG = [
    {
        "key": "executive_summary",
        "title": "Executive Summary",
        "order": 1,
        "query": "company overview mission product traction highlights",
    },
    {
        "key": "problem_solution",
        "title": "Problem & Solution",
        "order": 2,
        "query": "problem pain point solution product technology differentiation",
    },
    {
        "key": "market_analysis",
        "title": "Market Analysis",
        "order": 3,
        "query": "market size TAM SAM SOM market opportunity industry trends",
    },
    {
        "key": "competitor_analysis",
        "title": "Competitive Analysis",
        "order": 4,
        "query": "competitors competitive advantage moat differentiation landscape",
    },
    {
        "key": "founder_analysis",
        "title": "Founder & Team",
        "order": 5,
        "query": "founders team background experience qualifications expertise",
    },
    {
        "key": "financial_analysis",
        "title": "Financial & Traction",
        "order": 6,
        "query": "revenue ARR MRR growth customers traction metrics unit economics CAC LTV",
    },
    {
        "key": "risk_analysis",
        "title": "Risk Analysis",
        "order": 7,
        "query": "risks challenges competition regulatory execution market",
    },
    {
        "key": "recommendation",
        "title": "Investment Recommendation",
        "order": 8,
        "query": "investment thesis recommendation valuation ask check size",
    },
]


def _format_startup_data(startup_data: dict, research_map: dict) -> str:
    lines = [f"STARTUP: {startup_data.get('startup_name', 'Unknown')}"]
    for k, v in startup_data.items():
        if v is not None:
            lines.append(f"{k}: {json.dumps(v) if isinstance(v, (dict, list)) else v}")
    return "\n".join(lines)


def _build_section_prompt(
    section_key: str,
    startup_data: dict,
    research_map: dict,
    context: str,
) -> str:
    common = {
        "startup_data": _format_startup_data(startup_data, research_map),
        "retrieved_context": context,
        "market_research": json.dumps(research_map.get("market", {}), indent=2),
        "competitor_research": json.dumps(research_map.get("competitor", {}), indent=2),
        "founder_research": json.dumps(research_map.get("founder", {}), indent=2),
        "memo_summary": json.dumps(research_map.get("_memo_so_far", {}), indent=2),
    }

    templates = {
        "executive_summary": EXECUTIVE_SUMMARY_PROMPT,
        "problem_solution": PROBLEM_SOLUTION_PROMPT,
        "market_analysis": MARKET_ANALYSIS_PROMPT,
        "competitor_analysis": COMPETITOR_ANALYSIS_PROMPT,
        "founder_analysis": FOUNDER_ANALYSIS_PROMPT,
        "financial_analysis": FINANCIAL_ANALYSIS_PROMPT,
        "risk_analysis": RISK_ANALYSIS_PROMPT,
        "recommendation": RECOMMENDATION_PROMPT,
    }

    template = templates.get(section_key, "Write the {section_key} section.")
    return template.format(**common)


def generate_all_sections(
    startup_id: str | UUID,
    startup_data: dict,
    research_map: dict,
    on_section_complete: Callable | None = None,
) -> list[dict]:
    """
    Generate all memo sections. Returns list of section dicts.
    on_section_complete(section_key) called after each section for progress updates.
    """
    sections = []
    total_tokens = 0
    memo_so_far: dict[str, str] = {}

    for config in SECTIONS_CONFIG:
        key = config["key"]
        logger.info("generating_section", section=key, startup_id=str(startup_id))

        context = retrieve_context(
            query=config["query"],
            startup_id=startup_id,
            top_k=6,
        )

        research_map["_memo_so_far"] = memo_so_far
        prompt = _build_section_prompt(key, startup_data, research_map, context)

        content, tokens = chat_complete(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2500,
        )

        total_tokens += tokens
        memo_so_far[key] = content[:500]  # Track summary for recommendation section

        section = {
            "section_key": key,
            "section_order": config["order"],
            "title": config["title"],
            "content": content,
            "content_json": None,
            "citations": _extract_citations(content),
        }
        sections.append(section)

        if on_section_complete:
            on_section_complete(key)

        logger.info("section_complete", section=key, tokens=tokens)

    return sections, total_tokens


def extract_recommendation_meta(recommendation_section_content: str) -> dict:
    """Extract recommendation enum and confidence from the recommendation section."""
    match = re.search(r"```json\s*(\{.*?\})\s*```", recommendation_section_content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    # Fallback: parse from text
    content_lower = recommendation_section_content.lower()
    if "strong invest" in content_lower or "strong_invest" in content_lower:
        return {"recommendation": "strong_invest", "confidence_score": 0.85}
    elif "pass" in content_lower:
        return {"recommendation": "pass", "confidence_score": 0.70}
    elif "watch" in content_lower:
        return {"recommendation": "watch", "confidence_score": 0.60}
    return {"recommendation": "invest", "confidence_score": 0.65}


def _extract_citations(content: str) -> list[dict]:
    """Extract [Source: URL] citations from content."""
    pattern = r"\[Source:\s*(https?://[^\]]+)\]"
    urls = re.findall(pattern, content)
    return [{"url": url.strip()} for url in urls]
