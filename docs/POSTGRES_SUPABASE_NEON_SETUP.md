# Supabase + Neon Postgres Setup (FinPilot-AI)

FinPilot runs on **SQLite by default** (zero-setup) and switches to **Postgres**
automatically when `DATABASE_URL` is set. Same code, same tests. No code change needed.

## 1. Get a Postgres URL

### Option A — Supabase (recommended for auth/storage later)
1. Go to https://supabase.com/dashboard -> New project.
2. Project Settings -> Database -> Connection string -> **URI**.
   - Use port `5432` (direct) for migrations, or `6543` (pooler) for serverless.
   - Format: `postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres?sslmode=require`
3. Copy it. Keep `SUPABASE_URL` + `SUPABASE_ANON_KEY` from Project Settings -> API
   (needed only if you later use Supabase Auth/Storage; not required for SQL).

### Option B — Neon (recommended for autoscale branching)
1. Go to https://console.neon.tech -> New project.
2. Dashboard -> Connection Details -> copy **psql** connection string.
   - Format: `postgresql://[USER]:[PASS]@[EP].neon.tech:5432/[DB]?sslmode=require`
3. Create a `prod` branch before going live (Neon branching = instant rollback).

> I cannot provision Supabase/Neon for you without access. Paste the URL into
> `.env` locally or Render dashboard (see step 3). Never commit real URLs to git.

## 2. Configure locally

```powershell
copy .env.example .env
# edit .env:
# DATABASE_URL=postgresql://...?sslmode=require
pip install -r requirements.txt
python -m src.app.benchmarks.run_controller --json   # verifies engine
python run_server.py
curl http://localhost:8000/ready        # database.engine should be "Postgres"
curl http://localhost:8000/v1/ai/status # ai_ready + provider
curl http://localhost:8000/v1/db/status
```

First boot auto-creates all 7 tables + indexes + seeds 120 benchmark records
(`ON CONFLICT DO NOTHING`, safe to re-run).

## 3. Configure on Render (production)

Render dashboard -> finpilot-ai -> Environment -> add:
- `DATABASE_URL` = your Supabase/Neon URL (mark Secret)
- `LLM_PROVIDER=auto`, plus ONE of `OPENAI_API_KEY` / `OPENCODE_API_KEY` / `GROQ_API_KEY`
- `CORS_ORIGINS=https://your-frontend-domain` (never `*` + credentials)
- `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` (test keys first)

`render.yaml` already declares `healthCheckPath: /health` and secret placeholders.
Redeploy. Verify:
- `GET https://<app>.onrender.com/health` -> healthy
- `GET .../ready` -> database.connected true, engine Postgres
- Run “Month-End Close” in UI once (creates first reconciliation_runs row).

## 4. Migrate existing SQLite data (optional)

If you have local `src/app/data/finpilot.db` with runs you want to keep:

```powershell
$env:DATABASE_URL="postgresql://...?sslmode=require"
python scripts/migrate_sqlite_to_postgres.py
```

Script copies benchmark_records + runs/items/exceptions/approvals/audit/metrics
with `ON CONFLICT DO NOTHING`. Re-runnable, never deletes destination.

## 5. AI keys (OpenCode-compatible)

Resolution order (`src/app/services/llm_provider.py`):
`LLM_PROVIDER=disabled` -> simulation always.
Explicit `LLM_PROVIDER=openai|opencode|groq|anthropic|openai_compatible`.
`auto`: `LLM_BASE_URL+LLM_API_KEY` > `OPENCODE_API_KEY` > `OPENAI_API_KEY`
(+`OPENAI_BASE_URL` for gateways) > `GROQ_API_KEY` > `ANTHROPIC_API_KEY` > simulation.

- OpenCode Zen: `OPENCODE_API_KEY=<key>`, `OPENCODE_BASE_URL=https://opencode.ai/zen/v1`,
  `OPENCODE_MODEL=<model>` (or `LLM_MODEL`). Treated as OpenAI-compatible.
- Any OpenAI-compatible (OpenRouter/Ollama/vLLM): `OPENAI_BASE_URL=<url>`,
  `OPENAI_API_KEY=<key>`, `OPENAI_MODEL=<model>`.
- No key = deterministic templates (money math stays in Python, zero hallucination).

Check: `GET /v1/ai/status` (no secrets leaked).

## 6. Rollback

Unset `DATABASE_URL` and redeploy/restart -> instantly back to SQLite.
Postgres data remains untouched. To switch providers, just change the URL;
reboot re-runs idempotent DDL + seed.
