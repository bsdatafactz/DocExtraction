# Document Extraction System — Overview

Human-in-the-loop invoice (and resume) extraction: upload a document, parse/OCR it, extract
structured fields with an LLM, score confidence, escalate the uncertain ones to a stronger
model, and route only genuine uncertainty to a human reviewer. Built for the DataFactZ AI
Engineering Internship, Week 2 Use Case 2.

## Tech Stack

**Backend** — FastAPI, SQLAlchemy + Alembic, PostgreSQL, Pydantic schemas, JWT auth (bcrypt +
PyJWT), pytest.

**Parsing / OCR** — PyMuPDF (digital text layer) + PaddleOCR (scanned pages), OCR isolated in
its own `ProcessPoolExecutor` worker so it can't block the API.

**LLM** — DeepSeek-V3.2 (first pass) and GPT-5 (escalation only), both via one Azure AI Foundry
resource's OpenAI-SDK-compatible endpoint.

**Frontend** — React + TypeScript, React Router, plain `fetch`-based API client, no state
library beyond component state/context.

**Infra** — Docker Compose (backend, frontend, Postgres), all three containerized for local dev.

## What's Implemented

- Auth: signup/login, JWT sessions, first account auto-admin, role promotion by an existing admin.
- Multi-tenant project ownership — each user sees only their own projects; admin also sees
  projects orphaned by a deleted user.
- Upload → background pipeline: parse/OCR routing → LLM extraction → composite confidence
  scoring → conditional escalation → status transitions (`queued` → `parsing` → `extracting` →
  `escalated`? → `needs_review`).
- Review screen: original document next to editable fields, tabbed by section, low-confidence
  fields flagged, Approve / Flag-for-follow-up, corrections written to their own audit-trail table.
- Two document types with real schemas: **invoice** and **resume** (contract is a selectable
  type with no schema yet — flagged "coming soon" rather than silently mis-extracting).
- Per-document and per-project export, JSON or CSV, using the reviewed (correction-applied)
  record.
- Real LLM cost tracking: prompt/completion tokens captured per call, priced per configurable
  $/1M-token rates, surfaced per-project and (for admin) per-user.
- Admin dashboard: status counts, processing-time averages, escalation rate, reviewed/
  auto-approved counts, upload trend chart — globally or scoped to one project.
- User management (admin): list, promote, delete (cascades the deleted user's projects/
  documents/files).
- Branded UI (DataFactZ navy/orange), light + dark theme.

**Not implemented / explicitly deferred:** contract-type extraction schema, a real job queue
(pipeline runs on FastAPI's in-process `BackgroundTasks`, fine at current scale), object storage
for uploads (local volume for now).

## PaddleOCR Performance (measured, not estimated)

Ran the actual `parse_document()` pipeline against three scanned pages from the project's test
set, on CPU (`enable_mkldnn=False` — this box's oneDNN build hits an unimplemented PaddlePaddle
inference kernel, so it falls back to plain kernels), using PP-OCRv6 (medium det + rec models):

| Sample | OCR confidence | Chars extracted | Time (incl. model init) |
|---|---|---|---|
| `scanned_00.pdf` | **0.99** | 659 | 39.1s |
| `scanned_02.pdf` | 0.70 | 433 | 44.1s |
| `scanned_04.pdf` | 0.63 | 205 | 36.3s |
| `digital_03.pdf` (control, no OCR) | — | 713 | 0.0s |

Takeaways:

- **Confidence swings hard with scan quality** — 0.63 to 0.99 across three samples from the same
  test set, no outliers excluded. That's *why* OCR confidence is folded into the composite
  field-confidence score as a discount (`heuristic_score × ocr_confidence`) rather than trusted
  on its own.
- **It's slow** — 35–45 seconds per scanned page on CPU, one page at a time (single worker,
  model loaded once). Fine for the demo's volume; would need GPU inference or a larger worker
  pool before this could handle real upload volume without a growing queue.
- **It genuinely fails sometimes, and the pipeline is built to notice.** A real demo run earlier
  in this project escalated a badly-degraded scanned invoice to GPT-5 and it still came back
  `illegible` on every field (composite 0.25) — the confidence gate caught it and routed it to a
  human instead of guessing.
- **It's a printed-text OCR engine, not a handwriting model.** Detection generally still finds
  handwritten regions; recognition on cursive/handwritten text is unreliable, since PP-OCRv6's
  recognition model is trained on printed/scene text. Not a problem for this project's invoices
  (almost always printed), but worth knowing if a scan had a handwritten annotation on it — that
  region's confidence would drop and get flagged the same way a bad scan does.
