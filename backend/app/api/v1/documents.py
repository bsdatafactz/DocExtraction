import json
import os
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, require_admin
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.document import Correction, Document
from app.models.project import Project
from app.models.user import User
from app.schemas.confidence import DocumentConfidence, FieldConfidence
from app.schemas.document import (
    CorrectionRequest,
    DocumentDetail,
    DocumentStatus,
    DocumentSummary,
    UploadResponse,
)
from app.schemas.invoice import InvoiceExtraction
from app.schemas.project import IMPLEMENTED_DOCUMENT_TYPES
from app.schemas.registry import get_extraction_schema
from app.schemas.resume import ResumeExtraction
from app.services.pipeline import run_pipeline

# Creating/listing documents is scoped to a project — a document only makes
# sense in the context of the document type (and therefore extraction
# schema) its project was created with.
project_documents_router = APIRouter(prefix="/projects/{project_id}/documents", tags=["documents"])

# Everything else operates on a document by its own id, unscoped — a
# document's id is already globally unique, so re-scoping these by project
# would just add a redundant path segment.
router = APIRouter(prefix="/documents", tags=["documents"])


def _get_project_or_404(project_id: int, db: Session, user: User) -> Project:
    project = db.get(Project, project_id)
    if project is None or (user.role != "admin" and project.owner_id != user.id):
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _check_document_access(document: Document, user: User) -> None:
    if user.role != "admin" and document.project.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found")


@project_documents_router.post("", response_model=UploadResponse)
def upload_document(
    project_id: int,
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UploadResponse:
    project = _get_project_or_404(project_id, db, user)
    if project.document_type not in IMPLEMENTED_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Extraction for document type '{project.document_type}' isn't implemented yet.",
        )

    os.makedirs(settings.upload_dir, exist_ok=True)
    stored_name = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(settings.upload_dir, stored_name)
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    document = Document(
        project_id=project.id,
        filename=file.filename or stored_name,
        file_path=file_path,
        status=DocumentStatus.QUEUED.value,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    background_tasks.add_task(run_pipeline, document.id)

    return UploadResponse(id=document.id, filename=document.filename, status=DocumentStatus.QUEUED)


@project_documents_router.get("", response_model=list[DocumentSummary])
def list_documents(
    project_id: int,
    status: DocumentStatus | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[DocumentSummary]:
    _get_project_or_404(project_id, db, user)
    query = db.query(Document).filter(Document.project_id == project_id)
    if status is not None:
        query = query.filter(Document.status == status.value)
    documents = (
        query.order_by(Document.created_at.desc()).offset(offset).limit(min(limit, 200)).all()
    )
    summaries = []
    for doc in documents:
        aggregate = _aggregate_confidence(doc)
        summary = DocumentSummary.model_validate(doc)
        summary.aggregate_confidence = aggregate
        summaries.append(summary)
    return summaries


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(
    document_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> DocumentDetail:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    _check_document_access(document, user)

    extraction = _latest_extraction(document)
    confidence = _document_confidence(document)

    detail = DocumentDetail.model_validate(document)
    detail.document_type = document.project.document_type
    detail.aggregate_confidence = confidence.aggregate if confidence else None
    detail.extraction = extraction
    detail.confidence = confidence
    return detail


@router.get("/{document_id}/file")
def get_document_file(
    document_id: int, token: str | None = None, db: Session = Depends(get_db)
) -> FileResponse:
    # <img>/<iframe>/pdf.js can't attach an Authorization header, so this one
    # endpoint also accepts the JWT as a query param — still authenticated,
    # just via the one channel a browser-native embed can actually use.
    if token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_access_token(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    document = db.get(Document, document_id)
    if document is None or not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="Document file not found")
    _check_document_access(document, user)
    return FileResponse(
        document.file_path, filename=document.filename, content_disposition_type="inline"
    )


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> None:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    _check_document_access(document, user)

    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    db.delete(document)
    db.commit()


@router.post("/{document_id}/corrections", response_model=DocumentDetail)
def submit_corrections(
    document_id: int,
    request: CorrectionRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> DocumentDetail:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    for field_name, value in request.corrected_fields.items():
        if isinstance(value, list):
            corrected_value = json.dumps(value)
        elif value is None:
            corrected_value = None
        else:
            corrected_value = str(value)
        db.add(
            Correction(
                document_id=document.id,
                field_name=field_name,
                corrected_value=corrected_value,
                reviewer=admin.email,
            )
        )

    if request.approve:
        document.status = DocumentStatus.APPROVED.value
    db.commit()

    return get_document(document_id, db, admin)


def _latest_extraction(document: Document) -> InvoiceExtraction | ResumeExtraction | None:
    if not document.extractions:
        return None
    latest = max(document.extractions, key=lambda e: e.created_at)
    schema_cls, _ = get_extraction_schema(document.project.document_type)
    return schema_cls.model_validate(latest.raw_json)


def _document_confidence(document: Document) -> DocumentConfidence | None:
    if not document.field_confidences:
        return None
    fields = [
        FieldConfidence(
            field_name=fc.field_name,
            self_reported=fc.self_reported,
            heuristic_score=fc.heuristic_score,
            composite=fc.composite,
            escalated=fc.escalated,
            cross_model_agreement=fc.cross_model_agreement,
        )
        for fc in document.field_confidences
    ]
    aggregate = sum(f.composite for f in fields) / len(fields) if fields else 0.0
    return DocumentConfidence(
        document_id=document.id,
        fields=fields,
        aggregate=aggregate,
        needs_review=document.status == DocumentStatus.NEEDS_REVIEW.value,
    )


def _aggregate_confidence(document: Document) -> float | None:
    confidence = _document_confidence(document)
    return confidence.aggregate if confidence else None
