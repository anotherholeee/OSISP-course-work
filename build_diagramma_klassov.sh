#!/usr/bin/env bash
# Сборка крупного PNG диаграммы классов
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v plantuml >/dev/null; then
  echo "Установите PlantUML: sudo dnf install plantuml" >&2
  exit 1
fi
plantuml -tpng -charset UTF-8 diagramma_klassov_korzina.puml
# Дополнительно удвоенный масштаб (если нужен ещё крупнее):
# plantuml -tpng -scale 2.5 diagramma_klassov_korzina.puml -o .
ls -la diagramma_klassov_korzina.png 2>/dev/null || ls -la diagramma_klassov_korzina/*.png 2>/dev/null
