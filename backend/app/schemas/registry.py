"""Single place that maps a project's document_type to its extraction
schema and the domain-specific part of the LLM prompt. Adding a new
implemented document type means adding one entry here (plus a schema file)
— pipeline.py, extraction.py, and confidence.py all dispatch through this
rather than hardcoding a schema.
"""

from app.schemas.invoice import InvoiceExtraction
from app.schemas.resume import ResumeExtraction

INVOICE_PROMPT_INTRO = """You are an invoice data extraction system. Extract \
fields from the invoice text into JSON matching the schema below exactly. \
Rules:
- If a field does not apply to this document (e.g. no due date was ever \
set), set field_status[field] = "not_applicable" and leave the value null.
- If a field is present on the document but you cannot read it confidently, \
set field_status[field] = "illegible".
- If a field is present and readable, set field_status[field] = "extracted" \
and include your own 0.0-1.0 confidence in self_reported_confidence[field].
- Never guess a value to fill a field — a wrong guess is worse than null.

Schema:
"""

RESUME_PROMPT_INTRO = """You are a resume data extraction system. Extract \
fields from the resume text into JSON matching the schema below exactly. \
Rules:
- If a field does not apply to this resume (e.g. no listed projects), set \
field_status[field] = "not_applicable" and leave the value null or empty.
- If a field is present but you cannot read it confidently, set \
field_status[field] = "illegible".
- If a field is present and readable, set field_status[field] = "extracted" \
and include your own 0.0-1.0 confidence in self_reported_confidence[field].
- Never guess a value to fill a field — a wrong guess is worse than null.

Schema:
"""

EXTRACTION_SCHEMAS = {
    "invoice": (InvoiceExtraction, INVOICE_PROMPT_INTRO),
    "resume": (ResumeExtraction, RESUME_PROMPT_INTRO),
}


def get_extraction_schema(document_type: str):
    """Returns (schema_cls, prompt_intro) for an implemented document type."""
    return EXTRACTION_SCHEMAS[document_type]
