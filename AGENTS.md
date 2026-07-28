# AGENTS.md

## Stack
FastAPI + React. PostgreSQL (docker-compose). No managed cloud AI (no Textract/Document AI/Azure DI).

## Commands
- Backend: `uvicorn app.main:app --reload`
- Frontend: `npm run dev` (in /frontend)
- Tests: `pytest backend/tests`
- Full stack: `docker-compose up`

## Conventions
- All extraction schemas are Pydantic models in `backend/schemas/`
- Confidence is a composite per-field score (self-assessed confidence × heuristic checks — format/regex validity, OCR-region confidence, line-item-sum-vs-total reconciliation), never a fixed constant. DeepSeek runs first on every doc; only documents below the confidence threshold get re-extracted with the escalation model (Azure AI Foundry-hosted OpenAI — no Claude API access on this project). Cross-model agreement is a secondary signal computed only on that escalated subset — don't run both models on every document, it defeats the cost rationale.
- Never crash on validation failure — catch `ValidationError`, retry once with a repair prompt, then route to review queue
- Migrations via Alembic, not raw SQL edits

## Do not touch
- `backend/schemas/invoice.py` without updating the ERD diagram and the Alembic migration together
- Confidence thresholds without re-running the accuracy report — they trade off reviewer workload against error rate reaching the DB

See `PLAN.md` for the day-by-day build order and deliverables checklist.