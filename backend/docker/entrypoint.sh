#!/bin/sh
set -e

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
WORKERS="${UVICORN_WORKERS:-1}"

run_api() {
  if [ "$WORKERS" -gt 1 ] 2>/dev/null; then
    exec uvicorn app.main:app \
      --host "$HOST" \
      --port "$PORT" \
      --workers "$WORKERS" \
      --proxy-headers \
      --forwarded-allow-ips='*'
  fi

  exec uvicorn app.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --proxy-headers \
    --forwarded-allow-ips='*'
}

case "${1:-api}" in
  api)
    run_api
    ;;
  migrate)
    exec alembic upgrade head
    ;;
  *)
    exec "$@"
    ;;
esac
