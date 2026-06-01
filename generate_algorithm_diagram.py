#!/usr/bin/env python3
"""Algorithm flowchart — clean orthogonal arrows + explanatory txt."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT_SVG = ROOT / "risunok_algoritm_korzina.svg"
OUT_TXT = ROOT / "risunok_algoritm_korzina.txt"

EXPLANATION_TXT = """
+==============================================================================+
|                    Схема алгоритма (приложение Б)                            |
|              Программа «Корзина» — libtrashhook.so + trash-util              |
+==============================================================================+

  Две подсистемы одного проекта:
    A) libtrashhook.so — перехват unlink() при LD_PRELOAD (помещение в корзину)
    B) trash-util      — просмотр, восстановление, очистка, статистика

  Общий модуль trash_common.c: пути ~/.local/share/Trash/{files,info},
  формат *.trashinfo, trash_ensure_layout() и др.


УСЛОВНЫЕ ОБОЗНАЧЕНИЯ
  ( )  — начало / конец
  [ ]  — действие (прямоугольник на PNG/SVG)
  <>   — условие (ромб)
  -->  — переход
  [FB] — call_real_unlink(): обычное удаление без корзины (только часть A)
  [ER] — return -1: ошибка перехвата / записи метаданных (только часть A)
  [EXIT] — return из main() / выход из цикла меню


==============================================================================
  ЧАСТЬ A. libtrashhook.so — перехват при удалении (схема на рисунке)
==============================================================================

( Начало A )
    Вызов unlink(), unlinkat() или remove() из прикладной программы (rm и др.)
    при подключённой через LD_PRELOAD библиотеке libtrashhook.so.

--> [ pthread_once: init_real_symbols() ]
    Один раз находим «настоящие» функции unlink/unlinkat в libc через dlsym().

--> <> Обход перехвата?
    Проверка: уже внутри перехвата (in_hook) или задано TRASH_HOOK_DISABLE.
    Да  --> [FB]  (не дублировать перехват)
    Нет --> дальше

--> [ resolve_absolute_path() ]
    Строим абсолютный путь к файлу (getcwd, /proc/self/fd/N).

--> <> Путь получен?
    Нет --> [FB]
    Да  --> дальше

--> [ lstat(abs_path) ]
    Читаем метаданные объекта перед удалением.

--> <> lstat успешен?
    Нет --> [ER]  (файл недоступен)
    Да  --> дальше

--> <> Это каталог?
    Да  --> [ER]  (корзина только для обычных файлов)
    Нет --> дальше

--> <> Файл в $HOME?
    Корзина действует только для файлов в домашнем каталоге пользователя.
    Нет --> [FB]  (вне $HOME — удалить как обычно)
    Да  --> дальше

--> [ trash_ensure_layout(); trash_paths() ]
    Создаём ~/.local/share/Trash/files и .../info при необходимости.

--> [ generate_id; заполнить trash_entry ]
    Уникальный ID, исходный путь, права, владелец, время удаления.

--> [ rename() → Trash/files ]
    Перенос файла в каталог корзины одной файловой операцией.

--> <> rename успешен?
    Да  --> (переход к «Файл перенесён?» / trash_write_info)
    Нет --> дальше (возможно другой раздел диска)

--> <> errno == EXDEV?
    Разные файловые системы: rename невозможен.
    Нет --> [FB]
    Да  --> [ safe_copy_file() + call_real_unlink() ]
            Копирование в корзину и удаление оригинала.

--> <> Файл перенесён?
    Нет --> [FB]
    Да  --> дальше

--> [ trash_write_info() ]
    Запись *.trashinfo с путём восстановления и атрибутами.

--> <> Запись успешна?
    Нет --> [ER]  (откат: удалить копию из files)
    Да  --> [ return 0 ]

--> ( Конец A )
    Файл в корзине; для приложения удаление выглядит успешным.


БОКОВЫЕ ВЫХОДЫ ЧАСТИ A (на рисунке — справа и слева внизу)
==============================================================================

[FB] call_real_unlink() (без корзины)
    Когда перехват не применяется или перенос в корзину невозможен.
    Вызывается настоящий unlink() из libc — файл удаляется окончательно.

[ER] return -1 (ошибка)
    Критическая ошибка: lstat, каталог, сбой записи метаданных.
    Возвращается код ошибки; errno сохраняется.


ТАБЛИЦА ВЕТВЛЕНИЙ — ЧАСТЬ A
==============================================================================
  Узел                  | Да / Нет | Куда
  ----------------------|----------|----------------------------------
  Обход перехвата?      | Да       | [FB]
  Путь получен?         | Нет      | [FB]
  lstat успешен?        | Нет      | [ER]
  Это каталог?          | Да       | [ER]
  Файл в $HOME?         | Нет      | [FB]
  rename успешен?       | Да       | к записи .trashinfo
  errno == EXDEV?       | Нет      | [FB]
  Файл перенесён?       | Нет      | [FB]
  Запись успешна?       | Нет      | [ER]


==============================================================================
  ЧАСТЬ B. trash-util — управление корзиной (trash_util.c)
==============================================================================

( Начало B )
    Запуск: ./trash-util  или  ./trash-util <команда> [аргументы]

--> <> argc >= 2?
    Нет  --> [ run_menu() ]  (интерактивное меню — см. ниже)
    Да   --> дальше

--> <> argv[1] — какая команда?
    list    --> [ list_entries() ]     --> [EXIT]
    restore --> <> argc >= 3 (ID задан)?
                Нет  --> сообщение об ошибке, return 1
                Да   --> [ restore_entry(argv[2]) ] --> [EXIT]
    purge   --> [ purge_entries() ]    --> [EXIT]
    info    --> [ info_entries() ]     --> [EXIT]
    menu    --> [ run_menu() ]         --> [EXIT]
    иное    --> [ print_help() ], return 1


--- B.1. list_entries() — список удалённых файлов ---

--> [ trash_paths() ]
    Пути ~/.local/share/Trash/files и .../info.

--> [ opendir(info_dir) ]

--> <> Каталог info открыт?
    Нет, errno == ENOENT --> «Корзина пуста.», return 0
    Нет, иная ошибка     --> perror, return 1
    Да                   --> дальше

--> [ Цикл readdir: только *.trashinfo ]
    Для каждого файла: trash_parse_info() → вывод
    «ID | Дата удаления | Исходный путь».

--> <> Найдено записей count > 0?
    Нет --> «Корзина пуста.»
    Да  --> (таблица уже выведена)

--> [ return 0 ]


--- B.2. restore_entry(id) — восстановление по ID ---

--> [ trash_paths(); пути files/<id> и info/<id>.trashinfo ]

--> <> Файл в files существует (access)?
    Нет --> stderr «не найден», return 1
    Да  --> дальше

--> [ trash_parse_info() → entry.original_path, mode, uid, gid, times ]

--> [ ensure_parent_dirs(исходный путь) ]
    Создаём недостающие каталоги в пути назначения.

--> <> Исходный путь уже занят (access F_OK)?
    Да  --> [ trash_resolve_unique_path() ]
            rename(files/id → уникальное имя)
            chmod, chown, utimensat по метаданным из .trashinfo
    Нет --> rename(files/id → original_path)
            chmod, chown, utimensat

--> [ unlink(info_path) ]
    Удаляем метаданные из корзины (ошибка — perror, но return 0).

--> [ return 0 ]


--- B.3. purge_entries() — полная очистка корзины ---

--> [ trash_paths() ]

--> [ nftw(files_dir) + nftw(info_dir) ]
    Рекурсивное удаление содержимого (FTW_DEPTH | FTW_PHYS).

--> <> nftw успешен (или ENOENT)?
    Нет --> perror, return 1
    Да  --> дальше

--> [ trash_ensure_layout() ]
    Воссоздаём пустые каталоги files и info.

--> «Корзина очищена.», [ return 0 ]


--- B.4. info_entries() — статистика ---

--> [ trash_paths() ]

--> [ trash_dir_size_bytes(files_dir) ]
--> [ Подсчёт *.trashinfo в info_dir ]

--> Вывод: «Файлов в корзине: N», «Занято места: … байт»
--> [ return 0 ]


--- B.5. run_menu() — интерактивное меню (цикл for(;;)) ---

( Вход в меню )
    Печать:
      === trash-util menu ===
      1) Показать содержимое корзины (list)
      2) Восстановить файл по ID (restore)
      3) Показать статистику (info)
      4) Очистить корзину (purge)
      0) Выход

--> [ fgets(выбор) ]

--> <> EOF на вводе?
    Да  --> «Завершение (EOF).», [EXIT] return 0
    Нет --> дальше

--> <> Первый символ выбора?
    '1' --> [ list_entries() ]        --> снова начало цикла меню
    '2' --> [ fgets(ID) ]
            <> ID пустой?
              Да  --> «отменена», цикл
              Нет --> [ restore_entry(id) ], цикл
    '3' --> [ info_entries() ], цикл
    '4' --> [ fgets(confirm): «yes» / иное ]
            Да (yes)  --> [ purge_entries() ]
            Нет       --> «Очистка отменена.»
            цикл
    '0' --> «Выход из меню.», [EXIT] return 0
    иное  --> «Неизвестный пункт меню.», цикл

( Конец B )
    Код возврата main: 0 при успехе команды/меню, 1 при ошибке или help.


ТАБЛИЦА ВЕТВЛЕНИЙ — ЧАСТЬ B (кратко)
==============================================================================
  Узел / команда           | Условие        | Действие
  -------------------------|----------------|--------------------------------
  argc >= 2?               | Нет            | run_menu()
  argv[1]                  | list           | list_entries
  argv[1]                  | restore        | нужен ID → restore_entry
  argv[1]                  | purge          | purge_entries
  argv[1]                  | info           | info_entries
  argv[1]                  | menu           | run_menu()
  argv[1]                  | иное           | print_help, exit 1
  opendir info (list)      | ENOENT         | «пуста»
  restore: файл в files?   | Нет            | ошибка
  restore: путь занят?     | Да             | unique_path + rename
  restore: путь занят?     | Нет            | rename в original_path
  purge: nftw              | ошибка         | return 1
  menu: выбор              | 1–4, 0         | см. run_menu выше
  menu: purge              | confirm == yes | purge_entries
  menu: purge              | иначе          | отмена


СВЯЗЬ ЧАСТЕЙ A И B
==============================================================================
  A помещает файлы в Trash/files и пишет Trash/info/*.trashinfo.
  B читает те же каталоги: list/info перечисляют записи, restore возвращает
  файл на исходный путь, purge удаляет всё содержимое корзины.
  При restore перехват A не задействован (прямой rename/unlink в утилите).
"""


def build_svg() -> str:
    CX = 480
    BX = 270
    DX, DY = 88, 64
    STEP = 90

    nodes = [
        ("start", "Начало"),
        ("proc", "pthread_once:\ninit_real_symbols()"),
        ("dec", "Обход\nперехвата?"),
        ("proc", "resolve_absolute_path()"),
        ("dec", "Путь\nполучен?"),
        ("proc", "lstat(abs_path)"),
        ("dec", "lstat\nуспешен?"),
        ("dec", "Это\nкаталог?"),
        ("dec", "Файл в\n$HOME?"),
        ("proc", "trash_ensure_layout()\ntrash_paths()"),
        ("proc", "generate_id,\nзаполнить entry"),
        ("proc", "rename() → Trash/files"),
        ("dec", "rename\nуспешен?"),
        ("dec", "errno ==\nEXDEV?"),
        ("proc", "safe_copy_file()\n+ real_unlink()"),
        ("dec", "Файл\nперенесён?"),
        ("proc", "trash_write_info()"),
        ("dec", "Запись\nуспешна?"),
        ("proc", "return 0"),
        ("end", "Конец"),
    ]

    n = len(nodes)
    top = 70
    H = top + 40 + n * STEP + 200
    W = 900

    ys = [top + 40 + i * STEP for i in range(n)]

    # Side exit boxes — fixed at bottom, arrows merge into them
    FB_X, ER_X = 720, 160
    FB_Y = H - 175
    ER_Y = H - 175
    END_Y = H - 85

    p = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}">',
        "<defs>",
        "<marker id='ar' viewBox='0 0 10 10' refX='9' refY='5' markerWidth='7' "
        "markerHeight='7' orient='auto-start-reverse'>",
        "<path d='M 0 0 L 10 5 L 0 10 z' fill='#333'/></marker>",
        "</defs>",
        f"<text x='{W/2}' y='30' text-anchor='middle' font-size='17' font-weight='bold' "
        "font-family='DejaVu Sans, Arial'>Схема алгоритма</text>",
        f"<text x='{W/2}' y='50' text-anchor='middle' font-size='11' "
        "font-family='DejaVu Sans, Arial'>"
        "Часть A: libtrashhook.so (перехват unlink). Часть B: trash-util — в .txt</text>",
    ]

    def bh(kind):
        return DY if kind == "dec" else (36 if kind in ("start", "end") else 44)

    def bot(i):
        return ys[i] + bh(nodes[i][0]) / 2

    def top(i):
        return ys[i] - bh(nodes[i][0]) / 2

    def left_edge(i):
        return CX - (DX if nodes[i][0] == "dec" else BX / 2)

    def right_edge(i):
        return CX + (DX if nodes[i][0] == "dec" else BX / 2)

    def draw(kind, i, text):
        cy = ys[i]
        if kind in ("start", "end"):
            p.append(
                f"<ellipse cx='{CX}' cy='{cy}' rx='58' ry='18' fill='#fff' "
                f"stroke='#333' stroke-width='2'/>"
            )
        elif kind == "dec":
            y0 = cy - DY / 2
            pts = f"{CX},{y0} {CX+DX},{cy} {CX},{y0+DY} {CX-DX},{cy}"
            p.append(f"<polygon points='{pts}' fill='#fff' stroke='#333' stroke-width='2'/>")
        else:
            bh2 = 44
            p.append(
                f"<rect x='{CX-BX/2}' y='{cy-bh2/2}' width='{BX}' height='{bh2}' "
                f"fill='#fff' stroke='#333' stroke-width='2' rx='3'/>"
            )
        for j, ln in enumerate(text.split("\n")):
            p.append(
                f"<text x='{CX}' y='{cy - 8 + j*14}' text-anchor='middle' font-size='10' "
                f"font-family='DejaVu Sans, Arial'>{ln}</text>"
            )

    def path(pts, arrow=True):
        d = f"M {pts[0][0]:.1f},{pts[0][1]:.1f}"
        for x, y in pts[1:]:
            d += f" L {x:.1f},{y:.1f}"
        mk = " marker-end='url(#ar)'" if arrow else ""
        p.append(f"<path d=\"{d}\" fill='none' stroke='#333' stroke-width='1.6'{mk}/>")

    def down(i, j):
        path([(CX, bot(i) + 2), (CX, top(j) - 2)])

    def lbl(x, y, t):
        p.append(
            f"<text x='{x}' y='{y}' font-size='9' font-weight='bold' "
            f"font-family='DejaVu Sans, Arial'>{t}</text>"
        )

    def to_fb(i, label="Нет", exit_left=False):
        cy = ys[i]
        x0 = left_edge(i) if exit_left else right_edge(i)
        lx = x0 - 26 if exit_left else x0 + 8
        lbl(lx, cy - 4, label)
        path([(x0, cy), (FB_X, cy), (FB_X, FB_Y)])

    def to_er(i, label="Нет", exit_right=False):
        cy = ys[i]
        x0 = right_edge(i) if exit_right else left_edge(i)
        bus = ER_X + 195
        lx = x0 + 8 if exit_right else x0 - 26
        lbl(lx, cy - 4, label)
        path([(x0, cy), (bus, cy), (bus, ER_Y)])

    for i, (k, t) in enumerate(nodes):
        draw(k, i, t)

    # Side boxes
    p.append(
        f"<rect x='{FB_X-100}' y='{FB_Y}' width='200' height='48' fill='#fff8e6' "
        f"stroke='#333' stroke-width='2' rx='4'/>"
    )
    p.append(
        f"<text x='{FB_X}' y='{FB_Y+20}' text-anchor='middle' font-size='10' "
        f"font-weight='bold' font-family='DejaVu Sans, Arial'>call_real_unlink()</text>"
    )
    p.append(
        f"<text x='{FB_X}' y='{FB_Y+34}' text-anchor='middle' font-size='9' "
        f"font-family='DejaVu Sans, Arial'>(без корзины)</text>"
    )
    p.append(
        f"<rect x='{ER_X}' y='{ER_Y}' width='195' height='48' fill='#ffebee' "
        f"stroke='#333' stroke-width='2' rx='4'/>"
    )
    p.append(
        f"<text x='{ER_X+97}' y='{ER_Y+28}' text-anchor='middle' font-size='10' "
        f"font-weight='bold' font-family='DejaVu Sans, Arial'>return -1 (ошибка)</text>"
    )

    # Main vertical chain
    chain = [
        (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9),
        (9, 10), (10, 11), (11, 12), (14, 15), (15, 16), (16, 17), (17, 18), (18, 19),
    ]
    for a, b in chain:
        down(a, b)

    # Branches
    to_fb(2, label="Да", exit_left=False)
    to_fb(4, label="Нет", exit_left=True)
    to_er(6, label="Нет", exit_right=False)
    to_er(7, label="Да", exit_right=True)
    to_fb(8, label="Нет", exit_left=True)

    # rename Да — обход вправо и вниз к trash_write_info (16)
    cy = ys[12]
    skip_x = CX + 95
    lbl(CX + DX + 5, cy - 4, "Да")
    path([(right_edge(12), cy), (skip_x, cy), (skip_x, top(16) - 2), (CX, top(16) - 2)])
    lbl(CX - DX - 22, cy - 4, "Нет")
    down(12, 13)

    to_fb(13, label="Нет", exit_left=True)
    down(13, 14)
    lbl(CX + DX + 5, ys[13] - 4, "Да")
    to_fb(15, label="Нет", exit_left=True)
    to_er(17, label="Нет", exit_right=False)

    # FB / ER → Конец
    path([(FB_X, FB_Y + 48), (FB_X, END_Y - 22), (CX + 55, END_Y - 22), (CX + 55, END_Y - 20)])
    path([(ER_X + 97, ER_Y + 48), (ER_X + 97, END_Y - 22), (CX - 55, END_Y - 22), (CX - 55, END_Y - 20)])

    p.append(
        f"<text x='{W/2}' y='{H-22}' text-anchor='middle' font-size='9' fill='#555' "
        f"font-family='DejaVu Sans, Arial'>"
        "Часть B (trash-util, меню, CLI): см. risunok_algoritm_korzina.txt</text>"
    )

    p.append("</svg>")
    return "\n".join(p)


def main():
    OUT_TXT.write_text(EXPLANATION_TXT.strip() + "\n", encoding="utf-8")
    OUT_SVG.write_text(build_svg(), encoding="utf-8")
    print(f"Wrote {OUT_SVG}")
    print(f"Wrote {OUT_TXT}")


if __name__ == "__main__":
    main()
