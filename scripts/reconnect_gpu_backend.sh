#!/bin/bash
# scripts/reconnect_gpu_backend.sh <cloudflare-tunnel-url>
#
# Local half of the Colab GPU reconnect flow. After running
# ml_training/balanceai_gpu_setup.ipynb (Runtime -> Run all) in Colab and
# copying the printed tunnel URL, run this script with that URL. It:
#   1. verifies the tunnel is actually reachable and lists the models Ollama
#      sees on the other end,
#   2. updates the repo's .env (OLLAMA_HOST=<url>) so it stays correct for
#      the next plain restart too,
#   3. stops any existing uvicorn backend,
#   4. restarts it with OLLAMA_HOST and OLLAMA_BASE_URL both pointed at the
#      tunnel (pharmacy_service.py reads settings.OLLAMA_HOST via
#      src/api/core/config.py; medical_understanding.py reads the
#      OLLAMA_BASE_URL env var directly -- both must be set, which is why
#      both are exported here),
#   5. fires one real /pharmacy/match query through the full stack
#      (embedding retrieval -> Ollama reasoning over the Colab GPU) and
#      reports pass/fail.
#
# Usage:
#   scripts/reconnect_gpu_backend.sh https://xxxx-xxxx.trycloudflare.com

set -uo pipefail

URL="${1:-}"
if [ -z "$URL" ]; then
  echo "usage: $0 <cloudflare-tunnel-url>" >&2
  exit 1
fi
URL="${URL%/}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$REPO_ROOT/src/api"
UVICORN_BIN="$REPO_ROOT/.venv/bin/uvicorn"
ENV_FILE="$REPO_ROOT/.env"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$REPO_ROOT/session_history/backend_restart_${STAMP}.log"
mkdir -p "$REPO_ROOT/session_history"

ts() { date '+%Y-%m-%d %H:%M:%S'; }
log() { echo "[$(ts)] $*"; }
fail() { echo "[$(ts)] FAIL: $*" >&2; exit 1; }

log "[1/5] checking tunnel reachability: $URL"
TAGS_JSON="$(curl -s --max-time 10 "$URL/api/tags")" || fail "could not reach $URL/api/tags"
echo "$TAGS_JSON" | python3 -c "
import json,sys
try:
    d = json.load(sys.stdin)
except Exception as e:
    print('invalid JSON from tunnel:', e); sys.exit(1)
models = [m.get('name') for m in d.get('models', [])]
if not models:
    print('tunnel reachable but no models listed'); sys.exit(1)
print('tunnel reachable, models on Colab side:')
for m in models:
    print('  -', m)
" || fail "tunnel at $URL did not return a usable model list"

if ! echo "$TAGS_JSON" | grep -q "HuatuoGPT"; then
  log "WARNING: HuatuoGPT model not visible in tunnel's /api/tags -- check the Colab pull step"
fi

log "[2/5] updating $ENV_FILE (OLLAMA_HOST=$URL)"
if [ -f "$ENV_FILE" ] && grep -q '^OLLAMA_HOST=' "$ENV_FILE"; then
  sed -i "s|^OLLAMA_HOST=.*|OLLAMA_HOST=$URL|" "$ENV_FILE"
else
  echo "OLLAMA_HOST=$URL" >> "$ENV_FILE"
fi

log "[3/5] stopping existing backend (if any)"
pkill -f "uvicorn main:app" 2>/dev/null && sleep 2 || log "no existing backend process found"

log "[4/5] starting backend with OLLAMA_HOST=$URL OLLAMA_BASE_URL=$URL"
cd "$API_DIR" || fail "cannot cd into $API_DIR"
OLLAMA_HOST="$URL" OLLAMA_BASE_URL="$URL" \
  setsid nohup "$UVICORN_BIN" main:app --host 0.0.0.0 --port 8000 --workers 2 \
  >"$LOG_FILE" 2>&1 < /dev/null &
NEW_PID=$!
log "backend relaunched, pid=$NEW_PID, log=$LOG_FILE"

UP=0
for _ in $(seq 1 20); do
  if curl -s -o /dev/null http://127.0.0.1:8000/docs; then
    UP=1
    break
  fi
  sleep 2
done
[ "$UP" -eq 1 ] || fail "backend did not come up on :8000 within 40s -- see $LOG_FILE"
log "backend is up on :8000"

log "[5/5] real end-to-end test query: POST /pharmacy/match"
TEST_RESPONSE="$(curl -s --max-time 90 -X POST http://127.0.0.1:8000/pharmacy/match \
  -H "Content-Type: application/json" \
  -d '{"text": "I have had a burning sensation when urinating and lower back pain for two days"}')"

echo "$TEST_RESPONSE" | python3 -c "
import json, sys
raw = sys.stdin.read()
try:
    d = json.loads(raw)
except Exception:
    print('FAIL: /pharmacy/match did not return JSON:', raw[:500]); sys.exit(1)
if 'disease_id' in d or 'disease_name' in d:
    print('PASS: got disease_id=%r disease_name=%r' % (d.get('disease_id'), d.get('disease_name')))
else:
    print('FAIL: unexpected response shape:', json.dumps(d)[:500]); sys.exit(1)
" || fail "end-to-end /pharmacy/match query failed -- check $LOG_FILE and that the Colab-side model is pulled"

log "DONE. Backend is live on :8000, HuatuoGPT reasoning routed through $URL"
