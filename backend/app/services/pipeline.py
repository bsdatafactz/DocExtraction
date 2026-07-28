"""Orchestrates one document through the full pipeline. Called as a
background task from the upload endpoint."""

import logging
from datetime import datetime

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.document import Document, Extraction, FieldConfidenceRecord
from app.schemas.document import DocumentStatus
from app.schemas.registry import get_extraction_schema
from app.services import confidence as confidence_service
from app.services import extraction as extraction_service
from app.services import parsing as parsing_service

logger = logging.getLogger(__name__)


def run_pipeline(document_id: int) -> None:
    """Runs in a FastAPI BackgroundTask, after the request that queued it
    has already returned — so it opens its own DB session rather than
    reusing the request-scoped one, which `get_db` closes as soon as the
    response is sent."""
    db = SessionLocal()
    try:
        document = db.get(Document, document_id)
        if document is None:
            return

        schema_cls, prompt_intro = get_extraction_schema(document.project.document_type)

        document.status = DocumentStatus.PARSING.value
        document.parsing_started_at = datetime.utcnow()
        db.commit()
        parsed = parsing_service.parse_document(document.file_path)
        document.is_scanned = parsed.is_scanned
        document.parsing_completed_at = datetime.utcnow()

        ocr_scores = [p.ocr_confidence for p in parsed.pages if p.ocr_confidence is not None]
        ocr_confidence = sum(ocr_scores) / len(ocr_scores) if ocr_scores else None

        document.status = DocumentStatus.EXTRACTING.value
        document.extraction_started_at = datetime.utcnow()
        db.commit()
        result = extraction_service.extract_with_deepseek(parsed.full_text, schema_cls, prompt_intro)
        db.add(
            Extraction(
                document_id=document.id,
                model_name="deepseek-chat",
                raw_json=result.model_dump(mode="json"),
            )
        )

        conf = confidence_service.score_document(document.id, result, ocr_confidence=ocr_confidence)

        if confidence_service.needs_escalation(conf):
            document.status = DocumentStatus.ESCALATED.value
            db.commit()
            escalated_result = extraction_service.extract_with_azure_openai(
                parsed.full_text, schema_cls, prompt_intro
            )
            db.add(
                Extraction(
                    document_id=document.id,
                    model_name=f"azure-openai:{settings.azure_openai_deployment}",
                    raw_json=escalated_result.model_dump(mode="json"),
                    is_escalation=True,
                )
            )
            conf = confidence_service.score_document(
                document.id,
                escalated_result,
                escalated=True,
                prior_extraction=result,
                ocr_confidence=ocr_confidence,
            )

        for field_conf in conf.fields:
            db.add(
                FieldConfidenceRecord(
                    document_id=document.id,
                    field_name=field_conf.field_name,
                    self_reported=field_conf.self_reported,
                    heuristic_score=field_conf.heuristic_score,
                    composite=field_conf.composite,
                    escalated=field_conf.escalated,
                    cross_model_agreement=field_conf.cross_model_agreement,
                )
            )

        document.extraction_completed_at = datetime.utcnow()
        document.status = (
            DocumentStatus.NEEDS_REVIEW.value if conf.needs_review else DocumentStatus.APPROVED.value
        )
        db.commit()

    except Exception:
        logger.exception("Pipeline failed for document %s", document_id)
        db.rollback()
        document = db.get(Document, document_id)
        if document is not None:
            document.status = DocumentStatus.FAILED.value
            db.commit()
    finally:
        db.close()
