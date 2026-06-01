#!/usr/bin/env python3
"""Context diagram — hook flows on upper corridor, util on lower; color-coded."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT_SVG = ROOT / "risunok_vzaimodejstvie_korzina.svg"

HOOK_COLOR = "#1565c0"
UTIL_COLOR = "#2e7d32"
USER_COLOR = "#6a1b9a"
EXT_COLOR = "#e65100"
SYS_COLOR = "#455a64"


def build_svg() -> str:
    W, H = 1720, 1220
    p = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        "<defs>",
        '<marker id="ah" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto">',
        f'<path d="M0,0 L9,4 L0,8 Z" fill="{HOOK_COLOR}"/>',
        "</marker>",
        '<marker id="au" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto">',
        f'<path d="M0,0 L9,4 L0,8 Z" fill="{UTIL_COLOR}"/>',
        "</marker>",
        '<marker id="ag" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto">',
        '<path d="M0,0 L9,4 L0,8 Z" fill="#333"/>',
        "</marker>",
        "</defs>",
        f'<text x="{W/2}" y="40" text-anchor="middle" font-size="22" font-weight="bold" '
        'font-family="DejaVu Sans, Arial">Схема взаимодействия с пользователем и внешней средой</text>',
        f'<text x="{W/2}" y="68" text-anchor="middle" font-size="14" font-family="DejaVu Sans, Arial">'
        "«Корзина» для программ, использующих системный вызов unlink()</text>",
    ]

    def grp(x, y, w, h, title, fill):
        p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="#333" stroke-width="2" rx="6"/>')
        p.append(f'<text x="{x+w/2}" y="{y+24}" text-anchor="middle" font-size="14" font-weight="bold" '
                 f'font-family="DejaVu Sans, Arial">{title}</text>')

    def box(x, y, w, h, lines):
        p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#fff" stroke="#333" stroke-width="1.8" rx="4"/>')
        for i, ln in enumerate(lines):
            p.append(f'<text x="{x+w/2}" y="{y+22+i*16}" text-anchor="middle" font-size="11" '
                     f'font-family="DejaVu Sans, Arial">{ln}</text>')

    def cyl(cx, cy, w, h, title, sub):
        x, y = cx - w / 2, cy - h / 2
        p.append(f'<ellipse cx="{cx}" cy="{y+9}" rx="{w/2-5}" ry="9" fill="#e3f2fd" stroke="#333" stroke-width="1.8"/>')
        p.append(f'<rect x="{x}" y="{y+9}" width="{w}" height="{h-18}" fill="#e3f2fd" stroke="#333" stroke-width="1.8"/>')
        p.append(f'<ellipse cx="{cx}" cy="{y+h-9}" rx="{w/2-5}" ry="9" fill="#e3f2fd" stroke="#333" stroke-width="1.8"/>')
        p.append(f'<text x="{cx}" y="{cy-5}" text-anchor="middle" font-size="12" font-weight="bold" '
                 f'font-family="DejaVu Sans, Arial">{title}</text>')
        p.append(f'<text x="{cx}" y="{cy+11}" text-anchor="middle" font-size="10" font-family="DejaVu Sans, Arial">{sub}</text>')
        return {"l": x, "r": x + w, "cx": cx, "cy": cy}

    def arr(pts, label=None, color="#333", mid=None, marker="ag"):
        d = f"M {pts[0][0]:.0f},{pts[0][1]:.0f}"
        for x, y in pts[1:]:
            d += f" L {x:.0f},{y:.0f}"
        p.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.8" marker-end="url(#{marker})"/>')
        if label and mid:
            lx, ly = mid
            tw = len(label) * 6.4 + 12
            p.append(f'<rect x="{lx-tw/2}" y="{ly-14}" width="{tw}" height="17" fill="white" stroke="#ddd" rx="2"/>')
            p.append(f'<text x="{lx}" y="{ly}" text-anchor="middle" font-size="11" font-weight="bold" '
                     f'font-family="DejaVu Sans, Arial" fill="{color}">{label}</text>')

    # -------- Блоки --------
    grp(40, 100, 400, 340, "Системная программа", "#f5f5f5")
    box(70, 150, 340, 72, ["libtrashhook.so", "перехват unlink(), unlinkat(), remove()"])
    box(70, 280, 340, 72, ["trash-util", "list, restore, purge, info, menu"])
    HOOK_R, HOOK_Y = 410, 186
    UTIL_R, UTIL_Y = 410, 316

    grp(470, 130, 300, 195, "Системные средства", "#f1f8e9")
    box(495, 170, 125, 68, ["libc", "unlink, rename,", "open, read, write"])
    box(635, 170, 125, 68, ["libdl", "dlsym(RTLD_NEXT)"])
    LIBC_L, LIBC_R, LIBC_Y = 495, 620, 204

    grp(470, 395, 300, 155, "Внешние программы", "#fff8e6")
    box(490, 435, 260, 48, ["rm и др. + LD_PRELOAD=libtrashhook.so"])
    box(490, 493, 260, 38, ["demo-cycle.sh, setup-test-area.sh"])
    RM_CX, RM_TOP = 620, 435

    grp(1140, 100, 540, 720, "Файловая среда", "#f8fbff")
    home = cyl(1280, 195, 175, 88, "$HOME", "рабочие файлы")
    tfiles = cyl(1280, 430, 175, 88, "Trash/files", "удалённые объекты")
    tinfo = cyl(1280, 665, 175, 88, "Trash/info", ".trashinfo")

    grp(40, 760, 400, 210, "Пользователь и среда запуска", "#e8f4fc")
    box(75, 835, 105, 44, ["Пользователь"])
    box(220, 825, 170, 68, ["Терминал", "ввод команд,", "вывод сообщений"])
    USER_R, USER_Y = 180, 857
    TERM_L, TERM_R, TERM_Y = 220, 390, 857

    # Коридоры (подписи на полосах)
    p.append('<rect x="430" y="108" width="680" height="52" fill="#e3f2fd" stroke="#90caf9" stroke-width="1" rx="4" opacity="0.55"/>')
    p.append('<text x="440" y="128" font-size="10" fill="#1565c0" font-family="DejaVu Sans, Arial">'
             "коридор libtrashhook.so → файловая среда</text>")
    p.append('<rect x="430" y="318" width="680" height="52" fill="#e8f5e9" stroke="#a5d6a7" stroke-width="1" rx="4" opacity="0.55"/>')
    p.append('<text x="440" y="338" font-size="10" fill="#2e7d32" font-family="DejaVu Sans, Arial">'
             "коридор trash-util → файловая среда</text>")

    YH1, YH2, YH3 = 118, 142, 166
    YU1, YU2, YU3 = 328, 352, 376
    # Отдельная вертикальная шина для каждого потока (без общего «столба»)
    VX_H = [980, 1055, 1130]
    VX_U = [1220, 1295, 1370]

    # -------- Пользователь --------
    arr([(USER_R, USER_Y + 18), (TERM_L, USER_Y + 18)], "ввод команды", USER_COLOR, (200, USER_Y + 11), "ag")
    arr([(TERM_L, USER_Y - 18), (USER_R, USER_Y - 18)], "результат", USER_COLOR, (200, USER_Y - 25), "ag")
    arr([(TERM_R, TERM_Y), (TERM_R, 720), (RM_CX, 720), (RM_CX, RM_TOP)],
        "LD_PRELOAD + rm", EXT_COLOR, (500, 714), "ag")
    arr([(70, UTIL_Y), (70, 750), (UTIL_R - 200, 750), (UTIL_R - 200, UTIL_Y)],
        "команды trash-util", USER_COLOR, (120, 744), "ag")

    # -------- rm → hook (левая кромка) --------
    arr([(RM_CX, RM_TOP), (RM_CX, 560), (35, 560), (35, HOOK_Y), (70, HOOK_Y)],
        "вызов unlink()", EXT_COLOR, (120, 554), "ag")

    # -------- hook → libc --------
    arr([(HOOK_R, HOOK_Y), (450, HOOK_Y), (450, LIBC_Y), (LIBC_L, LIBC_Y)],
        "системные вызовы", SYS_COLOR, (472, HOOK_Y - 8), "ag")
    arr([(LIBC_R, LIBC_Y), (635, LIBC_Y)], color=SYS_COLOR, marker="ag")

    # -------- hook → файлы (верхний коридор, синий, вход слева) --------
    arr([(HOOK_R, HOOK_Y - 10), (HOOK_R, YH1), (VX_H[0], YH1), (VX_H[0], home["cy"]), (home["l"], home["cy"])],
        "чтение", HOOK_COLOR, (580, YH1 - 8), "ah")
    p.append(f'<text x="{VX_H[0]-4}" y="{home["cy"]-12}" font-size="10" fill="{HOOK_COLOR}" '
             f'font-family="DejaVu Sans, Arial" text-anchor="end">↓ $HOME</text>')
    arr([(HOOK_R, HOOK_Y), (HOOK_R, YH2), (VX_H[1], YH2), (VX_H[1], tfiles["cy"]), (tfiles["l"], tfiles["cy"])],
        "запись объекта", HOOK_COLOR, (580, YH2 - 8), "ah")
    p.append(f'<text x="{VX_H[1]-4}" y="{tfiles["cy"]-12}" font-size="10" fill="{HOOK_COLOR}" '
             f'font-family="DejaVu Sans, Arial" text-anchor="end">↓ files</text>')
    arr([(HOOK_R, HOOK_Y + 10), (HOOK_R, YH3), (VX_H[2], YH3), (VX_H[2], tinfo["cy"]), (tinfo["l"], tinfo["cy"])],
        "метаданные", HOOK_COLOR, (580, YH3 - 8), "ah")
    p.append(f'<text x="{VX_H[2]-4}" y="{tinfo["cy"]-12}" font-size="10" fill="{HOOK_COLOR}" '
             f'font-family="DejaVu Sans, Arial" text-anchor="end">↓ info</text>')

    # -------- util → файлы (нижний коридор, зелёный, вход справа) --------
    arr([(UTIL_R, UTIL_Y - 10), (UTIL_R, YU1), (VX_U[0], YU1), (VX_U[0], home["cy"]), (home["r"], home["cy"])],
        "restore", UTIL_COLOR, (580, YU1 - 8), "au")
    p.append(f'<text x="{VX_U[0]+4}" y="{home["cy"]-12}" font-size="10" fill="{UTIL_COLOR}" '
             f'font-family="DejaVu Sans, Arial">↓ $HOME</text>')
    arr([(UTIL_R, UTIL_Y), (UTIL_R, YU2), (VX_U[1], YU2), (VX_U[1], tfiles["cy"]), (tfiles["r"], tfiles["cy"])],
        "list / purge", UTIL_COLOR, (580, YU2 - 8), "au")
    p.append(f'<text x="{VX_U[1]+4}" y="{tfiles["cy"]-12}" font-size="10" fill="{UTIL_COLOR}" '
             f'font-family="DejaVu Sans, Arial">↓ files</text>')
    arr([(UTIL_R, UTIL_Y + 10), (UTIL_R, YU3), (VX_U[2], YU3), (VX_U[2], tinfo["cy"]), (tinfo["r"], tinfo["cy"])],
        "чтение метаданных", UTIL_COLOR, (560, YU3 - 8), "au")
    p.append(f'<text x="{VX_U[2]+4}" y="{tinfo["cy"]-12}" font-size="10" fill="{UTIL_COLOR}" '
             f'font-family="DejaVu Sans, Arial">↓ info</text>')

    # Легенда
    p.append(f'<rect x="40" y="{H-62}" width="900" height="48" fill="#fafafa" stroke="#ccc" rx="4"/>')
    p.append(f'<line x1="55" y1="{H-38}" x2="85" y2="{H-38}" stroke="{HOOK_COLOR}" stroke-width="3"/>')
    p.append(f'<text x="92" y="{H-34}" font-size="10" font-family="DejaVu Sans, Arial">libtrashhook.so (верхний коридор, вход слева)</text>')
    p.append(f'<line x1="420" y1="{H-38}" x2="450" y2="{H-38}" stroke="{UTIL_COLOR}" stroke-width="3"/>')
    p.append(f'<text x="457" y="{H-34}" font-size="10" font-family="DejaVu Sans, Arial">trash-util (нижний коридор, вход справа)</text>')

    p.append("</svg>")
    return "\n".join(p)


def main():
    OUT_SVG.write_text(build_svg(), encoding="utf-8")
    print(f"Wrote {OUT_SVG}")


if __name__ == "__main__":
    main()
