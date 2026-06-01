#!/usr/bin/env python3
"""Generate functional structure diagram (text + optional SVG/PNG)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT_TXT = ROOT / "risunok_funkcionalnaya_struktura_korzina.txt"
OUT_SVG = ROOT / "risunok_funkcionalnaya_struktura_korzina.svg"
OUT_PNG = ROOT / "risunok_funkcionalnaya_struktura_korzina.png"

C_SCEN = "#fff3e0"
C_UTIL = "#e8f5e9"
C_HOOK = "#1565c0"
C_UTIL_MOD = "#2e7d32"
C_MK = "#6d4c41"


TEXT_DIAGRAM = """\
Связи «системная часть → прикладные сценарии»:

  trash_hook.c  ──►  rm + LD_PRELOAD     (библиотека подключается при удалении)
  trash_hook.c  ──►  demo-cycle.sh       (в скрипте: rm с LD_PRELOAD)

  trash_util.c  ──►  trash-util CLI/меню  (утилита собрана из trash_util.c)
  trash_util.c  ──►  demo-cycle.sh        (в скрипте вызывается trash-util list)

  Makefile      ──►  demo-cycle.sh       (сборка перед демо: make)

  Пользователь  ──►  setup-test-area.sh  (ручной запуск подготовки тестов)

Сценарии → внешние утилиты: demo → make, gcc, rm; setup → bash; rm-сценарий → rm.
"""


def build_text_diagram() -> str:
    return TEXT_DIAGRAM


def ortho_path(points: list[tuple[int, int]]) -> str:
    if not points:
        return ""
    parts = [f"M {points[0][0]} {points[0][1]}"]
    for x, y in points[1:]:
        parts.append(f"L {x} {y}")
    return " ".join(parts)


def build_svg() -> str:
    w, h = 1620, 1320
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        "<defs>",
        '<marker id="ah" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto">',
        f'<path d="M0,0 L9,4 L0,8 Z" fill="{C_HOOK}"/>',
        "</marker>",
        '<marker id="au" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto">',
        f'<path d="M0,0 L9,4 L0,8 Z" fill="{C_UTIL_MOD}"/>',
        "</marker>",
        '<marker id="am" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto">',
        f'<path d="M0,0 L9,4 L0,8 Z" fill="{C_MK}"/>',
        "</marker>",
        '<marker id="ag" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto">',
        '<path d="M0,0 L9,4 L0,8 Z" fill="#444"/>',
        "</marker>",
        "</defs>",
        '<text x="810" y="42" text-anchor="middle" font-size="24" font-weight="bold" '
        'font-family="DejaVu Sans, Liberation Sans, Arial">Функциональная структура программы</text>',
        '<text x="810" y="72" text-anchor="middle" font-size="15" font-family="DejaVu Sans, Arial">'
        "«Корзина» для программ, использующих системный вызов unlink()</text>",
    ]

    def rect(x, y, rw, rh, fill, label_lines, stroke="#333"):
        parts.append(
            f'<rect x="{x}" y="{y}" width="{rw}" height="{rh}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="2" rx="4"/>'
        )
        for i, ln in enumerate(label_lines):
            parts.append(
                f'<text x="{x + rw/2}" y="{y + 28 + i*20}" text-anchor="middle" '
                f'font-size="13" font-family="DejaVu Sans, Arial">{ln}</text>'
            )

    def conn(points, color="#444", marker="ag", label=None, lx=0, ly=0):
        d = ortho_path(points)
        parts.append(
            f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2.2" '
            f'marker-end="url(#{marker})"/>'
        )
        if label:
            tw = len(label) * 6.5 + 14
            parts.append(
                f'<rect x="{lx - tw/2}" y="{ly - 15}" width="{tw}" height="18" '
                f'fill="white" stroke="#ddd" rx="2"/>'
            )
            parts.append(
                f'<text x="{lx}" y="{ly}" text-anchor="middle" font-size="11" '
                f'font-weight="bold" font-family="DejaVu Sans, Arial" fill="{color}">{label}</text>'
            )

    # --- Пользовательский уровень ---
    parts.append('<rect x="60" y="95" width="1060" height="118" fill="#e8f4fc" stroke="#333" stroke-width="2"/>')
    parts.append('<text x="590" y="118" text-anchor="middle" font-size="17" font-weight="bold">Пользовательский уровень</text>')
    rect(90, 130, 170, 70, "#fff", ["Пользователь"])
    rect(300, 130, 260, 70, "#fff", ["Прикладные программы", "(rm, утилиты)"])
    rect(600, 130, 220, 70, "#fff", ["trash-util", "(управление)"])
    rect(870, 130, 230, 70, "#fff", ["LD_PRELOAD=", "libtrashhook.so"])
    conn([(260, 165), (300, 165)])
    conn([(560, 165), (600, 165)], label="при необходимости", lx=555, ly=158)
    conn([(820, 165), (870, 165)])

    # --- Системная часть (сначала фон, потом модули) ---
    parts.append('<rect x="60" y="240" width="1060" height="500" fill="#f5f5f5" stroke="#333" stroke-width="3"/>')
    parts.append(
        '<text x="590" y="268" text-anchor="middle" font-size="17" font-weight="bold">'
        "Системная часть программы (ядро на языке C)</text>"
    )
    hook_x, hook_y, hook_w, hook_h = 90, 285, 340, 185
    util_x, util_y = 470, 285
    util_w, util_h = 340, 185
    rect(hook_x, hook_y, hook_w, hook_h, "#fff", [
        "trash_hook.c → libtrashhook.so",
        "перехват unlink(), unlinkat(), remove()",
        "пути, перенос в корзину, dlsym",
    ])
    rect(util_x, util_y, util_w, util_h, "#fff", [
        "trash_util.c → trash-util",
        "list, restore, purge, info, menu",
        "восстановление, очистка корзины",
    ])
    common_y = 495
    rect(200, common_y, 520, 115, "#e8f5e9", [
        "trash_common.c / trash_common.h",
        "Trash/{files,info}, .trashinfo, ID",
    ], stroke="#2e7d32")
    hook_cx = hook_x + hook_w // 2
    util_cx = util_x + util_w // 2
    conn([(hook_cx, hook_y + hook_h), (hook_cx, common_y)], label="Использует", lx=hook_cx + 42, ly=488)
    conn([(util_cx, util_y + util_h), (util_cx, common_y)], label="Использует", lx=util_cx + 42, ly=488)
    mk_y = 635
    rect(90, mk_y, 980, 85, "#fafafa", [
        "Makefile — libtrashhook.so, trash-util, trash_common.o",
    ])
    mk_cx = 580
    mk_bot = mk_y + 85
    hook_bot = hook_y + hook_h
    util_bot = util_y + util_h

    # --- Прикладные сценарии ---
    scen_y = 820
    parts.append(f'<rect x="60" y="{scen_y}" width="1060" height="155" fill="{C_SCEN}" stroke="#333" stroke-width="3"/>')
    parts.append(
        f'<text x="590" y="{scen_y + 28}" text-anchor="middle" font-size="17" font-weight="bold">'
        "Прикладные сценарии</text>"
    )
    # (x, y, w, h, lines) — top = scen_top
    scen_top = scen_y + 50
    scenarios = [
        (100, scen_top, 220, 88, ["demo-cycle.sh", "сборка, rm, list"]),
        (350, scen_top, 220, 88, ["setup-test-area.sh", "подготовка ~/test_area"]),
        (600, scen_top, 220, 88, ["trash-util (CLI / меню)", "list, restore, purge"]),
        (850, scen_top, 220, 88, ["rm + LD_PRELOAD", "удаление в корзину"]),
    ]
    scen_tops = []
    for sx, sy, sw, sh, lines in scenarios:
        rect(sx, sy, sw, sh, "#fff", lines)
        scen_tops.append((sx + sw // 2, sy))

    demo_t, setup_t, cli_t, rm_t = scen_tops

    # --- Внешние утилиты ---
    util_panel_y = 1010
    parts.append(f'<rect x="60" y="{util_panel_y}" width="1060" height="145" fill="{C_UTIL}" stroke="#333" stroke-width="3"/>')
    parts.append(
        f'<text x="590" y="{util_panel_y + 28}" text-anchor="middle" font-size="17" font-weight="bold">'
        "Внешние утилиты</text>"
    )
    rect(130, 1055, 100, 52, "#fff", ["make"])
    rect(130, 1115, 100, 52, "#fff", ["gcc"])
    rect(250, 1055, 100, 52, "#fff", ["rm"])
    rect(410, 1055, 100, 52, "#fff", ["bash"])
    rect(910, 1055, 100, 52, "#fff", ["rm"])

    # --- Внешняя среда ---
    ext_x = 1160
    parts.append(f'<rect x="{ext_x}" y="240" width="380" height="915" fill="#fff8e6" stroke="#333" stroke-width="3"/>')
    parts.append(f'<text x="{ext_x + 190}" y="268" text-anchor="middle" font-size="17" font-weight="bold">Внешняя среда и ОС</text>')
    rect(ext_x + 25, 295, 330, 100, "#fff", ["Системные вызовы и libc", "unlink, unlinkat, rename, ..."])
    rect(ext_x + 25, 415, 330, 90, "#fff", ["libdl — dlsym(RTLD_NEXT, …)"])
    rect(ext_x + 25, 525, 330, 120, "#fff", ["Файловая система", "Trash/files, Trash/info"])
    rect(ext_x + 25, 665, 330, 85, "#fff", ["HOME, LD_PRELOAD,", "TRASH_HOOK_DISABLE"])
    rect(ext_x + 25, 770, 330, 55, "#fff", ["$HOME — рабочие файлы"])
    bus = ext_x - 15

    # --- Легенда: стрелки ядро → сценарии ---
    parts.append('<rect x="60" y="728" width="1060" height="44" fill="#fafafa" stroke="#bbb" stroke-width="1" rx="4"/>')
    parts.append(
        '<text x="80" y="748" font-size="12" font-weight="bold" font-family="DejaVu Sans, Arial">'
        "Цвет стрелок к сценариям:</text>"
    )
    parts.append(f'<line x1="230" y1="762" x2="260" y2="762" stroke="{C_HOOK}" stroke-width="3"/>')
    parts.append(f'<text x="268" y="766" font-size="11" font-family="DejaVu Sans, Arial">trash_hook.c</text>')
    parts.append(f'<line x1="400" y1="762" x2="430" y2="762" stroke="{C_UTIL_MOD}" stroke-width="3"/>')
    parts.append(f'<text x="438" y="766" font-size="11" font-family="DejaVu Sans, Arial">trash_util.c</text>')
    parts.append(f'<line x1="560" y1="762" x2="590" y2="762" stroke="{C_MK}" stroke-width="3"/>')
    parts.append(f'<text x="598" y="766" font-size="11" font-family="DejaVu Sans, Arial">Makefile</text>')
    parts.append(
        '<text x="700" y="766" font-size="11" font-family="DejaVu Sans, Arial" fill="#555">'
        "на стрелке — что именно делает модуль в этом сценарии</text>"
    )

    # Пользователь → ядро
    conn([(710, 200), (710, 222), (640, 222), (640, 285)], label="запуск", lx=668, ly=214)
    conn([(985, 200), (985, 218), (260, 218), (260, 285)], label="подмена", lx=540, ly=208)

    # Пользователь → setup-test-area (отдельно, не из ядра)
    conn(
        [(175, 200), (175, 760), (460, 760), (460, setup_t[1])],
        color="#6a1b9a",
        marker="ag",
        label="запуск вручную",
        lx=240,
        ly=782,
    )

    # Горизонтали между ядром (низ ~720) и сценариями (верх ~870)
    conn(
        [(hook_cx + 100, hook_bot), (hook_cx + 100, 812), (rm_t[0], 812), (rm_t[0], rm_t[1])],
        color=C_HOOK,
        marker="ah",
        label="libtrashhook.so",
        lx=750,
        ly=802,
    )
    conn(
        [(hook_cx - 80, hook_bot), (hook_cx - 80, 798), (demo_t[0], 798), (demo_t[0], demo_t[1])],
        color=C_HOOK,
        marker="ah",
        label="rm в demo",
        lx=210,
        ly=788,
    )
    conn(
        [(util_cx, util_bot), (util_cx, 822), (cli_t[0], 822), (cli_t[0], cli_t[1])],
        color=C_UTIL_MOD,
        marker="au",
        label="реализует",
        lx=700,
        ly=812,
    )
    conn(
        [(util_cx - 90, util_bot), (util_cx - 90, 806), (demo_t[0] + 55, 806), (demo_t[0] + 55, demo_t[1])],
        color=C_UTIL_MOD,
        marker="au",
        label="list в demo",
        lx=400,
        ly=796,
    )
    conn(
        [(mk_cx, mk_bot), (mk_cx, 790), (demo_t[0] - 35, 790), (demo_t[0] - 35, demo_t[1])],
        color=C_MK,
        marker="am",
        label="make в demo",
        lx=500,
        ly=780,
    )

    # Makefile → gcc (сборка)
    conn(
        [(mk_cx - 100, mk_bot), (mk_cx - 100, 1090), (180, 1090), (180, 1115)],
        color=C_MK,
        marker="am",
        label="сборка",
        lx=320,
        ly=1078,
    )

    # Сценарии → утилиты (серые, подписи)
    conn([(demo_t[0], scen_top + 88), (demo_t[0], 1040), (180, 1040), (180, 1055)], label="make", lx=195, ly=1032)
    conn([(demo_t[0] + 50, scen_top + 88), (demo_t[0] + 50, 1048), (300, 1048), (300, 1055)], label="rm", lx=310, ly=1040)
    conn([(setup_t[0], scen_top + 88), (setup_t[0], 1042), (460, 1042), (460, 1055)], label="bash", lx=475, ly=1034)
    conn([(rm_t[0], scen_top + 88), (rm_t[0], 1040), (960, 1040), (960, 1055)], label="rm", lx=975, ly=1032)

    # Ядро → ОС
    hook_r = hook_x + hook_w
    util_r = util_x + util_w
    conn([(hook_r, 340), (bus, 340), (ext_x + 25, 340)], label="вызовы", lx=bus - 50, ly=332)
    conn([(hook_r, 390), (bus + 12, 390), (bus + 12, 460), (ext_x + 25, 460)], label="dlsym", lx=bus - 38, ly=418)
    conn([(hook_r, 440), (bus + 24, 440), (bus + 24, 585), (ext_x + 25, 585)], label="запись", lx=bus - 28, ly=510)
    conn([(util_r, 400), (bus + 36, 400), (bus + 36, 585), (ext_x + 25, 600)], label="чтение", lx=bus - 16, ly=495)

    parts.append("</svg>")
    return "\n".join(parts)


def write_png() -> None:
    import shutil
    import subprocess

    for cmd in (
        ["magick", "-background", "white", "-density", "200", str(OUT_SVG), str(OUT_PNG)],
        ["convert", "-background", "white", "-density", "200", str(OUT_SVG), str(OUT_PNG)],
        ["rsvg-convert", "-b", "white", "-d", "200", "-p", "200", str(OUT_SVG), "-o", str(OUT_PNG)],
    ):
        if shutil.which(cmd[0]):
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"Wrote {OUT_PNG}")
            return
    print("PNG skipped: install ImageMagick, rsvg-convert, or similar")


def main() -> None:
    OUT_TXT.write_text(build_text_diagram(), encoding="utf-8")
    print(f"Wrote {OUT_TXT}")
    OUT_SVG.write_text(build_svg(), encoding="utf-8")
    print(f"Wrote {OUT_SVG}")
    write_png()


if __name__ == "__main__":
    main()
