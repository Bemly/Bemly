"""2D finishing for the BEMLY logo: bloom, dust, optional sub-line, encode.

    python3 post.py RENDER_DIR OUT.mp4 [--sub STUDIOS] [--audio ref.mp4] [--still N out.png]

Reads the beauty_/mask_ PNG pairs written by build_scene.py.  Frames that
were not rendered are black before the first one and a hold of the last one
after it (the logo is static by then).
"""
import sys, os, json, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter, zoom

W, H = 1920, 1080


def to_lin(c):
    c = np.asarray(c, np.float32) / 255
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def to_srgb8(lin, rng):
    lin = np.clip(lin, 0, 1)
    s = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055) * 255
    s += rng.random(s.shape, dtype=np.float32) - 0.5        # dither: the halo is a long dark gradient
    return np.clip(np.rint(s), 0, 255).astype(np.uint8)


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def blur(a, sigma):
    """Gaussian blur; wide ones run on a reduced copy."""
    if sigma >= 12:
        k = 4
        small = a.reshape(H // k, k, W // k, k).mean((1, 3))
        return zoom(gaussian_filter(small, sigma / k, mode='constant'), k, order=1)
    return gaussian_filter(a, sigma, mode='constant')


# halo = sum of three gaussians of the glow mask, fitted to the reference's
# falloff (cyan next to the edge, deeper blue further out); linear RGB gains
HALO = [(3.5, (0.06, 0.55, 0.45)), (10.0, (0.03, 0.50, 1.80)), (26.0, (0.005, 0.10, 0.36))]
DUST = (0.10, 0.42, 1.0)


def halo_of(mask, gain=1.0):
    out = np.zeros((H, W, 3), np.float32)
    for sigma, col in HALO:
        b = blur(mask, sigma)
        for c in range(3):
            out[..., c] += b * (col[c] * gain)
    return out


class Dust:
    """Little blue squares drifting around the lockup while it glows."""

    def __init__(self, meta, cy, n=46, seed=7):
        r = np.random.default_rng(seed)
        ppu = meta['px_per_u']
        x0, x1 = W / 2 + meta['slots'][0] * ppu - 150, W / 2 + meta['slots'][-1] * ppu + 150
        self.x = r.uniform(x0, x1, n)
        self.y = cy + r.choice([-1, 1], n) * r.uniform(95, 250, n) * r.uniform(0.75, 1, n)
        close = r.random(n) < 0.25                       # a few sit between the letters
        self.y[close] = cy + r.uniform(-110, 110, close.sum())
        self.vx, self.vy = r.normal(0, 5, n), r.normal(-4, 5, n)     # px / s
        self.size = r.choice([3, 4, 4, 5, 5, 6], n)
        self.amp = r.uniform(0.45, 1.0, n) ** 1.3
        self.ph, self.fr = r.uniform(0, 6.28, n), r.uniform(1.5, 5.0, n)
        u = (self.x - x0) / (x1 - x0)                    # 0..1 left to right, follows the waves
        span = meta['stagger'] * (len(meta['slots']) - 1)
        self.t_in = meta['waves'][0] - 4 + u * span + r.uniform(0, 14, n)
        self.t_out = meta['waves'][3] - 4 + u * span + r.uniform(0, 9, n)
        self.fps = meta['fps']

    def draw(self, f):
        img = np.zeros((H, W), np.float32)
        a = smooth((f - self.t_in) / 5) * (1 - smooth((f - self.t_out) / 6))
        a = a * self.amp * (0.6 + 0.4 * np.sin(self.ph + self.fr * f / self.fps * 2))
        t = f / self.fps
        for i in np.nonzero(a > 0.004)[0]:
            x, y, s = self.x[i] + self.vx[i] * t, self.y[i] + self.vy[i] * t, self.size[i]
            xi, yi = int(np.floor(x)), int(np.floor(y))
            fx, fy = x - xi, y - yi
            for dx, dy, wgt in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
                xs, ys = xi + dx, yi + dy
                if 0 <= xs < W - s and 0 <= ys < H - s:
                    img[ys:ys + s, xs:xs + s] += a[i] * wgt
        return img


def subline(text, cy, width=506, cap=55):
    """Wide-tracked bold caps under the lockup -> coverage mask."""
    font = None
    for path, idx in (('/System/Library/Fonts/Avenir Next.ttc', 8), ('/System/Library/Fonts/Avenir Next.ttc', 0),
                      ('/System/Library/Fonts/Supplemental/Futura.ttc', 2), ('/System/Library/Fonts/Helvetica.ttc', 1)):
        try:
            font = ImageFont.truetype(path, 100, index=idx)
            if 'Heavy' in font.getname()[1] or 'Bold' in font.getname()[1]:
                break
        except OSError:
            continue
    size = 100 * cap / (font.getbbox('S')[3] - font.getbbox('S')[1])
    font = font.font_variant(size=size)
    adv = [font.getlength(ch) for ch in text]
    track = (width - sum(adv)) / max(1, len(text) - 1)
    im = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(im)
    x = W / 2 - width / 2
    top = font.getbbox('S')[1]
    for ch, a in zip(text, adv):
        d.text((x, cy - cap / 2 - top), ch, font=font, fill=255)
        x += a + track
    return np.asarray(im, np.float32) / 255


def load(render_dir, f, first, last):
    if f < first:
        return None
    f = min(f, last)
    b = np.asarray(Image.open(os.path.join(render_dir, 'beauty_%04d.png' % f)).convert('RGBA'))
    m = np.asarray(Image.open(os.path.join(render_dir, 'mask_%04d.png' % f)).convert('RGBA'))
    alpha = b[..., 3:].astype(np.float32) / 255
    return to_lin(b[..., :3]) * alpha, alpha[..., 0], to_lin(m[..., 0]) * (m[..., 3].astype(np.float32) / 255)


def main():
    argv = sys.argv[1:]
    render_dir, out = argv[0], argv[1]
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
    sub, audio = opt('--sub'), opt('--audio')
    meta = json.load(open(os.path.join(render_dir, 'meta.json')))
    have = sorted(int(n[7:11]) for n in os.listdir(render_dir) if n.startswith('beauty_'))
    first, last = have[0], have[-1]
    shift = -41 if sub else 0                    # with a sub-line the lockup sits higher, as in the reference
    cy = H / 2 + shift
    dust = Dust(meta, cy)
    sub_mask = subline(sub, cy + 146) if sub else None
    t_sub = meta['waves'][3] + 9.5               # sub-line fades in while the last wave lands
    rng = np.random.default_rng(1)

    def frame(f):
        img = np.zeros((H, W, 3), np.float32)
        got = load(render_dir, f, first, last)
        if got is None:
            return to_srgb8(img, rng)
        rgb, alpha, mask = (np.roll(a, shift, axis=0) for a in got)
        d = dust.draw(f)
        behind = halo_of(mask) + (d + 1.6 * blur(d, 2.5))[..., None] * np.array(DUST, np.float32)
        img = rgb + behind * (1 - alpha[..., None]) + halo_of(mask, 0.10) * alpha[..., None]
        if sub:
            a = smooth((f - t_sub) / 3.0)
            g = a * (1 - smooth((f - (t_sub + 6)) / 14.0))       # blue flash that dies down
            white = smooth((f - (t_sub + 1.5)) / 3.0)
            col = np.array([0.02, 0.22, 0.75], np.float32) * (1 - white) + white
            img = img * (1 - (sub_mask * a)[..., None]) + (sub_mask * a)[..., None] * col
            if g > 0.003:
                img += halo_of(sub_mask * g, 0.8) * (1 - sub_mask * a * white)[..., None]
        return to_srgb8(img, rng)

    if '--still' in argv:
        i = argv.index('--still')
        Image.fromarray(frame(int(argv[i + 1]))).save(argv[i + 2])
        return
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H),
           '-r', str(meta['fps']), '-i', '-']
    if audio:
        cmd += ['-i', audio, '-map', '0:v', '-map', '1:a', '-c:a', 'copy', '-shortest']
    cmd += ['-c:v', 'libx264', '-crf', '13', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-colorspace', 'bt709',
            '-color_primaries', 'bt709', '-color_trc', 'bt709', '-movflags', '+faststart', out]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    settled = max(last, dust.t_out.max() + 6, t_sub + 20) + 1    # nothing moves after this
    black, hold = frame(0).tobytes(), None
    for f in range(meta['frames']):
        if f < first:
            enc.stdin.write(black)
        elif f >= settled:
            hold = hold or frame(f).tobytes()
            enc.stdin.write(hold)
        else:
            enc.stdin.write(frame(f).tobytes())
    enc.stdin.close()
    enc.wait()


if __name__ == '__main__':
    main()
