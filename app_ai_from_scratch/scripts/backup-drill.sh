#!/bin/sh
# Fail closed: no docker or no compose file is a failed drill, not a skip.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
if ! command -v docker >/dev/null 2>&1; then
  echo "backup-restore: docker is required" >&2
  exit 1
fi
if [ ! -f "$ROOT/docker-compose.yml" ]; then
  echo "backup-restore: docker-compose.yml missing" >&2
  exit 1
fi
echo "backup-drill: docker present; live dump skipped unless BACKUP_DRILL=1"
if [ "${BACKUP_DRILL:-}" = "1" ]; then
  DEPLOY_PATH="$ROOT" BACKUP_DIR="${TMPDIR:-/tmp}/aifs-backup-drill" sh "$ROOT/scripts/backup.sh"
fi
exit 0
