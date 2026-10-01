#!/bin/bash
# ml_training/colab_setup.sh
#
# One-shot, idempotent GPU-session setup for serving the HuatuoGPT-o1-8B model
# out of a Colab runtime for BalanceAI's pharmacy_service.py / medical_understanding.py.
#
# WHAT THIS REPLACES: the old manual cycle every time the free-tier Colab VM
# recycled -- install zstd, install ollama, start ollama serve with the right
# host env var, re-pull the ~5.7GB HuatuoGPT model from scratch, install
# cloudflared, start the tunnel, copy the URL. That took real hours per cycle,
# most of it the model re-download.
#
# WHAT'S NOW CACHED ACROSS RECYCLES (this is the actual time saver):
#   If Google Drive is mounted at /content/drive (see balanceai_gpu_setup.ipynb),
#   this script points OLLAMA_MODELS at a folder on Drive instead of the
#   ephemeral Colab local disk. The 5.7GB model pull then only ever happens
#   ONCE, on the very first run. Every later run -- even after the VM is fully
#   wiped and reassigned -- finds the model already on Drive and skips the
#   pull entirely (seconds instead of ~10-20 minutes depending on Colab's
#   network luck).
#
# WHAT A HUMAN DOES EACH TIME (this is now down to 2 real actions):
#   1. Open balanceai_gpu_setup.ipynb in Colab, Runtime -> Run all.
#      (This mounts Drive, then runs this script.)
#   2. Copy the "TUNNEL URL" printed at the end and run, on the local machine:
#        scripts/reconnect_gpu_backend.sh <tunnel-url>
#
# Safe to re-run: every step below checks current state first and skips work
# that's already done (installed binary, running server, pulled model,
# live tunnel), so re-running this mid-session (e.g. tunnel died) is cheap.

set -uo pipefail

MODEL_TAG="hf.co/bartowski/HuatuoGPT-o1-8B-GGUF:Q5_K_M"
MODEL_MATCH="HuatuoGPT-o1-8B-GGUF"
DRIVE_ROOT="/content/drive/MyDrive"
DRIVE_MODELS_DIR="$DRIVE_ROOT/balanceai_ollama_models"
LOG_DIR="/content/balanceai_setup_logs"
OLLAMA_PORT=11434

mkdir -p "$LOG_DIR"
ts() { date '+%Y-%m-%d %H:%M:%S'; }
log() { echo "[$(ts)] $*"; }

log "[1/6] zstd"
if command -v zstd >/dev/null 2>&1; then
  log "zstd already installed, skipping"
else
  apt-get -qq update >"$LOG_DIR/apt_update.log" 2>&1
  apt-get -qq install -y zstd >"$LOG_DIR/zstd_install.log" 2>&1
  log "zstd installed"
fi

log "[2/6] ollama binary"
if command -v ollama >/dev/null 2>&1; then
  log "ollama already installed, skipping ($(ollama --version 2>&1 | head -1))"
else
  curl -fsSL https://ollama.com/install.sh | sh >"$LOG_DIR/ollama_install.log" 2>&1
  log "ollama installed"
fi

log "[3/6] model storage location"
if [ -d "$DRIVE_ROOT" ]; then
  mkdir -p "$DRIVE_MODELS_DIR"
  export OLLAMA_MODELS="$DRIVE_MODELS_DIR"
  log "Drive mounted -- using persistent model dir: $OLLAMA_MODELS"
  log "(model pull below is skipped on every run after the first)"
else
  log "WARNING: Drive not mounted at $DRIVE_ROOT -- model storage will be" >&2
  log "ephemeral local disk and the ~5.7GB model will re-download next session." >&2
  log "Mount Drive first (see balanceai_gpu_setup.ipynb) to avoid this." >&2
fi

log "[4/6] ollama serve"
if curl -s "http://127.0.0.1:${OLLAMA_PORT}/api/tags" >/dev/null 2>&1; then
  log "ollama server already running on :${OLLAMA_PORT}, skipping"
else
  OLLAMA_HOST="0.0.0.0:${OLLAMA_PORT}" OLLAMA_MODELS="${OLLAMA_MODELS:-}" \
    setsid nohup ollama serve >"$LOG_DIR/ollama_serve.log" 2>&1 < /dev/null &
  log "ollama serve launched (pid $!), waiting for it to come up..."
  up=0
  for _ in $(seq 1 30); do
    if curl -s "http://127.0.0.1:${OLLAMA_PORT}/api/tags" >/dev/null 2>&1; then
      up=1
      break
    fi
    sleep 2
  done
  if [ "$up" -eq 1 ]; then
    log "ollama server is up"
  else
    log "ERROR: ollama server did not come up within 60s -- see $LOG_DIR/ollama_serve.log" >&2
    exit 1
  fi
fi

log "[5/6] HuatuoGPT model"
if ollama list 2>/dev/null | grep -qF "$MODEL_MATCH"; then
  log "model already present in \$OLLAMA_MODELS, skipping pull (this is the time save)"
else
  log "pulling $MODEL_TAG (~5.7GB) -- one-time cost if OLLAMA_MODELS points at Drive"
  ollama pull "$MODEL_TAG" 2>&1 | tee "$LOG_DIR/ollama_pull.log"
fi

log "[6/6] cloudflared tunnel"
if ! command -v cloudflared >/dev/null 2>&1; then
  curl -fsSL -o /usr/local/bin/cloudflared \
    https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
  chmod +x /usr/local/bin/cloudflared
  log "cloudflared installed"
else
  log "cloudflared already installed, skipping"
fi

pkill -f "cloudflared tunnel --url http://127.0.0.1:${OLLAMA_PORT}" >/dev/null 2>&1 || true
sleep 1
rm -f "$LOG_DIR/cloudflared.log"
setsid nohup cloudflared tunnel --url "http://127.0.0.1:${OLLAMA_PORT}" \
  >"$LOG_DIR/cloudflared.log" 2>&1 < /dev/null &
log "cloudflared launched (pid $!), waiting for tunnel URL..."

URL=""
for _ in $(seq 1 30); do
  URL=$(grep -oE "https://[a-zA-Z0-9-]+\.trycloudflare\.com" "$LOG_DIR/cloudflared.log" 2>/dev/null | head -1)
  [ -n "$URL" ] && break
  sleep 2
done

echo ""
echo "============================================================"
if [ -n "$URL" ]; then
  echo " TUNNEL URL:  $URL"
  echo ""
  echo " On the local machine, run:"
  echo "   scripts/reconnect_gpu_backend.sh $URL"
else
  echo " ERROR: could not read a tunnel URL from $LOG_DIR/cloudflared.log"
  echo " Check that file directly in a cell: !cat $LOG_DIR/cloudflared.log"
fi
echo "============================================================"
