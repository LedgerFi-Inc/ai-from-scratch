#!/bin/sh
# Restore a dump into a throwaway postgres container. Never the live DB.
set -eu
dump=${1:-}
if [ -z "$dump" ] || [ ! -f "$dump" ]; then
  echo "usage: restore.sh <dump>" >&2
  exit 1
fi
cid=$(docker run -d --rm -e POSTGRES_PASSWORD=restore -p 127.0.0.1::5432 postgres:17-alpine)
trap 'docker stop "$cid" >/dev/null' EXIT
# wait
i=0
while [ "$i" -lt 30 ]; do
  docker exec "$cid" pg_isready -U postgres && break
  i=$((i + 1))
  sleep 1
done
docker exec -i "$cid" pg_restore --no-owner -U postgres -d postgres < "$dump"
echo "restore ok"
