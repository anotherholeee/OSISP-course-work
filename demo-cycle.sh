#!/usr/bin/env bash
# Один прогон демо: сборка → тестовый файл в $HOME → rm с перехватом → list.
# Восстановление: скопируйте ID из вывода и выполните:
#   ./trash-util restore <ID>
# или запустите ./trash-util и пункты 1 и 2.

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
make -q 2>/dev/null || make
F="$HOME/.trash-demo-cycle.txt"
echo "тест цикла $(date -Is)" >"$F"
echo "Создан файл: $F"
LD_PRELOAD="$ROOT/libtrashhook.so" rm -f "$F"
echo "Удалён с LD_PRELOAD (должен оказаться в корзине)."
echo ""
exec ./trash-util list
