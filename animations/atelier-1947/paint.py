"""Tiny procedural 'gouache and ink' painting toolkit.

Everything is drawn in world coordinates (x right, y down) into a Ctx that
maps a world rectangle onto a pixel canvas, so the same scene can be painted
at any camera position and zoom with consistent texture.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


# ---------------------------------------------------------------- noise ----

def _hash(ix, iy, seed):
    h = (ix.astype(np.int64) * 374761393 + iy.astype(np.int64) * 668265263
         + seed * 1013904223) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 0xFFFFFF).astype(np.float32) / float(0xFFFFFF)


def vnoise(x, y, seed=0):
    ix = np.floor(x)
    iy = np.floor(y)
    fx = (x - ix).astype(np.float32)
    fy = (y - iy).astype(np.float32)
    ix = ix.astype(np.int64)
    iy = iy.astype(np.int64)
    ux = fx * fx * (3 - 2 * fx)
    uy = fy * fy * (3 - 2 * fy)
    a = _hash(ix, iy, seed)
    b = _hash(ix + 1, iy, seed)
    c = _hash(ix, iy + 1, seed)
    d = _hash(ix + 1, iy + 1, seed)
    return (a + (b - a) * ux) * (1 - uy) + (c + (d - c) * ux) * uy


def fbm(x, y, seed=0, octaves=4):
    tot = np.zeros_like(x, dtype=np.float32)
    amp, norm, f = 1.0, 0.0, 1.0
    for o in range(octaves):
        tot += amp * vnoise(x * f, y * f, seed + 17 * o)
        norm += amp
        amp *= 0.5
        f *= 2.03
    return tot / norm


def noise1(t, seed=0):
    """Smooth 1-D noise in [-1, 1] for scalar or array t."""
    t = np.asarray(t, dtype=np.float64)
    return vnoise(t, np.full_like(t, 0.5), seed) * 2 - 1


# ---------------------------------------------------------------- curves ---

def smooth(pts, n=10, closed=False):
    """Catmull-Rom spline through pts."""
    p = np.asarray(pts, dtype=np.float64)
    if len(p) < 3:
        return p
    if closed:
        p = np.vstack([p[-1:], p, p[:2]])
    else:
        p = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    out = []
    t = np.linspace(0, 1, n, endpoint=False)[:, None]
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        seg = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2
                     + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)
        out.append(seg)
    if not closed:
        out.append(p[-2][None])
    return np.vstack(out)


def ellipse(cx, cy, rx, ry, n=48, a0=0, a1=2 * np.pi, rot=0.0):
    a = np.linspace(a0, a1, n)
    x, y = rx * np.cos(a), ry * np.sin(a)
    c, s = np.cos(rot), np.sin(rot)
    return np.stack([cx + x * c - y * s, cy + x * s + y * c], 1)


def rect(x0, y0, x1, y1):
    return np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], dtype=np.float64)


def xform(pts, ox=0, oy=0, s=1.0, rot=0.0, flipy=False):
    p = np.asarray(pts, dtype=np.float64).copy()
    if flipy:
        p[:, 1] = -p[:, 1]
    c, sn = np.cos(rot), np.sin(rot)
    x = p[:, 0] * c - p[:, 1] * sn
    y = p[:, 0] * sn + p[:, 1] * c
    return np.stack([ox + x * s, oy + y * s], 1)


def lerp(a, b, t):
    return a + (b - a) * t


def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# ----------------------------------------------------------------- canvas --

class Ctx:
    def __init__(self, x0, y0, x1, y1, W, H, bg=(0, 0, 0), alpha0=0.0):
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1
        self.W, self.H = W, H
        self.s = float(W / (x1 - x0))
        self.img = np.empty((H, W, 3), np.float32)
        self.img[:] = bg
        self.alpha = np.full((H, W), alpha0, np.float32)
        self.hole = np.zeros((H, W), np.float32)

    # pixel <-> world
    def px(self, pts):
        p = np.asarray(pts, dtype=np.float64)
        return np.stack([(p[:, 0] - self.x0) * self.s, (p[:, 1] - self.y0) * self.s], 1)

    def world_grid(self, bx0, by0, bx1, by1):
        xs = self.x0 + (np.arange(bx0, bx1) + 0.5) / self.s
        ys = self.y0 + (np.arange(by0, by1) + 0.5) / self.s
        return np.meshgrid(xs.astype(np.float64), ys.astype(np.float64))

    def bbox(self, P, pad=1):
        bx0 = int(max(0, np.floor(P[:, 0].min()) - pad))
        by0 = int(max(0, np.floor(P[:, 1].min()) - pad))
        bx1 = int(min(self.W, np.ceil(P[:, 0].max()) + pad))
        by1 = int(min(self.H, np.ceil(P[:, 1].max()) + pad))
        if bx1 <= bx0 or by1 <= by0:
            return None
        return bx0, by0, bx1, by1

    def visible(self, pts, margin=0):
        p = np.asarray(pts)
        return not (p[:, 0].max() < self.x0 - margin or p[:, 0].min() > self.x1 + margin or
                    p[:, 1].max() < self.y0 - margin or p[:, 1].min() > self.y1 + margin)

    def mask(self, pts, blur_w=0.0, pad=1):
        P = self.px(pts)
        bp = int(blur_w * self.s * 2.5) + pad
        b = self.bbox(P, bp)
        if b is None:
            return None, None
        bx0, by0, bx1, by1 = b
        # keep huge coordinates manageable for PIL
        Q = P - [bx0, by0]
        lim = 4 * max(self.W, self.H)
        Q = np.clip(Q, -lim, lim)
        im = Image.new('L', (bx1 - bx0, by1 - by0), 0)
        ImageDraw.Draw(im).polygon([tuple(q) for q in Q], fill=255)
        if blur_w > 0:
            r = blur_w * self.s
            if r > 0.6:
                im = im.filter(ImageFilter.GaussianBlur(float(min(r, 120))))
        m = np.asarray(im, np.float32) / 255.0
        return m, b

    def fill(self, pts, color, a=1.0, tex=0.0, cvar=0.0, tsc=(1.0, 1.0), seed=0,
             grad=None, blur=0.0, mode='over', octaves=4):
        if len(pts) < 3:
            return
        m, b = self.mask(pts, blur)
        if m is None:
            return
        bx0, by0, bx1, by1 = b
        m = m * a
        if not m.any():
            return
        need_w = tex or cvar or grad is not None
        if need_w:
            X, Y = self.world_grid(bx0, by0, bx1, by1)
        col = np.asarray(color, np.float32)
        if grad is not None:
            col = grad(X, Y).astype(np.float32)
        if tex or cvar:
            n = fbm(X / tsc[0], Y / tsc[1], seed, octaves)
            if tex:
                m = m * (1 - tex * np.clip(n * 1.6 - 0.3, 0, 1))
            if cvar:
                col = col * (1 + cvar * (n - 0.5) * 2)[..., None]
        if col.ndim == 1:
            col = np.broadcast_to(col, m.shape + (3,))
        self._comp(b, m, col, mode)

    def _comp(self, b, m, col, mode):
        bx0, by0, bx1, by1 = b
        I = self.img[by0:by1, bx0:bx1]
        mm = m[..., None]
        if mode == 'over':
            I[:] = I * (1 - mm) + col * mm
            A = self.alpha[by0:by1, bx0:bx1]
            A[:] = A + m * (1 - A)
        elif mode == 'mul':
            I[:] = I * (1 - mm + col * mm)
        elif mode == 'add':
            I[:] = I + col * mm
        elif mode == 'screen':
            I[:] = 1 - (1 - I) * (1 - col * mm)

    def cut(self, pts):
        """Punch a hole (alpha 0) and mark it as a window opening."""
        m, b = self.mask(pts)
        if m is None:
            return
        bx0, by0, bx1, by1 = b
        A = self.alpha[by0:by1, bx0:bx1]
        A[:] = A * (1 - m)
        I = self.img[by0:by1, bx0:bx1]
        I[:] = I * (1 - m)[..., None]
        Hh = self.hole[by0:by1, bx0:bx1]
        Hh[:] = np.maximum(Hh, m)

    def stroke(self, pts, w, color, a=1.0, taper=(0.3, 0.3), closed=False, wob=0.25,
               seed=0, n=None, tex=0.0, mode='over'):
        """Ink line with pressure-like width variation."""
        p = np.asarray(pts, dtype=np.float64)
        if closed:
            p = np.vstack([p, p[:1]])
        if len(p) < 2:
            return
        if not self.visible(p, margin=w * 3):
            return
        # skip lines thinner than ~0.25px (they vanish anyway)
        if w * self.s < 0.25:
            a = a * w * self.s / 0.25
            w = 0.25 / self.s
        d = np.diff(p, axis=0)
        L = np.hypot(d[:, 0], d[:, 1])
        keep = np.concatenate([[True], L > 1e-9])
        p = p[keep]
        if len(p) < 2:
            return
        d = np.gradient(p, axis=0)
        nrm = np.stack([-d[:, 1], d[:, 0]], 1)
        nrm /= np.maximum(np.hypot(nrm[:, 0], nrm[:, 1]), 1e-12)[:, None]
        seg = np.hypot(*np.diff(p, axis=0).T)
        s = np.concatenate([[0], np.cumsum(seg)])
        tot = max(s[-1], 1e-9)
        u = s / tot
        prof = np.ones_like(u)
        if taper[0] > 0:
            prof *= np.clip(u / taper[0], 0, 1) ** 0.6 * 0.85 + 0.15
        if taper[1] > 0:
            prof *= np.clip((1 - u) / taper[1], 0, 1) ** 0.6 * 0.85 + 0.15
        if wob:
            prof *= 1 + wob * noise1(s / (w * 18 + 1e-9) + seed * 3.1, seed)
        hw = 0.5 * w * prof
        left = p + nrm * hw[:, None]
        right = p - nrm * hw[:, None]
        poly = np.vstack([left, right[::-1]])
        self.fill(poly, color, a, tex=tex, tsc=(w * 6, w * 6), seed=seed, mode=mode)

    def radial(self, cx, cy, r, color, a=1.0, mode='add', power=2.0, clip=None):
        P = self.px([[cx - r, cy - r], [cx + r, cy + r]])
        b = self.bbox(P)
        if b is None:
            return
        X, Y = self.world_grid(*b)
        d = np.hypot(X - cx, Y - cy) / r
        m = (np.clip(1 - d, 0, 1) ** power).astype(np.float32) * a
        if clip is not None:
            m = m * clip[b[1]:b[3], b[0]:b[2]]
        col = np.broadcast_to(np.asarray(color, np.float32), m.shape + (3,))
        self._comp(b, m, col, mode)

    def grad_all(self, fn, mode='mul'):
        X, Y = self.world_grid(0, 0, self.W, self.H)
        col = fn(X, Y).astype(np.float32)
        if mode == 'mul':
            self.img *= col
        elif mode == 'add':
            self.img += col
