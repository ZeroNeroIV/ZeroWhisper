# ZeroWhisper

Self-hosted personal finance manager with encrypted storage and an AI-powered expense entry agent.

## Features

- **Multi-vault**: create independent databases, each its own encrypted or open vault
- **Secure vaults**: AES-256 SQLCipher encryption, PBKDF2-SHA256 key derivation, BIP39 recovery phrase
- **Open vaults**: unencrypted, no passphrase, auto-unlock on startup — anyone who can reach the app can register and log in
- Dual-currency transactions (JOD + USD with exchange rate tracking)
- Natural language expense entry via "Whisper" AI agent (OpenAI, Groq, or local Whisper)
- Voice input with server-side transcription (local faster-whisper — free, offline, multilingual)
- CSV import with automatic bank format detection
- Interactive dashboards: cash flow, Sankey diagram, burn-rate heatmap, net worth trend
- MCP server for querying your finances from Cursor/Claude Desktop
- Mobile-friendly responsive UI
- JWT authentication with access + refresh tokens

## Architecture

```
Browser → nginx(:80) → static files (frontend build)
                     → /api /auth /setup /mcp → FastAPI(:8000)
```

In dev mode, Vite's dev server proxies those prefixes to FastAPI directly; nginx is bypassed.

## Quick Start

Prerequisites: Docker, Docker Compose.

```bash
git clone <repo>
cd ZeroWhisper
cp .env.example .env
# Edit .env: set JWT_SECRET (required). AI keys are optional — local Whisper runs offline.
make prod
# Open http://localhost
```

On first run, the browser opens the vault setup page. Create a **secure vault** (passphrase + 24-word recovery phrase) or an **open vault** (no passphrase, auto-unlocks). Then register your user account.

## Vault Types

| Type | Encryption | Unlock | Registration |
|------|-----------|--------|--------------|
| Secure | AES-256 SQLCipher | Passphrase required after each restart | Restricted to users you create |
| Open | None (plain SQLite) | Automatic on startup | Anyone with access to the URL can register |

You can have multiple vaults. Only one is active at a time.

## Development

```bash
make dev        # Start with hot-reload (backend :8000, frontend :5173, nginx :80)
make test       # Run backend pytest suite
make logs       # Tail service logs
make backup     # Backup encrypted DB
```

Running services directly:

```bash
# Backend — requires .env and an initialized vault
cd backend && uvicorn app.main:app --reload

# Frontend
cd frontend && npm run dev

# Alembic migrations
cd backend && alembic upgrade head
```

## AI & Voice Input

ZeroWhisper uses AI for two things: the Whisper chat agent (natural language → transaction) and voice transcription (mic → text).

**Transcription priority** (first available key wins):

1. **Groq** (`GROQ_API_KEY`) — free tier, fast
2. **OpenAI** (`OPENAI_API_KEY`) — paid
3. **Local faster-whisper** — always available, runs on CPU, no API key needed

The local model (`small` by default, ~484 MB) is downloaded on first use and cached in a named Docker volume (`whisper_models`), so it survives container rebuilds.

**Chat agent** uses OpenAI or Gemini (`AI_PROVIDER`). Without an API key, the agent tab is disabled.

## Remote Access

To access ZeroWhisper from anywhere, use Tailscale:

```bash
tailscale serve --bg 80   # exposes port 80 over HTTPS at your MagicDNS hostname
```

## API Documentation

When the server is running, visit `http://localhost:8000/docs` for the interactive Swagger UI.

| Prefix | Description |
|--------|-------------|
| `/setup` | Vault management (initialize, unlock, recover, list, create open vault) |
| `/auth` | Login and token refresh |
| `/api/transactions` | Create, list, update, delete transactions |
| `/api/imports` | CSV import |
| `/api/exchange-rates` | JOD/USD rate management |
| `/api/api-keys` | API key management |
| `/api/whisper` | Natural language expense entry |
| `/api/analytics` | Spending breakdowns and trends |
| `/api/dashboard` | Dashboard data |
| `/mcp` | MCP server endpoint |

## MCP Integration

Generate an API key in Settings → API Keys, then add the server to Cursor (`~/.cursor/mcp.json`) or Claude Desktop:

```json
{
  "mcpServers": {
    "zerowhisper": {
      "url": "http://localhost/mcp",
      "headers": { "X-API-Key": "zwp_your_key_here" }
    }
  }
}
```

Available tools: `get_balance`, `get_recent_transactions`, `get_spending_by_category`, `get_net_worth`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET` | (required) | JWT signing secret — generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `OPENAI_API_KEY` | `""` | OpenAI key for Whisper agent + transcription |
| `GROQ_API_KEY` | `""` | Groq key for transcription (free tier) |
| `WHISPER_MODEL` | `gpt-4o-mini` | OpenAI model for the chat agent |
| `AI_PROVIDER` | `openai` | Chat agent provider: `openai` or `gemini` |
| `GEMINI_API_KEY` | `""` | Gemini key (if `AI_PROVIDER=gemini`) |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model |
| `LOCAL_WHISPER_MODEL` | `small` | Local transcription model: `tiny`, `base`, `small`, `medium`, `large-v3` |
| `AUTO_FETCH_EXCHANGE_RATE` | `false` | Auto-fetch JOD/USD rate from Frankfurter API |
| `DEFAULT_EXCHANGE_RATE` | `0.709` | Fallback JOD per USD |
| `LOG_LEVEL` | `INFO` | Logging level |

See `.env.example` for the full list.

## Security

- Secure vault databases are encrypted with AES-256 via SQLCipher. Running `sqlite3 data/zerowhisper.db` shows "file is not a database".
- The encryption key is derived via PBKDF2-SHA256 (260,000 iterations) and held only in memory — never written to disk, env files, or logs.
- The 24-word BIP39 recovery phrase is shown once at vault creation. Back it up offline.
- Open vaults are intentionally unencrypted. Use them only on networks you trust.

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLModel, pysqlcipher3, faster-whisper, Alembic, python-jose, passlib
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS v4, Fluent UI v9, Recharts
- **Infrastructure**: Docker, nginx, Docker Compose
