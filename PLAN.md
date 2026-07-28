# Invoice Extraction System — Implementation Plan

DataFactZ AI Engineering Internship, Week 2, Use Case 2. Document type: **invoices**.
Personal deadline: Thursday EOD. Brief's own schedule has the demo on Friday — confirm which one is real before Thursday, since it changes how much slack Wed/Thu have.

---

## 0. Open decisions before coding starts

- **Postgres vs SQLite.** Brief wants "a real relational schema with migrations and an ERD." Postgres + Alembic is the more defensible answer in Q&A; SQLite is faster to stand up. Recommendation: Postgres in docker-compose — it's one extra container and matches the diagram already drawn.
- **Test set sourcing.** Need 20+ messy invoices, ≥25% scanned/image-based. Use a public invoice dataset (e.g. SROIE, or a Kaggle invoice OCR set) rather than hand-sourcing — faster and gives you scans with realistic skew for free.
- **Confirm Thu-vs-Fri deadline** with whoever assigned it.

---

## Day 1 — Monday (today)

- [x] Lock document type: invoices
- [x] Pull test set: 21 invoices (15 digital + 6 scanned = 28.6% scanned), all as real PDFs — see `test_set/README.md` for sources (Hugging Face: mychen76/invoices-and-receipts_ocr_v1, chainyo/rvl-cdip-invoice), why the digital half had to be re-rendered as born-digital PDFs (source images had no text layer at all), and the caveats on the auto-derived ground truth. Verified against the real parser: all 15 digital PDFs → `is_scanned=False`; all 6 scanned PDFs → `is_scanned=True`, routed to the OCR stub.
  - [ ] Still open: spot-check the 10 auto-derived ground-truth JSONs against `test_set/digital/originals/*.jpg` before treating them as final
  - [ ] Still open: verify scanned_00 is a fit (it's an AP voucher, not a vendor invoice, per `test_set/scanned/originals/scanned_00.jpg`) — keep as an edge case or swap it
- [x] Define Pydantic schema — 10+ fields, nested `line_items: list[LineItem]`, done in `backend/app/schemas/invoice.py` with an explicit `field_status` enum (extracted / not_applicable / illegible) for genuinely-absent fields
- [ ] Write 1-page problem statement (business framing, user, success criteria, out of scope)
- [ ] Draft design doc skeleton (architecture, ERD placeholder, API surface placeholder, scalability placeholder) + finalize the architecture diagram

---

## Day 2 — Tuesday

- [ ] Parsing router: detect digital-text-layer PDFs vs scanned/image-based → PyMuPDF for the former, PaddleOCR for the latter
- [ ] Run parsing/OCR across the full test set, log failures/edge cases (skew, low DPI)
- [ ] First extraction pass: DeepSeek call against the Pydantic schema (structured JSON output)
- [ ] Validation-failure handling: catch `ValidationError`, retry once with a repair prompt, never crash
- [ ] Checkpoint: extraction working end-to-end on at least a few digital + scanned samples

---

## Day 3 — Wednesday

- [ ] Composite per-field confidence: self-assessed score × heuristic checks (regex/format validity, OCR-region confidence, line-item-sum-vs-total reconciliation)
- [ ] Escalation logic: aggregate confidence below T1 → re-run with the Azure OpenAI (Foundry) escalation model; disagreement between DeepSeek/Azure-OpenAI fields lowers confidence further
- [ ] Postgres schema + Alembic migrations: `documents`, `extractions` (per model, per attempt), `field_confidence`, `corrections` (audit trail), `reviews`
- [ ] Persist raw extraction(s) + confidence scores
- [ ] Start ground-truth labeling: hand-label 10 documents

---

## Day 4 — Thursday

- [ ] Review screen (React): original document viewer + editable extracted-fields form, side by side
- [ ] Correction submit → writes to `corrections`, marks record approved, lands in `documents` as final
- [ ] Accuracy measurement: field-level match vs the 10 ground-truth docs, normalized (dates, currency, whitespace) before comparing — report pre-review and post-review numbers
- [ ] CSV/JSON export endpoint
- [ ] Cost estimate: $/1,000 docs for DeepSeek-only vs DeepSeek+escalation, projected at 100 users (pilot) and 5,000 users (production), with math shown
- [ ] Status report (due 6 PM per brief)

---

## Day 5 — Friday (if the real deadline, not Thursday)

- [ ] Presentation deck (10-15 slides): problem → architecture → decisions → demo → lessons learned
- [ ] Rehearse demo path: upload a scanned doc → queue status → review-screen correction → export
- [ ] Finalize AI usage log
- [ ] docker-compose + README pass: confirm a clean checkout runs in under 15 minutes
- [ ] Pattern-justification section: 2+ rejected alternatives per major decision (see below)

---

## Rejected alternatives to write up (pattern justification)

| Decision | Rejected alternative 1 | Rejected alternative 2 |
|---|---|---|
| Parsing strategy | Vision LLM directly on every page image | OCR-only with no digital-text-layer fast path |
| Confidence signal | Raw LLM self-reported score alone | Cross-model agreement on every document |
| Model escalation | Single model for everything | Both models on every document |
| Database | SQLite (faster setup) | No audit trail — overwrite on correction |

---

## Deliverables checklist (from brief)

- [ ] Problem statement (1 page)
- [ ] Solution design doc (4-8 pages): architecture, data flow, ERD, API surface, security, 100x-scale section
- [ ] Architecture diagram
- [ ] Pattern justification (table above, expanded)
- [ ] Working demo, docker-compose, README <15 min
- [ ] Branded UI (Handbook 7)
- [ ] Cost estimate (pilot 100 / production 5,000 users, math shown)
- [ ] Deck (10-15 slides)
- [ ] AI usage log (current through Friday demo)
- [ ] Accuracy report (field-level, vs 10 ground-truth docs, methodology stated)
