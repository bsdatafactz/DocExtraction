"""Parse/OCR routing.

Digital PDFs (have an extractable text layer) go through PyMuPDF. Pages with
no usable text layer are treated as scanned/image-based and routed to OCR.
This per-page routing, not a single fixed parser, is what lets one pipeline
handle both the clean digital invoices and the skewed scans in the test set.
"""

import os
import tempfile

import fitz
from pydantic import BaseModel

# Below this many characters of extracted text, a page is treated as
# image-based rather than digital — a bare page number or stray glyph from a
# scan shouldn't count as "has a text layer".
DIGITAL_TEXT_MIN_CHARS = 20

# Higher than a PDF page's default render DPI (72) — OCR accuracy drops
# sharply below ~150-200 DPI on real scans.
_OCR_RENDER_DPI = 200

_ocr_engine = None


class ParsedPage(BaseModel):
    page_number: int
    text: str
    is_scanned: bool
    ocr_confidence: float | None = None


class ParsedDocument(BaseModel):
    pages: list[ParsedPage]
    is_scanned: bool
    full_text: str


def parse_document(file_path: str) -> ParsedDocument:
    doc = fitz.open(file_path)
    pages: list[ParsedPage] = []
    for page_number, page in enumerate(doc):
        text = page.get_text()
        if len(text.strip()) >= DIGITAL_TEXT_MIN_CHARS:
            pages.append(ParsedPage(page_number=page_number, text=text, is_scanned=False))
        else:
            ocr_text, ocr_confidence = _run_ocr(page)
            pages.append(
                ParsedPage(
                    page_number=page_number,
                    text=ocr_text,
                    is_scanned=True,
                    ocr_confidence=ocr_confidence,
                )
            )
    doc.close()

    return ParsedDocument(
        pages=pages,
        is_scanned=any(p.is_scanned for p in pages),
        full_text="\n\n".join(p.text for p in pages),
    )


def _get_ocr_engine():
    # Model loading takes several seconds — load once per process, not
    # per page/document.
    global _ocr_engine
    if _ocr_engine is None:
        from paddleocr import PaddleOCR

        _ocr_engine = PaddleOCR(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            # This CPU's oneDNN build hits an unimplemented PIR-attribute
            # conversion in PaddlePaddle's inference backend — the plain
            # (non-MKLDNN) kernels work fine, just slightly slower.
            enable_mkldnn=False,
        )
    return _ocr_engine


def _run_ocr(page: "fitz.Page") -> tuple[str, float]:
    pix = page.get_pixmap(dpi=_OCR_RENDER_DPI)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        pix.save(tmp.name)
        tmp_path = tmp.name

    try:
        result = _get_ocr_engine().predict(tmp_path)
    finally:
        os.remove(tmp_path)

    if not result:
        return "", 0.0

    page_result = result[0]
    texts = page_result.get("rec_texts", [])
    scores = page_result.get("rec_scores", [])
    text = "\n".join(texts)
    confidence = sum(scores) / len(scores) if scores else 0.0
    return text, confidence
