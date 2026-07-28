---
name: schema-change
description: Use whenever adding, renaming, or removing a field on the invoice extraction Pydantic schema (backend/schemas/invoice.py) — keeps the schema, Alembic migration, ERD diagram, and review-screen form from drifting out of sync.
---

Changing the invoice extraction schema touches four places that must move together. Do all four in the same change, in this order:

1. **Pydantic schema** (`backend/schemas/invoice.py`) — add/rename/remove the field. If it's a field that can be genuinely absent from a document, decide explicitly whether it's `Optional` with a null default or carries its own presence/confidence signal — don't let "missing" and "extraction failed" collapse into the same value.
2. **Alembic migration** — generate and check in a migration for the corresponding `extractions` / `documents` table column. Never hand-edit the schema without a matching migration.
3. **ERD diagram** in the design doc — update it in the same commit. A stale ERD is a specific, callable-out gap in the design-doc review.
4. **Review-screen form** (frontend) — the human review UI renders extracted fields for correction; a new schema field with no corresponding form input is invisible to reviewers and will silently never get corrected.

Also check: does this field affect the composite confidence heuristics (e.g., a new numeric field that should participate in a reconciliation check, like line-item sums vs. total)? If so, update the confidence-scoring logic too — see `CLAUDE.md`'s architecture section for how composite confidence is computed.

Before finishing, re-run the accuracy report against the 10 ground-truth documents if the field change affects anything already hand-labeled — a schema change can silently shift field-level accuracy numbers reported in the design doc.
