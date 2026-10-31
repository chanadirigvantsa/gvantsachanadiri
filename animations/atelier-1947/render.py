"""Render the 10 s vertical animation: night facade -> through the lit window
-> the couture atelier.  Usage:

    python3 render.py [out_dir] [--frames a:b] [--preview]

Writes PNG frames to out_dir/frames and encodes out_dir/atelier-1947.mp4.
"""
import os
import sys
import subprocess
from multiprocessing import Pool

import numpy as np
from PIL import Image

from paint import Ctx, fbm, sstep
import exterior as ex
import interior as it

FPS = 24
DUR = 10.0
NF = int(FPS * DUR)
OUT_W, OUT_H = 1080, 1920
SS = 4 / 3                                 # supersampling
RW, RH = int(OUT_W * SS), int(OUT_H * SS)

PAPER = np.array([0.95, 0.91, 0.82], np.float32)

# ------------------------------------------------------------------ camera --
O0 = ex.OPEN_W / 16.9                    # opening width / frame width at t=0
O_PASS, T_PASS = 1.45, 6.6               # opening comfortably past the frame
S_PASS, S_END = 1.40, 1.66               # interior scale at the pass and at the end
R0 = 1.9                                 # interior/opening scale ratio at t=0
AIM = np.array([0.0, -(ex.OPEN_BOT + ex.OPEN_TOP) / 2 - 0.3])
C0 = np.array([0.0, -12.0])
Q = np.array([0.0, -0.02])               # picture point that sits on AIM
D0, TREE_DZ = 30.0, 6.0

_ts = np.linspace(0, DUR, 4001)
_dt = _ts[1] - _ts[0]
_ramp = sstep(0.0, 1.6, _ts)
_cum = np.concatenate([[0], np.cumsum((_ramp[1:] + _ramp[:-1]) / 2) * _dt])
_k_pass = np.searchsorted(_ts, T_PASS)
_v0 = np.log(O_PASS / O0) / _cum[_k_pass]
_logO = np.log(O0) + _v0 * _cum
_kS = (np.log(S_PASS) - np.log(R0 * O0)) / (np.log(O_PASS) - np.log(O0))
_vS_pass = _kS * _v0
# exponential slow-down after the pass so that S reaches S_END
_lam = 1.0
for _ in range(60):
    f = _vS_pass / _lam * (1 - np.exp(-_lam * (DUR - T_PASS)))
    _lam *= f / np.log(S_END / S_PASS)
_logS = np.where(_ts <= T_PASS, np.log(R0 * O0) + _kS * _v0 * _cum,
                 np.log(S_PASS) + _vS_pass / _lam * (1 - np.exp(-_lam * (_ts - T_PASS))))


def cam(t):
    O = float(np.exp(np.interp(t, _ts, _logO)))
    S = float(np.exp(np.interp(t, _ts, _logS)))
    Z = O * RW / ex.OPEN_W                       # px per metre on the facade
    g = 1 - sstep(0.4, 6.0, t)
    d = (AIM - C0) * (O0 * RW / ex.OPEN_W) * g   # aim's offset from frame centre, px
    d = -d                                       # aim sits below centre at the start
    C = AIM + d / Z
    aim_px = np.array([RW / 2, RH / 2]) - d
    return O, S, Z, C, aim_px


# -------------------------------------------------------------------- sky --

def make_sky():
    y = np.linspace(0, 1, RH, dtype=np.float32)[:, None, None]
    top = np.array([0.055, 0.07, 0.16], np.float32)
    bot = np.array([0.17, 0.20, 0.32], np.float32)
    sky = np.broadcast_to(top + (bot - top) * y ** 0.8, (RH, RW, 3)).copy()
    X, Y = np.meshgrid(np.arange(RW, dtype=np.float64), np.arange(RH, dtype=np.float64))
    n = fbm(X / 220, Y / 60, 77, 4)
    sky *= (0.9 + 0.2 * n)[..., None]
    # soft drifting cloud bands catching the moon
    clouds = np.clip(fbm(X / 500, Y / 90, 78, 5) * 1.8 - 0.95, 0, 1) * (1 - y[..., 0] * 1.2).clip(0, 1)
    sky += clouds[..., None] * np.array([0.22, 0.22, 0.26], np.float32)
    # moon
    mx, my, mr = RW * 0.66, RH * 0.045, RW * 0.032
    d = np.hypot(X - mx, Y - my)
    d2 = np.hypot(X - mx - mr * 0.45, Y - my + mr * 0.2)
    moon = np.clip((mr - d) / 2.0, 0, 1) * np.clip((d2 - mr * 0.9) / 2.0, 0, 1)
    halo = np.exp(-np.maximum(d - mr, 0) / (mr * 2.5)) * 0.18
    sky = sky + halo[..., None] * np.array([0.75, 0.68, 0.5], np.float32)
    sky = sky * (1 - moon[..., None]) + moon[..., None] * np.array([0.98, 0.90, 0.70], np.float32)
    rng = np.random.RandomState(2)
    for _ in range(40):
        sx, sy = rng.uniform(0, RW), rng.uniform(0, RH * 0.25)
        r = rng.uniform(1.0, 2.2)
        m = np.clip(1 - np.hypot(X - sx, Y - sy) / r, 0, 1)
        sky += m[..., None] * rng.uniform(0.3, 0.7) * np.array([1, 0.95, 0.8], np.float32)
    return sky.astype(np.float32)


# ------------------------------------------------------------------ paper --

def make_paper():
    X, Y = np.meshgrid(np.arange(OUT_W, dtype=np.float64), np.arange(OUT_H, dtype=np.float64))
    fine = fbm(X / 1.3, Y / 1.3, 11, 2)
    fib = fbm(X / 9, Y / 2.2, 12, 3)
    mott = fbm(X / 140, Y / 140, 13, 4)
    grain = 0.94 + 0.05 * fine + 0.035 * fib + 0.03 * mott
    # vignette that softens into unpainted cream paper at the deckled edges
    u = X / OUT_W - 0.5
    v = Y / OUT_H - 0.5
    r = np.hypot(u * 1.15, v)
    vig = 1 - 0.28 * sstep(0.3, 0.75, r)
    edge = np.minimum.reduce([X, Y, OUT_W - 1 - X, OUT_H - 1 - Y]) / OUT_W
    rag = edge + 0.012 * (fbm(X / 30, Y / 30, 14, 3) - 0.5)
    paper_show = 1 - sstep(0.004, 0.028, rag)
    return (grain * vig).astype(np.float32), paper_show.astype(np.float32)


_SKY = None
_PAPER = None


def frame(i):
    global _SKY, _PAPER
    if _SKY is None:
        _SKY = make_sky()
        _PAPER = make_paper()
    t = i / FPS
    O, S, Z, C, aim_px = cam(t)
    out = None
    draw_ext = O < 1.62
    if draw_ext:
        hw, hh = RW / 2 / Z, RH / 2 / Z
        fc = Ctx(C[0] - hw, C[1] - hh, C[0] + hw, C[1] + hh, RW, RH)
        ex.facade(fc, t)
        hole = fc.hole
    else:
        hole = np.ones((RH, RW), np.float32)

    # interior, rendered only where the window opening shows it
    ys, xs = np.nonzero(hole > 0.001)
    interior = None
    if len(xs):
        bx0, bx1 = max(0, xs.min() - 2), min(RW, xs.max() + 3)
        by0, by1 = max(0, ys.min() - 2), min(RH, ys.max() + 3)
        sp = S * RW
        wx0 = Q[0] + (bx0 - aim_px[0]) / sp
        wy0 = Q[1] + (by0 - aim_px[1]) / sp
        ic = Ctx(wx0, wy0, wx0 + (bx1 - bx0) / sp, wy0 + (by1 - by0) / sp, bx1 - bx0, by1 - by0)
        it.draw(ic, t)
        interior = np.zeros((RH, RW, 3), np.float32)
        img = ic.img
        # seen from afar the lit window reads as warm glowing glass
        glow = 0.55 * (1 - sstep(0.12, 0.95, O))
        if glow > 0:
            img = img * (1 - glow) + glow * np.array([1.0, 0.82, 0.52], np.float32)
        interior[by0:by1, bx0:bx1] = img

    if draw_ext:
        out = _SKY.copy()
        if interior is not None:
            out = out * (1 - hole[..., None]) + interior * hole[..., None]
        out = out * (1 - fc.alpha[..., None]) + fc.img
        D = D0 * O0 / O
        if D - TREE_DZ > 0.4:
            Zt = Z * D / (D - TREE_DZ)
            hw, hh = RW / 2 / Zt, RH / 2 / Zt
            tc = Ctx(C[0] - hw, C[1] - hh, C[0] + hw, C[1] + hh, RW, RH)
            ex.trees(tc)
            out = out * (1 - tc.alpha[..., None]) + tc.img
    else:
        out = interior

    im = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
    im = im.resize((OUT_W, OUT_H), Image.LANCZOS)
    a = np.asarray(im, np.float32) / 255
    grain, paper_show = _PAPER
    a = a * grain[..., None]
    a = a * (1 - paper_show[..., None]) + PAPER * paper_show[..., None]
    # gentle warm grade and lifted blacks, like gouache on cream stock
    a = 0.035 * PAPER + a * 0.955
    fade = sstep(0.0, 0.6, t)
    a = a * fade + (1 - fade) * np.array([0.06, 0.07, 0.14], np.float32)
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))


def work(args):
    i, d = args
    path = os.path.join(d, f'f{i:04d}.png')
    frame(i).save(path)
    return i


if __name__ == '__main__':
    out_dir = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'out'
    fr = range(NF)
    for a in sys.argv:
        if a.startswith('--frames='):
            lo, hi = a.split('=')[1].split(':')
            fr = range(int(lo), int(hi))
    fdir = os.path.join(out_dir, 'frames')
    os.makedirs(fdir, exist_ok=True)
    with Pool(os.cpu_count()) as p:
        for i in p.imap_unordered(work, [(i, fdir) for i in fr]):
            print('frame', i, flush=True)
    if '--no-encode' not in sys.argv:
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS),
                        '-i', os.path.join(fdir, 'f%04d.png'), '-c:v', 'libx264', '-preset', 'slow',
                        '-crf', '17', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                        os.path.join(out_dir, 'atelier-1947.mp4')], check=True)
