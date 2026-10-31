"""Night facade of a Haussmann building, Paris 1947.

World units are metres; x to the right, y = -elevation (y down).
"""
import numpy as np
from paint import smooth, ellipse, rect, noise1, sstep

INK = (0.12, 0.12, 0.155)
STONE = (0.33, 0.36, 0.47)
STONE_HI = (0.50, 0.52, 0.61)
STONE_SH = (0.18, 0.20, 0.30)
WIN = (0.065, 0.085, 0.155)
ZINC = (0.20, 0.235, 0.335)
GOLD = (0.90, 0.72, 0.40)
WARM = (1.0, 0.80, 0.50)
CREAM = (0.93, 0.89, 0.80)

BAYS = [-7.2, -3.6, 0.0, 3.6, 7.2]
FX0, FX1 = -9.0, 9.0

# lit window opening (the one we fly through)
OPEN_W = 1.4
OPEN_BOT, OPEN_TOP = 6.6, 9.6          # elevations
OPEN_RECT = rect(-OPEN_W / 2, -OPEN_TOP, OPEN_W / 2, -OPEN_BOT)


def E(h):
    """elevation -> y"""
    return -h


def scroll(cx, cy, r0, r1, a0, a1, n=40, flip=1):
    a = np.linspace(a0, a1, n)
    r = np.linspace(r0, r1, n)
    return np.stack([cx + flip * r * np.cos(a), cy + r * np.sin(a)], 1)


# ------------------------------------------------------------- railing -----

def railing(c, x0, x1, elev, h, lit_glow=False, panel=0.56, seed=0):
    yb, yt = E(elev), E(elev + h)
    if not c.visible(rect(x0, yt, x1, yb), margin=0.2):
        return
    w = 0.024
    rim = (0.95, 0.76, 0.45)
    n = max(1, int(round((x1 - x0) / panel)))
    pw = (x1 - x0) / n
    lines = []
    lines.append(np.array([[x0, yt], [x1, yt]]))
    lines.append(np.array([[x0, yt + 0.05], [x1, yt + 0.05]]))
    lines.append(np.array([[x0, yb - 0.03], [x1, yb - 0.03]]))
    for i in range(n + 1):
        x = x0 + i * pw
        lines.append(np.array([[x, yt], [x, yb]]))
    scrolls = []
    for i in range(n):
        px0 = x0 + i * pw
        cx = px0 + pw / 2
        cy = (yt + 0.05 + yb - 0.03) / 2
        hh = (yb - 0.03) - (yt + 0.05)
        r = min(pw, hh) * 0.27
        # central ring
        scrolls.append(ellipse(cx, cy, r * 0.42, r * 0.42, 28))
        for f in (-1, 1):
            # S-curves from the ring out to the corners
            scrolls.append(scroll(cx + f * r * 1.15, cy - r * 0.55, r * 0.15, r * 0.75,
                                  -np.pi * 0.2, np.pi * 1.55, 36, flip=f))
            scrolls.append(scroll(cx + f * r * 1.15, cy + r * 0.55, r * 0.15, r * 0.75,
                                  np.pi * 0.2, -np.pi * 1.55, 36, flip=f))
            # little leaf spears up and down
            scrolls.append(np.array([[cx + f * pw * 0.42, yt + 0.05], [cx + f * pw * 0.42, yb - 0.03]]))
    for k, L in enumerate(lines):
        c.stroke(L, w * 1.5, INK, taper=(0, 0), wob=0.1, seed=seed + k)
    for k, L in enumerate(scrolls):
        c.stroke(L, w, INK, taper=(0.15, 0.15), wob=0.15, seed=seed + 50 + k)
    if lit_glow:
        # gold rim light on the iron in front of the lit window
        for k, L in enumerate(scrolls + lines):
            if L[:, 0].max() < -1.1 or L[:, 0].min() > 1.1:
                continue
            c.stroke(L + [0.004, -0.006], w * 0.35, rim, a=0.55, taper=(0.3, 0.3), wob=0.4,
                     seed=seed + 200 + k)


# ------------------------------------------------------------- windows -----

def dark_window(c, cx, e0, w, h, seed=0):
    x0, x1 = cx - w / 2, cx + w / 2
    y0, y1 = E(e0 + h), E(e0)
    c.fill(rect(x0, y0, x1, y1), WIN, tex=0.0, cvar=0.25, tsc=(0.4, 1.2), seed=seed)
    # a cool moon reflection streak
    c.fill(np.array([[x0 + w * 0.15, y0], [x0 + w * 0.42, y0], [x0 + w * 0.05, y1], [x0, y1],
                     [x0, y0 + h * 0.6]]), (0.30, 0.34, 0.48), a=0.22, tex=0.7, tsc=(0.2, 0.5),
           seed=seed + 1)
    # casement frame
    for xx in (cx,):
        c.stroke([[xx, y0], [xx, y1]], 0.05, (0.20, 0.22, 0.31), taper=(0, 0), wob=0.1)
    for fr in (0.33, 0.62):
        yy = lerp_(y0, y1, fr)
        c.stroke([[x0, yy], [x1, yy]], 0.035, (0.20, 0.22, 0.31), taper=(0, 0), wob=0.1)
    c.stroke(rect(x0, y0, x1, y1), 0.035, INK, closed=True, taper=(0, 0), wob=0.2, seed=seed)


def lerp_(a, b, t):
    return a + (b - a) * t


def surround(c, cx, e0, w, h, sw=0.2, seed=0, warm=0.0):
    x0, x1 = cx - w / 2 - sw, cx + w / 2 + sw
    y0, y1 = E(e0 + h + sw), E(e0)
    col = STONE_HI
    c.fill(rect(x0, y0, x1, y1), col, a=0.55, cvar=0.12, tsc=(0.3, 0.9), seed=seed)
    c.stroke(rect(x0, y0, x1, y1), 0.03, INK, closed=True, taper=(0.05, 0.05), wob=0.3,
             seed=seed + 3)
    # crossettes / ears at the top corners
    c.fill(rect(x0 - 0.08, y0, x0, y0 + 0.28), col, a=0.55)
    c.fill(rect(x1, y0, x1 + 0.08, y0 + 0.28), col, a=0.55)
    # inner shadow (reveal)
    c.fill(rect(cx - w / 2, E(e0 + h), cx - w / 2 + 0.07, E(e0)), STONE_SH, a=0.6)
    c.fill(rect(cx - w / 2, E(e0 + h), cx + w / 2, E(e0 + h) + 0.06), STONE_SH, a=0.6)


def hood(c, cx, etop, w, kind, seed=0):
    """Cornice / pediment over a window."""
    x0, x1 = cx - w / 2 - 0.42, cx + w / 2 + 0.42
    y = E(etop)
    c.fill(rect(x0 + 0.05, y, x1 - 0.05, y + 0.22), STONE_SH, a=0.55, blur=0.04)
    slab = rect(x0, y - 0.18, x1, y)
    c.fill(slab, STONE_HI, a=0.8, cvar=0.1, seed=seed)
    c.stroke(slab, 0.028, INK, closed=True, taper=(0, 0), wob=0.3, seed=seed)
    c.stroke([[x0, y - 0.18], [x1, y - 0.18]], 0.03, (0.70, 0.71, 0.76), a=0.6, taper=(0.2, 0.2))
    if kind == 'tri':
        tri = np.array([[x0, y - 0.18], [cx, y - 0.95], [x1, y - 0.18]])
        c.fill(tri, STONE, a=1.0, cvar=0.12, seed=seed + 1)
        c.stroke(tri, 0.03, INK, taper=(0.1, 0.1), wob=0.3, seed=seed + 2)
        c.stroke(np.array([[x0 + 0.25, y - 0.24], [cx, y - 0.8], [x1 - 0.25, y - 0.24]]),
                 0.02, INK, a=0.7, taper=(0.2, 0.2), seed=seed + 5)
    elif kind == 'seg':
        u = np.linspace(-1, 1, 40)
        arc = np.stack([cx + u * (x1 - x0) / 2, y - 0.18 - 0.62 * np.sqrt(1 - 0.75 * u ** 2) + 0.31], 1)
        arc[:, 1] = np.minimum(arc[:, 1], y - 0.18)
        poly = np.vstack([arc, [[x1, y - 0.18], [x0, y - 0.18]]])
        c.fill(poly, STONE, a=1.0, cvar=0.12, seed=seed + 1)
        c.stroke(arc, 0.032, INK, taper=(0.1, 0.1), wob=0.3, seed=seed + 2)
        inner = np.stack([cx + u * (x1 - x0) / 2 * 0.85, arc[:, 1] + 0.1], 1)
        inner[:, 1] = np.minimum(inner[:, 1], y - 0.2)
        c.stroke(inner, 0.018, INK, a=0.6, taper=(0.3, 0.3), seed=seed + 4)
        # cartouche
        c.fill(ellipse(cx, y - 0.42, 0.14, 0.11), STONE_HI, a=0.8)
        c.stroke(ellipse(cx, y - 0.42, 0.14, 0.11), 0.02, INK, closed=True)
    # consoles
    for xx in (x0 + 0.14, x1 - 0.14):
        con = smooth([[xx - 0.05, y], [xx + 0.05, y], [xx + 0.045, y + 0.12], [xx + 0.02, y + 0.18],
                      [xx - 0.02, y + 0.18], [xx - 0.045, y + 0.12]], 4, closed=True)
        c.fill(con, STONE_HI, a=0.8)
        c.stroke(con, 0.018, INK, closed=True, taper=(0, 0))


# --------------------------------------------------------------- facade ----

def facade(c, t=0.0, lit=1.0):
    # neighbours
    c.fill(rect(-40, E(22.8), FX0, 4), (0.15, 0.17, 0.27), cvar=0.2, tsc=(1.5, 3), seed=7)
    c.fill(rect(FX1, E(21.5), 40, 4), (0.14, 0.16, 0.25), cvar=0.2, tsc=(1.5, 3), seed=8)
    c.fill(np.array([[-40, E(22.8)], [FX0, E(22.8)], [FX0, E(26.0)], [-40, E(26.0)]]),
           (0.12, 0.14, 0.23), cvar=0.2, seed=9)
    c.fill(np.array([[FX1, E(21.5)], [40, E(21.5)], [40, E(24.0)], [FX1 + 1.0, E(24.6)]]),
           (0.11, 0.13, 0.22), cvar=0.2, seed=10)
    for side, x00 in ((-1, -12.6), (1, 10.8)):
        for i in range(3):
            xx = x00 + i * 3.4
            for e in (6.8, 10.7, 13.9, 17.0):
                c.fill(rect(xx, E(e + 2.3), xx + 1.2, E(e)), (0.07, 0.08, 0.15), a=0.8)
    c.stroke([[FX0, E(26)], [FX0, 0]], 0.05, INK, a=0.8, taper=(0, 0))
    c.stroke([[FX1, E(24.6)], [FX1, 0]], 0.05, INK, a=0.8, taper=(0, 0))

    # main stone body with vertical gouache streaks
    c.fill(rect(FX0, E(19.6), FX1, 0), STONE, cvar=0.16, tsc=(0.7, 2.6), seed=11)
    c.fill(rect(FX0, E(19.6), FX1, 0), STONE_HI, a=0.18, tex=0.9, tsc=(0.35, 1.5), seed=12)
    # gentle moonlight from upper left, darker toward the street
    c.fill(rect(FX0, E(19.6), FX1, 0), (0, 0, 0), a=1.0, mode='mul',
           grad=lambda X, Y: np.stack([0.80 + 0.2 * sstep(0, -20, Y) - 0.04 * X / 9] * 3, -1))

    # rusticated ground floor
    for k, e in enumerate(np.arange(0.45, 4.2, 0.45)):
        c.stroke([[FX0, E(e)], [FX1, E(e)]], 0.035, INK, a=0.75, taper=(0, 0), wob=0.3, seed=20 + k)
        c.stroke([[FX0, E(e) + 0.04], [FX1, E(e) + 0.04]], 0.025, STONE_HI, a=0.4, taper=(0, 0))
    # ground floor openings: carriage door in the centre, shops either side
    for bx in BAYS:
        if bx == 0:
            w, top = 2.6, 3.9
            arch = np.vstack([[[-w / 2, 0], [-w / 2, E(top - w / 2)]],
                              ellipse(0, E(top - w / 2), w / 2, w / 2 * 0.9, 30, np.pi, 2 * np.pi),
                              [[w / 2, E(top - w / 2)], [w / 2, 0]]])
            c.fill(arch, (0.10, 0.09, 0.12), cvar=0.2, tsc=(0.2, 0.8), seed=30)
            c.stroke(arch, 0.05, INK, taper=(0, 0))
            for xx in (-0.65, 0.65):
                c.stroke(rect(xx - 0.45, E(2.6), xx + 0.45, E(0.4)), 0.03, (0.22, 0.20, 0.24),
                         closed=True, taper=(0, 0))
            c.stroke([[0, E(top - 0.2)], [0, 0]], 0.04, (0.22, 0.20, 0.24), taper=(0, 0))
            # keystone
            c.fill(np.array([[-0.2, E(top + 0.1)], [0.2, E(top + 0.1)], [0.13, E(top - 0.35)],
                             [-0.13, E(top - 0.35)]]), STONE_HI)
        else:
            w = 2.2
            arch = np.vstack([[[bx - w / 2, E(0.3)], [bx - w / 2, E(2.9)]],
                              ellipse(bx, E(2.9), w / 2, 0.6, 24, np.pi, 2 * np.pi),
                              [[bx + w / 2, E(2.9)], [bx + w / 2, E(0.3)]]])
            c.fill(arch, WIN, cvar=0.25, seed=31 + int(bx))
            c.stroke(arch, 0.045, INK, taper=(0, 0))
            c.stroke([[bx, E(3.4)], [bx, E(0.3)]], 0.04, (0.2, 0.22, 0.3), taper=(0, 0))

    # string course + entresol
    c.fill(rect(FX0, E(4.4), FX1, E(4.2)), STONE_HI, a=0.8)
    c.stroke([[FX0, E(4.4)], [FX1, E(4.4)]], 0.03, INK, taper=(0, 0))
    c.stroke([[FX0, E(4.2)], [FX1, E(4.2)]], 0.03, INK, taper=(0, 0))
    for i, bx in enumerate(BAYS):
        surround(c, bx, 4.7, 1.2, 1.3, sw=0.15, seed=40 + i)
        dark_window(c, bx, 4.7, 1.2, 1.3, seed=60 + i)

    # balcony slab of the etage noble + its shadow + consoles
    c.fill(rect(FX0 + 0.2, E(6.4), FX1 - 0.2, E(5.95)), STONE_SH, a=0.7, blur=0.08)
    for i, bx in enumerate(BAYS + [-9 + 0.6, 9 - 0.6, -5.4, -1.8, 1.8, 5.4]):
        con = smooth([[bx - 0.13, E(6.4)], [bx + 0.13, E(6.4)], [bx + 0.11, E(6.15)], [bx + 0.05, E(5.98)],
                      [bx - 0.05, E(5.98)], [bx - 0.11, E(6.15)]], 4, closed=True)
        c.fill(con, STONE_HI, a=0.85)
        c.stroke(con, 0.025, INK, closed=True, taper=(0, 0), seed=70 + i)
    slab = rect(FX0 + 0.1, E(6.62), FX1 - 0.1, E(6.4))
    c.fill(slab, STONE_HI, cvar=0.1, seed=80)
    c.stroke(slab, 0.03, INK, closed=True, taper=(0, 0))

    # etage noble windows
    for i, bx in enumerate(BAYS):
        surround(c, bx, OPEN_BOT, OPEN_W, OPEN_TOP - OPEN_BOT, sw=0.2, seed=90 + i)
        hood(c, bx, OPEN_TOP + 0.2, OPEN_W, 'seg' if bx == 0 else ('tri' if abs(bx) == 3.6 else 'flat'),
             seed=100 + i)
        if bx != 0:
            dark_window(c, bx, OPEN_BOT, OPEN_W, OPEN_TOP - OPEN_BOT, seed=110 + i)

    # upper floors
    for k, (e0, h, rail_h, cont) in enumerate(((10.5, 2.6, 0.8, False), (13.7, 2.4, 0.8, False),
                                                (16.7, 2.3, 0.9, True))):
        c.fill(rect(FX0, E(e0 - 0.1), FX1, E(e0 - 0.3)), STONE_HI, a=0.5)
        c.stroke([[FX0, E(e0 - 0.1)], [FX1, E(e0 - 0.1)]], 0.025, INK, a=0.8, taper=(0, 0))
        if cont:
            c.fill(rect(FX0 + 0.2, E(e0 - 0.1), FX1 - 0.2, E(e0 - 0.45)), STONE_SH, a=0.6, blur=0.06)
            c.fill(rect(FX0 + 0.1, E(e0), FX1 - 0.1, E(e0 - 0.18)), STONE_HI)
            c.stroke(rect(FX0 + 0.1, E(e0), FX1 - 0.1, E(e0 - 0.18)), 0.025, INK, closed=True,
                     taper=(0, 0))
        for i, bx in enumerate(BAYS):
            surround(c, bx, e0, 1.3, h, sw=0.17, seed=130 + 10 * k + i)
            dark_window(c, bx, e0, 1.3, h, seed=160 + 10 * k + i)
            if k == 0:
                hood(c, bx, e0 + h + 0.17, 1.3, 'flat', seed=190 + i)
            if not cont:
                railing(c, bx - 0.75, bx + 0.75, e0, rail_h, panel=0.5, seed=300 + 10 * k + i)
        if cont:
            railing(c, FX0 + 0.2, FX1 - 0.2, e0, rail_h, panel=0.6, seed=400)

    # main cornice with dentils
    c.fill(rect(FX0 - 0.1, E(19.35), FX1 + 0.1, E(19.05)), STONE_SH, a=0.7, blur=0.05)
    c.fill(rect(FX0 - 0.25, E(20.05), FX1 + 0.25, E(19.35)), STONE_HI, cvar=0.12, seed=500)
    c.fill(rect(FX0 - 0.25, E(19.75), FX1 + 0.25, E(19.62)), STONE_SH, a=0.6)
    if c.s * 0.1 > 1.0:
        for xx in np.arange(FX0 - 0.2, FX1 + 0.2, 0.22):
            c.fill(rect(xx, E(19.62), xx + 0.11, E(19.45)), STONE_SH, a=0.7)
    c.stroke([[FX0 - 0.25, E(20.05)], [FX1 + 0.25, E(20.05)]], 0.035, INK, taper=(0, 0))
    c.stroke([[FX0 - 0.25, E(19.35)], [FX1 + 0.25, E(19.35)]], 0.03, INK, taper=(0, 0))
    c.stroke([[FX0 - 0.25, E(20.0)], [FX1 + 0.25, E(20.0)]], 0.025, (0.75, 0.75, 0.80), a=0.5,
             taper=(0.1, 0.1))

    # mansard roof
    roof = np.array([[FX0 - 0.1, E(20.05)], [FX1 + 0.1, E(20.05)], [FX1 - 0.7, E(23.7)],
                     [FX1 - 1.2, E(24.1)], [FX0 + 1.2, E(24.1)], [FX0 + 0.7, E(23.7)]])
    c.fill(roof, ZINC, cvar=0.18, tsc=(0.4, 1.5), seed=510)
    for xx in np.arange(FX0 + 0.3, FX1, 0.55):
        c.stroke([[xx, E(20.05)], [xx * 0.93, E(23.7)]], 0.02, (0.13, 0.15, 0.24), a=0.7,
                 taper=(0, 0))
    c.stroke(roof, 0.035, INK, closed=True, taper=(0, 0))
    # moonlit roof ridge
    c.stroke([[FX0 + 1.2, E(24.1)], [FX1 - 1.2, E(24.1)]], 0.05, (0.62, 0.62, 0.66), a=0.6,
             taper=(0.2, 0.2))
    for i, bx in enumerate(BAYS):
        dw = 1.15
        dorm = np.vstack([[[bx - dw / 2 - 0.15, E(20.3)], [bx - dw / 2 - 0.15, E(22.3)]],
                          ellipse(bx, E(22.3), dw / 2 + 0.15, 0.55, 24, np.pi, 2 * np.pi),
                          [[bx + dw / 2 + 0.15, E(22.3)], [bx + dw / 2 + 0.15, E(20.3)]]])
        c.fill(dorm, STONE_HI, cvar=0.1, seed=520 + i)
        c.stroke(dorm, 0.03, INK, taper=(0, 0))
        win = np.vstack([[[bx - dw / 2, E(20.4)], [bx - dw / 2, E(22.2)]],
                         ellipse(bx, E(22.2), dw / 2, 0.4, 20, np.pi, 2 * np.pi),
                         [[bx + dw / 2, E(22.2)], [bx + dw / 2, E(20.4)]]])
        c.fill(win, WIN, cvar=0.2, seed=530 + i)
        c.stroke([[bx, E(22.5)], [bx, E(20.4)]], 0.035, (0.2, 0.22, 0.3), taper=(0, 0))
    for cx in (-5.4, 5.4):
        ch = rect(cx - 0.55, E(25.7), cx + 0.55, E(23.6))
        c.fill(ch, (0.24, 0.24, 0.32), cvar=0.2, seed=540)
        c.stroke(ch, 0.03, INK, closed=True, taper=(0, 0))
        c.fill(rect(cx - 0.65, E(25.85), cx + 0.65, E(25.7)), STONE_HI)
        for j, px in enumerate((-0.3, 0.0, 0.3)):
            c.fill(rect(cx + px - 0.07, E(26.3 + 0.05 * j), cx + px + 0.07, E(25.85)), (0.30, 0.25, 0.28))

    # street: pavement + wet road with reflections
    c.fill(rect(-40, 0, 40, 0.35), (0.26, 0.28, 0.36), cvar=0.15, seed=550)
    c.stroke([[-40, 0.35], [40, 0.35]], 0.04, INK, taper=(0, 0))
    c.fill(rect(-40, 0.35, 40, 30), (0.09, 0.11, 0.19), cvar=0.25, tsc=(2.0, 0.25), seed=560)
    c.fill(rect(-40, 0.35, 40, 30), (0.25, 0.29, 0.42), a=0.35, tex=0.95, tsc=(1.2, 0.12), seed=561)
    if lit > 0:
        # golden reflection of the lit window on the wet street
        refl = np.array([[-0.55, 0.45], [0.55, 0.45], [0.9, 3.4], [-0.9, 3.4]])
        c.fill(refl, GOLD, a=0.5 * lit, tex=0.95, tsc=(0.6, 0.07), seed=570)

    # ---- the lit window --------------------------------------------------
    lit_window(c, t, lit)


def lit_window(c, t, lit):
    x0, x1 = -OPEN_W / 2, OPEN_W / 2
    y0, y1 = E(OPEN_TOP), E(OPEN_BOT)
    # warm light spilling on the surround and the stone around it
    c.radial(0, E(8.1), 3.6, (0.55, 0.40, 0.20), a=0.55 * lit, power=2.2, mode='add')
    c.radial(0, E(7.0), 1.6, (0.55, 0.42, 0.25), a=0.5 * lit, power=1.6, mode='add')
    # light pool on the balcony floor
    c.fill(np.array([[x0, E(6.62)], [x1, E(6.62)], [x1 + 0.4, E(6.4)], [x0 - 0.4, E(6.4)]]),
           (0.95, 0.75, 0.45), a=0.55 * lit)
    c.cut(OPEN_RECT)
    # open casement leaves (swung inward), painted cream, catching lamplight
    lw = 0.2
    for side in (-1, 1):
        xo = side * OPEN_W / 2
        xi = xo - side * lw
        leaf = np.array([[xo, y0 + 0.02], [xi, y0 + 0.14], [xi, y1 - 0.05], [xo, y1]])
        c.fill(leaf, (0.80, 0.66, 0.46), cvar=0.15, seed=600 + side)
        # glass in the leaf
        for k in range(3):
            g0 = lerp_(y0 + 0.2, y1 - 0.12, k / 3) + 0.04
            g1 = lerp_(y0 + 0.2, y1 - 0.12, (k + 1) / 3) - 0.04
            pane = np.array([[xo - side * 0.04, g0], [xi + side * 0.035, g0 + 0.09],
                             [xi + side * 0.035, g1 + 0.06], [xo - side * 0.04, g1]])
            c.fill(pane, (0.98, 0.86, 0.60), a=0.7)
            c.fill(pane, (0.55, 0.40, 0.25), a=0.35, tex=0.9, tsc=(0.05, 0.3), seed=610 + k)
        c.stroke(leaf, 0.018, INK, closed=True, taper=(0, 0), wob=0.3, seed=620 + side)
        c.stroke([[xi, y0 + 0.14], [xi, y1 - 0.05]], 0.03, (0.35, 0.25, 0.18), taper=(0.05, 0.05))
    # sheer curtain tied back to the right
    sway = 0.015 * np.sin(t * 1.3)
    cur = smooth([[0.25, y0 + 0.02], [0.5, y0 + 0.02], [x1 - 0.21, y0 + 0.4], [x1 - 0.2, E(8.0)],
                  [x1 - 0.32 + sway, E(7.4)], [x1 - 0.30 + sway, y1], [x1 - 0.45, y1],
                  [x1 - 0.42 + sway, E(7.5)], [x1 - 0.31, E(8.05)], [0.05 + sway, y0 + 0.25]], 8,
                 closed=True)
    c.fill(cur, (0.99, 0.93, 0.78), a=0.5 * lit + 0.2, tex=0.5, tsc=(0.03, 0.4), seed=630)
    for k in range(5):
        xx = 0.3 + k * 0.06
        c.stroke(smooth([[xx, y0 + 0.05], [xx + 0.1, y0 + 0.5], [x1 - 0.28, E(8.05)],
                         [x1 - 0.36 + 0.02 * k + sway, y1 - 0.05]], 8),
                 0.008, (0.70, 0.55, 0.38), a=0.6, taper=(0.4, 0.4), seed=640 + k)
    c.fill(ellipse(x1 - 0.24, E(8.02), 0.05, 0.03), GOLD)
    # window frame (dormant) around the opening
    c.stroke(OPEN_RECT, 0.05, (0.62, 0.48, 0.32), closed=True, taper=(0, 0), wob=0.2)
    c.stroke(OPEN_RECT, 0.016, INK, closed=True, taper=(0, 0), wob=0.3, seed=650)
    c.stroke([[x0, y0 + 0.04], [x1, y0 + 0.04]], 0.05, (0.70, 0.55, 0.36), taper=(0, 0))
    # continuous balcony railing of the etage noble
    railing(c, FX0 + 0.3, FX1 - 0.3, 6.62, 0.95, lit_glow=lit > 0, panel=0.6, seed=700)


# ---------------------------------------------------------------- trees ----

TREE_COL = (0.085, 0.115, 0.165)
TREE_HI = (0.20, 0.27, 0.32)


def _blob(cx, cy, r, seed, n=40):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    rr = r * (1 + 0.18 * noise1(a * 1.6 + seed * 7.3, seed) + 0.08 * noise1(a * 6 + seed, seed + 1))
    return np.stack([cx + rr * np.cos(a), cy + rr * np.sin(a) * 0.85], 1)


def trees(c):
    rng = np.random.RandomState(4)
    for tx, top in ((-6.9, 9.0), (7.0, 8.6)):
        trunk = np.array([[tx - 0.28, 0.3], [tx + 0.28, 0.3], [tx + 0.14, E(4.0)], [tx - 0.12, E(4.0)]])
        c.fill(trunk, (0.07, 0.08, 0.12), cvar=0.2, seed=800)
        for k in range(3):
            c.stroke(smooth([[tx, E(3.5)], [tx + (k - 1) * 1.1, E(5.0)],
                             [tx + (k - 1) * 2.0, E(6.2)]], 8), 0.16, (0.07, 0.08, 0.12),
                     taper=(0, 0.6))
        blobs = []
        for k in range(26):
            ang = rng.uniform(0, 2 * np.pi)
            rad = rng.uniform(0, 1) ** 0.6
            bx = tx + np.cos(ang) * rad * 3.2
            by = E((top - 2.6) + np.sin(ang) * rad * 2.2)
            br = rng.uniform(0.7, 1.3)
            blobs.append((bx, by, br, k))
        blobs.sort(key=lambda b: b[1])
        for bx, by, br, k in blobs:
            poly = _blob(bx, by, br, 900 + k)
            c.fill(poly, TREE_COL, cvar=0.25, tsc=(0.3, 0.3), seed=900 + k)
            hi = _blob(bx - 0.15 * br, by - 0.25 * br, br * 0.6, 950 + k)
            c.fill(hi, TREE_HI, a=0.35, tex=0.85, tsc=(0.12, 0.12), seed=950 + k)
            # leaf fans on the edge
            for j in range(3):
                aa = rng.uniform(np.pi * 1.1, np.pi * 1.9)
                lx, ly = bx + np.cos(aa) * br, by + np.sin(aa) * br * 0.85
                for f in range(5):
                    fa = aa + (f - 2) * 0.35
                    leaf = ellipse(lx + np.cos(fa) * 0.25, ly + np.sin(fa) * 0.25, 0.26, 0.07, 10,
                                   rot=fa)
                    c.fill(leaf, TREE_COL)
    # an unlit candelabra street lamp
    lx = 4.6
    c.fill(rect(lx - 0.07, E(4.0), lx + 0.07, 0.3), (0.05, 0.06, 0.10))
    c.fill(rect(lx - 0.16, E(0.9), lx + 0.16, 0.3), (0.05, 0.06, 0.10))
    for f in (-1, 1):
        c.stroke(smooth([[lx, E(3.6)], [lx + f * 0.35, E(3.9)], [lx + f * 0.55, E(4.3)]], 8), 0.06,
                 (0.05, 0.06, 0.10), taper=(0, 0))
        lan = np.array([[lx + f * 0.55 - 0.15, E(4.85)], [lx + f * 0.55 + 0.15, E(4.85)],
                        [lx + f * 0.55 + 0.09, E(4.3)], [lx + f * 0.55 - 0.09, E(4.3)]])
        c.fill(lan, (0.05, 0.06, 0.10))
        c.fill(rect(lx + f * 0.55 - 0.06, E(4.75), lx + f * 0.55 + 0.06, E(4.4)), (0.22, 0.26, 0.36))
    c.fill(rect(lx - 0.17, E(4.95), lx + 0.17, E(4.4)), (0.05, 0.06, 0.10))
    c.fill(rect(lx - 0.07, E(4.75), lx + 0.07, E(4.5)), (0.22, 0.26, 0.36))
