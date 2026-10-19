#!/usr/bin/env bash
# Daily job: snapshot pricing pages, diff, rebuild site, check links.
set -euo pipefail
cd "$(dirname "$0")"
PY=${PY:-$( [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3 )}
case "${1:-all}" in
  scrape) $PY scripts/snapshot.py ;;
  build)  $PY scripts/build.py && $PY scripts/check_links.py ;;
  serve)  $PY scripts/build.py && $PY -m http.server "${PORT:-8787}" -d dist ;;
  all)    $PY scripts/snapshot.py && $PY scripts/build.py && $PY scripts/check_links.py ;;
  *) echo "usage: ./run.sh [all|scrape|build|serve]"; exit 1 ;;
esac
