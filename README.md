# Invoice Extraction

See `PLAN.md` for the build plan and `CLAUDE.md`/`AGENTS.md` for architecture and conventions.

## Run it

```
cp .env.example .env   # fill in DEEPSEEK_API_KEY and the AZURE_OPENAI_* values
docker compose up -d --build
```

- Backend: http://localhost:8000 (`/health`, `/api/v1/documents`)
- Frontend: http://localhost:5174
- Postgres: localhost:5435 (ports remapped from the usual 8000/5432/5173 because this dev box already runs other unrelated Postgres/Vite containers — adjust back to the defaults in `docker-compose.yml` on a clean machine if you want the standard ports)

## Local (non-docker) development

```
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

```
cd frontend && npm install && npm run dev
```

Tests: `pytest backend/tests` from the repo root.
