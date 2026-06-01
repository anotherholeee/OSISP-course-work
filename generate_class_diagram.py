#!/usr/bin/env python3
"""Large class/module diagram PNG (appendix G)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT_SVG = ROOT / "diagramma_klassov_korzina.svg"
OUT_PNG = ROOT / "diagramma_klassov_korzina.png"

W, H = 1400, 2000
CX = W // 2
BW = 420
BH = 36
GAP = 28
FONT = "DejaVu Sans, Liberation Sans, Arial, sans-serif"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def box(x, y, w, h, title, lines, stroke="#333", fill="#fff"):
    parts = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="2.5" rx="2"/>',
        f'<text x="{x+w/2}" y="{y+26}" text-anchor="middle" font-size="16" '
        f'font-weight="bold" font-family="{FONT}">{esc(title)}</text>',
        f'<line x1="{x}" y1="{y+38}" x2="{x+w}" y2="{y+38}" stroke="{stroke}" stroke-width="1.5"/>',
    ]
    for i, ln in enumerate(lines):
        parts.append(
            f'<text x="{x+14}" y="{y+58+i*22}" font-size="13" font-family="{FONT}">{esc(ln)}</text>'
        )
    return "\n".join(parts), h


def arrow_ortho(points, label=None, lx=0, ly=0):
    d = f"M {points[0][0]:.0f} {points[0][1]:.0f}"
    for x, y in points[1:]:
        d += f" L {x:.0f} {y:.0f}"
    s = [
        f'<path d="{d}" fill="none" stroke="#333" stroke-width="2" marker-end="url(#ar)"/>'
    ]
    if label:
        s.append(f'<rect x="{lx-4}" y="{ly-14}" width="{len(label)*7+12}" height="18" fill="white"/>')
        s.append(
            f'<text x="{lx}" y="{ly}" font-size="13" font-weight="bold" '
            f'font-family="{FONT}">{esc(label)}</text>'
        )
    return "\n".join(s)


def build_svg() -> str:
    p = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        "<defs>",
        '<marker id="ar" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto">',
        '<path d="M0,0 L10,5 L0,10 Z" fill="#333"/>',
        "</marker>",
        "</defs>",
        f'<text x="{CX}" y="50" text-anchor="middle" font-size="24" font-weight="bold" '
        f'font-family="{FONT}">Диаграмма классов (структуры данных и модули)</text>',
        f'<text x="{CX}" y="82" text-anchor="middle" font-size="15" font-family="{FONT}">'
        "«Корзина» для программ, использующих системный вызов unlink()</text>",
    ]

    x = CX - BW // 2
    y = 110

    util_lines = [
        "+main(argc, argv)",
        "+list_entries()",
        "+restore_entry(id)",
        "+purge_entries()",
        "+info_entries()",
        "+run_menu()",
    ]
    h_util = 38 + len(util_lines) * 22 + 16
    s, _ = box(x, y, BW, h_util, "trash_util.c", util_lines)
    p.append(s)
    util_bot = y + h_util

    y_hook = util_bot + 80
    hook_lines = [
        "+unlink(pathname)",
        "+unlinkat(dirfd, pathname, flags)",
        "+remove(pathname)",
        "-unlink_to_trash_abs(abs_path)",
        "-safe_copy_file(src, dst, mode)",
        "-call_real_unlink(path)",
    ]
    h_hook = 38 + len(hook_lines) * 22 + 16
    s, _ = box(x, y_hook, BW, h_hook, "trash_hook.c", hook_lines)
    p.append(s)
    hook_bot = y_hook + h_hook

    y_entry = hook_bot + 80
    entry_lines = [
        "+id : char[NAME_MAX]",
        "+original_path : char[PATH_MAX]",
        "+deletion_date : char[64]",
        "+mode : mode_t",
        "+uid : uid_t  +gid : gid_t",
        "+atime_sec / atime_nsec : long",
        "+mtime_sec / mtime_nsec : long",
    ]
    h_entry = 38 + len(entry_lines) * 22 + 16
    s, _ = box(x, y_entry, BW, h_entry, "trash_entry", entry_lines, fill="#E8F5E9")
    p.append(s)
    entry_bot = y_entry + h_entry
    entry_top = y_entry

    y_common = entry_bot + 80
    common_lines = [
        "+trash_get_home(buf, size)",
        "+trash_paths(root, files, info)",
        "+trash_ensure_layout()",
        "+trash_parse_info(path, entry)",
        "+trash_write_info(path, entry)",
        "+trash_generate_id(path, dst, sz)",
        "+trash_url_encode_path() / decode_path()",
        "+trash_resolve_unique_path()",
        "+trash_dir_size_bytes(path)",
    ]
    h_common = 38 + len(common_lines) * 22 + 16
    s, _ = box(x, y_common, BW, h_common, "trash_common.c", common_lines)
    p.append(s)
    common_top = y_common

    util_cy = y + h_util // 2
    hook_cy = y_hook + h_hook // 2
    entry_cy = y_entry + h_entry // 2
    common_cy = y_common + h_common // 2

    # util -> hook
    p.append(arrow_ortho([(CX, util_bot), (CX, y_hook)], None))
    # util -> common (right bus)
    bus_r = CX + BW // 2 + 50
    p.append(arrow_ortho([(CX, util_bot), (bus_r, util_bot), (bus_r, common_top), (CX, common_top)]))
    # hook -> entry
    p.append(arrow_ortho([(CX, hook_bot), (CX, entry_top)], "метаданные", CX + 12, (hook_bot + entry_top) // 2))
    # util -> entry
    p.append(arrow_ortho([(CX - 60, util_bot), (CX - 60, entry_top), (CX - BW // 2, entry_top)], "восстановление",
                         CX - 130, entry_top - 20))
    # common -> entry
    p.append(arrow_ortho([(CX, common_top), (CX, entry_bot)], "операции", CX + 12, (common_top + entry_bot) // 2))
    # hook -> common
    bus_l = CX - BW // 2 - 50
    p.append(arrow_ortho([(CX, hook_bot), (bus_l, hook_bot), (bus_l, common_top), (CX - BW // 2, common_top)]))

    p.append("</svg>")
    return "\n".join(p)


def main():
    OUT_SVG.write_text(build_svg(), encoding="utf-8")
    print(f"Wrote {OUT_SVG}")
    try:
        import subprocess
        subprocess.run(
            ["magick", "-background", "white", "-density", "200", str(OUT_SVG), str(OUT_PNG)],
            check=True,
        )
        print(f"Wrote {OUT_PNG}")
    except (FileNotFoundError, subprocess.CalledProcessError):
        subprocess.run(
            ["convert", "-background", "white", "-density", "200", str(OUT_SVG), str(OUT_PNG)],
            check=False,
        )


if __name__ == "__main__":
    main()
