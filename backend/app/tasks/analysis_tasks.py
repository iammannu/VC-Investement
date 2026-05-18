"""
Full analysis pipeline:
1. Extract PDF text + OCR fallback
2. Scrape startup website
3. Chunk + embed all content → Qdrant
4. Extract structured startup data (LLM)
5. Research: market, competitors, founders
6. Generate all 8 memo sections
7. Finalize memo
"""
import json
import time
from uuid import UUID

import structlog
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)

# Use sync SQLAlchemy for Celery tasks
def _get_sync_db() -> Session:
    engine = create_engine(settings.DATABASE_URL_SYNC, pool_pre_ping=True)
    return Session(engine)


def _update_job(db: Session, job_id: str, step: str, completed_steps: list[str]) -> None:
    from app.models.memo import AnalysisJob
    job = db.get(AnalysisJob, UUID(job_id))
    if job:
        job.current_step = step
        job.steps_completed = completed_steps
        db.commit()


@celery_app.task(bind=True, name="app.tasks.analysis_tasks.run_full_analysis", max_retries=2)
def run_full_analysis(self, startup_id: str, job_id: str) -> dict:
    from app.models.startup import Startup, StartupStatus
    from app.models.document import Document, DocumentType, DocumentStatus
    from app.models.memo import Memo, MemoSection, MemoStatus, ResearchData, ResearchType, AnalysisJob
    from app.core.storage import download_file
    from app.services.document.pdf_extractor import extract_text_from_pdf, extract_structured_data
    from app.services.document.web_scraper import scrape_website
    from app.services.document.chunker import chunk_text
    from app.services.ai.embeddings import embed_texts
    from app.core.vector_store import upsert_chunks
    from app.services.ai.memo_generator import generate_all_sections, extract_recommendation_meta

    db = _get_sync_db()
    start_time = time.time()
    completed: list[str] = []

    try:
        # ── Load startup ───────────────────────────────────
        startup = db.get(Startup, UUID(startup_id))
        if not startup:
            raise ValueError(f"Startup {startup_id} not found")

        startup.status = StartupStatus.PROCESSING
        db.commit()
        _update_job(db, job_id, "extracting_pdf", completed)

        # ── Step 1: PDF Extraction ─────────────────────────
        logger.info("step_pdf_extraction", startup_id=startup_id)
        pdf_doc = db.execute(
            select(Document).where(
                Document.startup_id == UUID(startup_id),
                Document.doc_type == DocumentType.PITCH_DECK,
            )
        ).scalar_one_or_none()

        raw_text = ""
        page_count = 0
        all_chunks: list[dict] = []

        if pdf_doc and pdf_doc.storage_key:
            pdf_bytes = download_file(pdf_doc.storage_key)
            raw_text, page_count, ocr_used = extract_text_from_pdf(pdf_bytes)

            pdf_doc.raw_text = raw_text
            pdf_doc.page_count = page_count
            pdf_doc.ocr_used = ocr_used
            pdf_doc.status = DocumentStatus.DONE
            db.commit()

            # Chunk text per page for better retrieval metadata
            import fitz
            doc_fitz = fitz.open(stream=pdf_bytes, filetype="pdf")
            pages_text = [page.get_text() for page in doc_fitz]
            from app.services.document.chunker import chunk_pages
            all_chunks.extend(chunk_pages(pages_text, source_type="deck"))

        completed.append("pdf_extraction")
        _update_job(db, job_id, "scraping_website", completed)

        # ── Step 2: Website Scraping ───────────────────────
        logger.info("step_website_scraping", startup_id=startup_id)
        website_text = ""
        if startup.website_url:
            website_text, _ = scrape_website(startup.website_url, use_playwright=False)
            if website_text:
                web_doc = db.execute(
                    select(Document).where(
                        Document.startup_id == UUID(startup_id),
                        Document.doc_type == DocumentType.WEBSITE,
                    )
                ).scalar_one_or_none()

                if not web_doc:
                    from app.models.document import Document as Doc
                    web_doc = Doc(
                        startup_id=UUID(startup_id),
                        doc_type=DocumentType.WEBSITE,
                        source_url=startup.website_url,
                        status=DocumentStatus.DONE,
                    )
                    db.add(web_doc)
                    db.flush()

                web_doc.raw_text = website_text
                web_doc.status = DocumentStatus.DONE
                db.commit()

                web_chunks = chunk_text(website_text, source_type="website")
                all_chunks.extend(web_chunks)

        completed.append("website_scraping")
        _update_job(db, job_id, "embedding_content", completed)

        # ── Step 3: Embed + Store in Qdrant ───────────────
        logger.info("step_embedding", startup_id=startup_id, chunks=len(all_chunks))
        if all_chunks:
            texts = [c["text"] for c in all_chunks]
            embeddings = embed_texts(texts)
            for chunk, emb in zip(all_chunks, embeddings):
                chunk["embedding"] = emb
            upsert_chunks(all_chunks, startup_id, pdf_doc.id if pdf_doc else startup_id)

        completed.append("embedding")
        _update_job(db, job_id, "extracting_startup_data", completed)

        # ── Step 4: Extract Structured Startup Data ────────
        logger.info("step_structured_extraction", startup_id=startup_id)
        combined_text = f"{raw_text}\n\n{website_text}"
        startup_data = extract_structured_data(combined_text)

        # Update startup record with extracted data
        startup.name = startup_data.get("startup_name") or startup.name
        startup.industry = startup_data.get("industry")
        startup.stage = startup_data.get("stage")
        startup.geography = startup_data.get("geography")
        startup.founding_year = startup_data.get("founding_year")
        startup.extracted_data = startup_data
        db.commit()

        completed.append("startup_extraction")
        _update_job(db, job_id, "researching_market", completed)

        # ── Step 5: Market Research ────────────────────────
        logger.info("step_market_research", startup_id=startup_id)
        market_data = _research_market(startup_data)
        _save_research(db, startup_id, ResearchType.MARKET, market_data)

        completed.append("market_research")
        _update_job(db, job_id, "researching_competitors", completed)

        # ── Step 5b: Competitor Research ──────────────────
        competitor_data = _research_competitors(startup_data)
        _save_research(db, startup_id, ResearchType.COMPETITOR, competitor_data)

        # ── Step 5c: Founder Research ──────────────────────
        founder_data = _research_founders(startup_data)
        _save_research(db, startup_id, ResearchType.FOUNDER, founder_data)

        completed.append("research")
        _update_job(db, job_id, "generating_memo", completed)

        # ── Step 6: Create Memo Record ─────────────────────
        logger.info("step_memo_generation", startup_id=startup_id)
        memo = Memo(
            startup_id=UUID(startup_id),
            status=MemoStatus.GENERATING,
            version=1,
        )
        db.add(memo)
        db.flush()

        # Update job with memo_id
        job = db.get(AnalysisJob, UUID(job_id))
        if job:
            job.memo_id = memo.id
        db.commit()

        research_map = {
            "market": market_data,
            "competitor": competitor_data,
            "founder": founder_data,
        }

        def on_section_complete(section_key: str):
            _update_job(db, job_id, f"generating_{section_key}", completed)

        # ── Step 7: Generate Memo Sections ────────────────
        sections_data, total_tokens = generate_all_sections(
            startup_id=startup_id,
            startup_data=startup_data,
            research_map=research_map,
            on_section_complete=on_section_complete,
        )

        # Persist sections
        for s in sections_data:
            section = MemoSection(
                memo_id=memo.id,
                section_key=s["section_key"],
                section_order=s["section_order"],
                title=s["title"],
                content=s["content"],
                content_json=s.get("content_json"),
                citations=s.get("citations", []),
            )
            db.add(section)

        # Extract recommendation meta from last section
        rec_section = next((s for s in sections_data if s["section_key"] == "recommendation"), None)
        rec_meta = extract_recommendation_meta(rec_section["content"]) if rec_section else {}

        from app.models.memo import Recommendation
        memo.status = MemoStatus.COMPLETE
        memo.recommendation = Recommendation(rec_meta.get("recommendation", "watch"))
        memo.confidence_score = rec_meta.get("confidence_score", 0.6)
        memo.total_tokens_used = total_tokens
        memo.generation_time_seconds = int(time.time() - start_time)

        startup.status = StartupStatus.DONE
        db.commit()

        completed.append("memo_generation")
        _update_job(db, job_id, "done", completed)

        logger.info(
            "analysis_complete",
            startup_id=startup_id,
            memo_id=str(memo.id),
            tokens=total_tokens,
            seconds=memo.generation_time_seconds,
        )
        return {"memo_id": str(memo.id), "status": "complete"}

    except Exception as e:
        logger.error("analysis_failed", startup_id=startup_id, error=str(e))
        # Update startup and job to failed state
        try:
            startup = db.get(Startup, UUID(startup_id))
            if startup:
                startup.status = StartupStatus.FAILED
                db.commit()
            from app.models.memo import AnalysisJob as AJ
            job = db.get(AJ, UUID(job_id))
            if job:
                job.current_step = "failed"
                job.error_message = str(e)
                db.commit()
        except Exception:
            pass
        raise self.retry(exc=e, countdown=60) if self.request.retries < 2 else e
    finally:
        db.close()


def _research_market(startup_data: dict) -> dict:
    """Generate market research via LLM (web search optional in production)."""
    from app.services.ai.llm_client import extract_json
    industry = startup_data.get("industry", "technology")
    problem = startup_data.get("problem_statement", "")
    prompt = f"""
Research the market for a startup in the {industry} industry.
Problem they solve: {problem}

Provide market analysis in JSON:
{{
  "tam_estimate": "string with $ amount and reasoning",
  "sam_estimate": "string",
  "som_estimate": "string",
  "market_growth_rate": "string e.g. '23% CAGR'",
  "key_trends": ["trend1", "trend2", "trend3"],
  "market_timing": "string assessment",
  "sources_used": ["description of data sources referenced"]
}}
Use realistic estimates. State uncertainty clearly.
"""
    try:
        data, _ = extract_json(prompt)
        return data if isinstance(data, dict) else {}
    except Exception as e:
        logger.error("market_research_failed", error=str(e))
        return {"error": str(e)}


def _research_competitors(startup_data: dict) -> dict:
    from app.services.ai.llm_client import extract_json
    name = startup_data.get("startup_name", "")
    industry = startup_data.get("industry", "")
    problem = startup_data.get("problem_statement", "")
    prompt = f"""
Identify competitors for: {name} in {industry}
They solve: {problem}

Return JSON:
{{
  "competitors": [
    {{
      "name": "string",
      "description": "string",
      "estimated_funding": "string or null",
      "key_strength": "string",
      "key_weakness": "string",
      "differentiator_vs_startup": "string"
    }}
  ],
  "competitive_dynamics": "string summary",
  "moat_assessment": "string"
}}
List 4-6 real competitors if known, or likely competitors based on the space.
"""
    try:
        data, _ = extract_json(prompt)
        return data if isinstance(data, dict) else {}
    except Exception as e:
        logger.error("competitor_research_failed", error=str(e))
        return {"error": str(e)}


def _research_founders(startup_data: dict) -> dict:
    from app.services.ai.llm_client import extract_json
    founders = startup_data.get("founders", [])
    if not founders:
        return {"founders_assessed": [], "team_quality": "insufficient data"}
    prompt = f"""
Assess these founders for their startup in {startup_data.get('industry', 'tech')}:
{json.dumps(founders, indent=2)}

Return JSON:
{{
  "founders_assessed": [
    {{
      "name": "string",
      "founder_market_fit_score": "1-10",
      "relevant_experience": "string",
      "red_flags": ["string"] or [],
      "green_flags": ["string"] or []
    }}
  ],
  "team_quality": "exceptional|strong|adequate|weak|insufficient_data",
  "key_gaps": ["string"],
  "overall_assessment": "string"
}}
"""
    try:
        data, _ = extract_json(prompt)
        return data if isinstance(data, dict) else {}
    except Exception as e:
        logger.error("founder_research_failed", error=str(e))
        return {"error": str(e)}


def _save_research(db: Session, startup_id: str, research_type, data: dict) -> None:
    from app.models.memo import ResearchData
    rd = ResearchData(
        startup_id=UUID(startup_id),
        research_type=research_type,
        data=data,
        model_used=settings.OPENAI_MODEL,
    )
    db.add(rd)
    db.commit()


@celery_app.task(name="app.tasks.analysis_tasks.regenerate_memo_section")
def regenerate_memo_section(memo_id: str, section_key: str) -> dict:
    from app.models.memo import Memo, MemoSection
    from app.models.startup import Startup
    from app.services.ai.memo_generator import SECTIONS_CONFIG, _build_section_prompt, _extract_citations
    from app.services.ai.retrieval import retrieve_context
    from app.services.ai.llm_client import chat_complete
    from app.services.ai.memo_generator import SYSTEM_PROMPT

    db = _get_sync_db()
    try:
        memo = db.get(Memo, UUID(memo_id))
        if not memo:
            raise ValueError(f"Memo {memo_id} not found")

        startup = db.get(Startup, memo.startup_id)
        startup_data = startup.extracted_data or {}

        research_data = {}
        for rd in startup.research_data if hasattr(startup, 'research_data') else []:
            research_data[rd.research_type.value] = rd.data

        config = next((s for s in SECTIONS_CONFIG if s["key"] == section_key), None)
        if not config:
            raise ValueError(f"Unknown section: {section_key}")

        context = retrieve_context(config["query"], memo.startup_id)
        prompt = _build_section_prompt(section_key, startup_data, research_data, context)
        content, _ = chat_complete(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )

        section = db.execute(
            select(MemoSection).where(
                MemoSection.memo_id == UUID(memo_id),
                MemoSection.section_key == section_key,
            )
        ).scalar_one_or_none()

        if section:
            section.content = content
            section.citations = _extract_citations(content)
            section.is_edited = False
        db.commit()

        return {"status": "done", "section_key": section_key}
    finally:
        db.close()
