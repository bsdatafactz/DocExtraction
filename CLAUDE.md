# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Invoice extraction system with human-in-the-loop review, built for the DataFactZ AI Engineering Internship (Week 2, Use Case 2). Full requirements are in `3_Week 2_Use_Case_2_Document_Extraction_Brief.docx`; the day-by-day build order and deliverables checklist are in `PLAN.md`. As of this writing the repo is pre-implementation — no backend/frontend code exists yet, so the commands and paths below are the target layout, not a description of what's currently on disk.

## Commands

See `AGENTS.md` — it's the source of truth for run/test commands and cross-tool conventions (kept there so non-Claude tools reading this repo see the same thing). Don't duplicate command definitions here; update `AGENTS.md` instead and this file will stay accurate by reference.

## Architecture

The pipeline has five stages, each a rejected-alternatives decision the design doc has to defend (see `PLAN.md`'s pattern-justification table):

1. **Parse/OCR routing** — detect whether a page has an extractable text layer. Digital PDFs go through PyMuPDF; scanned/image-based pages go through PaddleOCR. This routing decision, not a single fixed parser, is what makes the pipeline handle both cleanly.
2. **LLM extraction** — DeepSeek runs first against a Pydantic schema (structured JSON output). Validation failures are caught and retried once with a repair prompt, never allowed to crash the pipeline.
3. **Confidence scoring & escalation** — confidence is a *composite* per-field score (self-assessed confidence × heuristic checks like regex/format validity, OCR-region confidence, line-item-sum-vs-total reconciliation), not a raw model-reported number. Only documents whose aggregate score falls below threshold get re-extracted with the escalation model — an Azure AI Foundry-hosted OpenAI deployment (no Claude API access on this project, so the "stronger model" tier is OpenAI via Foundry, not Claude); cross-model agreement is then a secondary signal computed just on that escalated subset. This two-tier design is deliberate — running both models on every document was considered and rejected because it doubles cost with no escalation savings.
4. **Human review** — documents still below threshold after escalation route to a review screen: original document next to editable extracted fields. Corrections write to their own audit-trail table, distinct from the raw model extraction(s), so pre-review and post-review accuracy can both be computed from stored data.
5. **Persistence & export** — approved records land in Postgres and export to CSV/JSON.

### Data model shape

The DB needs to keep raw extraction(s) per model, per-field confidence, and human corrections as separate, queryable history — not just a single "final record" table — because the accuracy report requires comparing raw-extraction accuracy against post-review accuracy on the 10 hand-labeled ground-truth documents. Any schema change here should update the ERD and the Alembic migration in the same change (see `AGENTS.md`'s "Do not touch" section).

### Hard constraints

- No managed cloud AI services (no Azure Document Intelligence, AWS Textract, Google Document AI) — parsing/OCR must be open-source; LLM APIs (Claude, DeepSeek, OpenAI) are fine.
- Accuracy comparisons must normalize values (date formats, currency symbols, whitespace) before exact-match comparison, or field-level accuracy reads artificially low from formatting noise rather than real extraction errors.
