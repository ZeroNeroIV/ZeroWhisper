# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ZeroWhisper is a self-hosted personal finance manager with an encrypted SQLite database (SQLCipher), dual-currency support (JOD + USD), and an AI-powered natural language expense entry agent ("Whisper"). The stack is Python/FastAPI backend + React/Vite frontend, deployed via Docker Compose with nginx.

## Commands

### Development (Docker, with hot-reload)
```bash
make dev        # backend :8000, frontend :5173
make logs       # tail service logs
make test       # run backend pytest suite
```

### Running services directly (no Docker)
```bash
# Backend — requires .env and an initialized DB
cd backend && uvicorn app.main:app --reload

# Frontend — proxies /api, /setup, /auth, /mcp to localhost:8000
cd frontend && npm run dev

# Alembic migrations
cd backend && alembic upgrade head
```

### Single backend test
```bash
cd backend && python -m pytest tests/test_sqlcipher_spike.py -v
```

### Frontend lint/type-check
```bash
cd frontend && npm run lint
cd frontend && npx tsc --noEmit
```

### E2E tests (Playwright, requires running stack)
```bash
cd e2e && npx playwright test
```

### Production
```bash
cp .env.example .env  # set JWT_SECRET and OPENAI_API_KEY
make prod             # runs detached on port 80
```

## Architecture

### Request flow
```
Browser → nginx(:80) → static files (frontend build)
                     → /api /auth /setup /mcp (proxy → FastAPI :8000)
```
In dev mode, Vite's dev server proxies those same prefixes to FastAPI; there is no nginx.

### Backend (`backend/app/`)
- **`main.py`** — mounts all routers; adds `SetupGuardMiddleware`
- **`middleware/setup_guard.py`** — blocks all endpoints with 503 until the DB key is loaded into memory. Always-allowed paths: `/health`, `/setup/*`, `/docs`, `/openapi.json`
- **`database.py`** — module-level `_engine` (starts `None`); call `initialize_engine(db_path, key)` from the setup flow to create the SQLCipher engine. The key is held only in memory. A `_PysqlcipherConnWrapper` works around the `deterministic` kwarg incompatibility between SQLAlchemy 2.0 and pysqlcipher3
- **`config.py`** — `pydantic-settings` `Settings`; reads from `.env`; raises at startup if `JWT_SECRET` is the insecure default
- **`dependencies.py`** — FastAPI dependencies: `get_current_user` (JWT Bearer) and `get_current_user_by_api_key` (X-API-Key header, used by the MCP router)
- **`models/`** — SQLModel table models: `User`, `Transaction`, `ExchangeRate`, `ApiKey`
- **`schemas/`** — Pydantic request/response schemas (separate from table models)
- **`services/`** — business logic layer called by routers: `auth`, `setup`, `transactions`, `csv_import`, `exchange_rate`, `api_key_service`, `openai_service`, `whisper_service`, `mcp_service`, `analytics_service`
- **`routers/`** — one file per feature group matching the API prefix table in README

### Frontend (`frontend/src/`)
- **`lib/api.ts`** — single axios instance with base URL `/`. Interceptor auto-refreshes JWT on 401 and stores tokens in `localStorage`
- **`contexts/AuthContext.tsx`** — global auth state; consumed via `hooks/useAuth.ts`
- **`hooks/`** — data-fetching hooks: `useTransactions`, `useWhisper`, `useSettings`
- **`pages/`** — one file per route: `LoginPage`, `SetupPage`, `DashboardPage`, `TransactionsPage`, `WhisperPage`, `VisualizationsPage`, `SettingsPage`
- **`components/layout/`** — `DashboardLayout` (wraps protected pages), `Sidebar`, `TopBar`, `ProtectedRoute`
- **`components/features/`** — `TransactionForm`, `TransactionProposalCard` (Whisper review), `CsvImportDialog`
- **`components/ui/`** — Shadcn UI primitives (auto-generated; don't hand-edit)
- Path alias: `@/` maps to `frontend/src/`

### First-run setup flow
1. Backend starts; `_engine` is `None`; all non-setup requests return 503
2. Browser hits `/setup/status` → redirected to `/setup` if not initialized
3. User sets a passphrase → `/setup/initialize` → backend derives key via PBKDF2-SHA256 and calls `initialize_engine()`; a BIP39 24-word mnemonic is shown once
4. Subsequent restarts require `/setup/unlock` (passphrase re-entry) or `/setup/recover` (mnemonic)

### Transaction model
`amount_original` + `currency_original` (JOD or USD) → `amount_base` in JOD using `exchange_rate`. Soft-deleted via `is_deleted` flag. `source` field tracks `"manual"`, `"whisper"`, or `"csv"`.

## Key conventions
- Backend linter: `ruff` (line length 100, target Python 3.12). Run with `cd backend && ruff check .`
- All monetary columns use `Numeric(precision=18, scale=6)` via SQLAlchemy `Column` — never `float`
- The MCP router authenticates via API key (`X-API-Key`), not JWT; all other protected routes use JWT Bearer
- Alembic autogenerate requires the models to be imported before `SQLModel.metadata` is inspected — `alembic/env.py` imports all models explicitly
- E2E tests run against the full Docker stack on port 80; `globalSetup` handles initialization state
