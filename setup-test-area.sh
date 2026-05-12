#!/usr/bin/env bash
# Создаёт ~/test_area с file_a.txt и file_b.txt для демонстрации (см. MENU_TEST_GUIDE.md).
# Запуск: из любого каталога:  /путь/к/kursach/setup-test-area.sh

set -euo pipefail
DIR="${HOME}/test_area"
mkdir -p "$DIR"
rm -f "$DIR/file_a.txt" "$DIR/file_b.txt" "$DIR/file_b.txt.1"

echo "alpha" >"$DIR/file_a.txt"
echo "beta"  >"$DIR/file_b.txt"

echo "Готово. Создано:"
ls -la "$DIR"
echo ""
echo "Дальше (из каталога с libtrashhook.so, например kursach):"
echo "  LD_PRELOAD=\"\$PWD/libtrashhook.so\" rm \"\$HOME/test_area/file_a.txt\""
echo "  LD_PRELOAD=\"\$PWD/libtrashhook.so\" rm \"\$HOME/test_area/file_b.txt\""
echo "  ./trash-util"
echo "В меню: 1 — список (2 записи), 2 — восстановить по ID из списка."
