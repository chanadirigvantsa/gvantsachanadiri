"""The couture atelier behind the lit window.

Picture coordinates: x right, y down, origin near the dress form; a frame
width of 1.0 is the room seen at interior scale S = 1.
"""
import numpy as np
from paint import smooth, ellipse, rect, noise1, sstep, xform

INK = (0.15, 0.13, 0.135)
WALL = (0.80, 0.775, 0.72)
WALL_LINE_HI = (0.93, 0.91, 0.86)
WALL_LINE_SH = (0.52, 0.50, 0.50)
FLOOR = (0.50, 0.40, 0.31)
WOOD = (0.30, 0.21, 0.17)
BRASS = (0.83, 0.64, 0.30)
IVORY = (0.95, 0.915, 0.83)
SMOCK = (0.97, 0.96, 0.93)
SKIN = (0.90, 0.73, 0.60)
HAIR = (0.33, 0.28, 0.26)
TROUSER = (0.17, 0.17, 0.21)
LINEN = (0.42, 0.37, 0.32)
PAPER = (0.95, 0.92, 0.83)
MIDNIGHT = (0.12, 0.16, 0.30)
GOLD = (0.86, 0.68, 0.36)
SAGE = (0.42, 0.52, 0.40)

LAMP = np.array([0.245, -0.125])      # light source under the shade
FX = 0.04                             # dress form centre line
WALL_BASE = 0.19
VP = np.array([0.0, -0.2])            # vanishing point

MAN_O = np.array([-0.175, 0.44])      # man's feet in picture coords
MAN_K = 0.491                         # picture units per metre


# ------------------------------------------------------------- helpers -----

def man_pts(pts, lean=0.085, tilt_c=None, tilt=0.0):
    """Man-local metres (x right, y up from floor) -> picture coordinates."""
    p = np.asarray(pts, dtype=np.float64).copy()
    if tilt_c is not None and tilt:
        cx, cy = tilt_c
        c, s = np.cos(tilt), np.sin(tilt)
        dx, dy = p[:, 0] - cx, p[:, 1] - cy
        p[:, 0] = cx + dx * c + dy * s
        p[:, 1] = cy - dx * s + dy * c
    sh = np.clip(p[:, 1] - 0.6, 0, None) * lean
    x = p[:, 0] + sh
    return np.stack([MAN_O[0] + x * MAN_K, MAN_O[1] - p[:, 1] * MAN_K], 1)


def shade_x(base, x0, x1, lo=0.72, hi=1.04):
    base = np.asarray(base, np.float32)

    def g(X, Y):
        k = lo + (hi - lo) * sstep(x0, x1, X)
        return base[None, None, :] * k[..., None]
    return g


def limb(a, b, c_, w0, w1, n=12):
    """Thick sleeve/leg outline along a two-segment path."""
    path = smooth([a, b, c_], n)
    d = np.gradient(path, axis=0)
    nrm = np.stack([-d[:, 1], d[:, 0]], 1)
    nrm /= np.hypot(nrm[:, 0], nrm[:, 1])[:, None]
    w = np.linspace(w0, w1, len(path))[:, None] / 2
    return np.vstack([path + nrm * w, (path - nrm * w)[::-1]]), path


# --------------------------------------------------------------- shapes ----

def shapes(t):
    S = {}
    # ---------------- dress form garment ----------------
    u = np.linspace(-1, 1, 60)
    hem_y = 0.29 + 0.03 * np.sqrt(1 - u ** 2) + 0.0035 * np.abs(np.sin(u * 15))
    hem = np.stack([FX + u * 0.172, hem_y], 1)
    left = smooth([[FX - 0.172, 0.29], [FX - 0.15, 0.17], [FX - 0.11, 0.06], [FX - 0.065, -0.03],
                   [FX - 0.045, -0.075]], 8)
    right = left[::-1].copy()
    right[:, 0] = 2 * FX - right[:, 0]
    S['skirt'] = np.vstack([hem[::-1], left, right])
    S['skirt_hem'] = hem
    sway = 0.004 * np.sin(t * 0.9)
    jacket = smooth([
        [FX - 0.022, -0.272], [FX - 0.05, -0.262], [FX - 0.078, -0.25], [FX - 0.083, -0.225],
        [FX - 0.073, -0.19], [FX - 0.064, -0.15], [FX - 0.052, -0.11], [FX - 0.043, -0.083],
        [FX - 0.058, -0.055], [FX - 0.085, -0.02], [FX - 0.094, 0.006],
        [FX - 0.05, 0.016], [FX, 0.02], [FX + 0.05, 0.016],
        [FX + 0.094, 0.006], [FX + 0.085, -0.02], [FX + 0.058, -0.055], [FX + 0.043, -0.083],
        [FX + 0.052, -0.11], [FX + 0.064, -0.15], [FX + 0.073, -0.19], [FX + 0.083, -0.225],
        [FX + 0.078, -0.25], [FX + 0.05, -0.262], [FX + 0.022, -0.272]], 6, closed=True)
    S['jacket'] = jacket
    S['neck'] = rect(FX - 0.02, -0.302, FX + 0.02, -0.262)
    # loose length of fabric over the form's far shoulder
    S['drape'] = smooth([[FX + 0.045, -0.266], [FX + 0.082, -0.255], [FX + 0.105, -0.2],
                         [FX + 0.118 + sway, -0.08], [FX + 0.128 + sway * 1.5, 0.05],
                         [FX + 0.142 + sway * 2, 0.135], [FX + 0.112 + sway * 2, 0.14],
                         [FX + 0.096 + sway * 1.5, 0.05], [FX + 0.085 + sway, -0.07],
                         [FX + 0.07, -0.19], [FX + 0.05, -0.24]], 6, closed=True)

    # ---------------- the man ----------------
    breathe = 0.004 * np.sin(t * 2 * np.pi / 3.4)
    hand = 0.018 * np.sin(t * 2 * np.pi / 2.8 + 0.6)
    tilt = 0.30 + 0.035 * np.sin(t * 2 * np.pi / 4.5)
    S['tilt'] = tilt
    smock = smooth([
        [-0.06, 1.47 + breathe], [-0.15, 1.45 + breathe], [-0.205, 1.40], [-0.215, 1.28],
        [-0.205, 1.06], [-0.215, 0.82], [-0.235, 0.57],
        [-0.02, 0.555], [0.205, 0.565],
        [0.20, 0.80], [0.215, 1.0], [0.20, 1.18], [0.185, 1.33], [0.15, 1.43 + breathe],
        [0.06, 1.475 + breathe]], 6, closed=True)
    S['smock_l'] = smock
    S['smock'] = man_pts(smock)
    S['leg_far'] = man_pts([[-0.14, 0.6], [-0.03, 0.6], [-0.025, 0.08], [-0.115, 0.08]])
    S['leg_near'] = man_pts([[-0.01, 0.6], [0.13, 0.6], [0.14, 0.08], [0.035, 0.08]])
    S['shoe_far'] = man_pts(smooth([[-0.13, 0.085], [-0.02, 0.085], [0.03, 0.03], [0.03, 0.0],
                                     [-0.14, 0.0]], 5, closed=True))
    S['shoe_near'] = man_pts(smooth([[0.035, 0.085], [0.13, 0.085], [0.19, 0.035], [0.195, 0.0],
                                      [0.035, -0.003]], 5, closed=True))
    hc = np.array([0.03, 1.56])
    S['head_c'] = hc
    head = smooth([[0.0, 1.745], [0.08, 1.735], [0.122, 1.685], [0.13, 1.64], [0.148, 1.607],
                   [0.131, 1.593], [0.128, 1.575],
                   [0.105, 1.525], [0.055, 1.505], [0.0, 1.515], [-0.045, 1.55], [-0.06, 1.62],
                   [-0.05, 1.69]], 6, closed=True)
    S['head_l'] = head
    S['head'] = man_pts(head, tilt_c=hc, tilt=tilt)
    S['hp'] = lambda pts: man_pts(pts, tilt_c=hc, tilt=tilt)
    S['neck_man'] = man_pts([[-0.035, 1.53], [0.06, 1.53], [0.07, 1.45], [-0.04, 1.45]])
    # far arm (on the form's shoulder)
    sl, path = limb([0.06, 1.38], [0.17, 1.17], [0.40, 1.22 + hand * 0.3], 0.085, 0.07)
    S['arm_far'] = man_pts(sl)
    S['arm_far_path'] = man_pts(path)
    S['hand_far'] = man_pts(smooth([[0.215, 1.30 + hand * 0.3], [0.255, 1.33 + hand * 0.3],
                                     [0.30, 1.375], [0.285, 1.395], [0.25, 1.38], [0.21, 1.37]], 5,
                                    closed=True))
    # near arm (pinning at the waist), gently moving
    wr = [0.275, 1.05 + hand]
    sl, path = limb([0.13, 1.37], [0.085, 1.13 + hand * 0.4], wr, 0.095, 0.068)
    S['arm_near'] = man_pts(sl)
    S['arm_near_path'] = man_pts(path)
    S['hand_near'] = man_pts(smooth([[wr[0] - 0.01, wr[1] - 0.04], [wr[0] + 0.05, wr[1] - 0.03],
                                     [wr[0] + 0.085, wr[1] + 0.0], [wr[0] + 0.08, wr[1] + 0.025],
                                     [wr[0] + 0.04, wr[1] + 0.035], [wr[0] - 0.005, wr[1] + 0.035]], 5,
                                    closed=True))
    S['pin_tip'] = man_pts([[wr[0] + 0.082, wr[1] + 0.012], [wr[0] + 0.13, wr[1] + 0.012]])
    return S


# ------------------------------------------------------------ sketches -----

def croquis(c, cx, cy, rot, seed, wash):
    w, h = 0.085, 0.12
    rng = np.random.RandomState(seed)
    T = lambda p: xform(p, cx, cy, 1.0, rot)
    paper = T(rect(-w / 2, -h / 2, w / 2, h / 2))
    if not c.visible(paper, 0.02):
        return
    c.fill(T(rect(-w / 2 + 0.003, -h / 2 + 0.004, w / 2 + 0.004, h / 2 + 0.005)), (0.3, 0.3, 0.35), a=0.25,
           blur=0.003)
    c.fill(paper, PAPER, cvar=0.05, tsc=(0.02, 0.02), seed=seed)
    # gouache wash behind the figure
    blob = T(smooth([[-0.025, -0.03], [0.02, -0.04], [0.03, 0.01], [0.012, 0.045], [-0.03, 0.035]], 6,
                    closed=True) + rng.uniform(-0.006, 0.006, 2))
    c.fill(blob, wash, a=0.45, tex=0.6, tsc=(0.006, 0.02), seed=seed + 1)
    # the figure: tiny head, cinched waist, full skirt
    sw = rng.uniform(0.026, 0.034)
    lines = [
        smooth([[-0.004, -0.044], [0.0, -0.05], [0.004, -0.044], [0.0, -0.039]], 5, closed=True),
        np.array([[0.0, -0.039], [0.0, -0.034]]),
        smooth([[-0.011, -0.032], [-0.008, -0.02], [-0.004, -0.008], [-0.009, 0.0]], 5),
        smooth([[0.011, -0.032], [0.008, -0.02], [0.004, -0.008], [0.009, 0.0]], 5),
        smooth([[-0.009, 0.0], [-sw * 0.6, 0.02], [-sw, 0.042]], 5),
        smooth([[0.009, 0.0], [sw * 0.6, 0.02], [sw, 0.042]], 5),
        smooth([[-sw, 0.042], [0.0, 0.047], [sw, 0.042]], 5),
        np.array([[-0.003, 0.046], [-0.004, 0.056]]),
        np.array([[0.004, 0.046], [0.006, 0.056]]),
        smooth([[-0.016, -0.05], [0.0, -0.056], [0.017, -0.05]], 5),     # hat brim
    ]
    for k in range(4):
        xx = (k - 1.5) * sw * 0.4
        lines.append(np.array([[xx * 0.25, 0.004], [xx, 0.043]]))
    for k, L in enumerate(lines):
        c.stroke(T(L), 0.0012, INK, a=0.9, taper=(0.3, 0.3), seed=seed + k)
    # pins
    for px in (-w / 2 + 0.008, w / 2 - 0.008):
        c.fill(T(ellipse(px, -h / 2 + 0.006, 0.0022, 0.0022, 10)), (0.55, 0.45, 0.3))


# -------------------------------------------------------------- drawing ----

def draw(c, t):
    S = shapes(t)

    # wall
    c.fill(rect(-4, -4, 4, WALL_BASE), WALL, cvar=0.08, tsc=(0.06, 0.35), seed=1)
    c.fill(rect(-4, -4, 4, WALL_BASE), (0.70, 0.70, 0.72), a=0.25, tex=0.9, tsc=(0.04, 0.2), seed=2)
    for k, x in enumerate(np.arange(-1.26, 1.3, 0.28)):
        for (y0, y1) in ((-1.05, -0.09), (-0.02, 0.125)):
            r_ = rect(x - 0.11, y0, x + 0.11, y1)
            c.stroke(r_ + [0.003, 0.003], 0.004, WALL_LINE_HI, closed=True, taper=(0, 0), wob=0.2)
            c.stroke(r_, 0.0035, WALL_LINE_SH, closed=True, taper=(0, 0), wob=0.3, seed=k)
            r2 = rect(x - 0.095, y0 + 0.015, x + 0.095, y1 - 0.015)
            c.stroke(r2, 0.0018, WALL_LINE_SH, a=0.6, closed=True, taper=(0, 0), wob=0.3, seed=k + 9)
    c.fill(rect(-4, -0.06, 4, -0.045), WALL_LINE_HI, a=0.7)
    c.stroke([[-4, -0.045], [4, -0.045]], 0.003, WALL_LINE_SH, taper=(0, 0))
    c.fill(rect(-4, 0.155, 4, WALL_BASE), (0.62, 0.60, 0.58))
    c.stroke([[-4, 0.155], [4, 0.155]], 0.003, INK, a=0.6, taper=(0, 0))

    # sketches pinned on the wall
    for k, (sx, sy, rot, wash) in enumerate((
            (-0.245, -0.465, -0.05, MIDNIGHT), (-0.075, -0.505, 0.04, GOLD), (0.105, -0.455, -0.03, MIDNIGHT),
            (0.255, -0.43, 0.06, GOLD), (0.16, -0.30, 0.03, (0.55, 0.55, 0.6)),
            (-0.43, -0.40, 0.02, GOLD), (0.42, -0.35, -0.04, MIDNIGHT), (-0.40, -0.22, -0.03, MIDNIGHT),
            (-0.60, -0.45, 0.05, GOLD), (0.60, -0.48, 0.03, GOLD))):
        croquis(c, sx, sy, rot, 40 + k * 13, wash)

    # cast shadows on the wall (light from the lamp on the right)
    def proj(p, kx=1.32, ky=1.22, dy=0.0):
        p = np.asarray(p)
        return np.stack([LAMP[0] + (p[:, 0] - LAMP[0]) * kx, LAMP[1] + (p[:, 1] - LAMP[1]) * ky + dy], 1)
    shadow = (0.60, 0.60, 0.70)
    for key in ('smock', 'head', 'jacket', 'skirt', 'arm_near', 'arm_far'):
        sp = proj(S[key])
        sp[:, 1] = np.minimum(sp[:, 1], WALL_BASE)
        c.fill(sp, shadow, a=0.55, mode='mul', blur=0.008)

    # parquet floor in perspective
    c.fill(rect(-4, WALL_BASE, 4, 4), FLOOR, cvar=0.12, tsc=(0.3, 0.02), seed=5)
    for k, xb in enumerate(np.arange(-3.0, 3.0, 0.075)):
        d = np.array([xb, WALL_BASE]) - VP
        p1 = VP + d * (4.0 / d[1])
        c.stroke([[xb, WALL_BASE], p1], 0.0025, (0.30, 0.23, 0.19), a=0.6, taper=(0, 0), wob=0.2, seed=k)
    for k in range(1, 30):
        y = VP[1] + (WALL_BASE - VP[1]) * (1 + k * 0.09) ** 1.0
        c.stroke([[-4, y], [4, y]], 0.0018, (0.33, 0.25, 0.20), a=0.35, taper=(0, 0))
    c.fill(rect(-4, WALL_BASE, 4, 4), (0.70, 0.55, 0.40), a=0.2, tex=0.95, tsc=(0.15, 0.01), seed=6)
    # floor shadows
    c.fill(ellipse(FX - 0.06, 0.40, 0.17, 0.025), (0.55, 0.55, 0.65), a=0.6, mode='mul', blur=0.01)
    c.fill(ellipse(MAN_O[0] - 0.08, 0.445, 0.16, 0.022), (0.55, 0.55, 0.65), a=0.6, mode='mul', blur=0.01)

    draw_table(c, t)
    draw_far_arm(c, S)
    draw_form(c, S, t)
    draw_man(c, S, t)
    light(c)
    emissive(c, t)


def draw_table(c, t):
    top = np.array([[0.13, 0.035], [1.2, 0.035], [1.2, 0.0], [0.16, 0.0]])
    c.fill(top, (0.36, 0.26, 0.20), cvar=0.12, tsc=(0.1, 0.01), seed=70)
    c.fill(rect(0.13, 0.035, 1.2, 0.055), WOOD)
    c.stroke([[0.13, 0.035], [1.2, 0.035]], 0.002, (0.6, 0.45, 0.3), a=0.7, taper=(0, 0))
    c.stroke(np.vstack([top, [[0.13, 0.055], [1.2, 0.055]]])[[3, 0, 4]], 0.0025, INK, taper=(0, 0))
    for lx in (0.155, 0.7):
        leg = np.array([[lx - 0.009, 0.055], [lx + 0.009, 0.055], [lx + 0.004, 0.24], [lx - 0.004, 0.24]])
        c.fill(leg, WOOD)
        c.stroke(leg, 0.0018, INK, closed=True, taper=(0, 0))
    # lamp: brass base and stem (shade drawn emissive later)
    lx = LAMP[0]
    c.fill(ellipse(lx, 0.026, 0.034, 0.009), BRASS, grad=shade_x(BRASS, lx - 0.03, lx + 0.03, 0.6, 1.2))
    c.stroke(ellipse(lx, 0.026, 0.034, 0.009), 0.0015, INK, closed=True, taper=(0, 0))
    stem = smooth([[lx - 0.006, 0.022], [lx - 0.004, -0.02], [lx - 0.012, -0.04], [lx - 0.004, -0.06],
                   [lx - 0.004, -0.09], [lx + 0.004, -0.09], [lx + 0.004, -0.06], [lx + 0.012, -0.04],
                   [lx + 0.004, -0.02], [lx + 0.006, 0.022]], 4)
    c.fill(stem, BRASS, grad=shade_x(BRASS, lx - 0.012, lx + 0.012, 0.55, 1.25))
    c.stroke(stem, 0.0012, INK, a=0.8, taper=(0, 0))
    # tape measure spilling over the edge
    tape = smooth([[0.27, 0.03], [0.30, 0.037], [0.305, 0.07], [0.3, 0.12], [0.295, 0.15]], 8)
    c.stroke(tape, 0.009, (0.93, 0.86, 0.66), taper=(0, 0.1), wob=0.1)
    c.stroke(tape + [0.004, 0], 0.0012, INK, a=0.6, taper=(0, 0.2))
    # scissors and spools
    c.stroke([[0.31, 0.02], [0.37, 0.012]], 0.003, (0.45, 0.45, 0.5), taper=(0, 0.5))
    c.stroke([[0.31, 0.02], [0.37, 0.027]], 0.003, (0.45, 0.45, 0.5), taper=(0, 0.5))
    c.stroke(ellipse(0.302, 0.016, 0.007, 0.004), 0.002, INK, closed=True)
    c.stroke(ellipse(0.302, 0.026, 0.007, 0.004), 0.002, INK, closed=True)
    for k, (sx, col) in enumerate(((0.395, MIDNIGHT), (0.415, GOLD), (0.44, IVORY))):
        sp = rect(sx - 0.007, 0.0, sx + 0.007, 0.028)
        c.fill(sp, col)
        c.stroke(sp, 0.0012, INK, closed=True, taper=(0, 0))
    # vase of lily of the valley
    vx = 0.19
    vase = smooth([[vx - 0.012, 0.03], [vx - 0.016, 0.012], [vx - 0.011, -0.004], [vx - 0.008, -0.012],
                   [vx + 0.008, -0.012], [vx + 0.011, -0.004], [vx + 0.016, 0.012], [vx + 0.012, 0.03]], 5)
    c.fill(vase, (0.92, 0.93, 0.95), grad=shade_x((0.92, 0.93, 0.95), vx - 0.016, vx + 0.016, 0.7, 1.05))
    c.stroke(vase, 0.0014, INK, taper=(0, 0))
    c.stroke([[vx + 0.006, 0.02], [vx + 0.008, 0.0]], 0.002, (1, 1, 1), a=0.8)
    rng = np.random.RandomState(11)
    for k, (ang, ln) in enumerate(((-0.55, 0.075), (-0.25, 0.09), (0.12, 0.085), (0.38, 0.07), (0.65, 0.06))):
        sway = 0.004 * np.sin(t * 1.1 + k)
        base = np.array([vx + (k - 2) * 0.002, -0.012])
        tip = base + [np.sin(ang) * ln + sway, -np.cos(ang) * ln * 0.9]
        bend = tip + [np.sign(ang + 0.01) * 0.018, 0.012]
        stem = smooth([base, (base + tip) / 2 + [0, -0.01], tip, bend], 6)
        c.stroke(stem, 0.0016, (0.38, 0.47, 0.34), taper=(0, 0.4))
        for j in range(5):
            fr = 0.45 + j * 0.12
            i = min(int(fr * (len(stem) - 1)), len(stem) - 1)
            bx, by = stem[i]
            c.stroke([[bx, by], [bx + 0.002, by + 0.006]], 0.0007, (0.38, 0.47, 0.34))
            bell = ellipse(bx + 0.002, by + 0.009, 0.0042 * (1 - j * 0.1), 0.0038 * (1 - j * 0.1), 12)
            c.fill(bell, (0.99, 0.98, 0.94))
            c.stroke(bell, 0.0006, INK, a=0.6, closed=True)
    for k, ang in enumerate((-0.18, 0.28)):
        base = np.array([vx, -0.01])
        tip = base + [np.sin(ang) * 0.065, -np.cos(ang) * 0.065]
        leaf = smooth([base, (base * 0.4 + tip * 0.6) + [0.008, 0], tip, (base * 0.4 + tip * 0.6) + [-0.008, 0]],
                      8, closed=True)
        c.fill(leaf, SAGE, grad=shade_x(SAGE, vx - 0.03, vx + 0.04, 0.7, 1.15))
        c.stroke(leaf, 0.001, INK, a=0.7, closed=True)
        c.stroke([base, tip], 0.0008, (0.3, 0.38, 0.28), a=0.8)


def draw_form(c, S, t):
    # stand
    c.fill(rect(FX - 0.006, 0.28, FX + 0.006, 0.39), (0.25, 0.20, 0.17))
    for dx in (-0.06, 0.0, 0.065):
        c.stroke([[FX, 0.385], [FX + dx, 0.405 - abs(dx) * 0.1]], 0.007, (0.25, 0.20, 0.17), taper=(0, 0))
        c.fill(ellipse(FX + dx, 0.407 - abs(dx) * 0.1, 0.006, 0.004), BRASS)
    # skirt with pleats
    wc = np.array([FX, -0.25])

    def skirt_grad(X, Y):
        ang = np.arctan2(X - wc[0], Y - wc[1])
        pleat = 0.5 + 0.5 * np.sin(ang * 70)
        v = 0.86 + 0.14 * pleat
        side = 0.7 + 0.36 * sstep(FX - 0.17, FX + 0.14, X)
        return np.asarray(IVORY, np.float32)[None, None] * (v * side)[..., None]
    c.fill(S['skirt'], IVORY, grad=skirt_grad)
    hem = S['skirt_hem']
    for k in range(-9, 10):
        a = k * 0.0435
        top = wc + [np.sin(a) * 0.19, np.cos(a) * 0.19]
        bot = wc + [np.sin(a) * 0.55, np.cos(a) * 0.55]
        i = np.argmin(np.abs(hem[:, 0] - bot[0]))
        bot = np.array([bot[0], hem[i, 1] - 0.004])
        c.stroke([top, bot], 0.0012, (0.45, 0.43, 0.45), a=0.45, taper=(0.5, 0.1), seed=k)
    c.stroke(S['skirt'], 0.0026, INK, closed=True, taper=(0, 0), wob=0.35, seed=3)
    c.fill(ellipse(FX, 0.31, 0.15, 0.012), (0.75, 0.73, 0.75), a=0.35, mode='mul', blur=0.004)

    # jacket
    c.fill(S['neck'], LINEN)
    c.fill(ellipse(FX, -0.302, 0.021, 0.007), (0.30, 0.26, 0.22))
    c.fill(S['jacket'], IVORY, grad=shade_x(IVORY, FX - 0.085, FX + 0.07, 0.68, 1.05))
    # padded hips: soft shading under the waist
    c.fill(smooth([[FX - 0.09, 0.0], [FX - 0.05, -0.045], [FX, -0.05], [FX + 0.05, -0.045], [FX + 0.09, 0.0],
                   [FX, 0.012]], 6, closed=True), (0.82, 0.80, 0.80), a=0.35, mode='mul', blur=0.006)
    c.stroke(S['jacket'], 0.0028, INK, closed=True, taper=(0, 0), wob=0.35, seed=4)
    # shawl collar and front
    collar = smooth([[FX - 0.022, -0.27], [FX - 0.03, -0.235], [FX - 0.012, -0.19], [FX, -0.165],
                     [FX + 0.012, -0.19], [FX + 0.03, -0.235], [FX + 0.022, -0.27]], 6)
    c.fill(collar, (0.80, 0.77, 0.72), a=0.9)
    c.fill(smooth([[FX - 0.02, -0.268], [FX - 0.012, -0.235], [FX, -0.222], [FX + 0.012, -0.235],
                   [FX + 0.02, -0.268]], 5), LINEN)
    for f in (-1, 1):
        lap = np.array([[FX + f * 0.022, -0.27], [FX + f * 0.045, -0.24], [FX + f * 0.012, -0.18],
                        [FX, -0.165], [FX + f * 0.015, -0.21]])
        c.fill(smooth(lap, 4, closed=True), IVORY, grad=shade_x(IVORY, FX - 0.05, FX + 0.05, 0.75, 1.0))
        c.stroke(smooth(lap, 4, closed=True), 0.0016, INK, a=0.85, closed=True, taper=(0, 0))
    c.stroke([[FX, -0.165], [FX + 0.002, -0.02]], 0.0016, INK, a=0.8, taper=(0, 0.2))
    for k, by in enumerate((-0.14, -0.115, -0.09, -0.065)):
        c.fill(ellipse(FX + 0.005, by, 0.0035, 0.0035, 12), (0.25, 0.22, 0.22))
    for f in (-1, 1):  # darts toward the waist
        c.stroke([[FX + f * 0.035, -0.2], [FX + f * 0.03, -0.09], [FX + f * 0.04, -0.03]], 0.0011, INK, a=0.5,
                 taper=(0.4, 0.4))
    # pins along the waist seam and shoulder
    for k, (px, py) in enumerate(((FX - 0.036, -0.082), (FX - 0.015, -0.079), (FX + 0.015, -0.079),
                                  (FX + 0.034, -0.081), (FX - 0.07, -0.245), (FX - 0.055, -0.257))):
        c.stroke([[px, py], [px + 0.006, py - 0.004]], 0.0008, (0.55, 0.55, 0.6))
        c.fill(ellipse(px, py, 0.0022, 0.0022, 10), GOLD)
    # draped fabric over the far shoulder
    c.fill(S['drape'], IVORY, grad=shade_x(IVORY, FX + 0.06, FX + 0.14, 0.75, 1.08))
    for k in range(3):
        c.stroke(smooth([[FX + 0.06 + k * 0.012, -0.25], [FX + 0.09 + k * 0.012, -0.12],
                         [FX + 0.105 + k * 0.01, 0.0], [FX + 0.115 + k * 0.008, 0.12]], 6), 0.0012,
                 (0.5, 0.48, 0.48), a=0.5, taper=(0.3, 0.3))
    c.stroke(S['drape'], 0.0022, INK, closed=True, taper=(0, 0), wob=0.35, seed=8)


def draw_far_arm(c, S):
    # reaching round behind the form; the hand is hidden by the jacket
    c.fill(S['arm_far'], SMOCK, grad=shade_x(SMOCK, -0.2, 0.0, 0.58, 0.85))
    c.stroke(S['arm_far'], 0.0022, INK, closed=True, taper=(0, 0), wob=0.3, seed=21)


def draw_man(c, S, t):
    hp = S['hp']
    # legs and shoes
    for k in ('leg_far', 'leg_near'):
        c.fill(S[k], TROUSER, cvar=0.15, tsc=(0.01, 0.05), seed=30)
        c.stroke(S[k], 0.002, INK, closed=True, taper=(0, 0))
    for k in ('shoe_far', 'shoe_near'):
        c.fill(S[k], (0.10, 0.09, 0.10))
        c.stroke(S[k][:len(S[k]) // 2], 0.0015, (0.45, 0.4, 0.4), a=0.6, taper=(0.3, 0.3))
    # smock
    c.fill(S['smock'], SMOCK, grad=shade_x(SMOCK, -0.29, -0.06, 0.66, 1.03))
    c.fill(S['smock'], (0.75, 0.78, 0.86), a=0.18, tex=0.9, tsc=(0.01, 0.05), seed=31)
    sl = S['smock_l']
    for k, line in enumerate((
            [[0.12, 1.42], [0.125, 1.1], [0.12, 0.8], [0.115, 0.57]],     # front opening
            [[-0.12, 1.2], [-0.135, 0.9], [-0.16, 0.6]],                  # fold
            [[0.0, 1.0], [-0.02, 0.8], [-0.04, 0.6]],                     # fold
            [[-0.16, 0.85], [-0.02, 0.83]],                               # side pocket
    )):
        c.stroke(man_pts(smooth(line, 6)), 0.0016, (0.45, 0.45, 0.5), a=0.7, taper=(0.3, 0.3), seed=40 + k)
    for by in (1.3, 1.1, 0.9, 0.7):
        bp = man_pts([[0.13, by]])[0]
        c.fill(ellipse(bp[0], bp[1], 0.0035, 0.0035, 10), (0.80, 0.78, 0.74))
        c.stroke(ellipse(bp[0], bp[1], 0.0035, 0.0035, 10), 0.0008, INK, closed=True)
    c.stroke(S['smock'], 0.0028, INK, closed=True, taper=(0, 0), wob=0.35, seed=41)
    # neck, shirt collar and tie
    c.fill(S['neck_man'], SKIN, grad=shade_x(SKIN, -0.17, -0.12, 0.7, 0.95))
    collar = man_pts([[-0.04, 1.49], [0.08, 1.485], [0.10, 1.43], [0.03, 1.40], [-0.03, 1.45]])
    c.fill(collar, (0.96, 0.95, 0.93))
    tie = man_pts([[0.045, 1.465], [0.07, 1.46], [0.075, 1.38], [0.06, 1.33], [0.045, 1.38]])
    c.fill(tie, (0.16, 0.18, 0.28))
    c.stroke(collar, 0.0015, INK, closed=True, taper=(0, 0))
    lapel = man_pts(smooth([[-0.03, 1.47], [0.02, 1.38], [0.11, 1.33], [0.15, 1.42]], 6))
    c.stroke(lapel, 0.0018, INK, a=0.8, taper=(0.2, 0.2))
    # head
    c.fill(S['head'], SKIN, grad=shade_x(SKIN, -0.14, -0.05, 0.72, 1.06))
    # balding crown highlight and fringe of hair round the back
    c.fill(hp(smooth([[0.0, 1.735], [0.06, 1.73], [0.09, 1.70], [0.05, 1.70], [0.0, 1.71]], 5, closed=True)),
           (1.0, 0.92, 0.8), a=0.45)
    fringe = hp(smooth([[-0.035, 1.705], [-0.058, 1.66], [-0.062, 1.60], [-0.045, 1.55], [-0.015, 1.535],
                        [-0.02, 1.565], [-0.03, 1.60], [-0.025, 1.64], [-0.01, 1.68], [0.005, 1.70]], 6,
                       closed=True))
    c.fill(fringe, HAIR, cvar=0.2, tsc=(0.003, 0.01), seed=50)
    for k in range(5):
        c.stroke(hp(smooth([[-0.03 + k * 0.006, 1.69 - k * 0.02], [-0.05 + k * 0.004, 1.63 - k * 0.01],
                            [-0.04, 1.56]], 5)), 0.0008, (0.2, 0.17, 0.16), a=0.6, taper=(0.4, 0.4))
    # ear
    ear = hp(smooth([[0.0, 1.645], [0.02, 1.645], [0.025, 1.61], [0.012, 1.585], [-0.002, 1.595]], 5,
                    closed=True))
    c.fill(ear, (0.86, 0.65, 0.54))
    c.stroke(ear, 0.0012, INK, closed=True, taper=(0, 0))
    # features: downcast eye, brow, nose, mouth, soft double chin
    c.stroke(hp(smooth([[0.075, 1.636], [0.09, 1.632], [0.103, 1.636]], 5)), 0.0013, INK, taper=(0.3, 0.3))
    c.stroke(hp(smooth([[0.07, 1.655], [0.088, 1.662], [0.108, 1.66]], 5)), 0.0014, HAIR, taper=(0.3, 0.3))
    c.stroke(hp(smooth([[0.098, 1.567], [0.112, 1.566], [0.118, 1.57]], 5)), 0.0012, (0.45, 0.25, 0.22),
             taper=(0.3, 0.3))
    c.stroke(hp(smooth([[0.05, 1.523], [0.08, 1.512], [0.11, 1.53]], 5)), 0.001, INK, a=0.5, taper=(0.3, 0.3))
    c.fill(hp(ellipse(0.085, 1.59, 0.018, 0.012, 16)), (0.92, 0.55, 0.48), a=0.25, blur=0.003)
    c.stroke(S['head'], 0.0024, INK, closed=True, taper=(0, 0), wob=0.35, seed=51)
    # near arm in front
    c.fill(S['arm_near'], SMOCK, grad=shade_x(SMOCK, -0.12, 0.0, 0.7, 1.04))
    path = S['arm_near_path']
    c.stroke(path[len(path) // 2:] + [0, 0.006], 0.0016, (0.5, 0.5, 0.55), a=0.6, taper=(0.4, 0.3))
    c.stroke(S['arm_near'], 0.0026, INK, closed=True, taper=(0, 0), wob=0.3, seed=52)
    c.fill(S['hand_near'], SKIN, grad=shade_x(SKIN, -0.06, 0.02, 0.8, 1.06))
    c.stroke(S['hand_near'], 0.0016, INK, closed=True, taper=(0, 0))
    c.stroke(S['pin_tip'], 0.0008, (0.65, 0.65, 0.7), taper=(0, 0))
    # pincushion on the wrist
    path = S['arm_near_path']
    pc = path[int(len(path) * 0.86)] + [0, -0.012]
    c.fill(ellipse(pc[0], pc[1], 0.011, 0.008), (0.36, 0.25, 0.30))
    c.stroke(ellipse(pc[0], pc[1], 0.011, 0.008), 0.0012, INK, closed=True)
    for k in range(4):
        a = -np.pi / 2 + (k - 1.5) * 0.5
        c.stroke([[pc[0] + np.cos(a) * 0.005, pc[1] + np.sin(a) * 0.005],
                  [pc[0] + np.cos(a) * 0.015, pc[1] + np.sin(a) * 0.015]], 0.0007, (0.6, 0.6, 0.65))
    pt = S['pin_tip'][0]
    c.fill(ellipse(pt[0], pt[1], 0.002, 0.002, 8), GOLD)


def light(c):
    lx, ly = LAMP

    def f(X, Y):
        d = np.hypot(X - lx, (Y - ly) * 0.85)
        warm = 1.0 / (1.0 + (d / 0.21) ** 2)
        # fan of light thrown up the wall above the shade, and down onto the table
        up = sstep(0.0, 0.05, (ly - 0.05 - Y)) * sstep(-0.1, 0.25, (ly - 0.05 - Y) * 0.55 - np.abs(X - lx)) \
            * np.exp(-np.maximum(ly - Y, 0) / 0.5)
        warm = warm + 0.35 * up
        amb = np.array([0.40, 0.43, 0.56], np.float32)
        wc = np.array([1.08, 0.90, 0.64], np.float32) * 1.3
        out = amb[None, None] + warm[..., None] * wc[None, None]
        # gentle falloff into darkness toward the far edges of the room
        edge = 1 - 0.35 * sstep(0.35, 0.8, np.hypot(X * 1.0, Y * 0.7))
        return out * edge[..., None]
    c.grad_all(f, 'mul')


def emissive(c, t):
    lx, ly = LAMP
    flick = 1 + 0.02 * noise1(t * 3.0, 5)
    c.radial(lx, ly, 0.16, (0.55, 0.38, 0.16), a=0.6 * flick, mode='add', power=2.0)
    shade = smooth([[lx - 0.034, -0.168], [lx + 0.034, -0.168], [lx + 0.062, -0.088], [lx, -0.084],
                    [lx - 0.062, -0.088]], 4, closed=True)
    c.fill(shade, (1.0, 0.90, 0.68), grad=shade_x((1.0, 0.90, 0.68), lx - 0.06, lx + 0.06, 0.82, 1.0))
    for k in range(9):
        x0 = lx - 0.03 + k * 0.0075
        c.stroke([[x0, -0.166], [lx + (x0 - lx) * 1.8, -0.088]], 0.0007, (0.85, 0.65, 0.4), a=0.6)
    c.stroke(shade, 0.0018, (0.5, 0.35, 0.2), closed=True, taper=(0, 0))
    c.fill(ellipse(lx, -0.087, 0.062, 0.006), (1.0, 0.95, 0.80))
    c.radial(lx, -0.07, 0.05, (0.6, 0.45, 0.2), a=0.5 * flick, mode='add')
    # dust motes drifting in the lamplight
    rng = np.random.RandomState(3)
    for k in range(26):
        x = lx + rng.uniform(-0.25, 0.12) + 0.006 * np.sin(t * 0.5 + k)
        y = ly + rng.uniform(-0.2, 0.25) - ((t * 0.006 + rng.uniform(0, 0.3)) % 0.3) + 0.15
        r = rng.uniform(0.0008, 0.0018)
        tw = 0.5 + 0.5 * np.sin(t * rng.uniform(1, 3) + k)
        d = np.hypot(x - lx, y - ly)
        a = 0.6 * tw * np.clip(1 - d / 0.3, 0, 1)
        if a > 0.02:
            c.radial(x, y, r * 3, (1.0, 0.85, 0.55), a=a, mode='add', power=1.5)
