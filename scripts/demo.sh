#!/usr/bin/env bash
# A local-only demo. Force all paid and outbound email integrations off.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${KNOWLEDGEFORGE_DEMO_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/knowledgeforge-demo}"
mkdir -p "$DATA_DIR"
export DATABASE_URL="sqlite+aiosqlite:///$DATA_DIR/knowledgeforge.db"
export STORAGE_PATH="$DATA_DIR/uploads"
export ENVIRONMENT=development STORAGE_BACKEND=local TASK_MODE=inline BOOTSTRAP_SCHEMA=true
export OPENAI_API_KEY= SMTP_HOST= PUBLIC_URL=http://localhost:3000 SECURE_COOKIES=false
export API_INTERNAL_URL=http://127.0.0.1:8000
cd "$ROOT/apps/api"
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock
.venv/bin/python -m app.seed
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
API_PID=$!
trap 'kill "$API_PID" 2>/dev/null || true' EXIT INT TERM
cd "$ROOT/apps/web"
npm ci
npm run dev -- --port 3000
