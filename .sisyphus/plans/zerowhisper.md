# ZeroWhisper — Personal Financial Manager + MCP Server

## TL;DR

> **Quick Summary**: Build a 100% self-hosted, local-first personal financial manager with encrypted SQLite storage, dual-currency (JOD/USD) support, a sarcastic NL2A "Whisper" agent for natural-language expense entry, interactive dashboards (Sankey, heatmaps, cash flow), and a Model Context Protocol server for IDE integration.
>
> **Deliverables**:
> - `backend/` — Python FastAPI with SQLModel + pysqlcipher3, JWT auth, agent service, MCP routes
> - `frontend/` — React Vite + TypeScript + Tailwind + Shadcn UI + Recharts dashboard
> - `docker/` — Multi-stage Dockerfiles + docker-compose for full containerized deployment
>
> **Estimated Effort**: XL (20-25 implementation tasks + 4 verification tasks)
> **Parallel Execution**: YES — 5 waves, max 6 concurrent tasks per wave
> **Critical Path**: SQLCipher Spike → First-Run Flow → Auth → Transaction CRUD → Whisper Agent → Dashboard → Final Verification

---

## Context

### Original Request
Build "ZeroWhisper" — a self-hosted personal financial manager with a FastAPI backend (SQLModel + pysqlcipher3 for encrypted SQLite), a React frontend dashboard (Vite + Tailwind + Shadcn + Recharts), an NL2A "Whisper" agent using OpenAI structured outputs, and an MCP server for IDE integration. Monorepo with backend/, frontend/, and docker/.

### Interview Summary
**Key Decisions**:
- **LLM Provider**: OpenAI only (structured outputs with `json_schema` strict mode)
- **DB Encryption Key**: First-run web setup flow (not env var)
- **Key Recovery**: BIP39 12-word recovery phrase (generated at first setup)
- **CSV Import**: Both template download + auto-detect common bank formats
- **Exchange Rates**: Manual entry with optional auto-fetch from public API
- **Whisper Agent**: Propose-only (user must confirm before DB write)
- **MCP Scope**: Full (balance, transactions, categories, net worth projection)
- **MCP Auth**: Static API key generated in dashboard
- **Network Binding**: LAN accessible (0.0.0.0)
- **Auth UX**: Separate login page with JWT
- **Test Strategy**: TDD with full test suite (pytest + Playwright)

### Metis Review
**Identified Risks & Mitigations**:
- **SQLCipher + SQLModel Compatibility**: High risk. pysqlcipher3 is a separate binary wrapper requiring C headers and SQLCipher binaries. Mitigation: Task 1 is a "Connectivity Spike" to prove the chain works before building further.
- **Cold Start Problem**: FastAPI cannot initialize a DB session until the encryption key is provided. Mitigation: State machine (UNINITIALIZED → KEY_SETTING → INITIALIZED) with a dedicated `/setup` endpoint that bypasses standard DB middleware.
- **Docker Build Bloat**: SQLCipher deps increase image size. Mitigation: Multi-stage Docker builds with builder pattern.
- **Prompt Drift**: Whisper's sarcastic persona may hallucinate categories/amounts. Mitigation: Strict `json_schema` response format from OpenAI, server-side validation of all structured outputs before presenting to user.
- **Data Loss on Key Loss**: Absolute. Mitigation: BIP39 recovery phrase printed at setup; user must back it up.

---

## Work Objectives

### Core Objective
Build a fully functional, self-hosted personal financial management system with encrypted local storage, natural-language expense entry, visual analytics, and MCP-based IDE integration.

### Concrete Deliverables
- `backend/` directory with FastAPI app, SQLModel schemas, JWT auth, Whisper agent, MCP routes
- `frontend/` directory with React dashboard, login page, chat interface, visualizations
- `docker/` directory with Dockerfiles, docker-compose.yml, nginx config
- `.env.example` and setup documentation

### Definition of Done
- [ ] `docker compose up` starts both backend and frontend
- [ ] First-run setup: user visits browser, sets DB encryption key, gets BIP39 recovery phrase
- [ ] User can register/login via JWT auth
- [ ] User can add transactions manually, via CSV import, and via natural language
- [ ] Dashboard shows Sankey diagram, burn-rate heatmap, cash flow chart
- [ ] Whisper agent accepts "Add 20 USD for Netflix" → proposes structured transaction → user confirms
- [ ] MCP server exposes financial stats (balance, transactions, categories, net worth)
- [ ] All schema tests pass: `pytest` + all E2E scenarios pass

### Must Have
- Encrypted SQLite database via pysqlcipher3 (verified: cannot open with standard sqlite3 browser)
- Dual-currency Transaction table (original + base JOD + exchange rate)
- First-run setup wizard (key → recovery phrase → admin account)
- JWT authentication on all protected endpoints
- Whisper NL2A endpoint with OpenAI structured outputs
- CSV import with template + auto-detect
- Dashboard with Sankey diagram, heatmap, cash flow chart
- MCP server routes for IDE querying stats
- Docker compose with multi-stage builds

### Must NOT Have (Guardrails)
- No plaintext DB key stored in env/files at any point (only in memory after setup)
- No arbitrary SQL execution by Whisper agent (structured JSON only, validated server-side)
- No external DB dependencies (SQLite only — no PostgreSQL, no MySQL)
- No real-time exchange rate polling by default (manual + optional toggle)
- No AI-slop patterns: no unnecessary abstractions, no generic "data/result/temp" naming, no excessive comments
- No PII/PHI leakage through MCP (MCP only exposes aggregated stats, not raw transaction descriptions)

---

## Verification Strategy (MANDATORY)

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: NO (greenfield)
- **Automated tests**: TDD with full test suite
- **Framework**: pytest (backend) + Playwright (frontend E2E)
- **TDD**: Each implementation task follows RED (failing test) → GREEN (minimal impl) → REFACTOR

### QA Policy
Every task MUST include agent-executed QA scenarios. Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **API/Backend**: Bash (curl) — Send requests, assert status codes + response body fields
- **Frontend/UI**: Playwright — Navigate, interact, assert DOM, screenshot
- **Database**: Bash (sqlite3 CLI with/without key) — Verify encryption, query tables
- **Library/Module**: Bash (python -c) — Import, call functions, assert output

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Foundation — 6 parallel tasks):
├── Task 1: SQLCipher connectivity spike [quick]
├── Task 2: Project scaffolding + Docker base [quick]
├── Task 3: Base SQLModel schemas (User, Transaction) [quick]
├── Task 4: Alembic + migration setup [quick]
├── Task 5: First-run setup flow (key → BIP39 → admin) [deep]
└── Task 6: Multi-stage Dockerfile for backend [quick]

Wave 2 (Backend Core — 6 parallel tasks):
├── Task 7: JWT auth (register, login, refresh, middleware) [unspecified-high]
├── Task 8: Transaction CRUD with dual-currency [unspecified-high]
├── Task 9: CSV import service (template + auto-detect) [deep]
├── Task 10: Exchange rate service [quick]
├── Task 11: MCP server routes [unspecified-high]
└── Task 12: API key management endpoint [quick]

Wave 3 (Whisper Agent + Frontend Start — 4 parallel tasks):
├── Task 13: OpenAI service layer + structured outputs [deep]
├── Task 14: Whisper agent endpoint + propose flow [unspecified-high]
├── Task 15: Frontend scaffolding (Vite + React + Tailwind + Shadcn) [visual-engineering]
└── Task 16: Login page + auth context [visual-engineering]

Wave 4 (Frontend — 5 parallel tasks):
├── Task 17: Dashboard layout + navigation shell [visual-engineering]
├── Task 18: Transaction list + entry forms [visual-engineering]
├── Task 19: Whisper chat interface [visual-engineering]
├── Task 20: Visualization dashboard (Sankey, heatmap, cash flow) [visual-engineering]
└── Task 21: Settings page (API key, exchange rate, recovery phrase) [visual-engineering]

Wave 5 (Integration — 3 parallel tasks):
├── Task 22: Docker Compose finalization + nginx [quick]
├── Task 23: End-to-end integration tests [unspecified-high]
└── Task 24: Documentation + README [writing]

Wave FINAL (4 parallel reviews):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Real manual QA (unspecified-high + playwright)
└── Task F4: Scope fidelity check (deep)
```

### Dependency Matrix
```
Task  Blocks          Blocked By
1      5, 8, 9, 11    —
2      6, 15, 22      —
3      4, 7, 8, 9     —
4      8, 9, 11       —
5      7, 12, 21      —
6      22             —
7      14, 16, 17     —
8      14, 18, 20     3
9      —              1, 3
10     20             —
11     —              1, 4
12     21             —
13     14             —
14     —              7, 13
15     16, 17, 18, 19, 20, 21  —
16     17             —
17     19, 20         7
18     —              8
19     —              14
20     —              10, 8, 17
21     —              12
22     —              2, 6
23     —              14, 17, 18, 19, 20, 21
24     —              22, 23
```

### Agent Dispatch Summary
- **Wave 1**: 6 tasks — 5 × `quick`, 1 × `deep`
- **Wave 2**: 6 tasks — 1 × `quick`, 4 × `unspecified-high`, 1 × `deep`
- **Wave 3**: 4 tasks — 2 × `deep/unspecified-high`, 2 × `visual-engineering`
- **Wave 4**: 5 tasks — 5 × `visual-engineering`
- **Wave 5**: 3 tasks — 1 × `quick`, 1 × `unspecified-high`, 1 × `writing`
- **FINAL**: 4 tasks — 1 × `oracle`, 2 × `unspecified-high`, 1 × `deep`

---

## TODOs

- [ ] 1. SQLCipher Connectivity Spike

  **What to do**:
  - Create `backend/` directory structure
  - Set up `pyproject.toml` with dependencies: fastapi, uvicorn, sqlmodel, pysqlcipher3, alembic, python-jose, passlib, bcrypt, httpx, pytest
  - Create a minimal test script that proves SQLCipher works with SQLAlchemy:
    1. Creates an encrypted SQLite database using `pysqlcipher3` connection string
    2. Creates a table using SQLModel
    3. Inserts a row
    4. Reads it back with the correct key → succeeds
    5. Tries to read with wrong key → fails with encryption error
  - This must work before ANY other backend task proceeds
  - If pysqlcipher3 fails to install/provide the right driver, document the fallback approach

  **Must NOT do**:
  - Do not spend time on app structure yet — this is purely a connectivity proof
  - Do not commit the .db file to git

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3, 4)
  - **Blocks**: Tasks 5, 8, 9, 11
  - **Blocked By**: None

  **Acceptance Criteria**:
  - [ ] Test script runs and confirms encrypted DB works
  - [ ] Same script confirms wrong key fails
  - [ ] pytest can be run against the test setup
  - [ ] `backend/pyproject.toml` exists with all dependencies

  **QA Scenarios**:
  ```
  Scenario: Encrypted DB works with correct key
    Tool: Bash (python -c)
    Preconditions: pysqlcipher3 installed in venv
    Steps:
      1. Run test script: `python backend/tests/test_sqlcipher_spike.py`
      2. Assert exit code 0
      3. Check that `test_spike.db` exists and is > 0 bytes
    Expected Result: All assertions pass, encrypted DB file created
    Evidence: .sisyphus/evidence/task-1-spike-ok.txt

  Scenario: Wrong key fails to read
    Tool: Bash (python -c)
    Preconditions: test_spike.db exists from previous scenario
    Steps:
      1. Run: `python -c "
  from sqlalchemy import create_engine, text
  e = create_engine('sqlite+pysqlcipher:///test_spike.db?cipher=aes-256-cfb&kdf_iter=64000')
  conn = e.connect()
  conn.execute(text('PRAGMA key=\\\\"wrong_key\\\"'))
  conn.execute(text('SELECT count(*) FROM sqlite_master'))
  "`
      2. Assert it raises an exception
    Expected Result: Operation fails with encryption error
    Evidence: .sisyphus/evidence/task-1-spike-wrong-key.txt
  ```

  **Commit**: YES
  - Message: `feat(db): sqlcipher connectivity spike`
  - Files: `backend/pyproject.toml`, `backend/tests/test_sqlcipher_spike.py`

- [ ] 2. Project Scaffolding and Docker Base

  **What to do**:
  - Create top-level monorepo structure:
    ```
    backend/
      app/
        __init__.py
        main.py
        config.py
        dependencies.py
        exceptions.py
      alembic/
      tests/
    frontend/
    docker/
      backend.Dockerfile
      frontend.Dockerfile
      nginx.conf
    docker-compose.yml
    .env.example
    .gitignore
    ```
  - Create `backend/app/main.py` with a minimal FastAPI app (health endpoint only for now)
  - Create `backend/app/config.py` with Pydantic Settings for all env vars
  - Create `.gitignore` (Python, Node, Docker, IDE files, *.db, .env)
  - Create `docker/backend.Dockerfile` with multi-stage build:
    - Stage 1 (builder): Install SQLCipher dev libraries + Python deps
    - Stage 2 (runtime): Slim image with compiled libs
  - Create `docker/frontend.Dockerfile` (multi-stage: build then nginx serve)

  **Must NOT do**:
  - No application logic yet — just structure
  - No API endpoints except `/health`

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3, 4)
  - **Blocks**: Tasks 6, 15, 22
  - **Blocked By**: None

  **Acceptance Criteria**:
  - [ ] `ls backend/app/main.py` exists and imports FastAPI
  - [ ] `uvicorn app.main:app` starts without error
  - [ ] `curl localhost:8000/health` returns `{"status": "ok"}`
  - [ ] Dockerfile builds: `docker build -f docker/backend.Dockerfile -t zerowhisper-backend .`

  **QA Scenarios**:
  ```
  Scenario: Health endpoint works
    Tool: Bash
    Preconditions: backend deps installed
    Steps:
      1. Start: `cd backend && uvicorn app.main:app --port 8000 &
      2. curl -s http://localhost:8000/health
      3. Kill server
    Expected Result: `{"status":"ok"}`
    Evidence: .sisyphus/evidence/task-2-health.txt
  ```

  **Commit**: YES
  - Message: `feat(infra): project scaffolding and docker base`
  - Files: project structure files

- [ ] 3. Base SQLModel Schemas (User + Transaction)

  **What to do**:
  - Create `backend/app/models/__init__.py` and `backend/app/models/user.py`:
    - `User` table: id (UUID), username (unique), email (unique), hashed_password, is_admin, created_at
  - Create `backend/app/models/transaction.py`:
    - `Transaction` table: id (UUID), user_id (FK→User), amount_original (Decimal), currency_original (String, JOD or USD), amount_base (Decimal, always JOD), exchange_rate (Decimal), category (String), description (Text), transaction_date (Date), created_at
  - Create `backend/app/models/__init__.py` that exports both
  - All models use SQLModel with proper typing
  - Create `backend/app/database.py` with SQLCipher connection logic:
    - Engine creation that accepts a DB key
    - Session dependency for FastAPI
    - Key pragma execution on each connection

  **Must NOT do**:
  - No Alembic yet (Task 4)
  - No relationships or complex queries yet
  - Keep pysqlcipher3 driver selection abstracted in database.py

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 4)
  - **Blocks**: Tasks 4, 7, 8, 9
  - **Blocked By**: None

  **Acceptance Criteria**:
  - [ ] `backend/app/models/user.py` has complete User model
  - [ ] `backend/app/models/transaction.py` has complete Transaction model with dual-currency fields
  - [ ] `backend/app/database.py` has engine factory accepting a key
  - [ ] Python import works: `from app.models import User, Transaction`

  **QA Scenarios**:
  ```
  Scenario: Models import correctly
    Tool: Bash
    Preconditions: backend deps installed
    Steps:
      1. `cd backend && python -c "from app.models import User, Transaction; print('OK')"`
      2. Verify output includes "OK"
    Expected Result: Models import without errors
    Evidence: .sisyphus/evidence/task-3-models-import.txt
  ```

  **Commit**: YES
  - Message: `feat(db): base SQLModel schemas`
  - Files: `backend/app/models/*`, `backend/app/database.py`

- [ ] 4. Alembic + Migration Setup

  **What to do**:
  - Initialize Alembic in `backend/`
  - Configure `alembic.ini` to use the async SQLCipher connection
  - Create `backend/app/alembic/env.py` that:
    - Imports SQLModel metadata
    - Reads DB key from a temporary source (for migration purposes)
    - Configures the SQLCipher connection
  - Create initial migration to create User and Transaction tables
  - Write a migration helper that can encrypt a fresh database

  **Must NOT do**:
  - No auto-generation of migrations from model changes (manual review only)
  - Don't commit migration-generated files without review

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3)
  - **Blocks**: Tasks 8, 9, 11
  - **Blocked By**: Task 3

  **Acceptance Criteria**:
  - [ ] `alembic upgrade head` runs successfully against a test DB
  - [ ] Tables exist after migration: `sqlite3 test.db ".tables"` shows users, transactions
  - [ ] `alembic history` shows the initial migration

  **QA Scenarios**:
  ```
  Scenario: Migration creates tables
    Tool: Bash
    Preconditions: Task 3 done, test database available
    Steps:
      1. `cd backend && alembic upgrade head`
      2. Check tables exist
    Expected Result: Migration succeeds, tables created
    Evidence: .sisyphus/evidence/task-4-migration-ok.txt
  ```

  **Commit**: YES (group with Task 3)
  - Message: `feat(db): alembic migrations`
  - Files: `alembic/*`, `alembic.ini`

- [ ] 5. First-Run Setup Flow (Key → BIP39 → Admin)

  **What to do**:
  - Create `backend/app/services/setup.py` with a SetupService:
    - State machine: UNINITIALIZED → KEY_SETTING → INITIALIZED
    - Key derivation: PBKDF2 on user-provided passphrase → 256-bit key for SQLCipher
    - BIP39 recovery phrase generation (12 words from a standard BIP39 wordlist)
    - Recovery phrase → key reconstruction logic
    - DB initialization: create database, set key, run migrations, create admin user
  - State is tracked in a JSON file or a simple marker (NOT in the encrypted DB — chicken-and-egg)
  - Create `backend/app/routers/setup.py` with endpoints:
    - `GET /setup/status` — returns current state (UNINITIALIZED / KEY_SETTING / INITIALIZED)
    - `POST /setup/initialize` — accepts {passphrase}, generates recovery phrase, initializes DB
    - `POST /setup/recover` — accepts {recovery_phrase, new_passphrase}, reconstructs key, re-encrypts
  - Store the BIP39 wordlist as a JSON file in the app

  **Must NOT do**:
  - Do NOT store the encryption key or recovery phrase in any file
  - Only return the recovery phrase ONCE (on initial setup) — require confirmation that user saved it
  - Recovery phrase regenerated every time is unacceptable — it must be deterministic from the key

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: NO (sequential)
  - **Parallel Group**: Wave 1
  - **Blocks**: Tasks 7, 12, 21
  - **Blocked By**: Tasks 1, 2, 3, 4

  **Acceptance Criteria**:
  - [ ] `curl localhost:8000/setup/status` returns `{"state":"UNINITIALIZED"}`
  - [ ] `POST /setup/initialize` with passphrase returns 12-word recovery phrase
  - [ ] After initialize, `GET /setup/status` returns `{"state":"INITIALIZED"}`
  - [ ] Recovery phrase can reconstruct the key: `POST /setup/recover` with phrase + new passphrase works
  - [ ] DB file exists and is encrypted after setup

  **QA Scenarios**:
  ```
  Scenario: Full first-run setup
    Tool: Bash (curl)
    Preconditions: Clean state (no DB file)
    Steps:
      1. curl -s GET /setup/status → {"state":"UNINITIALIZED"}
      2. curl -s -X POST /setup/initialize -d '{"passphrase":"MySecurePass123"}'
         → Extract recovery_phrase from response
      3. curl -s GET /setup/status → {"state":"INITIALIZED"}
      4. Verify DB encrypted: sqlite3 data/zerowhisper.db "SELECT 1" 2>&1 | grep -q "encrypted"
    Expected Result: Setup complete, DB encrypted
    Evidence: .sisyphus/evidence/task-5-setup.txt

  Scenario: Recovery with BIP39 phrase
    Tool: Bash (curl)
    Preconditions: DB initialized, we have recovery_phrase from setup
    Steps:
      1. Delete passphrase from memory (restart app or use --reset flag)
      2. curl -s -X POST /setup/recover -d '{"recovery_phrase":"<phrase>","new_passphrase":"NewPass456"}'
         → {"state":"INITIALIZED", "recovered": true}
      3. Login works with admin user
    Expected Result: Recovery succeeds, data accessible
    Evidence: .sisyphus/evidence/task-5-recovery.txt
  ```

  **Commit**: YES
  - Message: `feat(auth): first-run setup flow with BIP39 recovery`
  - Files: `backend/app/services/setup.py`, `backend/app/routers/setup.py`, BIP39 wordlist

- [ ] 6. Multi-Stage Backend Dockerfile

  **What to do**:
  - Refine `docker/backend.Dockerfile` created in Task 2:
    - Stage 1 (builder): `python:3.12-slim`, install build-essential, libsqlcipher-dev, openssl, pip install deps
    - Stage 2 (runtime): `python:3.12-slim`, copy compiled .so files from builder, install only runtime deps
    - Copy `backend/` into `/app`
    - Expose port 8000
    - CMD: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
  - Set WORKDIR to `/app`
  - Ensure pysqlcipher3 .so files are properly copied between stages

  **Must NOT do**:
  - No secrets baked into the image
  - No root user in runtime stage

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3, 4)
  - **Blocks**: Task 22
  - **Blocked By**: Task 2

  **Acceptance Criteria**:
  - [ ] `docker build -f docker/backend.Dockerfile -t zerowhisper-backend .` succeeds
  - [ ] Image runs: `docker run zerowhisper-backend python -c "import pysqlcipher3; print('OK')"`
  - [ ] Image size < 500MB

  **QA Scenarios**:
  ```
  Scenario: Docker image builds and runs
    Tool: Bash
    Preconditions: Docker installed
    Steps:
      1. docker build -f docker/backend.Dockerfile -t zerowhisper-backend .
      2. docker run zerowhisper-backend python -c "from app import main; print('OK')"
    Expected Result: Build succeeds, container runs Python
    Evidence: .sisyphus/evidence/task-6-docker-build.txt
  ```

  **Commit**: YES (group with Task 2)
  - Message: `feat(docker): backend Dockerfile`
  - Files: `docker/backend.Dockerfile`

- [ ] 7. JWT Authentication (Register, Login, Refresh, Middleware)

  **What to do**:
  - Create `backend/app/routers/auth.py`:
    - `POST /auth/register` — create user with hashed password (passlib bcrypt)
    - `POST /auth/login` — validate credentials, return JWT (access + refresh tokens)
    - `POST /auth/refresh` — refresh access token using refresh token
    - `POST /auth/logout` — invalidate token (optional, for future blacklist)
  - Create `backend/app/services/auth.py` with:
    - Token creation (access: 30min, refresh: 7d)
    - Password hashing/verification
    - Token validation + user extraction
  - Create `backend/app/dependencies.py` with:
    - `get_current_user` dependency that validates JWT from Authorization header and returns User
  - Create `backend/middleware/auth.py` — optional, can use FastAPI dependency injection instead
  - JWT_SECRET is auto-generated on first run and stored in an env-compatible format

  **Must NOT do**:
  - No OAuth providers (GitHub, Google) — JWT-only
  - Token blacklisting is out of scope for v1

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 8, 9, 10, 11, 12)
  - **Blocks**: Tasks 14, 16, 17
  - **Blocked By**: Tasks 3, 5

  **Acceptance Criteria**:
  - [ ] `POST /auth/register` creates user and returns 201
  - [ ] `POST /auth/login` with correct creds returns JWT
  - [ ] `POST /auth/login` with wrong password returns 401
  - [ ] Protected endpoint returns 401 without valid token
  - [ ] Token refresh works

  **QA Scenarios**:
  ```
  Scenario: Register and login flow
    Tool: Bash (curl)
    Preconditions: DB initialized from Task 5
    Steps:
      1. curl -s -X POST /auth/register -d '{"username":"alice","password":"secret123"}'
         → 201
      2. curl -s -X POST /auth/login -d '{"username":"alice","password":"secret123"}'
         → Extract access_token
      3. curl -s /api/transactions -H "Authorization: Bearer $TOKEN"
         → 200 (not 401)
      4. curl -s /api/transactions (no auth header)
         → 401
    Expected Result: Auth flow works end-to-end
    Evidence: .sisyphus/evidence/task-7-auth.txt
  ```

  **Commit**: YES
  - Message: `feat(auth): JWT auth endpoints and middleware`
  - Files: `backend/app/routers/auth.py`, `backend/app/services/auth.py`

- [ ] 8. Transaction CRUD with Dual-Currency Support

  **What to do**:
  - Create `backend/app/routers/transactions.py`:
    - `GET /api/transactions` — list transactions (paginated, filterable by date range, category, currency)
    - `POST /api/transactions` — create transaction
      - Accepts: amount_original, currency_original, category, description, transaction_date
      - Server-side: looks up current exchange rate (from Task 10), computes amount_base in JOD
    - `GET /api/transactions/{id}` — single transaction detail
    - `PUT /api/transactions/{id}` — update transaction
    - `DELETE /api/transactions/{id}` — soft-delete transaction
  - Create `backend/app/services/transactions.py` with business logic:
    - Exchange rate application
    - Category validation
    - Pagination logic
  - Create `backend/app/schemas/transaction.py` with Pydantic request/response schemas
  - All endpoints protected by JWT auth dependency

  **Must NOT do**:
  - No hard deletion (soft-delete only with `is_deleted` flag)
  - No auto-categorization yet (that's the Whisper agent's job)
  - No balance computation in this task (future task)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 7, 9, 10, 11, 12)
  - **Blocks**: Tasks 14, 18, 20
  - **Blocked By**: Tasks 3, 4, 5

  **Acceptance Criteria**:
  - [ ] `POST /api/transactions` creates a transaction with proper dual-currency fields
  - [ ] `GET /api/transactions` returns paginated list
  - [ ] `GET /api/transactions?category=Food` filters correctly
  - [ ] `PUT /api/transactions/{id}` updates fields
  - [ ] `DELETE /api/transactions/{id}` soft-deletes (sets is_deleted=True)
  - [ ] JWT protected: 401 without token

  **QA Scenarios**:
  ```
  Scenario: Create transaction with dual-currency
    Tool: Bash (curl)
    Preconditions: Authenticated user
    Steps:
      1. curl -s -X POST /api/transactions -H "Authorization: Bearer $TOKEN" \
         -d '{"amount_original":50,"currency_original":"USD","category":"Food","description":"Dinner","transaction_date":"2026-05-12"}'
      2. Verify response includes: amount_base (JOD equivalent), exchange_rate
      3. Verify amount_base is computed (e.g., if rate=0.709, amount_base should be ~35.45)
    Expected Result: Transaction created with dual-currency
    Evidence: .sisyphus/evidence/task-8-transaction.txt

  Scenario: Paginated list
    Tool: Bash (curl)
    Preconditions: At least 5 transactions exist
    Steps:
      1. curl -s "/api/transactions?page=1&page_size=3" -H "Authorization: Bearer $TOKEN"
      2. Verify response has: items, total, page, page_size
      3. Verify items length <= 3
    Expected Result: Pagination works correctly
    Evidence: .sisyphus/evidence/task-8-pagination.txt
  ```

  **Commit**: YES
  - Message: `feat(api): transaction CRUD with dual-currency`
  - Files: `backend/app/routers/transactions.py`, `backend/app/services/transactions.py`, `backend/app/schemas/transaction.py`

- [ ] 9. CSV Import Service (Template + Auto-Detect)

  **What to do**:
  - Create `backend/app/routers/imports.py`:
    - `GET /api/imports/template` — download a CSV template with headers and example row
    - `POST /api/imports/csv` — upload and process CSV file
  - Create `backend/app/services/csv_import.py`:
    - Template mode: expects exact column structure, strict validation
    - Auto-detect mode: For each of the 5 common bank formats (try each parser):
      - Header matching (date, amount, description columns by name)
      - Currency detection (column value or assume JOD)
      - Row-by-row validation
    - Returns: imported_count, errors[], skipped_rows[]
    - Rolls back ALL rows on unrecoverable error (e.g. file can't be parsed)
    - For recoverable errors (bad row), skips and reports
  - Store CSV template in `backend/app/static/template.csv`
  - Use Pydantic to validate each parsed row before DB insert
  - All transactions created via CSV get `source: "csv_import"` metadata

  **Must NOT do**:
  - Don't store uploaded CSV files permanently (process and discard)
  - Don't allow CSV import without authentication

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 7, 8, 10, 11, 12)
  - **Blocks**: None
  - **Blocked By**: Tasks 1, 3, 4, 5

  **Acceptance Criteria**:
  - [ ] `GET /api/imports/template` returns CSV file download
  - [ ] `POST /api/imports/csv` with valid CSV returns `{"imported": N, "errors": []}`
  - [ ] `POST /api/imports/csv` with bad rows returns `{"imported": N, "errors": [{"row": 3, "error": "..."}]}`
  - [ ] Auto-detect parses a bank-export-style CSV correctly

  **QA Scenarios**:
  ```
  Scenario: Import valid CSV via template
    Tool: Bash (curl)
    Preconditions: Auth token, template.csv file ready
    Steps:
      1. Create test CSV: echo "transaction_date,amount_original,currency_original,category,description\n2026-05-01,50,JOD,Food,Groceries\n2026-05-02,20,USD,Transport,Taxi" > /tmp/test.csv
      2. curl -s -X POST /api/imports/csv -H "Authorization: Bearer $TOKEN" \
         -F "file=@/tmp/test.csv"
      3. Verify response: {"imported": 2, "errors": []}
      4. GET /api/transactions?source=csv_import → 2 new transactions
    Expected Result: CSV rows imported successfully
    Evidence: .sisyphus/evidence/task-9-csv-import.txt

  Scenario: Import with bad rows
    Tool: Bash (curl)
    Preconditions: Auth token
    Steps:
      1. Create CSV with a bad row: echo "transaction_date,amount_original,currency_original,category,description\n2026-05-01,50,JOD,Food,OK\nnot-a-date,bad-amount,USD,Cat,Desc" > /tmp/bad.csv
      2. curl -s -X POST /api/imports/csv -F "file=@/tmp/bad.csv"
      3. Verify: imported=1, errors has 1 entry for row 2
    Expected Result: Good rows imported, bad row reported
    Evidence: .sisyphus/evidence/task-9-csv-bad-row.txt
  ```

  **Commit**: YES
  - Message: `feat(api): CSV import service with template and auto-detect`
  - Files: `backend/app/routers/imports.py`, `backend/app/services/csv_import.py`, `backend/app/static/template.csv`

- [ ] 10. Exchange Rate Service

  **What to do**:
  - Create `backend/app/services/exchange_rate.py`:
    - ExchangeRateStore: stores rate history in a simple table (date, rate, source)
    - `set_rate(rate: Decimal, date: date)` — manual rate entry
    - `get_rate(date: date) → Decimal` — get rate for a specific date
    - `auto_fetch_enabled` toggle in config
    - If auto-fetch enabled and no rate for today: fetch from exchangerate.host or frankfurter API
    - Cache fetched rates in the DB table to avoid repeated API calls
  - Add `ExchangeRate` model to `backend/app/models/transaction.py` (or new file)
    - id, date, jod_to_usd (Decimal), source (manual/api), created_at
  - Create `backend/app/routers/exchange_rates.py`:
    - `GET /api/exchange-rates/current` — current rate
    - `GET /api/exchange-rates/history` — rate history
    - `POST /api/exchange-rates` — set rate manually
    - `PUT /api/exchange-rates/auto-fetch` — toggle auto-fetch on/off

  **Must NOT do**:
  - Don't poll exchange rate APIs on a schedule (only on-demand)
  - Don't fail transaction creation if no rate is set (default to a configurable fallback rate)
  - Auto-fetch is OFF by default

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 7, 8, 9, 11, 12)
  - **Blocks**: Task 20
  - **Blocked By**: None

  **Acceptance Criteria**:
  - [ ] `POST /api/exchange-rates` with rate saves and returns it
  - [ ] `GET /api/exchange-rates/current` returns the latest rate
  - [ ] Rate is applied during transaction creation (Task 8 is updated to call get_rate)

  **QA Scenarios**:
  ```
  Scenario: Set and get exchange rate
    Tool: Bash (curl)
    Preconditions: Auth token, USD→JOD market rate
    Steps:
      1. curl -s -X POST /api/exchange-rates -H "Authorization: Bearer $TOKEN" \
         -d '{"rate": 0.709, "date": "2026-05-12"}'
      2. curl -s GET /api/exchange-rates/current -H "Authorization: Bearer $TOKEN"
      3. Verify: {"rate": 0.709, "date": "2026-05-12", "source": "manual"}
    Expected Result: Rate stored and retrievable
    Evidence: .sisyphus/evidence/task-10-rate.txt
  ```

  **Commit**: YES
  - Message: `feat(api): exchange rate service`
  - Files: `backend/app/services/exchange_rate.py`, `backend/app/routers/exchange_rates.py`

- [ ] 11. MCP Server Routes

  **What to do**:
  - Create `backend/app/routers/mcp.py` with MCP protocol routes:
    - `GET /mcp/manifest` — MCP server manifest (name, version, capabilities)
    - `GET /mcp/resources` — list available resources: `zerowhisper://balance`, `zerowhisper://transactions/recent`, `zerowhisper://transactions/by-category`, `zerowhisper://net-worth`
    - `GET /mcp/resources/{path}` — fetch specific resource data
    - `POST /mcp/tools/call` — call tool: `get_balance`, `get_recent_transactions`, `get_spending_by_category`, `get_net_worth`
    - `GET /mcp/prompts` — available prompt templates
  - Each resource/tool returns JSON with:
    - Resource: data payload
    - Tool: structured response appropriate for LLM consumption
  - Create `backend/app/services/mcp_service.py`:
    - `get_balance(user_id) → {"balance_jod": Decimal, "balance_usd": Decimal}`
    - `get_recent_transactions(user_id, limit=10) → [Transaction]`
    - `get_spending_by_category(user_id, month, year) → [{category, total, count}]`
    - `get_net_worth(user_id) → {"total_assets": ..., "total_liabilities": ..., "net_worth": ...}`
  - MCP routes authenticate via MCP API key (created in Task 12), separate from JWT

  **Must NOT do**:
  - Don't expose raw transaction descriptions in MCP (aggregated stats only)
  - Don't allow write operations through MCP (read-only for now)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 7, 8, 9, 10, 12)
  - **Blocks**: None
  - **Blocked By**: Tasks 3, 4, 5

  **Acceptance Criteria**:
  - [ ] `GET /mcp/manifest` returns valid MCP manifest JSON
  - [ ] `GET /mcp/resources` returns list of resources
  - [ ] `POST /mcp/tools/call` with `{"tool": "get_balance"}` returns balance
  - [ ] MCP routes authenticate via API key header

  **QA Scenarios**:
  ```
  Scenario: MCP manifest and balance tool
    Tool: Bash (curl)
    Preconditions: MCP API key configured, some transactions exist
    Steps:
      1. curl -s GET /mcp/manifest → verify has name, version, capabilities
      2. curl -s -X POST /mcp/tools/call -H "X-API-Key: $MCP_KEY" \
         -d '{"tool": "get_balance"}'
      3. Verify response has balance_jod and balance_usd
    Expected Result: MCP endpoints respond correctly
    Evidence: .sisyphus/evidence/task-11-mcp.txt
  ```

  **Commit**: YES
  - Message: `feat(mcp): MCP server routes`
  - Files: `backend/app/routers/mcp.py`, `backend/app/services/mcp_service.py`

- [ ] 12. API Key Management Endpoint

  **What to do**:
  - Create `backend/app/routers/api_keys.py`:
    - `GET /api/api-keys` — list user's API keys (masked: show last 4 chars)
    - `POST /api/api-keys` — generate new API key
    - `DELETE /api/api-keys/{id}` — revoke API key
  - Create `backend/app/models/api_key.py`:
    - ApiKey: id, user_id, key_hash, name, last_used_at, created_at, is_active
  - Add model to Alembic migrations
  - API keys are hashed with SHA-256 before storage
  - Full key only shown once at creation (like GitHub/GitLab pattern)
  - Keys are validated via a dependency in `backend/app/dependencies.py`: `get_current_user_by_api_key`
  - This dependency is used by MCP routes (Task 11)

  **Must NOT do**:
  - No plaintext key storage (always hash before saving)
  - No API key generated without authentication (user must be logged in)

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 7, 8, 9, 10, 11)
  - **Blocks**: Task 21
  - **Blocked By**: Task 5

  **Acceptance Criteria**:
  - [ ] `POST /api/api-keys` returns key + metadata (key shown once)
  - [ ] `GET /api/api-keys` returns list with masked keys
  - [ ] ApiKey model migrated and table exists
  - [ ] MCP routes work with valid API key

  **QA Scenarios**:
  ```
  Scenario: Generate and use API key
    Tool: Bash (curl)
    Preconditions: Authenticated user
    Steps:
      1. curl -s -X POST /api/api-keys -H "Authorization: Bearer $TOKEN" \
         -d '{"name": "mcp-dev"}'
         → Extract "key": "zwp_abc123def456..."
      2. curl -s GET /mcp/tools -H "X-API-Key: zwp_abc123def456..."
         → 200 OK
      3. curl -s GET /mcp/tools (no key)
         → 401
    Expected Result: API keys work for MCP auth
    Evidence: .sisyphus/evidence/task-12-apikey.txt
  ```

  **Commit**: YES
  - Message: `feat(api): API key management`
  - Files: `backend/app/routers/api_keys.py`, `backend/app/models/api_key.py`

- [ ] 13. OpenAI Service Layer + Structured Outputs

  **What to do**:
  - Create `backend/app/services/openai_service.py`:
    - Singleton service that holds OpenAI client (configured via env vars: API key, model, base URL)
    - `extract_transaction(nl_input: str) → TransactionProposal`:
      - Uses OpenAI structured outputs (`json_schema` response format)
      - Schema: `{amount_original: number, currency_original: "JOD"|"USD", description: string, category: string}`
      - Categories are constrained to a predefined list: Food, Transport, Housing, Utilities, Entertainment, Shopping, Health, Education, Income, Other
      - System prompt: "Extract financial transaction details from natural language. Be precise. If currency is not specified, assume JOD. If amount is ambiguous, ask for clarification."
    - `generate_persona(user_id, transaction, spending_context) → str`:
      - Takes the user's recent spending in that category
      - System prompt: "You are Whisper, a highly competent but slightly sarcastic financial assistant. Based on the user's spending in this category, generate a brief (1-2 sentence) response. Be helpful first, then gently roast if they're overspending. Never be mean or offensive."
      - Uses chat completions with the transaction and spending stats as context
    - `health_check() → bool` — validate API key works
  - Create `backend/app/schemas/agent.py` with Pydantic models:
    - `TransactionProposal` (amount_original, currency_original, description, category, confidence)
    - `WhisperResponse` (proposal: TransactionProposal, persona_message: str, spending_context: dict)
    - `AgentRequest` (message: str)
  - Keep the OpenAI client as a lazy singleton (created on first use)
  - Support configurable base URL (for future Groq/LM Studio compatibility)

  **Must NOT do**:
  - Don't hardcode the model name (env var: `WHISPER_MODEL`, default `gpt-4o-mini`)
  - Don't log the full API response (may contain PII in descriptions)
  - Don't make the persona generation mandatory if the extraction fails

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 14, 15, 16)
  - **Blocks**: Task 14
  - **Blocked By**: None

  **Acceptance Criteria**:
  - [ ] `extract_transaction("Spent 50 JOD on pizza")` returns structured TransactionProposal
  - [ ] Categories are constrained to the predefined list
  - [ ] `generate_persona(...)` returns a non-empty string
  - [ ] Service handles OpenAI API errors gracefully (returns error, doesn't crash)
  - [ ] `health_check()` returns False without valid API key

  **QA Scenarios**:
  ```
  Scenario: Extract transaction from NL
    Tool: Bash (python -c)
    Preconditions: OPENAI_API_KEY env var set
    Steps:
      1. Run: python -c "
      import asyncio
      from app.services.openai_service import OpenAIService
      svc = OpenAIService()
      result = asyncio.run(svc.extract_transaction('Spent 50 USD on Netflix'))
      print(result.model_dump_json())
      "
      2. Verify: amount_original=50, currency_original="USD", description contains "Netflix", category is one of valid categories
    Expected Result: Structured extraction works
    Evidence: .sisyphus/evidence/task-13-extract.txt
  ```

  **Commit**: YES
  - Message: `feat(agent): OpenAI service layer`
  - Files: `backend/app/services/openai_service.py`, `backend/app/schemas/agent.py`

- [ ] 14. Whisper Agent Endpoint + Propose Flow

  **What to do**:
  - Create `backend/app/routers/whisper.py`:
    - `POST /api/whisper/parse` — send natural language, get structured proposal + persona roast
      - Calls extract_transaction → generate_persona → returns WhisperResponse
      - Includes spending_context: category total this month, budget if set, percentage of income
    - `POST /api/whisper/confirm` — confirm a proposal and save to DB
      - Accepts: proposal_id (generated by parse), optional edits (user can modify fields)
      - Creates transaction in DB
    - `POST /api/whisper/reject` — discard a proposal
    - `GET /api/whisper/history` — past Whisper interactions
  - Create `backend/app/services/whisper_service.py`:
    - Orchestrates: parse → validate → get persona → return proposal
    - Tracks proposal sessions (pending/confirmed/rejected)
    - Computes spending_context: current month's total for the detected category
  - The proposal includes a `proposal_id` (UUID) that the frontend uses to confirm/reject
  - Proposals expire after 15 minutes (in-memory TTL cache or DB cleanup)

  **Must NOT do**:
  - Never auto-write to DB (user must confirm explicitly)
  - Don't store raw NL input long-term (privacy)
  - Don't confirm expired proposals

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 13, 15, 16)
  - **Blocks**: Task 19
  - **Blocked By**: Tasks 7, 13

  **Acceptance Criteria**:
  - [ ] `POST /api/whisper/parse` with "Add 20 USD for Netflix" returns proposal with amount=20, currency=USD
  - [ ] Response includes persona_message (non-empty, sounds like an assistant)
  - [ ] Response includes spending_context (at minimum: category, this_month_total)
  - [ ] `POST /api/whisper/confirm` with valid proposal_id creates transaction
  - [ ] `POST /api/whisper/confirm` with expired proposal_id returns 404
  - [ ] `POST /api/whisper/reject` discards proposal

  **QA Scenarios**:
  ```
  Scenario: Parse and confirm expense
    Tool: Bash (curl)
    Preconditions: Auth token, OPENAI_API_KEY set
    Steps:
      1. curl -s -X POST /api/whisper/parse -H "Authorization: Bearer $TOKEN" \
         -d '{"message": "Add 20 USD for Netflix"}'
         → Extract proposal_id, verify amount_original=20, currency_original="USD"
      2. curl -s -X POST /api/whisper/confirm -H "Authorization: Bearer $TOKEN" \
         -d '{"proposal_id": "<id>"}'
         → 201, return created transaction
      3. GET /api/transactions → new Netflix transaction appears
    Expected Result: Whisper flow works end-to-end
    Evidence: .sisyphus/evidence/task-14-whisper.txt

  Scenario: Persona roasts overspending
    Tool: Bash (curl)
    Preconditions: Multiple transactions in "Food" category this month
    Steps:
      1. Create 5 Food transactions totaling 300 JOD
      2. curl -s -X POST /api/whisper/parse -H "Authorization: Bearer $TOKEN" \
         -d '{"message": "Another 20 JOD for lunch"}'
      3. Verify persona_message references the overspending (contains "again", "already spent", or similar)
    Expected Result: Persona acknowledges spending pattern
    Evidence: .sisyphus/evidence/task-14-whisper-roast.txt
  ```

  **Commit**: YES
  - Message: `feat(agent): whisper agent endpoint and propose flow`
  - Files: `backend/app/routers/whisper.py`, `backend/app/services/whisper_service.py`

- [ ] 15. Frontend Scaffolding (Vite + React + Tailwind + Shadcn)

  **What to do**:
  - Initialize Vite + React + TypeScript project in `frontend/`
  - Install and configure Tailwind CSS (v4 if stable, v3 otherwise)
  - Initialize Shadcn UI components:
    - `button`, `card`, `input`, `label`, `form`, `dialog`, `select`, `table`, `tabs`, `avatar`, `badge`, `toast`, `dropdown-menu`, `separator`, `sheet`, `sonner`
  - Install additional deps: `recharts`, `lucide-react`, `date-fns`, `react-router-dom`, `axios`, `zod`, `react-hook-form`, `@hookform/resolvers`
  - Create project structure:
    ```
    src/
      components/ui/  (shadcn components)
      components/layout/
      components/features/
      pages/
      hooks/
      lib/
      types/
      contexts/
    ```
  - Create Vite proxy config to forward `/api/*` to backend on port 8000
  - Set up basic routing structure in `App.tsx`:
    - `/login` — login page (Task 16)
    - `/setup` — first-run setup
    - `/dashboard` — main dashboard (protected)
    - `/transactions` — transaction list
    - `/whisper` — chat interface
    - `/visualizations` — charts
    - `/settings` — settings
  - Configure TypeScript path aliases (`@/` → `src/`)
  - Create a basic `lib/utils.ts` with cn() helper

  **Must NOT do**:
  - No application logic or API calls in scaffolding
  - No global state management yet (use React context when needed)

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 13, 14, 16)
  - **Blocks**: Tasks 16, 17, 18, 19, 20, 21
  - **Blocked By**: Task 2

  **Acceptance Criteria**:
  - [ ] `npm run dev` starts Vite dev server
  - [ ] `npm run build` completes without errors
  - [ ] Shadcn components render (e.g., `<Button>Test</Button>` shows on page)
  - [ ] Proxy forwards `/api/*` to `localhost:8000`
  - [ ] Route structure works (pages render at correct paths)
  - [ ] Tailwind styles apply correctly

  **QA Scenarios**:
  ```
  Scenario: Frontend dev server starts and shows app
    Tool: Bash
    Preconditions: npm deps installed
    Steps:
      1. cd frontend && npm run dev &
      2. curl -s http://localhost:5173 | grep -q "ZeroWhisper" → check app renders
      3. curl -s http://localhost:5173/api/health | python -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='ok'" → proxy works
    Expected Result: App serves, proxy works
    Evidence: .sisyphus/evidence/task-15-frontend-scaffold.txt
  ```

  **Commit**: YES
  - Message: `feat(frontend): vite-react-tailwind-shadcn scaffold`
  - Files: `frontend/*`

- [ ] 16. Login Page + Auth Context

  **What to do**:
  - Create `src/pages/LoginPage.tsx`:
    - Login form with username + password fields
    - "Register" toggle for new users
    - Form validation with react-hook-form + zod
    - Error display for invalid credentials
    - Redirect to `/dashboard` on success
    - Link to `/setup` if DB is uninitialized
  - Create `src/contexts/AuthContext.tsx`:
    - AuthProvider wrapping the app
    - Stores JWT token in localStorage (with httpOnly consideration — localStorage is pragmatic for SPA)
    - `login(username, password)` → POST /auth/login → store token
    - `register(username, password)` → POST /auth/register
    - `logout()` → clear token → redirect to /login
    - `isAuthenticated` boolean
    - `token` getter for API calls
    - Auto-refresh token on 401 responses
  - Create `src/hooks/useAuth.ts` → convenience hook wrapping AuthContext
  - Create `src/lib/api.ts` → axios instance with interceptor:
    - Attaches `Authorization: Bearer <token>` to all requests
    - Handles 401 → attempts token refresh → if fails, logout
  - Create `src/components/layout/ProtectedRoute.tsx`:
    - Wraps routes that require authentication
    - Redirects to /login if not authenticated
  - Style everything with Shadcn components and Tailwind

  **Must NOT do**:
  - No OAuth/social login
  - No password complexity requirements in v1

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 13, 14, 15)
  - **Blocks**: Task 17
  - **Blocked By**: Tasks 7, 15

  **Acceptance Criteria**:
  - [ ] Login page renders at `/login` with form fields
  - [ ] Successful login redirects to `/dashboard`
  - [ ] Failed login shows error message
  - [ ] Auth token persists across page refresh (stored in localStorage, verify by reloading)
  - [ ] Protected routes redirect to `/login` when not authenticated
  - [ ] API calls include Bearer token header

  **QA Scenarios**:
  ```
  Scenario: Login flow
    Tool: Playwright
    Preconditions: Backend running, user registered
    Steps:
      1. Navigate to http://localhost:5173/login
      2. Fill username input with "alice"
      3. Fill password input with "secret123"
      4. Click login button
      5. Wait for navigation to /dashboard
    Expected Result: User is redirected to dashboard
    Evidence: .sisyphus/evidence/task-16-login.png

  Scenario: Invalid credentials
    Tool: Playwright
    Preconditions: Backend running
    Steps:
      1. Navigate to http://localhost:5173/login
      2. Fill username with "alice", password with "wrongpassword"
      3. Click login button
      4. Wait for error toast/message "Invalid credentials"
    Expected Result: Error message displayed, no redirect
    Evidence: .sisyphus/evidence/task-16-login-error.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): login page and auth context`
  - Files: `frontend/src/pages/LoginPage.tsx`, `frontend/src/contexts/AuthContext.tsx`, `frontend/src/hooks/useAuth.ts`, `frontend/src/lib/api.ts`

- [ ] 17. Dashboard Layout + Navigation Shell

  **What to do**:
  - Create `src/components/layout/DashboardLayout.tsx`:
    - Sidebar navigation (collapsible on mobile) with links to:
      - Dashboard (overview)
      - Transactions
      - Whisper Chat
      - Visualizations
      - Settings
    - Top bar with: current month selector, user avatar/dropdown (logout, profile)
    - Main content area using React Router `<Outlet />`
  - Create `src/components/layout/Sidebar.tsx`:
    - Icon + label for each nav item using lucide-react icons
    - Active route highlighting
    - Collapse/expand toggle
    - "ZeroWhisper" branding at top
  - Create `src/components/layout/TopBar.tsx`:
    - Date range picker for filtering all views
    - User avatar dropdown with logout
  - Create `src/pages/DashboardPage.tsx`:
    - Summary cards row: Total Balance (JOD + USD), Month Spending, Month Income, Whisper count
    - Mini recent transactions list (last 5)
    - Quick-add Whisper input (links to /whisper)
    - All data fetched from `/api/dashboard/summary`

  **Must NOT do**:
  - No heavy animations that impact performance
  - Don't build custom date picker — use Shadcn's or a simple one

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES (partial)
  - **Parallel Group**: Wave 4 (with Tasks 18, 19, 20, 21)
  - **Blocks**: Tasks 19, 20
  - **Blocked By**: Tasks 7, 15, 16

  **Acceptance Criteria**:
  - [ ] Sidebar shows all navigation items with icons
  - [ ] Clicking nav items changes the route
  - [ ] Active route is highlighted in sidebar
  - [ ] Dashboard page shows summary cards with data from backend
  - [ ] User avatar dropdown has logout option
  - [ ] Layout is responsive (sidebar collapses on mobile)
  - [ ] All pages within the layout render correctly

  **QA Scenarios**:
  ```
  Scenario: Dashboard loads with data
    Tool: Playwright
    Preconditions: Logged in, at least one transaction exists
    Steps:
      1. Navigate to http://localhost:5173/dashboard
      2. Verify sidebar is visible with nav items
      3. Verify summary cards show financial data (balance, spending)
      4. Take screenshot
    Expected Result: Dashboard renders with real data
    Evidence: .sisyphus/evidence/task-17-dashboard.png

  Scenario: Navigation works
    Tool: Playwright
    Preconditions: Logged in
    Steps:
      1. Navigate to /dashboard
      2. Click "Transactions" in sidebar
      3. Verify URL changes to /transactions
      4. Click "Whisper" in sidebar
      5. Verify URL changes to /whisper
    Expected Result: Navigation works correctly
    Evidence: .sisyphus/evidence/task-17-navigation.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): dashboard layout and navigation`
  - Files: `frontend/src/components/layout/*`, `frontend/src/pages/DashboardPage.tsx`

- [ ] 18. Transaction List + Entry Forms

  **What to do**:
  - Create `src/pages/TransactionsPage.tsx`:
    - Transaction list table with columns: Date, Description, Category, Amount (orig), Amount (JOD), Actions
    - Sortable columns (date, amount)
    - Filter bar: date range picker, category dropdown, currency toggle
    - Pagination controls
    - "Add Transaction" button → opens dialog/modal
    - "Import CSV" button → opens file upload dialog
    - Each row has edit/delete icons
  - Create `src/components/features/TransactionForm.tsx`:
    - Form fields: amount_original, currency_original (JOD/USD toggle), category (dropdown), description, transaction_date (date picker)
    - Validation with zod
    - Submit creates via POST /api/transactions
  - Create `src/components/features/TransactionRow.tsx`:
    - Single row with hover actions
    - Category badge (colored)
    - Currency indicator
  - Create `src/components/features/CsvImportDialog.tsx`:
    - File upload area (drag and drop + click)
    - Template download button
    - Import progress/result display
  - Create `src/hooks/useTransactions.ts`:
    - fetchTransactions(filters), createTransaction, updateTransaction, deleteTransaction
    - Pagination state management

  **Must NOT do**:
  - No inline editing (edit opens a modal)
  - No bulk operations in v1

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 17, 19, 20, 21)
  - **Blocks**: None
  - **Blocked By**: Tasks 8, 15

  **Acceptance Criteria**:
  - [ ] Transaction list loads and displays transactions from API
  - [ ] Add Transaction form creates a new transaction
  - [ ] CSV import dialog shows file upload and template download
  - [ ] Filters (date range, category, currency) work
  - [ ] Pagination works (page controls visible and functional)
  - [ ] Edit and delete actions work

  **QA Scenarios**:
  ```
  Scenario: Add transaction via form
    Tool: Playwright
    Preconditions: Logged in
    Steps:
      1. Navigate to /transactions
      2. Click "Add Transaction"
      3. Fill amount: 50, select currency: JOD, category: Food
      4. Fill description: "Lunch at restaurant", pick date: today
      5. Click Submit
      6. Verify new row appears in the table
    Expected Result: Transaction created and displayed
    Evidence: .sisyphus/evidence/task-18-add-transaction.png

  Scenario: Filter transactions
    Tool: Playwright
    Preconditions: Logged in, transactions in multiple categories
    Steps:
      1. Navigate to /transactions
      2. Select category filter: "Food"
      3. Verify only Food transactions shown
      4. Clear filter, verify all transactions shown
    Expected Result: Filtering works
    Evidence: .sisyphus/evidence/task-18-filter.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): transaction list and forms`
  - Files: `frontend/src/pages/TransactionsPage.tsx`, `frontend/src/components/features/Transaction*.tsx`, `frontend/src/hooks/useTransactions.ts`

- [ ] 19. Whisper Chat Interface

  **What to do**:
  - Create `src/pages/WhisperPage.tsx`:
    - Chat-style interface with message history
    - User messages (right-aligned, blue) and Whisper responses (left-aligned with avatar)
    - Input bar at bottom with send button
    - Loading state while waiting for Whisper response
  - Create `src/components/features/WhisperMessage.tsx`:
    - Renders a single chat bubble
    - User message: plain text
    - Whisper response: structured proposal card + persona roast text
  - Create `src/components/features/TransactionProposalCard.tsx`:
    - Shows: amount, currency, category, description (parsed by agent)
    - Editable fields (user can tweak before confirming)
    - Confirm and Reject buttons
    - Spending context indicator (e.g., "You've spent 300 JOD on Food this month")
  - Create `src/hooks/useWhisper.ts`:
    - `sendMessage(text)` → POST /api/whisper/parse
    - `confirmProposal(proposalId, edits?)` → POST /api/whisper/confirm
    - `rejectProposal(proposalId)` → POST /api/whisper/reject
    - Chat history from GET /api/whisper/history
  - Animated typing indicator while waiting for agent response

  **Must NOT do**:
  - No streaming/SSE (simple request-response is fine for v1)
  - Don't make persona roast too aggressive (keep it playful)

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 17, 18, 20, 21)
  - **Blocks**: None
  - **Blocked By**: Tasks 14, 15, 17

  **Acceptance Criteria**:
  - [ ] Chat interface renders with message history
  - [ ] Sending "Add 20 USD for Netflix" shows user message + Whisper response
  - [ ] Proposal card shows parsed fields (amount, currency, category, description)
  - [ ] Confirm button creates the transaction
  - [ ] Reject button dismisses the proposal
  - [ ] Typing indicator shows while waiting for response
  - [ ] Error state shows if API call fails

  **QA Scenarios**:
  ```
  Scenario: Full Whisper chat flow
    Tool: Playwright
    Preconditions: Logged in, OPENAI_API_KEY configured
    Steps:
      1. Navigate to /whisper
      2. Type "Add 20 USD for Netflix" in input
      3. Press Enter / click Send
      4. Wait for Whisper response (typing indicator → proposal card)
      5. Verify proposal shows: amount=20, currency=USD, category includes "Entertainment"
      6. Click Confirm
      7. Verify success toast and proposal changes to "Confirmed"
      8. Navigate to /transactions
      9. Verify Netflix transaction appears
    Expected Result: Full Whisper flow works
    Evidence: .sisyphus/evidence/task-19-whisper-ui.png

  Scenario: Reject proposal
    Tool: Playwright
    Preconditions: Logged in
    Steps:
      1. Navigate to /whisper
      2. Send "Spent 15 JOD on coffee"
      3. Wait for proposal card
      4. Click Reject
      5. Verify proposal is dismissed from chat
      6. Navigate to /transactions, verify no new transaction
    Expected Result: Proposal rejected, no transaction created
    Evidence: .sisyphus/evidence/task-19-whisper-reject.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): whisper chat interface`
  - Files: `frontend/src/pages/WhisperPage.tsx`, `frontend/src/components/features/Whisper*.tsx`, `frontend/src/hooks/useWhisper.ts`

- [ ] 20. Visualization Dashboard (Sankey, Heatmap, Cash Flow)

  **What to do**:
  - Create `src/pages/VisualizationsPage.tsx`:
    - Tabbed layout: Cash Flow, Sankey, Heatmap, Net Worth
  - Create `src/components/features/charts/CashFlowChart.tsx`:
    - Recharts ComposedChart (line + bar)
    - X-axis: days of month (or months if yearly view)
    - Y-axis: amount in JOD
    - Line: running balance
    - Bars: daily expenses (red) and income (green)
    - Date range selector
    - Data from GET /api/analytics/cash-flow?from=&to=
  - Create `src/components/features/charts/SankeyDiagram.tsx`:
    - Use Recharts Sankey or a custom SVG implementation
    - Actually, Recharts doesn't have native Sankey. Use a lightweight alternative or implement custom SVG
    - Option: `recharts` has `<Sankey>` since v2.12. Check current version. If not available, use `d3-sankey` directly with custom React component.
    - Nodes: Income categories (left) → spending categories (right)
    - Links: flow amounts between categories
    - Data from GET /api/analytics/sankey?month=&year=
  - Create `src/components/features/charts/BurnRateHeatmap.tsx`:
    - Recharts custom heatmap or custom grid
    - X-axis: days of month (1-31)
    - Y-axis: categories
    - Cell color intensity based on spending amount
    - Data from GET /api/analytics/heatmap?month=&year=
  - Create `src/components/features/charts/NetWorthChart.tsx`:
    - Recharts AreaChart
    - X-axis: time (months)
    - Y-axis: amount
    - Two areas: assets (green), liabilities (red), net worth line (blue)
    - Data from GET /api/analytics/net-worth
  - Create backend analytics endpoints:
    - `backend/app/routers/analytics.py`:
      - GET /api/analytics/cash-flow?from=&to=
      - GET /api/analytics/sankey?month=&year=
      - GET /api/analytics/heatmap?month=&year=
      - GET /api/analytics/net-worth
  - Create `backend/app/services/analytics_service.py` with aggregation queries

  **Must NOT do**:
  - Don't try to render Sankey with Recharts if it doesn't support it — use d3-sankey + custom SVG
  - Don't pre-compute heavy aggregations (keep queries efficient with SQL GROUP BY)
  - Labels should be truncated/rotated to avoid overlap

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 17, 18, 19, 21)
  - **Blocks**: None
  - **Blocked By**: Tasks 8, 10, 15, 17

  **Acceptance Criteria**:
  - [ ] Cash flow chart shows daily expenses and running balance
  - [ ] Sankey diagram shows income→category flows
  - [ ] Burn rate heatmap shows spending intensity by day+category
  - [ ] Net worth chart shows trends (with at least 2 data points)
  - [ ] All charts load data from backend API endpoints
  - [ ] Date/month selectors update chart data
  - [ ] Charts handle empty data gracefully (show "no data" message)

  **QA Scenarios**:
  ```
  Scenario: All charts render with data
    Tool: Playwright
    Preconditions: Logged in, 30+ transactions across multiple categories and dates
    Steps:
      1. Navigate to /visualizations
      2. Verify Cash Flow tab shows chart with bars and line
      3. Click Sankey tab, verify diagram renders
      4. Click Heatmap tab, verify grid with colors
      5. Take screenshot of each chart
    Expected Result: All visualizations render correctly
    Evidence: .sisyphus/evidence/task-20-charts.png

  Scenario: Empty state handling
    Tool: Playwright
    Preconditions: Logged in, fresh DB with no transactions
    Steps:
      1. Navigate to /visualizations
      2. Verify "No transaction data available" or equivalent message
    Expected Result: Charts don't crash, show empty state
    Evidence: .sisyphus/evidence/task-20-empty.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): visualization dashboard`
  - Files: `frontend/src/pages/VisualizationsPage.tsx`, `frontend/src/components/features/charts/*`, `backend/app/routers/analytics.py`, `backend/app/services/analytics_service.py`

- [ ] 21. Settings Page

  **What to do**:
  - Create `src/pages/SettingsPage.tsx`:
    - Tabbed settings: Profile, API Keys, Exchange Rates, Security, About
  - Profile tab:
    - Display username, email
    - Change password form
  - API Keys tab:
    - List of API keys (masked)
    - "Generate New Key" button
    - Revoke button per key
    - Shows full key once on creation with copy-to-clipboard
  - Exchange Rates tab:
    - Current rate display
    - Manual rate set form (rate value + date)
    - Rate history table
    - Auto-fetch toggle switch
    - Last fetched date display
  - Security tab:
    - Display recovery phrase (requires password re-entry to view)
    - Option to change DB encryption passphrase (requires current passphrase)
    - Warning about data loss if passphrase is lost
  - About tab:
    - App version
    - Link to docs
    - Tech stack info
  - Create `src/hooks/useSettings.ts` for API interactions
  - Create `backend/app/routers/settings.py`:
    - `GET /api/settings/profile` — user profile
    - `PUT /api/settings/profile` — update profile
    - `PUT /api/settings/password` — change password
    - `GET /api/settings/recovery-phrase` — returns stored BIP39 phrase (requires password verification)

  **Must NOT do**:
  - Recovery phrase shown only after password re-entry (security)
  - API key full value only shown once

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 17, 18, 19, 20)
  - **Blocks**: None
  - **Blocked By**: Tasks 5, 12, 15

  **Acceptance Criteria**:
  - [ ] All settings tabs render correctly
  - [ ] API key generation shows full key once, then masked in list
  - [ ] Copy-to-clipboard works for API key
  - [ ] Exchange rate can be set manually
  - [ ] Auto-fetch toggle works (backend setting updated)
  - [ ] Password change works
  - [ ] Recovery phrase display requires password re-entry

  **QA Scenarios**:
  ```
  Scenario: Generate API key from settings
    Tool: Playwright
    Preconditions: Logged in
    Steps:
      1. Navigate to /settings
      2. Click "API Keys" tab
      3. Click "Generate New Key"
      4. Verify modal shows full key (starts with "zwp_")
      5. Click copy button
      6. Verify key appears in list (masked: "zwp_*****f6a2")
    Expected Result: API key generation flow works
    Evidence: .sisyphus/evidence/task-21-apikeys.png

  Scenario: Set exchange rate
    Tool: Playwright
    Preconditions: Logged in
    Steps:
      1. Navigate to /settings → Exchange Rates tab
      2. Enter rate: 0.709, date: today
      3. Click Save
      4. Verify current rate display shows 0.709
      5. Verify rate history table has new entry
    Expected Result: Exchange rate updated
    Evidence: .sisyphus/evidence/task-21-rate.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): settings page`
  - Files: `frontend/src/pages/SettingsPage.tsx`, `frontend/src/hooks/useSettings.ts`, `backend/app/routers/settings.py`

- [ ] 22. Docker Compose Finalization + Nginx

  **What to do**:
  - Create `docker/docker-compose.yml`:
    - Services: `backend`, `frontend`, `nginx`
    - Backend service:
      - Build from `docker/backend.Dockerfile`
      - Port 8000
      - Volumes: `./data:/app/data` (persistent DB storage)
      - Environment: WHISPER_MODEL, OPENAI_API_KEY, LOG_LEVEL
      - Restart: unless-stopped
    - Frontend service:
      - Build from `docker/frontend.Dockerfile`
      - Port 5173 (or 80 behind nginx)
      - Environment: VITE_API_URL
    - Nginx service:
      - Uses `docker/nginx.conf`
      - Port 80 → frontend, /api/* → backend
      - Simple reverse proxy config
    - Network: internal network for services
  - Create `docker/nginx.conf`:
    - Serves frontend static build
    - Proxies `/api/*` to backend at `backend:8000`
    - Proxies `/mcp/*` to backend at `backend:8000`
    - Proxies `/setup/*` to backend at `backend:8000`
    - WebSocket support if needed
  - Create `docker-compose.override.yml` for local dev:
    - Frontend uses Vite dev server with hot reload
    - Backend uses uvicorn with --reload
  - Create `Makefile` at project root with useful commands:
    - `make dev` — docker compose up with override
    - `make build` — build all images
    - `make prod` — production docker compose up
    - `make clean` — remove volumes, rebuild
    - `make test` — run backend tests
    - `make backup` — backup the encrypted DB
    - `make logs` — tail logs

  **Must NOT do**:
  - Don't include the .env file in docker-compose.yml (use .env.example with instructions)
  - Don't expose backend ports directly in production (only through nginx)

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 5 (with Tasks 23, 24)
  - **Blocks**: None
  - **Blocked By**: Tasks 2, 6

  **Acceptance Criteria**:
  - [ ] `docker compose up` starts all 3 services
  - [ ] `curl http://localhost` serves frontend
  - [ ] `curl http://localhost/api/health` returns 200
  - [ ] Frontend can communicate with backend through nginx proxy
  - [ ] `make dev` starts with hot-reload
  - [ ] Volume mount creates data/ directory on host

  **QA Scenarios**:
  ```
  Scenario: Full stack starts via docker compose
    Tool: Bash
    Preconditions: Docker installed
    Steps:
      1. docker compose -f docker/docker-compose.yml up -d
      2. sleep 10  # Wait for services
      3. curl -s http://localhost/api/health → {"status":"ok"}
      4. curl -s http://localhost | grep -q "ZeroWhisper"
      5. docker compose down
    Expected Result: Full stack running, API + frontend accessible
    Evidence: .sisyphus/evidence/task-22-docker-compose.txt

  Scenario: Data persistence
    Tool: Bash
    Preconditions: Docker running
    Steps:
      1. docker compose -f docker/docker-compose.yml up -d
      2. curl -s -X POST /setup/initialize -d '{"passphrase":"test"}'
      3. docker compose down
      4. docker compose -f docker/docker-compose.yml up -d
      5. curl -s GET /setup/status → {"state":"INITIALIZED"}
      6. docker compose down
    Expected Result: DB persists across container restarts
    Evidence: .sisyphus/evidence/task-22-persistence.txt
  ```

  **Commit**: YES
  - Message: `feat(infra): docker compose finalization`
  - Files: `docker/docker-compose.yml`, `docker/nginx.conf`, `Makefile`

- [ ] 23. End-to-End Integration Tests

  **What to do**:
  - Create `backend/tests/e2e/` directory
  - Create `backend/tests/e2e/test_full_flow.py`:
    - `test_first_run_setup`:
      - Verify UNINITIALIZED state
      - Initialize with passphrase
      - Verify INITIALIZED state
      - Verify recovery phrase is valid BIP39 (12 words from standard list)
    - `test_auth_flow`:
      - Register user
      - Login with correct password → get JWT
      - Login with wrong password → 401
      - Access protected endpoint without token → 401
      - Access with valid token → 200
    - `test_transaction_crud`:
      - Create transaction (JOD)
      - Create transaction (USD, with exchange rate set)
      - Verify amount_base is computed correctly
      - List transactions with pagination
      - Filter transactions by category
      - Soft-delete transaction
      - Verify deleted transaction not in list
    - `test_csv_import`:
      - Create valid CSV, import → verify count
      - Create CSV with bad row → verify partial import + error
    - `test_whisper_agent` (requires OPENAI_API_KEY):
      - Parse NL input → verify structured proposal
      - Confirm proposal → verify transaction in DB
      - Reject proposal → verify no transaction created
    - `test_mcp_endpoints`:
      - Access MCP without API key → 401
      - Generate API key → use it for MCP → 200
      - Call get_balance tool → verify response structure
    - `test_encryption`:
      - Try to open DB with standard sqlite3 → verify it fails
      - Try to open with wrong SQLCipher key → verify it fails
  - Create `conftest.py` with fixtures:
    - `test_db` — temporary encrypted database
    - `test_client` — FastAPI TestClient
    - `auth_headers` — pre-authenticated headers
    - `sample_transactions` — set of test transactions

  **Must NOT do**:
  - Don't test against production DB
  - Don't require OpenAI key for tests that don't need it (skip with pytest.mark)
  - Tests must clean up after themselves

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 5 (with Tasks 22, 24)
  - **Blocks**: None
  - **Blocked By**: Tasks 7, 8, 9, 11, 12, 14, 17, 18, 19, 20, 21

  **Acceptance Criteria**:
  - [ ] `pytest backend/tests/e2e/ -v` passes all tests
  - [ ] Test coverage of key flows: setup, auth, CRUD, CSV, Whisper, MCP, encryption
  - [ ] Tests clean up temp DB files
  - [ ] OpenAI-dependent tests are marked and skipped without API key
  - [ ] Each test is independent (no shared state)

  **QA Scenarios**:
  ```
  Scenario: All E2E tests pass
    Tool: Bash
    Preconditions: Backend deps installed, OPENAI_API_KEY set (optional)
    Steps:
      1. cd backend && pytest tests/e2e/ -v --tb=short 2>&1
      2. Verify all expected tests pass
    Expected Result: All integration tests pass
    Evidence: .sisyphus/evidence/task-23-e2e-tests.txt
  ```

  **Commit**: YES
  - Message: `test: e2e integration tests`
  - Files: `backend/tests/e2e/*`

- [ ] 24. Documentation + README

  **What to do**:
  - Create `README.md` at project root:
    - Project overview and screenshots (placeholder)
    - Architecture diagram (ASCII or Mermaid)
    - Quick start guide:
      1. Prerequisites (Docker, OpenAI API key)
      2. `git clone` and `cd`
      3. `cp .env.example .env` and fill in
      4. `make dev` to start
      5. Open browser, go through setup flow
    - Detailed setup instructions:
      - Environment variables reference
      - First-run flow explanation
      - Recovery phrase backup instructions
    - Features overview with screenshots (placeholder)
    - API documentation (link to /docs when running)
    - MCP integration guide:
      - How to configure in Cursor/Claude Desktop
      - Available resources and tools
      - Example queries
    - Development guide:
      - Backend testing: `make test`
      - Adding migrations: Alembic instructions
      - Frontend development: hot reload
    - Security notes:
      - DB encryption
      - Key management
      - Recovery phrase
  - Create `CONTRIBUTING.md` (optional)
  - Create `.env.example` with all configurable env vars and comments

  **Must NOT do**:
  - No generated screenshots (placeholder text is fine)
  - Don't commit actual .env file

  **Recommended Agent Profile**:
  - **Category**: `writing`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 5 (with Tasks 22, 23)
  - **Blocks**: None
  - **Blocked By**: Tasks 22, 23

  **Acceptance Criteria**:
  - [ ] README.md exists with all sections
  - [ ] Quick start guide works (steps are accurate)
  - [ ] All env vars documented in .env.example
  - [ ] MCP integration guide is actionable

  **QA Scenarios**:
  ```
  Scenario: Verify README completeness
    Tool: Bash
    Preconditions: None
    Steps:
      1. grep -q "Quick Start" README.md → found
      2. grep -q "MCP Integration" README.md → found
      3. grep -q "Architecture" README.md → found
      4. grep -q "Security" README.md → found
    Expected Result: All required sections present
    Evidence: .sisyphus/evidence/task-24-readme.txt
  ```

  **Commit**: YES
  - Message: `docs: README and setup guide`
  - Files: `README.md`, `.env.example`

---

## Final Verification Wave (MANDATORY)
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, curl endpoint, run command). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in `.sisyphus/evidence/`. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high` (load_skills=[])
  Run `pytest`, `mypy backend/`, ESLint + TypeScript check on frontend. Review all changed files for: `try: except: pass`, `# type: ignore`, console.log in prod, commented-out code, unused imports. Check AI slop: excessive comments, over-abstraction, generic names (data/result/item/temp).
  Output: `Build [PASS/FAIL] | Lint [PASS/FAIL] | Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Real Manual QA** — `unspecified-high` (load_skills=["playwright"])
  Start from clean state (delete DB, docker compose down -v). Execute the first-run flow, register, add transactions via all three methods (manual, CSV, Whisper). Test cross-task integration. Save evidence to `.sisyphus/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff (git log/diff). Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance. Detect cross-task contamination.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **Wave 1 commits**: `feat(db): sqlcipher connectivity spike`, `feat(infra): project scaffolding and docker base`, `feat(db): base SQLModel schemas`, `feat(db): alembic migrations`, `feat(auth): first-run setup flow`, `feat(docker): backend Dockerfile`
- **Wave 2 commits**: `feat(auth): JWT auth endpoints and middleware`, `feat(api): transaction CRUD with dual-currency`, `feat(api): CSV import service`, `feat(api): exchange rate service`, `feat(mcp): MCP server routes`, `feat(api): API key management`
- **Wave 3 commits**: `feat(agent): OpenAI service layer`, `feat(agent): whisper agent endpoint`, `feat(frontend): vite-react-tailwind-scaffold`, `feat(frontend): login page and auth context`
- **Wave 4 commits**: `feat(frontend): dashboard layout`, `feat(frontend): transaction list and forms`, `feat(frontend): whisper chat interface`, `feat(frontend): visualization dashboard`, `feat(frontend): settings page`
- **Wave 5 commits**: `feat(infra): docker compose finalization`, `test: e2e integration tests`, `docs: README and setup guide`

---

## Success Criteria

### Verification Commands
```bash
# Backend tests
cd backend && pytest -v --cov=app --cov-report=term

# Frontend build check
cd frontend && npm run build

# Docker check
docker compose build && docker compose up -d
curl -s http://localhost:8000/health | python -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='ok'"

# First-run check
curl -s http://localhost:8000/setup/status | python -c "import sys,json; d=json.load(sys.stdin); assert d['state'] in ('UNINITIALIZED','KEY_SETTING','INITIALIZED')"

# Encryption check
file data/zerowhisper.db | grep -q "SQLite" && echo "WARNING: DB not encrypted" || echo "DB is encrypted"
sqlite3 data/zerowhisper.db "SELECT count(*) FROM sqlite_master" 2>&1 | grep -q "file is not a database" && echo "Encryption verified"

# Auth check
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login -d '{"username":"admin","password":"test"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/transactions | python -c "import sys,json; d=json.load(sys.stdin); assert 'items' in d"

# Frontend check
curl -s http://localhost:5173 | grep -q "ZeroWhisper" && echo "Frontend serves correctly"
```

### Final Checklist
- [ ] All "Must Have" present and verified
- [ ] All "Must NOT Have" absent (verified by search)
- [ ] All pytest tests pass (min 80% coverage)
- [ ] Frontend builds without errors
- [ ] Docker compose starts all services
- [ ] DB encryption verified (cannot read with standard sqlite3)
- [ ] First-run flow: UNINITIALIZED → KEY_SETTING → INITIALIZED
- [ ] JWT auth: protected endpoints return 401 without token
- [ ] Whisper agent: natural language input returns structured proposal
- [ ] CSV import: 10 rows in → 10 rows stored
- [ ] MCP endpoint returns financial stats
- [ ] All evidence files present in `.sisyphus/evidence/`
