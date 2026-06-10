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

### Backend (`backend/app/`) — hexagonal layout
- **`main.py`** — composition root: builds the DI `Container`, mounts all routers, defines the setup-guard middleware (503 until a vault is unlocked; always-allowed: `/health`, `/setup/*`, `/docs`, `/openapi.json`)
- **`core/domain/`** — pure dataclasses + enums: `User`, `Transaction` (with `TransactionType`), `Category` (with `CategoryType` and `parent_id`), `Wallet` (with `WalletType`), `ExchangeRate`
- **`core/ports/`** — abstract repository/provider interfaces (`TransactionRepository`, `WalletRepository`, `CategoryRepository`, `AIProvider`, `VaultManager`, ...)
- **`application/`** — use-case services: `transaction_service` (CRUD + `transfer()`), `wallet_service`, `category_service`, `whisper_service` (the agent), `analytics_service`, `mcp_service`, `auth_service`, `csv_import_service`, `bank_sync_service`
- **`infrastructure/`** — SQLModel repositories (flush-only — the request-scoped session in `DatabaseManager.get_session` is the unit-of-work boundary: commit on success, rollback on exception), `DatabaseManager` (SQLCipher engine + runtime `_run_migrations` ALTER TABLEs), `vault/manager.py`, `ai/` (OpenAI-compatible provider + factory)
- **`api/`** — `container.py` (DI), `deps.py` (`get_current_user` JWT Bearer; `get_current_user_by_api_key` for MCP), `routes/` (one file per feature)
- **`models/`** — SQLModel table models: `User`, `Transaction`, `ExchangeRate`, `ApiKey`, `Category`, `Wallet`, `BankConnection`. New models MUST be imported in `models/__init__.py` and `alembic/env.py`, or their tables are never created
- **`schemas/`** — Pydantic request/response schemas (separate from table models)

### Frontend (`frontend/src/`)
- **`lib/api.ts`** — single axios instance with base URL `/`. Interceptor auto-refreshes JWT on 401 and stores tokens in `localStorage`; `apiErrorDetail()` extracts backend error messages
- **`contexts/AuthContext.tsx`** — global auth state; consumed via `hooks/useAuth.ts`
- **`hooks/`** — data-fetching hooks: `useTransactions`, `useWallets`, `useCategories`, `useWhisper`, `useSettings`
- **`pages/`** — one file per route: `LoginPage`, `SetupPage`, `DashboardPage`, `TransactionsPage`, `WalletsPage`, `VisualizationsPage`, `SettingsPage`
- **`components/layout/`** — `DashboardLayout` (wraps protected pages, hosts `WhisperFAB`), `Sidebar`, `TopBar`, `ProtectedRoute`
- **`components/features/`** — `TransactionForm`, `TransactionProposalCard` (Whisper review; also renders plain agent replies), `WhisperFAB`, `CsvImportDialog`
- **`features/settings/`** — one file per Settings tab (`ApiKeysTab`, `CategoriesTab`, `ExchangeRatesTab`, `BanksTab`, `AiTab`, `AboutTab`); `lib/colorStyle.ts` is the single parser/builder for the category color protocol (solid / gradient / `animated:` prefix)
- UI library is Fluent UI (`@fluentui/react-components`) + Tailwind-style utility classes
- Path alias: `@/` maps to `frontend/src/`

### First-run setup flow
1. Backend starts; engine is `None`; all non-setup requests return 503
2. Browser hits `/setup/status` → redirected to `/setup` if not initialized
3. User creates a vault — encrypted (`/setup/vaults`, passphrase → PBKDF2-SHA256 key, BIP39 24-word mnemonic shown once) or open/unencrypted (`/setup/vaults/open`)
4. Subsequent restarts require `/setup/unlock` (passphrase) or `/setup/recover` (mnemonic); open vaults auto-unlock

### Domain model
- **Transaction** — `amount_original` + `currency_original` (JOD or USD) → `amount_base` in JOD via `exchange_rate`. `type` is `expense` | `income` | `transfer_out` | `transfer_in`; income/transfer_in add to a wallet's balance, the rest subtract. Soft-deleted via `is_deleted`. `source` tracks `"manual"`, `"whisper"`, `"csv_import"`, `"bank:*"`
- **Wallet** — typed (`cash`/`digital`/`savings`/`credit`/`other`); balance = `initial_balance` + signed sum of its transactions (cached in `balance`, refreshed on read). Archived via `is_active=False`; hard delete only when no transactions reference it
- **Transfer** — a linked pair of transactions sharing a `transfer_id`, categorized under the reserved `Transfer` category (type `transfer`). Deleting/editing one leg syncs the other; transfers are excluded from all spending/income analytics
- **Category** — two-level hierarchy via `parent_id` (e.g. `Family Savings` under `Savings`). Defaults (incl. sub-categories) are seeded on first access; categories in use or with children cannot be deleted
- **Whisper agent** — `POST /api/whisper/parse` classifies a message into an intent (`record_expense`, `record_income`, `transfer`, `query_balance`, `query_spending`, `unknown`), grounded in the user's wallets and categories. Mutating intents return a proposal held in a process-wide `ProposalStore` (TTL-bound) and are executed on `POST /api/whisper/confirm` (which accepts field `overrides`); queries are answered immediately

## Key conventions
- Backend linter: `ruff` (line length 100, target Python 3.12). Run with `cd backend && ruff check .`
- All monetary columns use `Numeric(precision=18, scale=6)` via SQLAlchemy `Column` — never `float`. Aggregations stay `Decimal` end-to-end; rounding to float happens once at the presentation edge
- Income vs expense is classified by `Transaction.type`, never by looking the category name up in a type map; category types only drive the orthogonal savings dimension
- The MCP router authenticates via API key (`X-API-Key`), not JWT; all other protected routes use JWT Bearer
- Alembic autogenerate requires the models to be imported before `SQLModel.metadata` is inspected — `alembic/env.py` imports all models explicitly
- E2E tests run against the full Docker stack on port 80; `globalSetup` handles initialization state
