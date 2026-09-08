#!/bin/sh
# Dump curso, payments, messages. Host-side. Fail closed.
set -eu
DEPLOY_PATH="${DEPLOY_PATH:-.}"
OUT="${BACKUP_DIR:-$DEPLOY_PATH/backups}"
mkdir -p "$OUT"
stamp=$(date -u +%Y%m%dT%H%M%SZ)

dump() {
  svc=$1
  db=$2
  file="$OUT/${svc}-${stamp}.dump"
  docker compose -f "$DEPLOY_PATH/docker-compose.yml" exec -T "$svc" pg_dump -Fc -U "$db" "$db" > "$file"
  echo "$file"
}

dump db curso
dump payments-db payments
dump messages-db messages
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/last-ok"
echo "backup ok $stamp"
