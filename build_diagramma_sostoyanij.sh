#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v plantuml >/dev/null; then
  echo "Установите PlantUML: sudo dnf install plantuml" >&2
  exit 1
fi
plantuml -tpng -tsvg -charset UTF-8 \
  diagramma_sostoyanij_korzina.puml \
  diagramma_sostoyanij_hook_korzina.puml
ls -la diagramma_sostoyanij_*.png diagramma_sostoyanij_*.svg 2>/dev/null || true
