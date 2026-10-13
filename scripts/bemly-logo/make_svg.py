"""Animated, self-contained SVG of the BEMLY logo (for a GitHub README).

    python3 make_svg.py IDPASS_DIR OUT.svg [--hold 6] [--pre 0.75] [--bg '#000'|none] [--once]

No script, no external files: every distinct pose of every gizmo is traced
into flat-shaded paths, CSS keyframes flip between them at 30 fps, and one
SVG filter grows the blue halo out of whatever is currently blue.
IDPASS_DIR comes from `build_scene.py --idpass`.
"""
import sys, os, json
from math import ceil
import numpy as np
from PIL import Image
from contourpy import contour_generator

FPS = 30
TONES = [(0.13, 0.24), (0.40, 0.54), (0.68, 0.86)]     # (depth threshold, depth the band is coloured as)
BASE_T = 0.04
WHITE_RAMP = [(0.0, (255, 255, 255)), (0.2, (244, 244, 244)), (1.0, (226, 226, 226))]   # neutral: must not trip the halo
GLOW_RAMP = [(0.0, (228, 243, 255)), (0.3, (214, 235, 255)), (0.55, (150, 205, 255)),
             (0.8, (40, 140, 252)), (1.0, (10, 90, 230))]
# halo layers: (blur radius, linear-light RGB gain); post.py's fit, a touch stronger since READMEs show it smaller
HALO = [(3.5, (0.06, 0.55, 0.45)), (10.0, (0.03, 0.55, 2.10)), (26.0, (0.006, 0.13, 0.46))]


def to_lin(c):
    c = np.asarray(c, np.float64) / 255
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def to_hex(lin):
    lin = np.clip(lin, 0, 1)
    s = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)
    r, g, b = (int(round(v * 255)) for v in s)
    h = '%02x%02x%02x' % (r, g, b)
    return '#' + (h[0] + h[2] + h[4] if h[0] == h[1] and h[2] == h[3] and h[4] == h[5] else h)


def ramp(stops, t):
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        if t <= p1:
            k = (t - p0) / (p1 - p0)
            return to_lin(c0) * (1 - k) + to_lin(c1) * k
    return to_lin(stops[-1][1])


def colour(t, glow, flat):
    lit = ramp(WHITE_RAMP, t) * (1 - glow) + ramp(GLOW_RAMP, t) * glow
    return to_hex(lit * (1 - flat) + flat)


def simplify(pts, tol):
    """Douglas-Peucker on a closed ring (first point not repeated)."""
    n = len(pts)
    if n < 8:
        return pts
    far = int(np.argmax(((pts - pts[0]) ** 2).sum(1)))
    keep = np.zeros(n + 1, bool)
    ring = np.vstack([pts, pts[:1]])
    keep[[0, far, n]] = True
    stack = [(0, far), (far, n)]
    while stack:
        a, b = stack.pop()
        if b - a < 2:
            continue
        seg = ring[b] - ring[a]
        rel = ring[a + 1:b] - ring[a]
        ln = np.hypot(*seg)
        d = np.abs(rel[:, 0] * seg[1] - rel[:, 1] * seg[0]) / ln if ln > 1e-9 else np.hypot(rel[:, 0], rel[:, 1])
        i = int(np.argmax(d))
        if d[i] > tol:
            m = a + 1 + i
            keep[m] = True
            stack += [(a, m), (m, b)]
    return ring[:-1][keep[:-1]]


def trace(mask, ss, tol, min_area=4.0):
    """bool mask at ss x resolution -> SVG path data in 1/10 px units ('' if empty)."""
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return ''
    x0, x1 = xs.min() // ss - 1, xs.max() // ss + 2
    y0, y1 = ys.min() // ss - 1, ys.max() // ss + 2
    h, w = mask.shape
    big = np.zeros(((y1 - y0) * ss, (x1 - x0) * ss), np.float32)
    sy0, sx0 = max(0, y0 * ss), max(0, x0 * ss)
    sub = mask[sy0:min(h, y1 * ss), sx0:min(w, x1 * ss)]
    big[sy0 - y0 * ss:sy0 - y0 * ss + sub.shape[0], sx0 - x0 * ss:sx0 - x0 * ss + sub.shape[1]] = sub
    cov = big.reshape(y1 - y0, ss, x1 - x0, ss).mean((1, 3))
    out = []
    for line in contour_generator(z=cov).lines(0.5):
        if len(line) < 4 or not np.allclose(line[0], line[-1]):
            continue
        p = line[:-1] + (x0 + 0.5, y0 + 0.5)
        if abs(np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1])) / 2 < min_area:
            continue
        q = np.rint(simplify(p, tol) * 10).astype(int)
        q = q[np.any(q != np.roll(q, 1, axis=0), axis=1)]
        if len(q) < 3:
            continue
        d = np.diff(q, axis=0)
        s = 'M%d %d' % tuple(q[0]) + 'l'
        nums = [str(v) for v in d.reshape(-1)]
        s += nums[0] + ''.join(v if v[0] == '-' else ' ' + v for v in nums[1:]) + 'z'
        out.append(s)
    return ''.join(out)


def main():
    argv = sys.argv[1:]
    src, out = argv[0], argv[1]
    opt = lambda k, d: argv[argv.index(k) + 1] if k in argv else d
    hold, pre, bg, once = float(opt('--hold', 6)), float(opt('--pre', 0.75)), opt('--bg', '#000'), '--once' in argv
    meta = json.load(open(os.path.join(src, 'meta.json')))
    W, H, ss, first, last = meta['width'], meta['height'], meta['ss'], meta['first'], meta['last']
    pre_f = round(pre * FPS)                       # extra time on the katakana before the first wave
    fade_in, fade_out = 8, 10
    total = (last - first) + pre_f + round(hold * FPS) + fade_out
    svg_f = lambda f: 0 if f <= first else f - first + pre_f
    dur = total / FPS

    cache = {}

    def frame(f):
        if f not in cache:
            cache.clear()
            a = np.asarray(Image.open(os.path.join(src, 'id_%04d.png' % f)).convert('RGBA'))
            lin = to_lin(a[..., :2])
            gid = np.where(a[..., 3] > 127, np.rint(lin[..., 0] * 6).astype(int) - 1, -1)
            cache[f] = (gid, lin[..., 1])
        return cache[f]

    # ---- shots: one per distinct state of one gizmo -------------------------
    shots = []
    for k, states in enumerate(meta['states']):
        f = first
        while f <= last:
            g = f
            while g < last and states[g + 1] == states[f]:
                g += 1
            shots.append((k, f, g + 1 if g < last else None))
            f = g + 1
    shots.sort(key=lambda s: (s[1], s[0]))

    groups, lengths = [], set()
    for k, f, f_end in shots:
        glow, flat, _ = meta['states'][k][f]
        a, b = svg_f(f), (total if f_end is None else svg_f(f_end))
        length = b - a
        gid, t = frame(f)
        sil = gid == k
        tol = 0.12 if length >= 3 else 0.4
        paths = [(trace(sil, ss, tol), colour(BASE_T, glow, flat))]
        if flat < 0.999:
            for thr, rep in TONES:
                c = colour(rep, glow, flat)
                d = trace(sil & (t > thr), ss, tol) if c != paths[-1][1] else ''
                if d:
                    paths.append((d, c))
        body = ''.join('<path fill="%s" d="%s"/>' % (c, d) for d, c in paths if d)
        cls = 'z' if once and f_end is None else 'h%d' % length      # play-once: the last pose stays up
        if cls != 'z':
            lengths.add(length)
        delay = '' if a == 0 else ' style="animation-delay:%ss"' % ('%.4f' % (a / FPS)).rstrip('0').rstrip('.')
        groups.append('<g class="f %s"%s>%s</g>' % (cls, delay, body))

    # ---- dust ----------------------------------------------------------------
    r = np.random.default_rng(7)
    n = 40
    waves = [svg_f(round(w)) for w in meta['waves']]
    span = meta['stagger'] * (len(meta['slots']) - 1)
    dust, dust_css = [], []
    for i in range(n):
        x = r.uniform(40, W - 40)
        y = H / 2 + r.choice([-1, 1]) * r.uniform(98, H / 2 - 14) if r.random() > 0.22 else H / 2 + r.uniform(-100, 100)
        u = x / W
        t_in = waves[0] - 4 + u * span + r.uniform(0, 14)
        t_out = waves[3] - 4 + u * span + r.uniform(0, 9)
        size, amp = r.choice([3, 4, 4, 5, 5, 6]), r.uniform(0.45, 1.0) ** 1.3
        dx, dy = r.normal(0, 5) * dur, r.normal(-4, 5) * dur
        pc = lambda fr: '%.3f%%' % (100 * fr / total)
        keys = ['0%%{opacity:0;transform:translate(0,0)}', '%s{opacity:0}' % pc(t_in)]
        tt, flick = t_in + 5, 1.0
        while tt < t_out:
            keys.append('%s{opacity:%.2f}' % (pc(tt), amp * flick))
            tt += r.uniform(6, 14)
            flick = r.uniform(0.35, 1.0)
        keys += ['%s{opacity:%.2f}' % (pc(t_out), amp * flick), '%s{opacity:0}' % pc(t_out + 6),
                 '100%%{opacity:0;transform:translate(%.0fpx,%.0fpx)}' % (dx, dy)]
        dust_css.append('@keyframes d%d{%s}' % (i, ''.join(keys).replace('%%', '%')))
        dust.append('<g style="animation-name:d%d"><rect x="%.0f" y="%.0f" width="%d" height="%d"/>'
                    '<rect x="%.1f" y="%.1f" width="%d" height="%d" opacity=".25"/></g>'
                    % (i, x, y, size, size, x - size / 2, y - size / 2, size * 2, size * 2))

    # ---- assemble --------------------------------------------------------------
    it = '1' if once else 'infinite'
    css = ['.f{opacity:0;animation:0s step-end %s;animation-duration:%.4fs}' % (it, dur)]
    for L in sorted(lengths):
        if L >= total:
            css.append('.h%d{opacity:1;animation:none}' % L)
        else:
            css.append('@keyframes h%d{0%%{opacity:1}%.4f%%{opacity:0}}.h%d{animation-name:h%d}'
                       % (L, min(100, ceil(1e4 * 100 * L / total) / 1e4), L, L))
    if once:
        css.append('@keyframes z{0%,to{opacity:1}}.z{animation-name:z;animation-fill-mode:forwards}')
    css.append('.d g{opacity:0;animation:0s linear %s;animation-duration:%.4fs}' % (it, dur))
    css += dust_css
    if not once:
        css.append('@keyframes a{0%%{opacity:0}%.3f%%,%.3f%%{opacity:1}100%%{opacity:0}}.a{animation:a %.4fs linear infinite}'
                   % (100 * fade_in / total, 100 * (total - fade_out) / total, dur))
    css = ''.join(css)

    k_mask = 1 / (1.0 - float(to_lin(GLOW_RAMP[0][1][0])))       # alpha = how blue (B - R, linear) the pixel is
    fx = ['<filter id="g" filterUnits="userSpaceOnUse" x="0" y="0" width="%d" height="%d">' % (W, H),
          '<feColorMatrix in="SourceGraphic" values="0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 %.3f 0 %.3f 0 0"/>' % (-k_mask, k_mask),
          '<feComposite in2="SourceAlpha" operator="in" result="m"/>']
    for i, (sigma, c) in enumerate(HALO):
        m = max(c)
        fx.append('<feGaussianBlur in="m" stdDeviation="%g"/>' % sigma)
        fx.append('<feColorMatrix values="0 0 0 0 %.3f 0 0 0 0 %.3f 0 0 0 0 %.3f 0 0 0 %.3f 0" result="h%d"/>'
                  % (c[0] / m, c[1] / m, c[2] / m, m, i))
    fx += ['<feComposite in="h0" in2="h1" operator="arithmetic" k2="1" k3="1"/>',
           '<feComposite in2="h2" operator="arithmetic" k2="1" k3="1" result="h"/>',
           '<feMerge><feMergeNode in="h"/><feMergeNode in="SourceGraphic"/></feMerge></filter>']

    svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-label="BEMLY">'
           % (W, H, W, H),
           '<title>BEMLY</title><style>%s</style><defs>%s</defs>' % (css, ''.join(fx))]
    if bg != 'none':
        svg.append('<rect width="%d" height="%d" rx="16" fill="%s"/>' % (W, H, bg))
    svg.append('<g class="a"><g class="d" fill="%s">%s</g>' % (to_hex(np.array([0.10, 0.42, 1.0])), ''.join(dust)))
    svg.append('<g filter="url(#g)"><g transform="scale(.1)">%s</g></g></g></svg>' % ''.join(groups))
    with open(out, 'w') as fh:
        fh.write('\n'.join(svg))
    print('%s: %d shots, %.1f s loop, %.0f kB' % (out, len(groups), dur, os.path.getsize(out) / 1024))


if __name__ == '__main__':
    main()
