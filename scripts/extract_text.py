#!/usr/bin/env python3
"""Extract all human-readable text lines from main/master READMEs."""
import json
import re
import subprocess

import sys

REPO = sys.argv[1] if len(sys.argv) > 1 else subprocess.run(
    ['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True).stdout.strip()
OUT = sys.argv[2] if len(sys.argv) > 2 else 'pixel_task.json'


def raw(branch):
    return subprocess.run(['git', '-C', REPO, 'show', f'{branch}:README.md'],
                          capture_output=True, text=True).stdout


ALLOWED_RANGES = [(0x20, 0x7e), (0x4e00, 0x9fff), (0x3000, 0x303f), (0xff01, 0xff5e)]
ALLOWED_CHARS = set('·×→∫Δ—…')


def keep(ch):
    if ch in ALLOWED_CHARS:
        return True
    return any(a <= ord(ch) <= b for a, b in ALLOWED_RANGES)


def strip_md(line):
    prev = None
    while prev != line:
        prev = line
        line = re.sub(r'\[!\[([^\]]*)\]\[[^\]]*\]\]\[[^\]]*\]', r'\1', line)
        line = re.sub(r'!\[([^\]]*)\]\[[^\]]*\]', r'\1', line)
        line = re.sub(r'\[([^\]]*)\]\[[^\]]*\]', r'\1', line)
        line = re.sub(r'!\[([^\]]*)\]\([^)]*\)', r'\1', line)
        line = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', line)
    return line


def formula(line):
    texts = re.findall(r'\\text\{([^}]*)\}', line)
    if not texts:
        return None
    if '\\int' in line:
        return f'{texts[0]} = ∫{texts[1]}→{texts[2]} {texts[3]} dt'
    if '\\stackrel' in line:
        return f'{texts[0]} ×{texts[1]} {texts[2]} → Δ{texts[3]} = 0'
    return ' '.join(texts)


def clean(text):
    out = []
    for rawline in text.splitlines():
        s = rawline.strip()
        if not s:
            continue
        if re.match(r'^\[[^\]]*\]:', s):
            continue
        if re.match(r'^</?\w', s) or s.startswith('<!--'):
            continue
        if s.startswith('$$'):
            continue
        if '\\text' in s or '\\stackrel' in s or '\\int' in s:
            f = formula(s)
            if f:
                out.append(f)
            continue
        for alt in re.findall(r'alt="([^"]+)"', s):
            out.append(alt)
        if '<img' in s or '<div' in s:
            continue
        if set(s) <= set('-|: '):
            continue
        if s.startswith('|'):
            s = s.replace('|', ' ')
        s = strip_md(s)
        s = re.sub(r'^#+\s*', '', s)
        s = re.sub(r'^[-*]\s+', '', s)
        s = s.replace('\\', ' ')
        s = re.sub(r'[*`]', '', s)
        s = ''.join(ch for ch in s if keep(ch))
        s = re.sub(r'\s+', ' ', s).strip()
        if s:
            out.append(s)
    seen = set()
    res = []
    for l in out:
        if l not in seen:
            seen.add(l)
            res.append(l)
    return res


main_lines = clean(raw('main'))
master_lines = clean(raw('master'))
seen = set(main_lines)
master_only = [l for l in master_lines if l not in seen]

charset = set('mainmaster')
for l in main_lines + master_only:
    charset |= set(l)
task = {'main': main_lines, 'master_only': master_only, 'charset': ''.join(sorted(charset))}
with open(OUT, 'w') as f:
    json.dump(task, f, ensure_ascii=False, indent=1)
print(f'main lines: {len(main_lines)}   master-only lines: {len(master_only)}')
print(f'charset: {len(charset)} chars')
print('--- MAIN ---')
for l in main_lines:
    print(' |', l)
print('--- MASTER ONLY ---')
for l in master_only:
    print(' |', l)
