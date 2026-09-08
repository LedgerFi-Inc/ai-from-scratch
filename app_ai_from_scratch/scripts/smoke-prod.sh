#!/bin/sh
# Read-only production smoke. Non-zero on any failure. Never skip.
set -eu
origin=${1:-${READINESS_ORIGIN:-}}
if [ -z "$origin" ]; then
  echo "usage: smoke-prod.sh <https://origin>" >&2
  exit 1
fi
origin=${origin%/}
fail=0
check() {
  name=$1
  shift
  if "$@"; then
    echo "ok  $name"
  else
    echo "FAIL $name" >&2
    fail=1
  fi
}
code() {
  curl -sS -o /dev/null -w '%{http_code}' --max-time 20 "$1"
}
check "https home 200" sh -c "test \"\$(curl -sS -o /dev/null -w '%{http_code}' --max-time 20 '$origin/')\" = 200"
check "api health" sh -c "test \"\$(curl -sS -o /dev/null -w '%{http_code}' --max-time 20 '$origin/api/health')\" = 200"
check "unsigned entitlements denied" sh -c "c=\$(curl -sS -o /dev/null -w '%{http_code}' --max-time 20 -X POST '$origin/api/internal/entitlements'); test \"\$c\" = 401 -o \"\$c\" = 403 -o \"\$c\" = 404"
check "terms 200" sh -c "test \"\$(curl -sS -o /dev/null -w '%{http_code}' --max-time 20 '$origin/terminos')\" = 200"
if [ "$fail" -ne 0 ]; then
  echo "smoke-prod failed against $origin" >&2
  exit 1
fi
echo "smoke-prod ok $origin"
