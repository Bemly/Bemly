#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate a self-contained animated SVG of Bemly's projects × licenses.

The SVG is designed to be embedded in a GitHub profile README via <img>:
no JavaScript, no foreignObject, no external fonts/images/CSS.
Motion uses SMIL. Base attributes are the final visible state so the
graphic still reads correctly when animations are disabled.

Usage (from the repo root, or any cwd — paths are relative to this file):
    python3 scripts/make_license_svg.py
    python3 scripts/make_license_svg.py --csv scripts/licenses.csv --out assets/licenses.svg
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

DIR = Path(__file__).resolve().parent
ROOT = DIR.parent

EXCLUDE_LICENSES = {"无", "仓库已删", "Other（未识别）", ""}

LICENSE_ALIASES = {
    "MIT License": "MIT",
    'BSD 3-Clause "New" or "Revised" License': "BSD-3-Clause",
}

# Order matters: first matching rule wins.
# 0BSD is a public-domain equivalent, so it sits with Unlicense / CC0 / WTFPL
# rather than the other permissive BSD-style licenses.
FAMILY_RULES = [
    ("hardware", lambda l: l.startswith("CERN-OHL")),
    ("public", lambda l: l in {"Unlicense", "CC0-1.0", "WTFPL", "0BSD"} or l.startswith("CC0")),
    (
        "content",
        lambda l: l.startswith(("CC-BY", "ODbL", "GFDL", "OFL")),
    ),
    ("strong", lambda l: l.startswith("GPL-") or l.startswith("AGPL-")),
    (
        "weak",
        lambda l: l.startswith(("LGPL", "MPL", "EPL", "EUPL", "LPPL")) or l in {"MS-RL"},
    ),
    ("permissive", lambda l: True),
]

FAMILIES = [
    # id, zh, en, color, color_dim, color_deep
    ("permissive", "宽松许可", "Permissive", "#2dd4bf", "#134e4a", "#99f6e4"),
    ("weak", "弱 Copyleft", "Weak Copyleft", "#fbbf24", "#5b4510", "#fde68a"),
    ("strong", "强 Copyleft", "Strong Copyleft", "#fb7185", "#5c1a27", "#fecdd3"),
    ("public", "公有领域", "Public Domain", "#c084fc", "#4c1d73", "#e9d5ff"),
    ("content", "内容 / 数据", "Content & Data", "#38bdf8", "#0c4a6e", "#bae6fd"),
    ("hardware", "硬件开源", "Hardware", "#a3e635", "#3f6212", "#d9f99d"),
]
FAMILY_INDEX = {f[0]: f for f in FAMILIES}

# Canvas
W = 1000
OUTER = 10
CARD_X = OUTER
CARD_Y = OUTER
CARD_W = W - 2 * OUTER
CARD_RX = 20

HEADER_TOP = 28
TITLE_Y = 46
SUB_Y = 70
LEGEND_Y = 96
HEADER_RULE_Y = 114
CONTENT_TOP = 128

ROW_H = 22
FAMILY_HEAD_H = 24

RAIL_X = 28
NAME_X = 48
NAME_SIZE = 11.5
BADGE_SIZE = 8.5
LINE_X0 = 372
LINE_X1 = 698
PILL_X = 710
PILL_W = 252
PILL_H_MIN = 16
COUNT_R = 10

# Animation timing (seconds)
TITLE_DUR = 0.55
ROW_START = 0.50
ROW_STAGGER = 0.046
ROW_DUR = 0.48
LINE_LAG = 0.14
LINE_DUR = 0.95
NODE_IN_DUR = 0.42
PULSE_DUR = 0.55
AMBIENT_PULSE = 2.8
PARTICLE_DUR = 3.15


def normalize_license(raw: str) -> str:
    raw = raw.strip()
    return LICENSE_ALIASES.get(raw, raw)


def family_of(license_id: str) -> str:
    for fid, pred in FAMILY_RULES:
        if pred(license_id):
            return fid
    return "permissive"


def parse_badges(note: str) -> list[str]:
    if not note:
        return []
    parts: list[str] = []
    for chunk in note.replace("/", "·").split("·"):
        tag = chunk.strip()
        if tag:
            parts.append(tag)
    return parts


def load_rows(csv_path: Path) -> list[dict]:
    rows: list[dict] = []
    with csv_path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for rec in reader:
            lic_raw = (rec.get("改后证书") or "").strip()
            if lic_raw in EXCLUDE_LICENSES:
                continue
            rows.append(
                {
                    "name": (rec.get("项目名称") or "").strip(),
                    "license": normalize_license(lic_raw),
                    "url": (rec.get("项目地址") or "").strip(),
                    "badges": parse_badges((rec.get("备注") or "").strip()),
                }
            )
    return rows


def group_projects(rows: list[dict]) -> list[dict]:
    """Return families → licenses → projects, in display order."""
    by_lic: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_lic[r["license"]].append(r)

    fam_lics: dict[str, list[str]] = defaultdict(list)
    for lic in by_lic:
        fam_lics[family_of(lic)].append(lic)

    families = []
    for fid, zh, en, color, dim, deep in FAMILIES:
        licenses = fam_lics.get(fid, [])
        if not licenses:
            continue
        licenses.sort(key=lambda l: (-len(by_lic[l]), l.lower()))
        lic_blocks = []
        for lic in licenses:
            projects = sorted(by_lic[lic], key=lambda p: p["name"].lower())
            lic_blocks.append({"id": lic, "projects": projects, "count": len(projects)})
        families.append(
            {
                "id": fid,
                "zh": zh,
                "en": en,
                "color": color,
                "dim": dim,
                "deep": deep,
                "licenses": lic_blocks,
                "count": sum(l["count"] for l in lic_blocks),
            }
        )
    return families


def layout(families: list[dict]) -> float:
    """Assign y coordinates. Returns the card's bottom y (content end + pad)."""
    y = CONTENT_TOP
    idx = 0
    for fam in families:
        fam["y0"] = y
        y += FAMILY_HEAD_H
        for lic in fam["licenses"]:
            lic["color"] = fam["color"]
            lic["dim"] = fam["dim"]
            lic["deep"] = fam["deep"]
            lic["family"] = fam["id"]
            lic["y0"] = y
            for i, proj in enumerate(lic["projects"]):
                proj["cy"] = y + ROW_H / 2
                proj["idx"] = idx
                proj["color"] = fam["color"]
                proj["deep"] = fam["deep"]
                proj["lic"] = lic["id"]
                idx += 1
                y += ROW_H
            lic["y1"] = y
            lic["cy"] = (lic["y0"] + lic["y1"]) / 2
            lic["span"] = lic["y1"] - lic["y0"]
            # Fan attachment points along a small window around the pill center.
            n = lic["count"]
            spread = min(max(n - 1, 0) * 6.0, 44.0)
            for i, proj in enumerate(lic["projects"]):
                if n == 1:
                    proj["ty"] = lic["cy"]
                else:
                    t = i / (n - 1)
                    proj["ty"] = lic["cy"] - spread / 2 + t * spread
        fam["y1"] = y
        y += 8  # breath between families
    return y + 36  # bottom padding for footer


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def mono_w(text: str, size: float) -> float:
    """Approximate width of a monospace run (0.6em typical for JetBrains/Consolas)."""
    return len(text) * size * 0.6


def badge_w(tag: str) -> float:
    # CJK is ~1em, ASCII ~0.62em, plus horizontal padding.
    w = 0.0
    for ch in tag:
        w += BADGE_SIZE if ord(ch) > 0x7F else BADGE_SIZE * 0.62
    return w + 10


def curve(x1: float, y1: float, x2: float, y2: float) -> str:
    c = (x2 - x1) * 0.52
    return (
        f"M{x1:.1f},{y1:.1f} "
        f"C{x1 + c:.1f},{y1:.1f} {x2 - c:.1f},{y2:.1f} {x2:.1f},{y2:.1f}"
    )


def t(sec: float) -> str:
    """Format a clock value for SMIL begin/dur."""
    return f"{sec:.3f}s".replace(".000s", "s")


def build_svg(families: list[dict], n_projects: int, n_licenses: int, card_bottom: float) -> str:
    h = card_bottom + OUTER
    card_h = card_bottom - CARD_Y

    # Precompute animation start times
    def row_begin(i: int) -> float:
        return ROW_START + i * ROW_STAGGER

    def line_begin(i: int) -> float:
        return row_begin(i) + LINE_LAG

    # First project index of each license (for node appear)
    out: list[str] = []
    a = out.append

    a('<?xml version="1.0" encoding="UTF-8"?>')
    a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h:.0f}"')
    a(f'     viewBox="0 0 {W} {h:.0f}" role="img"')
    a('     aria-labelledby="title desc">')
    a("  <title id=\"title\">Bemly · Projects × Licenses</title>")
    a(
        "  <desc id=\"desc\">"
        + esc(
            f"Bemly 的 {n_projects} 个 GitHub 项目与 {n_licenses} 种开源许可证的对应关系。"
            "左侧是项目，右侧是许可证，连线按许可家族着色。"
        )
        + "</desc>"
    )

    # ------------------------------------------------------------------ styles
    a("  <style><![CDATA[")
    a("    .ui {")
    a('      font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans SC",')
    a('                   "Noto Sans CJK SC", "Source Han Sans SC", sans-serif;')
    a("    }")
    a("    .mono {")
    a('      font-family: "JetBrains Mono", "SFMono-Regular", "Menlo",')
    a('                   Consolas, "Liberation Mono", monospace;')
    a("    }")
    a("    text { font-variant-ligatures: none; }")
    a("  ]]></style>")

    # ------------------------------------------------------------------ defs
    a("  <defs>")
    a("    <linearGradient id=\"bg\" x1=\"0\" y1=\"0\" x2=\"1\" y2=\"1\">")
    a('      <stop offset="0%" stop-color="#101726"/>')
    a('      <stop offset="45%" stop-color="#0c1320"/>')
    a('      <stop offset="100%" stop-color="#10141f"/>')
    a("    </linearGradient>")
    a("    <linearGradient id=\"bgShine\" x1=\"0\" y1=\"0\" x2=\"0\" y2=\"1\">")
    a('      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.045"/>')
    a('      <stop offset="18%" stop-color="#ffffff" stop-opacity="0"/>')
    a('      <stop offset="100%" stop-color="#000000" stop-opacity="0.18"/>')
    a("    </linearGradient>")
    a("    <linearGradient id=\"titleGrad\" x1=\"0\" y1=\"0\" x2=\"1\" y2=\"0\">")
    a('      <stop offset="0%" stop-color="#5eead4">')
    a('        <animate attributeName="stop-color"')
    a('                 values="#2dd4bf;#67e8f9;#c084fc;#5eead4;#2dd4bf"')
    a('                 dur="10s" repeatCount="indefinite"/>')
    a("      </stop>")
    a('      <stop offset="100%" stop-color="#99f6e4">')
    a('        <animate attributeName="stop-color"')
    a('                 values="#99f6e4;#a5b4fc;#67e8f9;#99f6e4"')
    a('                 dur="10s" repeatCount="indefinite"/>')
    a("      </stop>")
    a("    </linearGradient>")
    a("    <linearGradient id=\"ruleGrad\" x1=\"0\" y1=\"0\" x2=\"1\" y2=\"0\">")
    a('      <stop offset="0%" stop-color="#2dd4bf" stop-opacity="0"/>')
    a('      <stop offset="15%" stop-color="#2dd4bf" stop-opacity="0.7"/>')
    a('      <stop offset="50%" stop-color="#64748b" stop-opacity="0.35"/>')
    a('      <stop offset="85%" stop-color="#c084fc" stop-opacity="0.55"/>')
    a('      <stop offset="100%" stop-color="#c084fc" stop-opacity="0"/>')
    a("    </linearGradient>")
    a("    <pattern id=\"dots\" width=\"22\" height=\"22\" patternUnits=\"userSpaceOnUse\">")
    a('      <circle cx="1.2" cy="1.2" r="0.8" fill="#94a3b8" fill-opacity="0.09"/>')
    a("    </pattern>")
    a("    <linearGradient id=\"midFade\" x1=\"0\" y1=\"0\" x2=\"1\" y2=\"0\">")
    a('      <stop offset="0%" stop-color="#ffffff" stop-opacity="0"/>')
    a('      <stop offset="50%" stop-color="#ffffff" stop-opacity="0.04"/>')
    a('      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>')
    a("    </linearGradient>")
    a('    <filter id="cardShadow" x="-8%" y="-4%" width="116%" height="110%">')
    a('      <feDropShadow dx="0" dy="6" stdDeviation="10" flood-color="#000000" flood-opacity="0.45"/>')
    a("    </filter>")
    a('    <filter id="glow" x="-40%" y="-40%" width="180%" height="180%">')
    a('      <feGaussianBlur stdDeviation="1.4" result="b"/>')
    a('      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>')
    a("    </filter>")
    a('    <clipPath id="cardClip">')
    a(f'      <rect x="{CARD_X}" y="{CARD_Y}" width="{CARD_W}" height="{card_h:.1f}" rx="{CARD_RX}"/>')
    a("    </clipPath>")
    a("  </defs>")

    # ------------------------------------------------------------------ card
    a(
        f'  <rect x="{CARD_X}" y="{CARD_Y}" width="{CARD_W}" height="{card_h:.1f}"'
        f' rx="{CARD_RX}" fill="url(#bg)" stroke="#2a3550" stroke-width="1" filter="url(#cardShadow)"/>'
    )
    a(
        f'  <rect x="{CARD_X}" y="{CARD_Y}" width="{CARD_W}" height="{card_h:.1f}"'
        f' rx="{CARD_RX}" fill="url(#bgShine)"/>'
    )
    a(f'  <rect x="{CARD_X}" y="{CARD_Y}" width="{CARD_W}" height="{card_h:.1f}" rx="{CARD_RX}" fill="url(#dots)"/>')

    # Animated living border (ambient, loops forever)
    peri = 2 * (CARD_W + card_h)  # rough, actual rounded peri slightly less; pathLength handles it
    a(
        f'  <rect x="{CARD_X + 0.6}" y="{CARD_Y + 0.6}" width="{CARD_W - 1.2}" height="{card_h - 1.2:.1f}"'
        f' rx="{CARD_RX - 0.4}" fill="none" stroke="#5eead4" stroke-opacity="0.28"'
        f' stroke-width="1.1" pathLength="1000" stroke-dasharray="70 40 14 40 160 50" stroke-linecap="round">'
    )
    a('    <animate attributeName="stroke-dashoffset" from="0" to="-1000" dur="22s" repeatCount="indefinite"/>')
    a("  </rect>")

    # ================================================================== header
    # Title
    a('  <g class="ui">')
    a('    <set attributeName="opacity" to="0" begin="0s"/>')
    a(f'    <animate attributeName="opacity" from="0" to="1" begin="0s" dur="{t(TITLE_DUR)}" fill="freeze"/>')
    # small live dot
    a(f'    <circle cx="36" cy="{TITLE_Y - 1}" r="4" fill="#2dd4bf">')
    a('      <animate attributeName="opacity" values="1;0.35;1" dur="2.2s" repeatCount="indefinite"/>')
    a("    </circle>")
    a(
        f'    <text x="48" y="{TITLE_Y}" font-size="22"'
        f' font-weight="700" letter-spacing="0.4">'
        f'<tspan fill="url(#titleGrad)">Bemly</tspan>'
        f'<tspan fill="#e8edf7">  ·  Projects × Licenses</tspan></text>'
    )
    a(
        f'    <text x="48" y="{SUB_Y}" fill="#93a0b8" font-size="12.5">'
        f"项目与许可证的对应关系"
        f'<tspan dx="14" fill="#64748b" class="mono" font-size="11.5">'
        f"{n_projects} 个项目  ·  {n_licenses} 种许可证</tspan></text>"
    )
    a("  </g>")

    # Legend
    a('  <g class="ui">')
    a('    <set attributeName="opacity" to="0" begin="0s"/>')
    a('    <animate attributeName="opacity" from="0" to="1" begin="0.2s" dur="0.5s" fill="freeze"/>')
    lx = 48.0
    for fid, zh, en, color, dim, deep in FAMILIES:
        # only show families that exist
        if not any(f["id"] == fid for f in families):
            continue
        label = zh
        # width: color chip + gap + text
        tw = 0
        for ch in label:
            tw += 11 if ord(ch) > 0x7F else 11 * 0.55
        # "Copyleft" mixed — use a generous estimate
        tw = max(tw, 11 * 0.95 * (2 if "Copyleft" not in label else 8.2))
        if "Copyleft" in label:
            tw = 86
        elif label == "内容 / 数据":
            tw = 78
        elif label == "宽松许可":
            tw = 58
        elif label == "公有领域":
            tw = 58
        elif label == "硬件开源":
            tw = 58
        a(f'    <rect x="{lx:.1f}" y="{LEGEND_Y - 9}" width="10" height="10" rx="2" fill="{color}"/>')
        a(
            f'    <text x="{lx + 14:.1f}" y="{LEGEND_Y}" fill="#cbd5e1" font-size="11"'
            f' dominant-baseline="middle">{esc(label)}</text>'
        )
        lx += 14 + tw + 16
    a("  </g>")

    # Header rule
    a(
        f'  <line x1="32" y1="{HEADER_RULE_Y}" x2="968" y2="{HEADER_RULE_Y}"'
        f' stroke="url(#ruleGrad)" stroke-width="1" pathLength="1" stroke-dasharray="1" stroke-dashoffset="0">'
    )
    a('    <set attributeName="stroke-dashoffset" to="1" begin="0s"/>')
    a('    <animate attributeName="stroke-dashoffset" from="1" to="0" begin="0.25s" dur="0.9s" fill="freeze"/>')
    a("  </line>")

    # Soft wash behind the curve area
    a(
        f'  <rect x="{LINE_X0}" y="{CONTENT_TOP - 6}" width="{LINE_X1 - LINE_X0}"'
        f' height="{card_bottom - CONTENT_TOP - 8:.1f}" fill="url(#midFade)" clip-path="url(#cardClip)"/>'
    )

    # ============================================================ family rails
    # & headers (appear with first row of that family)
    for fam in families:
        first_idx = fam["licenses"][0]["projects"][0]["idx"]
        b = row_begin(first_idx)
        rail_y = fam["y0"] + 4
        rail_h = fam["y1"] - fam["y0"] - 6
        a(f'  <g>')
        a('    <set attributeName="opacity" to="0" begin="0s"/>')
        a(f'    <animate attributeName="opacity" from="0" to="1" begin="{t(b)}" dur="0.45s" fill="freeze"/>')
        a(
            f'    <rect x="{RAIL_X}" y="{rail_y:.1f}" width="3.5" height="{rail_h:.1f}"'
            f' rx="1.75" fill="{fam["color"]}" fill-opacity="0.9">'
        )
        a('      <set attributeName="height" to="0" begin="0s"/>')
        a(
            f'      <animate attributeName="height" from="0" to="{rail_h:.1f}"'
            f' begin="{t(b)}" dur="{t(max(0.6, len(fam["licenses"]) * 0.18))}" fill="freeze"'
            f' calcMode="spline" keyTimes="0;1" keySplines="0.22 1 0.36 1"/>'
        )
        a("    </rect>")
        a(
            f'    <text x="{NAME_X}" y="{fam["y0"] + 14:.1f}" class="ui" font-size="10.5"'
            f' font-weight="600" fill="{fam["color"]}" letter-spacing="0.6">{esc(fam["zh"])}'
            f'<tspan class="mono" font-size="9" font-weight="400" fill="{fam["color"]}"'
            f' fill-opacity="0.7" dx="8">{esc(fam["en"].upper())}  ·  {fam["count"]}</tspan></text>'
        )
        a("  </g>")

    # ============================================================ curves (under labels)
    a('  <g fill="none" stroke-linecap="round" stroke-linejoin="round">')
    for fam in families:
        for lic in fam["licenses"]:
            for proj in lic["projects"]:
                i = proj["idx"]
                d = curve(LINE_X0, proj["cy"], LINE_X1, proj["ty"])
                lb = line_begin(i)
                col = proj["color"]
                # Base stroke (draw in, then stay)
                a(
                    f'    <path d="{d}" stroke="{col}" stroke-width="1.35"'
                    f' stroke-opacity="0.52" pathLength="1" stroke-dasharray="1" stroke-dashoffset="0">'
                )
                a('      <set attributeName="stroke-dashoffset" to="1" begin="0s"/>')
                a('      <set attributeName="stroke-opacity" to="0" begin="0s"/>')
                a(
                    f'      <animate attributeName="stroke-dashoffset" from="1" to="0"'
                    f' begin="{t(lb)}" dur="{t(LINE_DUR)}" fill="freeze"'
                    f' calcMode="spline" keyTimes="0;1" keySplines="0.4 0 0.2 1"/>'
                )
                a(
                    f'      <animate attributeName="stroke-opacity" from="0" to="0.55"'
                    f' begin="{t(lb)}" dur="0.25s" fill="freeze"/>'
                )
                a("    </path>")
                # Flowing particle (starts after the line has drawn)
                pb = lb + LINE_DUR * 0.85
                a(
                    f'    <path d="{d}" stroke="{proj["deep"]}" stroke-width="2.1"'
                    f' stroke-opacity="0.9" pathLength="1" stroke-dasharray="0.07 0.93"'
                    f' stroke-dashoffset="0" filter="url(#glow)">'
                )
                a('      <set attributeName="stroke-opacity" to="0" begin="0s"/>')
                a(
                    f'      <animate attributeName="stroke-opacity" from="0" to="0.92"'
                    f' begin="{t(pb)}" dur="0.25s" fill="freeze"/>'
                )
                a(
                    f'      <animate attributeName="stroke-dashoffset" from="0" to="-1"'
                    f' begin="{t(pb)}" dur="{t(PARTICLE_DUR)}" repeatCount="indefinite"/>'
                )
                a("    </path>")
    a("  </g>")

    # ============================================================ project rows
    badge_colors = {
        "私有": ("#c084fc", "#2e1064"),
        "归档": ("#94a3b8", "#1e293b"),
        "fork": ("#38bdf8", "#0c4a6e"),
    }

    for fam in families:
        for lic in fam["licenses"]:
            for proj in lic["projects"]:
                i = proj["idx"]
                b = row_begin(i)
                cy = proj["cy"]
                a(f'  <g class="mono">')
                a('    <set attributeName="opacity" to="0" begin="0s"/>')
                a(
                    f'    <animate attributeName="opacity" from="0" to="1"'
                    f' begin="{t(b)}" dur="{t(ROW_DUR)}" fill="freeze"/>'
                )
                a(
                    f'    <animateTransform attributeName="transform" type="translate"'
                    f' from="-16 0" to="0 0" begin="{t(b)}" dur="{t(ROW_DUR)}" fill="freeze"'
                    f' calcMode="spline" keyTimes="0;1" keySplines="0.22 1 0.36 1"/>'
                )
                # tiny endpoint dot at the start of the curve
                a(
                    f'    <circle cx="{LINE_X0 - 4:.1f}" cy="{cy:.1f}" r="2.1"'
                    f' fill="{proj["color"]}" fill-opacity="0.85"/>'
                )
                a(
                    f'    <text x="{NAME_X}" y="{cy:.1f}" fill="#e8eef8" font-size="{NAME_SIZE}"'
                    f' dominant-baseline="central">{esc(proj["name"])}</text>'
                )
                # badges sit just after the name
                bx = NAME_X + mono_w(proj["name"], NAME_SIZE) + 8
                for tag in proj["badges"]:
                    fg, bg = badge_colors.get(tag, ("#cbd5e1", "#1e293b"))
                    bw = badge_w(tag)
                    bh = 12.5
                    a(
                        f'    <rect x="{bx:.1f}" y="{cy - bh/2:.1f}" width="{bw:.1f}" height="{bh}"'
                        f' rx="3.2" fill="{bg}" stroke="{fg}" stroke-opacity="0.55" stroke-width="0.7"/>'
                    )
                    a(
                        f'    <text x="{bx + bw/2:.1f}" y="{cy:.1f}" class="ui" font-size="{BADGE_SIZE}"'
                        f' fill="{fg}" text-anchor="middle" dominant-baseline="central">{esc(tag)}</text>'
                    )
                    bx += bw + 4
                a("  </g>")

    # ============================================================ license nodes
    for fam in families:
        for lic in fam["licenses"]:
            first = min(p["idx"] for p in lic["projects"])
            # Appear as the first line of this license starts drawing
            b = line_begin(first)
            # Stronger pulse when the last line of this group arrives
            last = max(p["idx"] for p in lic["projects"])
            pulse_at = line_begin(last) + LINE_DUR * 0.75

            count = lic["count"]
            # Slightly taller pill for popular licenses
            ph = PILL_H_MIN if count == 1 else min(PILL_H_MIN + 1.5 + count * 0.5, 20)
            cy = lic["cy"]
            cx = PILL_X  # left of pill; we'll draw from PILL_X
            # Arrival dot at the curve's end
            a(f'  <g>')
            a('    <set attributeName="opacity" to="0" begin="0s"/>')
            a(
                f'    <animate attributeName="opacity" from="0" to="1"'
                f' begin="{t(b)}" dur="{t(NODE_IN_DUR)}" fill="freeze"/>'
            )
            a(
                f'    <circle cx="{LINE_X1 + 4:.1f}" cy="{cy:.1f}" r="2.2"'
                f' fill="{lic["color"]}"/>'
            )

            # Positioned + scaled around the pill center
            pcx = PILL_X + PILL_W / 2
            pcy = cy
            a(f'    <g transform="translate({pcx:.1f},{pcy:.1f})">')
            # appear scale
            a("      <g>")
            a(
                f'        <animateTransform attributeName="transform" type="scale"'
                f' from="0.78" to="1" begin="{t(b)}" dur="{t(NODE_IN_DUR)}" fill="freeze"'
                f' calcMode="spline" keyTimes="0;1" keySplines="0.22 1 0.36 1"/>'
            )
            # arrival pulse, then ambient pulse (nested so they don't collide)
            a("        <g>")
            a(
                f'          <animateTransform attributeName="transform" type="scale"'
                f' values="1;1.055;1" begin="{t(pulse_at)}" dur="{t(PULSE_DUR)}"'
                f' fill="freeze" calcMode="spline" keyTimes="0;0.4;1"'
                f' keySplines="0.2 0.8 0.2 1;0.4 0 0.2 1"/>'
            )
            a("          <g>")
            a(
                f'            <animateTransform attributeName="transform" type="scale"'
                f' values="1;1.03;1" begin="{t(pulse_at + PULSE_DUR)}" dur="{t(AMBIENT_PULSE)}"'
                f' repeatCount="indefinite"/>'
            )
            # pill in local coords
            a(
                f'          <rect x="{-PILL_W/2:.1f}" y="{-ph/2:.1f}" width="{PILL_W:.1f}"'
                f' height="{ph:.1f}" rx="{ph/2:.1f}" fill="{lic["dim"]}"'
                f' fill-opacity="0.92" stroke="{lic["color"]}" stroke-width="1.15"/>'
            )
            # left accent
            a(
                f'          <rect x="{-PILL_W/2:.1f}" y="{-ph/2 + 2.2:.1f}" width="3.4"'
                f' height="{ph - 4.4:.1f}" rx="1.6" fill="{lic["color"]}"/>'
            )
            a(
                f'          <text x="{-PILL_W/2 + 14:.1f}" y="0" class="mono" font-size="11.5"'
                f' font-weight="600" fill="{lic["deep"]}" dominant-baseline="central">{esc(lic["id"])}</text>'
            )
            if count > 1:
                # count chip on the right (hide ×1 to cut noise)
                chip = f"×{count}"
                cw = max(22, 8 + mono_w(chip, 10) + 8)
                ch = 12.5
                cxr = PILL_W / 2 - 8 - cw / 2
                a(
                    f'          <rect x="{cxr - cw/2:.1f}" y="{-ch/2:.1f}" width="{cw:.1f}"'
                    f' height="{ch}" rx="{ch/2}" fill="{lic["color"]}" fill-opacity="0.18"/>'
                )
                a(
                    f'          <text x="{cxr:.1f}" y="0" class="mono" font-size="10"'
                    f' font-weight="700" fill="{lic["color"]}" text-anchor="middle"'
                    f' dominant-baseline="central">{esc(chip)}</text>'
                )
            a("          </g>")
            a("        </g>")
            a("      </g>")
            a("    </g>")
            a("  </g>")

    # Footer hint
    a('  <g class="ui">')
    a('    <set attributeName="opacity" to="0" begin="0s"/>')
    a(
        f'    <animate attributeName="opacity" from="0" to="0.7"'
        f' begin="{t(line_begin(n_projects - 1) + LINE_DUR)}" dur="0.6s" fill="freeze"/>'
    )
    a(
        f'    <text x="{W/2:.1f}" y="{card_bottom - 16:.1f}" text-anchor="middle"'
        f' font-size="9.5" fill="#7b869c">github.com/Bemly  ·  按改后证书归类  ·  动画循环播放</text>'
    )
    a("  </g>")

    a("</svg>")
    a("")
    return "\n".join(out)


def print_report(rows: list[dict], families: list[dict]) -> None:
    from collections import Counter

    counts = Counter(r["license"] for r in rows)
    print(f"included projects: {len(rows)}")
    print(f"unique licenses:   {len(counts)}")
    print("licenses (count desc):")
    for lic, n in counts.most_common():
        print(f"  {n:2d}  {lic}  [{family_of(lic)}]")
    print("families:")
    for fam in families:
        print(f"  {fam['zh']} ({fam['en']}): {fam['count']} projects, {len(fam['licenses'])} licenses")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--csv", type=Path, default=DIR / "licenses.csv")
    p.add_argument("--out", type=Path, default=ROOT / "assets" / "licenses.svg")
    args = p.parse_args(argv)

    rows = load_rows(args.csv)
    if not rows:
        print("no projects with a real license found", file=sys.stderr)
        return 1
    families = group_projects(rows)
    card_bottom = layout(families)
    n_lic = sum(len(f["licenses"]) for f in families)
    svg = build_svg(families, len(rows), n_lic, card_bottom)
    args.out.write_text(svg, encoding="utf-8")
    print_report(rows, families)
    print(f"wrote {args.out}  ({args.out.stat().st_size} bytes, height {card_bottom + OUTER:.0f}px)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
