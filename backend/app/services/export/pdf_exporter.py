"""
PDF export using WeasyPrint + Jinja2 templates.
"""
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import structlog

logger = structlog.get_logger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"


def generate_memo_pdf(memo) -> bytes:
    """Render memo to PDF bytes."""
    try:
        from weasyprint import HTML, CSS
    except ImportError:
        logger.warning("weasyprint_not_installed", message="Falling back to plain text")
        return _fallback_text_pdf(memo)

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("memo.html")

    html_content = template.render(
        memo=memo,
        startup=memo.startup,
        sections=sorted(memo.sections, key=lambda s: s.section_order),
        recommendation_display={
            "strong_invest": "⚡ STRONG INVEST",
            "invest": "✅ INVEST",
            "watch": "👁 WATCH",
            "pass": "❌ PASS",
        }.get(memo.recommendation.value if memo.recommendation else "", "—"),
        confidence_pct=int((float(memo.confidence_score or 0)) * 100),
    )

    pdf_bytes = HTML(string=html_content, base_url=str(TEMPLATES_DIR)).write_pdf()
    logger.info("pdf_generated", memo_id=str(memo.id), size_kb=len(pdf_bytes) // 1024)
    return pdf_bytes


def _fallback_text_pdf(memo) -> bytes:
    """Simple text-based fallback when WeasyPrint is unavailable."""
    lines = [
        f"INVESTMENT MEMO",
        f"Company: {memo.startup.name or 'Unknown'}",
        f"Generated: {memo.created_at.strftime('%Y-%m-%d')}",
        f"Recommendation: {memo.recommendation.value if memo.recommendation else 'N/A'}",
        "",
    ]
    for section in sorted(memo.sections, key=lambda s: s.section_order):
        lines.append(f"\n{'='*60}")
        lines.append(f"{section.title.upper()}")
        lines.append("=" * 60)
        lines.append(section.content or "")

    return "\n".join(lines).encode("utf-8")
