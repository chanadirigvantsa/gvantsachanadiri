#!/usr/bin/env python3
"""Render four 9:16 Instagram reels on the history of the Fondation Louis Vuitton.

Every frame is drawn from code (typography plus original abstract illustrations),
and the soundtrack is synthesised, so there are no third-party images or music to clear.

Usage:  python3 make_reels.py            # all reels
        python3 make_reels.py 2 4        # only reels 2 and 4
        python3 make_reels.py --preview  # one still per scene into preview/
Needs Pillow, numpy and ffmpeg.
"""
import math, os, random, subprocess, sys, wave
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

INK = (9, 13, 28)
IVORY = (243, 238, 228)
GLASS = (150, 205, 235)
AMBER = (232, 176, 75)
RED = (214, 48, 49)
MUTED = (150, 160, 180)

FD = "/usr/share/fonts/opentype/inter/"
F_BLACK = FD + "InterDisplay-Black.otf"
F_BOLD = FD + "InterDisplay-Bold.otf"
F_SEMI = FD + "InterDisplay-SemiBold.otf"
F_REG = FD + "Inter-Regular.otf"
F_SERIF_I = "/usr/share/fonts/truetype/crosextra/Caladea-Italic.ttf"
F_MONO = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Medium.ttf"
if not os.path.exists(F_MONO):
    F_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

X0 = 84            # left text margin
TEXT_W = 880       # keep clear of the Reels UI on the right
CREDIT = "Gvantsa Chanadiri"


# ---------------------------------------------------------------- helpers
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x

def ease_out(x):
    x = clamp(x); return 1 - (1 - x) ** 3

def ease_in_out(x):
    x = clamp(x); return 3 * x * x - 2 * x * x * x

def ease_back(x):
    x = clamp(x); c = 1.9
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

def lerp(a, b, t):
    return a + (b - a) * t

def mix(c1, c2, t):
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))

@lru_cache(None)
def font(path, size):
    return ImageFont.truetype(path, size)

def wrap(text, f, maxw):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            test = (cur + " " + word).strip()
            if f.getlength(test) <= maxw or not cur:
                cur = test
            else:
                lines.append(cur); cur = word
        lines.append(cur)
    return lines

@lru_cache(4096)
def line_img(text, fpath, size, color, track=0):
    f = font(fpath, size)
    asc, desc = f.getmetrics()
    if track:
        w = int(sum(f.getlength(ch) + track for ch in text)) + 4
    else:
        w = int(f.getlength(text)) + 4
    im = Image.new("RGBA", (max(w, 1), asc + desc + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if track:
        x = 0
        for ch in text:
            d.text((x, 0), ch, font=f, fill=color); x += f.getlength(ch) + track
    else:
        d.text((0, 0), text, font=f, fill=color)
    return im

def with_alpha(im, a):
    if a >= 0.999:
        return im
    im = im.copy()
    im.putalpha(im.getchannel("A").point([int(v * a) for v in range(256)]))
    return im

def put(layer, im, x, y, a=1.0):
    if a <= 0.003:
        return
    layer.alpha_composite(with_alpha(im, a), (int(x), int(y)))

def text(layer, t, start, s, x, y, fpath, size, color=IVORY, maxw=TEXT_W,
         lead=1.18, stagger=0.09, dur=0.55, align="left", track=0, rise=46):
    """Animated paragraph: each line rises and fades in. Returns the bottom y."""
    f = font(fpath, size)
    lines = wrap(s, f, maxw)
    step = int(size * lead)
    for i, ln in enumerate(lines):
        k = ease_out((t - start - i * stagger) / dur)
        im = line_img(ln, fpath, size, color, track)
        xx = x if align == "left" else x - im.width / 2 if align == "center" else x - im.width
        put(layer, im, xx, y + i * step + (1 - k) * rise, k)
    return y + len(lines) * step

def label(layer, t, start, s, x, y, color=AMBER, size=30):
    k = ease_out((t - start) / 0.5)
    im = line_img(s.upper(), F_MONO, size, color, 3)
    put(layer, im, x - (1 - k) * 30, y, k)
    return y + int(size * 1.6)

def bezier(p0, p1, p2, n=24):
    out = []
    for i in range(n + 1):
        u = i / n
        out.append(((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0],
                    (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1]))
    return out

def mid_ctrl(a, b, bulge):
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy) or 1
    return (mx - dy / ln * bulge, my + dx / ln * bulge)


# ---------------------------------------------------------------- the building
# Unit space: x 0..1000, y 0..650 measured up from the waterline.
BLOCKS = [  # the white "iceberg" volumes (Ductal concrete)
    (170, 0, 430, 250), (390, 0, 650, 320), (610, 0, 830, 230),
    (300, 180, 520, 400), (520, 230, 700, 430), (240, 0, 330, 120),
]
SAILS = [  # A, B, C, D corners (bottom-left, bottom-right, top-right, top-left) + bulges
    ((10, 70), (270, 120), (250, 205), (-20, 140), 22, 30),
    ((60, 190), (340, 240), (310, 340), (20, 265), 28, 40),
    ((660, 120), (960, 80), (1010, 175), (690, 205), 24, 34),
    ((610, 260), (910, 215), (970, 310), (650, 350), 28, 42),
    ((120, 310), (420, 365), (385, 470), (90, 390), 32, 44),
    ((480, 385), (735, 425), (775, 525), (505, 475), 28, 40),
    ((800, 330), (1010, 315), (1030, 400), (835, 420), 20, 28),
    ((255, 430), (520, 478), (485, 565), (225, 505), 28, 38),
    ((370, 250), (560, 300), (520, 380), (345, 330), 18, 24),
    ((150, 430), (300, 455), (285, 525), (130, 495), 18, 24),
    ((340, 545), (570, 600), (610, 655), (370, 615), 18, 26),
    ((570, 525), (810, 560), (850, 640), (605, 610), 18, 26),
]

def sail_poly(sail, tx):
    A, B, C, D, b1, b2 = sail
    bottom = bezier(tx(A), tx(mid_ctrl(A, B, b1)), tx(B))
    top = bezier(tx(D), tx(mid_ctrl(D, C, b2)), tx(C))
    return bottom, top

def draw_building(layer, cx, base, scale, sails=12.0, blocks=1.0, colors=None,
                  reflect=True, trees=True, t=0.0, water=True):
    """Stylised glass-sail building. `sails` (0..12) and `blocks` (0..1) animate the build."""
    bw, bh = int(1100 * scale), int(700 * scale)
    lay = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    ox, oy = 50 * scale, bh - 2

    def tx(p):
        return (ox + p[0] * scale, oy - p[1] * scale)

    if trees:
        rnd = random.Random(7)
        for i in range(26):
            side = -1 if i % 2 else 1
            x = 500 + side * rnd.uniform(380, 560)
            y = rnd.uniform(0, 150)
            r = rnd.uniform(40, 90)
            c = mix((22, 48, 40), (40, 78, 58), rnd.random())
            px, py = tx((x, y))
            d.ellipse([px - r * scale, py - r * scale, px + r * scale, py + r * scale], fill=c + (255,))

    for i, (x1, y1, x2, y2) in enumerate(BLOCKS):
        k = ease_out(blocks * len(BLOCKS) - i)
        if k <= 0:
            continue
        top = lerp(y1, y2, k)
        shade = 255 if i % 2 == 0 else 228
        p1, p2 = tx((x1, top)), tx((x2, y1))
        d.rounded_rectangle([p1[0], p1[1], p2[0], p2[1]], radius=int(10 * scale),
                            fill=(shade, shade - 4, shade - 12, 255))
        for gx in range(int(x1) + 30, int(x2), 30):  # panel joints
            a, b = tx((gx, y1)), tx((gx, top))
            d.line([a, b], fill=(200, 196, 188, 255), width=1)

    full = int(sails)
    for i, s in enumerate(SAILS):
        if i > full:
            break
        k = 1.0 if i < full else sails - full
        if k <= 0:
            continue
        bottom, top = sail_poly(s, tx)
        if k < 1:  # sail grows upward from its bottom edge
            kk = ease_out(k)
            top = [(lerp(b[0], q[0], kk), lerp(b[1], q[1], kk)) for b, q in zip(bottom, top)]
        base_c = colors[i % len(colors)] if colors else GLASS
        sl = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sl)
        sd.polygon(bottom + top[::-1], fill=base_c + (120,))
        for j in range(1, 6):  # mullions across
            u = j / 6
            sd.line([(lerp(b[0], q[0], u), lerp(b[1], q[1], u)) for b, q in zip(bottom, top)],
                    fill=(255, 255, 255, 70), width=max(1, int(2 * scale)))
        for j in range(0, len(bottom), 4):  # mullions up
            sd.line([bottom[j], top[j]], fill=(255, 255, 255, 60), width=max(1, int(2 * scale)))
        sd.line(top, fill=(255, 255, 255, 230), width=max(2, int(4 * scale)))
        lay.alpha_composite(sl)

    x = int(cx - bw / 2 + 0)
    layer.alpha_composite(lay, (x, int(base - bh)))
    if water:
        wd = ImageDraw.Draw(layer)
        wd.rectangle([0, base, W, base + 6], fill=(255, 255, 255, 40))
        if reflect:
            ref = lay.transpose(Image.FLIP_TOP_BOTTOM).resize((bw, int(bh * 0.55)))
            ref = with_alpha(ref, 0.22).filter(ImageFilter.GaussianBlur(3))
            layer.alpha_composite(ref, (x, int(base + 6)))
        for i in range(10):  # shimmer
            y = base + 30 + i * 26
            off = math.sin(t * 2 + i) * 40
            ln = 120 + (i * 53) % 220
            xs = (i * 197 + off) % (W - ln)
            wd.line([(xs, y), (xs + ln, y)], fill=(200, 230, 255, 70 - i * 5), width=3)


# ---------------------------------------------------------------- backgrounds
@lru_cache(None)
def gradient(top, bottom):
    arr = np.zeros((H, W, 3), np.float32)
    v = np.linspace(0, 1, H)[:, None]
    for c in range(3):
        arr[:, :, c] = top[c] * (1 - v) + bottom[c] * v
    yy, xx = np.mgrid[0:H, 0:W]
    vign = 1 - 0.35 * (((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2) * 2
    arr *= vign[:, :, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")

@lru_cache(None)
def ghost_sails(seed):
    """Large faint sail shapes that drift behind everything."""
    im = Image.new("RGBA", (W + 400, H + 400), (0, 0, 0, 0))
    rnd = random.Random(seed)
    for _ in range(7):
        x, y = rnd.uniform(0, W + 200), rnd.uniform(0, H + 200)
        w, h = rnd.uniform(500, 900), rnd.uniform(220, 380)
        ang = rnd.uniform(-0.35, 0.35)
        A = (x, y); B = (x + w * math.cos(ang), y + w * math.sin(ang))
        D = (x - 60, y - h); C = (B[0] + 80, B[1] - h * 0.9)
        bottom = bezier(A, mid_ctrl(A, B, -70), B)
        top = bezier(D, mid_ctrl(D, C, -90), C)
        sl = Image.new("RGBA", im.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(sl)
        sd.polygon(bottom + top[::-1], fill=(170, 210, 240, 16))
        for j in range(1, 5):
            u = j / 5
            sd.line([(lerp(b[0], q[0], u), lerp(b[1], q[1], u)) for b, q in zip(bottom, top)],
                    fill=(220, 240, 255, 18), width=2)
        sd.line(top, fill=(230, 245, 255, 40), width=3)
        im.alpha_composite(sl)
    return im

def background(t, theme, seed):
    bg = gradient(*theme).copy()
    g = ghost_sails(seed)
    ox = 200 + math.sin(t * 0.25) * 120
    oy = 200 + t * 9 % 200
    bg.alpha_composite(g.crop((int(ox), int(oy), int(ox) + W, int(oy) + H)))
    return bg


# ---------------------------------------------------------------- big numbers
@lru_cache(64)
def number_masks(s, size):
    f = font(F_BLACK, size)
    w = int(f.getlength(s)) + 30
    hgt = int(size * 1.25)
    fill = Image.new("L", (w, hgt), 0)
    ImageDraw.Draw(fill).text((12, 0), s, font=f, fill=255)
    stroke = Image.new("L", (w, hgt), 0)
    ImageDraw.Draw(stroke).text((12, 0), s, font=f, fill=255, stroke_width=4, stroke_fill=255)
    outline = ImageChops.subtract(stroke, fill)
    return np.array(fill), np.array(outline)

def big_number(layer, s, x, y, size, level, a=1.0, fill_c=GLASS, line_c=IVORY, align="left"):
    """Outlined numerals that fill with 'glass' from the bottom up as `level` goes 0..1."""
    fill, outline = number_masks(s, size)
    h, w = fill.shape
    rows = np.arange(h)[:, None]
    cut = h - level * h
    fa = np.where(rows >= cut, fill, 0).astype(np.float32)
    rgba = np.zeros((h, w, 4), np.uint8)
    rgba[..., :3] = fill_c
    rgba[..., 3] = (fa * a).astype(np.uint8)
    im = Image.fromarray(rgba, "RGBA")
    ol = np.zeros((h, w, 4), np.uint8)
    ol[..., :3] = line_c
    ol[..., 3] = (outline * a).astype(np.uint8)
    im.alpha_composite(Image.fromarray(ol, "RGBA"))
    xx = x if align == "left" else x - w / 2
    layer.alpha_composite(im, (int(xx), int(y)))
    return w


# ---------------------------------------------------------------- scene library
class Scene:
    def __init__(self, dur, fn, **kw):
        self.dur, self.fn, self.kw = dur, fn, kw

def sc_hook(L, t, d, lines, kicker="", accent=None):
    y = 560
    if kicker:
        y = label(L, t, 0.0, kicker, X0, y - 90)
    y = text(L, t, 0.15, lines, X0, y, F_BOLD, 104, lead=1.06, stagger=0.12)
    if accent:
        text(L, t, 0.9, accent, X0, y + 40, F_SERIF_I, 64, color=GLASS)
    # underline sweep
    k = ease_out((t - 0.6) / 0.8)
    ImageDraw.Draw(L).line([(X0, y + 10), (X0 + 560 * k, y + 10)], fill=AMBER + (255,), width=6)

def sc_year(L, t, d, year, prev, title, body, visual=None, vis_kw=None, tag=""):
    if visual:
        visual(L, t, d, **(vis_kw or {}))
    k = ease_out(t / 0.7)
    shown = str(int(round(lerp(prev, year, k)))) if prev else str(year)
    label(L, t, 0.0, tag or "Chapter", X0, 300)
    big_number(L, shown, X0 - 12, 350, 300, ease_in_out((t - 0.3) / (d - 0.6)), a=ease_out(t / 0.4))
    y = text(L, t, 0.35, title, X0, 760, F_BOLD, 74, lead=1.08)
    text(L, t, 0.6, body, X0, y + 24, F_REG, 44, color=(205, 210, 222), lead=1.32, stagger=0.07)

def sc_stat(L, t, d, value, fmt, label_s, body, visual=None, vis_kw=None, prefix="", suffix="",
            count=None):
    if visual:
        visual(L, t, d, **(vis_kw or {}))
    k = count(t, d) if count else ease_out((t - 0.1) / 1.4)
    v = value * k
    s = prefix + (fmt.format(v)) + suffix
    label(L, t, 0.0, label_s, X0, 300)
    big_number(L, s, X0 - 12, 350, 260, ease_in_out((t - 0.2) / 1.6), a=ease_out(t / 0.4))
    text(L, t, 0.5, body, X0, 720, F_SEMI, 58, lead=1.18)

def sc_quote(L, t, d, quote, who, year=""):
    q = line_img("“", F_SERIF_I, 360, AMBER)
    put(L, q, X0 - 20, 330 - (1 - ease_out(t / 0.6)) * 40, ease_out(t / 0.6))
    if year:
        label(L, t, 0.1, year, X0, 300)
    y = text(L, t, 0.3, quote, X0, 640, F_SERIF_I, 84, lead=1.12, stagger=0.1)
    text(L, t, 0.9, who, X0, y + 40, F_REG, 40, color=(190, 198, 214), lead=1.3)

def sc_end(L, t, d, big, small, cta):
    y = text(L, t, 0.1, big, X0, 600, F_BOLD, 96, lead=1.06, stagger=0.1)
    y = text(L, t, 0.6, small, X0, y + 36, F_SERIF_I, 60, color=GLASS)
    k = ease_back((t - 1.1) / 0.6)
    if k > 0:
        im = line_img(cta, F_SEMI, 44, INK)
        pad = 28
        pill = Image.new("RGBA", (im.width + pad * 2, im.height + pad), (0, 0, 0, 0))
        ImageDraw.Draw(pill).rounded_rectangle([0, 0, pill.width - 1, pill.height - 1],
                                               radius=pill.height // 2, fill=IVORY + (255,))
        pill.alpha_composite(im, (pad, pad // 2 + 2))
        sz = (max(1, int(pill.width * k)), max(1, int(pill.height * k)))
        put(L, pill.resize(sz), X0, y + 70, clamp(k))

def sc_card(L, t, d, years, title, note, art, stat=""):
    """Exhibition card: an abstract homage panel plus caption."""
    k = ease_out(t / 0.6)
    pw, ph = 912, 760
    panel = art(pw, ph, t)
    mask = Image.new("L", (pw, ph), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, pw - 1, ph - 1], radius=36, fill=255)
    panel.putalpha(ImageChops.multiply(panel.getchannel("A"), mask))
    put(L, panel, X0, 300 + (1 - k) * 80, k)
    y = 1100
    y = label(L, t, 0.25, years, X0, y)
    y = text(L, t, 0.35, title, X0, y + 6, F_BOLD, 66, lead=1.08)
    y = text(L, t, 0.6, note, X0, y + 16, F_REG, 40, color=(205, 210, 222), lead=1.3)
    if stat:
        text(L, t, 0.9, stat, X0, y + 16, F_SEMI, 44, color=AMBER)


# ---------------------------------------------------------------- visuals
def v_building(L, t, d, sails=12, blocks=1, grow=False, y=1660, scale=0.78, colors=None, a=1.0):
    s = lerp(0, sails, ease_in_out((t - 0.2) / (d * 0.7))) if grow else sails
    b = lerp(0, blocks, ease_out((t - 0.1) / (d * 0.5))) if grow else blocks
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_building(lay, W / 2, y, scale, sails=s, blocks=b, colors=colors, t=t)
    put(L, lay, 0, (1 - ease_out(t / 0.8)) * 60, a * ease_out(t / 0.8))

def v_sails_count(L, t, d):
    v_building(L, t, d, sails=12, grow=True)

def v_stamp(L, t, d):
    v_building(L, t, d, sails=6, blocks=0.6, a=0.55)
    k = ease_back((t - 0.9) / 0.45)
    if k <= 0:
        return
    st = stamp_img()
    sz = 1.8 - 0.8 * k
    im = st.resize((int(st.width * sz), int(st.height * sz))).rotate(12, expand=True, resample=Image.BICUBIC)
    put(L, im, W / 2 - im.width / 2, 1330 - im.height / 2, clamp(k * 1.2))

@lru_cache(None)
def stamp_img():
    f = font(F_BLACK, 92)
    s1, s2 = "PERMIS", "ANNULÉ"
    w = int(max(f.getlength(s1), f.getlength(s2))) + 100
    im = Image.new("RGBA", (w, 280), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([6, 6, w - 6, 274], radius=18, outline=RED + (255,), width=10)
    d.text((w / 2, 82), s1, font=f, fill=RED + (255,), anchor="mm")
    d.text((w / 2, 196), s2, font=f, fill=RED + (255,), anchor="mm")
    rnd = np.random.default_rng(3)
    a = np.array(im.getchannel("A")).astype(np.float32)
    a *= (rnd.random(a.shape) > 0.12)
    im.putalpha(Image.fromarray(a.astype(np.uint8)))
    return im

def v_confetti(L, t, d):
    v_building(L, t, d, sails=12)
    rnd = random.Random(11)
    dr = ImageDraw.Draw(L)
    for i in range(70):
        x0 = rnd.uniform(60, W - 60)
        sp = rnd.uniform(160, 360)
        y = -40 + (t - rnd.uniform(0, 0.8)) * sp
        if y < -40 or y > 1500:
            continue
        x = x0 + math.sin(t * 2 + i) * 30
        r = rnd.uniform(8, 18)
        ang = t * rnd.uniform(1, 4) + i
        pts = [(x + r * math.cos(ang + k * 2.1), y + r * 0.6 * math.sin(ang + k * 2.1)) for k in range(3)]
        c = [GLASS, IVORY, AMBER][i % 3]
        dr.polygon(pts, fill=c + (200,))

@lru_cache(None)
def pane_grid():
    n, cell, gap = 60, 13, 1
    size = n * (cell + gap)
    rnd = np.random.default_rng(5)
    rgba = np.zeros((size, size, 4), np.uint8)
    order = np.zeros((size, size), np.float32) + 1e9
    for i in range(n):
        for j in range(n):
            y, x = i * (cell + gap), j * (cell + gap)
            tint = rnd.uniform(-1, 1)
            c = np.array(GLASS) + tint * np.array([40, 30, 15])
            rgba[y:y + cell, x:x + cell, :3] = np.clip(c, 0, 255)
            rgba[y:y + cell, x:x + cell, 3] = 235
            # sweep diagonally, like panes clipping onto a sail
            order[y:y + cell, x:x + cell] = (i + j) / (2 * n - 2) + rnd.uniform(0, 0.06)
    return rgba, order

def v_panes(L, t, d):
    rgba, order = pane_grid()
    k = ease_in_out((t - 0.1) / 1.6) * 1.07
    out = rgba.copy()
    out[..., 3] = np.where(order <= k, rgba[..., 3], 18)
    im = Image.fromarray(out, "RGBA").resize((680, 680))
    put(L, im, (W - 680) / 2, 980, ease_out(t / 0.4))

def v_iceberg(L, t, d):
    v_building(L, t, d, sails=0, blocks=1, grow=True, scale=0.85)

def v_galleries(L, t, d):
    dr = ImageDraw.Draw(L)
    rooms = [(0, 0, 3, 2), (3, 0, 5, 2), (5, 0, 8, 1), (5, 1, 8, 2), (0, 2, 2, 4), (2, 2, 4, 3),
             (2, 3, 4, 4), (4, 2, 8, 3), (4, 3, 6, 4), (6, 3, 8, 4), (1, 4, 6, 5)]
    u, ox, oy = 105, X0 + 10, 1060
    for i, (x1, y1, x2, y2) in enumerate(rooms):
        k = ease_out((t - 0.2 - i * 0.12) / 0.4)
        box = [ox + x1 * u + 6, oy + y1 * u + 6, ox + x2 * u - 6, oy + y2 * u - 6]
        dr.rectangle(box, outline=IVORY + (int(120 + 80 * k),), width=3)
        if k > 0:
            dr.rectangle([box[0] + 4, box[1] + 4, box[2] - 4, box[3] - 4], fill=AMBER + (int(150 * k),))
            dr.text((box[0] + 14, box[1] + 8), str(i + 1), font=font(F_MONO, 26), fill=INK + (int(255 * k),))

def v_seats(L, t, d):
    dr = ImageDraw.Draw(L)
    cx, cy = W / 2, 1000
    seats, row = [], 0
    while len(seats) < 350:
        r = 180 + row * 34
        n = 14 + row * 3
        for j in range(n):
            if len(seats) >= 350:
                break
            a = math.pi * (0.18 + 0.64 * j / (n - 1))
            seats.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        row += 1
    shown = int(350 * ease_in_out((t - 0.1) / 1.4))
    dr.rounded_rectangle([cx - 150, cy + 60, cx + 150, cy + 110], radius=10, fill=AMBER + (220,))
    for i, (x, y) in enumerate(seats):
        on = i < shown
        dr.ellipse([x - 9, y - 9, x + 9, y + 9], fill=(GLASS + (230,)) if on else (255, 255, 255, 25))

def v_ring(L, t, d):
    dr = ImageDraw.Draw(L)
    cx, cy, r = W / 2, 1360, 210
    k = ease_in_out((t - 0.1) / 2.0)
    dr.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255, 40), width=18)
    if k > 0:
        dr.arc([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * k, fill=AMBER + (255,), width=18)
    im = line_img("CITY OF PARIS", F_MONO, 30, IVORY, 3)
    put(L, im, cx - im.width / 2, cy - 20, ease_out((t - 1.6) / 0.5))

def v_scribble(L, t, d):
    rnd = random.Random(2)
    pts = []
    for i in range(900):
        u = i / 899
        x = 140 + u * 800 + 60 * math.sin(u * 23) + 30 * math.sin(u * 61 + 1)
        y = 1480 - 180 * math.sin(u * math.pi) + 90 * math.sin(u * 17) + 40 * math.cos(u * 41)
        pts.append((x, y))
    n = int(len(pts) * ease_in_out((t - 0.2) / (d * 0.75)))
    if n > 2:
        dr = ImageDraw.Draw(L)
        dr.line(pts[:n], fill=IVORY + (235,), width=5, joint="curve")
        x, y = pts[n - 1]
        dr.ellipse([x - 9, y - 9, x + 9, y + 9], fill=AMBER + (255,))

def v_glasshouse(L, t, d):
    dr = ImageDraw.Draw(L)
    cx, base = W / 2, 1640
    for i in range(9):
        k = ease_out((t - 0.2 - i * 0.1) / 0.6)
        if k <= 0:
            continue
        w = 820 - i * 70
        h = 560 - i * 40
        box = [cx - w / 2, base - h, cx + w / 2, base + h]
        dr.arc(box, 180, 180 + 180 * k, fill=(GLASS + (int(200 - i * 14),)), width=4)
    k = ease_out((t - 0.4) / 0.8)
    for j in range(-6, 7):
        x = cx + j * 62
        top = base - 560 * math.sqrt(max(0, 1 - (j * 62 / 410) ** 2))
        dr.line([(x, base), (x, lerp(base, top, k))], fill=(255, 255, 255, 50), width=2)
    dr.line([(80, base), (W - 80, base)], fill=IVORY + (180,), width=4)

def v_wireframe(L, t, d):
    dr = ImageDraw.Draw(L)
    cx, cy = W / 2, 1420
    rot = t * 0.6
    n = 16

    def surf(u, v):
        x = (u - 0.5) * 760
        z = (v - 0.5) * 420
        y = -140 * math.sin(math.pi * u) * (0.6 + 0.4 * v) - 90 * v + 60 * math.sin(3 * u + v)
        xr = x * math.cos(rot) - z * math.sin(rot)
        zr = x * math.sin(rot) + z * math.cos(rot)
        p = 900 / (900 + zr)
        return cx + xr * p, cy + (y + zr * 0.35) * p

    k = ease_out((t - 0.2) / 1.0)
    for i in range(n + 1):
        u = i / n
        dr.line([surf(u, j / 24) for j in range(25)], fill=GLASS + (int(200 * k),), width=2)
        dr.line([surf(j / 24, u) for j in range(25)], fill=(255, 255, 255, int(110 * k)), width=2)

def v_float(L, t, d):
    v_building(L, t, d, sails=12)
    dr = ImageDraw.Draw(L)
    for i in range(4):
        ph = (t * 0.5 + i / 4) % 1
        r = 60 + ph * 420
        dr.ellipse([W / 2 - r, 1720 - r * 0.12, W / 2 + r, 1720 + r * 0.12],
                   outline=(220, 240, 255, int(110 * (1 - ph))), width=3)

def v_skyline(L, t, d):
    dr = ImageDraw.Draw(L)
    base = 1700
    k = ease_out((t - 0.2) / 1.0)
    rise = (1 - k) * 200
    sky = [(100, 200), (150, 260), (200, 230), (250, 320), (300, 190), (340, 290), (380, 220)]
    for x, h in sky:  # towers on the horizon
        dr.rectangle([x, min(base, base - h + rise), x + 38, base], fill=(120, 140, 175, 200))
    ex = 760  # a lattice tower silhouette
    pts = [(ex - 90, base), (ex - 15, base - 400 + rise), (ex - 5, base - 490 + rise),
           (ex + 5, base - 490 + rise), (ex + 15, base - 400 + rise), (ex + 90, base)]
    dr.polygon(pts, fill=(120, 140, 175, 220))
    dr.polygon([(ex - 45, base), (ex, base - 95), (ex + 45, base)], fill=INK + (255,))
    dr.line([(60, base), (W - 60, base)], fill=IVORY + (200,), width=4)
    # terrace rail in the foreground
    dr.line([(0, 1790), (W, 1760)], fill=IVORY + (230,), width=8)
    for x in range(20, W, 70):
        dr.line([(x, 1790 - x * 30 / W), (x, 1900)], fill=IVORY + (150,), width=4)


# exhibition homages (abstract, original drawings)
def art_buren(w, h, t):
    im = Image.new("RGBA", (w, h), (20, 26, 50, 255))
    cols = [(237, 64, 82), (255, 196, 54), (40, 170, 120), (60, 120, 230), (240, 120, 40), (180, 70, 190)]
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_building(lay, W / 2, 1400, 0.82, colors=cols, t=t, reflect=False)
    im.alpha_composite(lay.crop((W // 2 - w // 2, 1400 - h + 120, W // 2 + w // 2, 1400 + 120)))
    d = ImageDraw.Draw(im)
    for x in range(0, w, 87):  # 8.7 cm stripes, scaled
        d.rectangle([x, h - 40, x + 43, h], fill=IVORY + (255,))
    return im

def art_shchukin(w, h, t):
    im = Image.new("RGBA", (w, h), (196, 52, 40, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([0, h * 0.62, w, h], fill=(40, 110, 70, 255))
    for i in range(5):
        a = t * 0.8 + i * 2 * math.pi / 5
        x, y = w / 2 + 250 * math.cos(a), h * 0.5 + 120 * math.sin(a)
        d.ellipse([x - 55, y - 120, x + 55, y + 120], fill=(232, 150, 110, 255))
    d.ellipse([w / 2 - 330, h * 0.5 - 170, w / 2 + 330, h * 0.5 + 170], outline=(232, 150, 110, 255), width=16)
    return im

def art_schiele_basquiat(w, h, t):
    im = Image.new("RGBA", (w, h), (235, 222, 196, 255))
    d = ImageDraw.Draw(im)
    rnd = random.Random(4)
    for i in range(16):  # nervous contour lines
        y = 120 + i * 34
        pts = [(x, y + rnd.uniform(-14, 14)) for x in range(40, w // 2, 30)]
        d.line(pts, fill=(60, 40, 30, 200), width=3)
    cx, cy, s = w * 0.72, h * 0.45, 1.6 + 0.08 * math.sin(t * 4)
    crown = [(-90, 60), (-90, -10), (-60, -70), (-35, -10), (0, -90), (35, -10), (60, -70), (90, -10), (90, 60)]
    d.line([(cx + x * s, cy + y * s) for x, y in crown], fill=(20, 20, 20, 255), width=12, joint="curve")
    d.line([(cx - 90 * s, cy + 60 * s), (cx + 90 * s, cy + 60 * s)], fill=(20, 20, 20, 255), width=12)
    d.rectangle([w * 0.55, h * 0.75, w * 0.9, h * 0.82], fill=(230, 180, 20, 255))
    return im

def art_morozov(w, h, t):
    im = Image.new("RGBA", (w, h), (30, 70, 140, 255))
    d = ImageDraw.Draw(im)
    blocks = [(0, 0, 0.5, 0.45, (240, 200, 60)), (0.5, 0, 1, 0.3, (220, 90, 70)),
              (0.5, 0.3, 1, 0.7, (80, 150, 90)), (0, 0.45, 0.5, 1, (200, 120, 170)),
              (0.5, 0.7, 1, 1, (240, 150, 60))]
    for i, (x1, y1, x2, y2, c) in enumerate(blocks):
        k = ease_out((t - i * 0.12) / 0.5)
        d.rectangle([x1 * w + 14, y1 * h + 14, lerp(x1 * w + 14, x2 * w - 14, k), y2 * h - 14], fill=c + (255,))
    return im

def art_four_hands(w, h, t):
    im = Image.new("RGBA", (w, h), (250, 250, 245, 255))
    d = ImageDraw.Draw(im)
    cols = [(255, 92, 160), (255, 220, 0), (0, 170, 230), (255, 120, 40)]
    for i, c in enumerate(cols):
        x, y = (i % 2) * w / 2, (i // 2) * h / 2
        k = ease_out((t - i * 0.15) / 0.4)
        if k > 0:
            d.rectangle([x + 10, y + 10, x + w / 2 - 10, y + h / 2 - 10], fill=c + (255,))
    s = 1.3
    cx, cy = w / 2, h / 2
    crown = [(-90, 60), (-90, -10), (-60, -70), (-35, -10), (0, -90), (35, -10), (60, -70), (90, -10), (90, 60)]
    d.line([(cx + x * s, cy + y * s) for x, y in crown], fill=(10, 10, 10, 255), width=14, joint="curve")
    d.line([(cx - 90 * s, cy + 60 * s), (cx + 90 * s, cy + 60 * s)], fill=(10, 10, 10, 255), width=14)
    return im

def art_colorfield(w, h, t):
    im = Image.new("RGBA", (w, h), (90, 22, 26, 255))
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    glow = 0.5 + 0.5 * math.sin(t * 1.5)
    d.rectangle([70, 70, w - 70, h * 0.48], fill=(int(220 + 20 * glow), 110, 40, 255))
    d.rectangle([70, h * 0.55, w - 70, h - 70], fill=(40, 20, 50, 255))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(14)))
    return im

def art_pool(w, h, t):
    im = Image.new("RGBA", (w, h), (40, 150, 215, 255))
    d = ImageDraw.Draw(im)
    for i in range(14):
        y0 = 40 + i * 52
        pts = []
        for x in range(0, w + 30, 30):
            y = y0 + 16 * math.sin(x / 70 + t * 2 + i) + 10 * math.sin(x / 23 - t * 3)
            pts.append((x, y))
        d.line(pts, fill=(235, 250, 255, 210), width=5, joint="curve")
    d.rectangle([0, h - 90, w, h], fill=(236, 214, 170, 255))
    d.rectangle([w * 0.62, h - 230, w * 0.66, h - 90], fill=(250, 250, 250, 255))
    return im

def art_squeegee(w, h, t):
    rnd = np.random.default_rng(9)
    base = np.zeros((h, w, 3), np.float32)
    cols = np.array([[200, 40, 40], [240, 200, 60], [40, 90, 170], [30, 30, 30], [230, 230, 230], [60, 150, 110]])
    bands = rnd.integers(0, len(cols), size=40)
    edges = np.sort(rnd.integers(0, h, size=40))
    for e, b in zip(edges, bands):
        base[e:, :] = cols[b]
    shift = (np.sin(np.arange(h) / 37.0) * 40 + rnd.normal(0, 6, h)).astype(int)
    k = int(w * ease_in_out(t / 1.6))
    out = base.copy()
    for y in range(h):
        out[y] = np.roll(base[y], shift[y], axis=0)
    out[:, k:] = (out[:, k:] * 0.25 + 30)
    rgba = np.concatenate([np.clip(out, 0, 255).astype(np.uint8), np.full((h, w, 1), 255, np.uint8)], axis=2)
    return Image.fromarray(rgba, "RGBA")


# ---------------------------------------------------------------- the four reels
NIGHT = ((10, 16, 36), (4, 6, 14))
DUSK = ((24, 22, 52), (8, 10, 24))
DEEP = ((6, 28, 44), (3, 8, 16))
PLUM = ((34, 14, 36), (8, 6, 18))

REELS = [
    dict(
        n=1, slug="01-thirteen-years", title="13 years, 3,600 panes of glass, 1 act of Parliament",
        theme=NIGHT, seed=1,
        scenes=[
            Scene(3.6, sc_hook, kicker="Fondation Louis Vuitton", lines="It took 13 years, 3,600 panes of glass and an act of Parliament.",
                  accent="The story of a ship in the woods."),
            Scene(3.8, sc_year, year=2001, prev=0, tag="The meeting",
                  title="Bernard Arnault meets Frank Gehry.",
                  body="The LVMH chairman had seen Gehry’s Guggenheim in Bilbao. He wanted something just as bold for Paris.",
                  visual=v_scribble),
            Scene(3.8, sc_year, year=2006, prev=2001, tag="The plan",
                  title="The project is unveiled.",
                  body="An art foundation in the Bois de Boulogne, on land granted by the City of Paris, next to the Jardin d’Acclimatation.",
                  visual=v_building, vis_kw=dict(sails=3, blocks=0.4, a=0.7)),
            Scene(3.8, sc_year, year=2008, prev=2006, tag="The build",
                  title="Construction begins.",
                  body="Every curved glass panel is a one-off, shaped for its exact place in the sails.",
                  visual=v_building, vis_kw=dict(sails=12, blocks=1, grow=True)),
            Scene(4.0, sc_year, year=2011, prev=2008, tag="The twist",
                  title="A court cancels the building permit.",
                  body="A neighbourhood association wins its case. Work could stop.",
                  visual=v_stamp),
            Scene(4.4, sc_quote, year="2011 · The rescue",
                  quote="A major work of art for the whole world.",
                  who="Parliament declares the project of general interest. In 2012 the Constitutional Council lets it stand."),
            Scene(4.2, sc_year, year=2014, prev=2011, tag="20 October",
                  title="The Fondation opens.",
                  body="Twelve glass sails over the trees of western Paris.",
                  visual=v_confetti),
            Scene(4.0, sc_end, big="12 years ago today.", small="Happy birthday, Fondation.",
                  cta="Next: the building in numbers →"),
        ]),
    dict(
        n=2, slug="02-by-the-numbers", title="The Fondation Louis Vuitton in numbers",
        theme=DEEP, seed=2,
        scenes=[
            Scene(3.2, sc_hook, kicker="Fondation Louis Vuitton", lines="One building.\nNumbers that sound made up.",
                  accent="Count along."),
            Scene(4.4, sc_stat, value=12, fmt="{:.0f}", label_s="Glass sails",
                  body="Twelve sails of glass wrap the building like a ship under full canvas.", visual=v_sails_count,
                  count=lambda t, d: math.floor(12 * ease_in_out((t - 0.2) / (d * 0.7)) + 0.999) / 12),
            Scene(4.4, sc_stat, value=3600, fmt="{:,.0f}", prefix="~", label_s="Glass panels",
                  body="Each one curved to fit its own place. Every dot below is one pane.", visual=v_panes),
            Scene(4.2, sc_stat, value=19000, fmt="{:,.0f}", label_s="Ductal panels",
                  body="Fibre-reinforced concrete panels clad the white “iceberg” under the sails.", visual=v_iceberg),
            Scene(3.8, sc_stat, value=11, fmt="{:.0f}", label_s="Galleries",
                  body="Eleven galleries of different sizes, plus terraces on several levels.", visual=v_galleries),
            Scene(3.8, sc_stat, value=350, fmt="{:.0f}", label_s="Auditorium seats",
                  body="A modular auditorium for concerts, talks and performances.", visual=v_seats),
            Scene(4.2, sc_stat, value=55, fmt="{:.0f}", label_s="Years",
                  body="The land is granted for 55 years. Then the building goes to the City of Paris.", visual=v_ring),
            Scene(3.6, sc_end, big="Which number surprised you?", small="Tell me in the comments.",
                  cta="Next: how Gehry did it →"),
        ]),
    dict(
        n=3, slug="03-how-gehry-did-it", title="How Frank Gehry built a cloud of glass",
        theme=DUSK, seed=3,
        scenes=[
            Scene(3.4, sc_hook, kicker="Design secrets", lines="It started as a few loose lines on paper.",
                  accent="How Gehry built a cloud of glass."),
            Scene(4.0, sc_year, year=1, prev=0, tag="Step one · the sketch",
                  title="Fast, scribbled sketches.",
                  body="Gehry draws in quick loops: a sail, a cloud, a ship moving through the trees.",
                  visual=v_scribble),
            Scene(4.2, sc_year, year=2, prev=1, tag="Step two · the memory",
                  title="19th-century glass.",
                  body="He looked to the glass roof of the Grand Palais and the old glasshouses of the Jardin d’Acclimatation next door.",
                  visual=v_glasshouse),
            Scene(4.2, sc_year, year=3, prev=2, tag="Step three · the code",
                  title="Aerospace software.",
                  body="The sails were modelled with tools first built for aircraft design. No two glass panels are alike.",
                  visual=v_wireframe),
            Scene(4.0, sc_year, year=4, prev=3, tag="Step four · the water",
                  title="It floats.",
                  body="The building sits on a cascading water basin, so it seems to drift among the trees.",
                  visual=v_float),
            Scene(4.0, sc_year, year=5, prev=4, tag="Step five · the view",
                  title="Look up.",
                  body="Rooftop terraces frame La Défense on one side and the Paris skyline on the other.",
                  visual=v_skyline),
            Scene(3.8, sc_end, big="The building is the first artwork in the collection.",
                  small="Save this for your next trip to Paris.", cta="Next: the blockbuster shows →"),
        ]),
    dict(
        n=4, slug="04-blockbusters", title="12 years of blockbuster shows",
        theme=PLUM, seed=4,
        scenes=[
            Scene(3.2, sc_hook, kicker="Since 2014", lines="Some of the biggest art shows Paris has ever seen.",
                  accent="A short history in eight frames."),
            Scene(3.2, sc_card, years="2016", title="Daniel Buren colours the sails",
                  note="L’Observatoire de la lumière: coloured filters on the glass, with his signature stripes.", art=art_buren),
            Scene(3.4, sc_card, years="2016–2017", title="The Shchukin Collection",
                  note="Matisse, Picasso, Gauguin: Icons of Modern Art from a Moscow collector.",
                  stat="1.2M+ visitors, a French record at the time", art=art_shchukin),
            Scene(3.0, sc_card, years="2018–2019", title="Egon Schiele & Jean-Michel Basquiat",
                  note="Two artists who died at 28, shown side by side.", art=art_schiele_basquiat),
            Scene(3.2, sc_card, years="2021–2022", title="The Morozov Collection",
                  note="The second great Moscow collection comes to Paris.", stat="1.2M+ visitors", art=art_morozov),
            Scene(3.0, sc_card, years="2023", title="Basquiat × Warhol",
                  note="Painting four hands: the works they made together.", art=art_four_hands),
            Scene(3.0, sc_card, years="2023–2024", title="Mark Rothko",
                  note="A full retrospective across the whole building.", art=art_colorfield),
            Scene(3.2, sc_card, years="2025", title="David Hockney 25",
                  note="More than 400 works, from 1955 to 2025.", stat="900,000+ visitors", art=art_pool),
            Scene(3.0, sc_card, years="2025–2026", title="Gerhard Richter",
                  note="Six decades of painting, from photo-paintings to squeegee abstracts.", art=art_squeegee),
            Scene(3.6, sc_end, big="Which one did you see?", small="Or which one do you wish you had?",
                  cta="Follow for more art history"),
        ]),
]


# ---------------------------------------------------------------- frame + chrome
def chrome(L, t, reel, idx, local, durs):
    dr = ImageDraw.Draw(L)
    # story-style progress segments
    n = len(durs)
    gap, x, y, total = 8, 60, 120, W - 120
    seg = (total - gap * (n - 1)) / n
    for i in range(n):
        x1 = x + i * (seg + gap)
        dr.rounded_rectangle([x1, y, x1 + seg, y + 6], radius=3, fill=(255, 255, 255, 60))
        p = 1 if i < idx else (local / durs[i] if i == idx else 0)
        if p > 0:
            dr.rounded_rectangle([x1, y, x1 + seg * clamp(p), y + 6], radius=3, fill=(255, 255, 255, 230))
    im = line_img(f"FLV HISTORY  {reel['n']:02d}/04", F_MONO, 26, (210, 215, 228), 2)
    put(L, im, 60, 150)
    im = line_img(CREDIT.upper(), F_MONO, 26, (160, 168, 186), 2)
    put(L, im, W - 60 - im.width, 150)

def render_frame(reel, t, durs, starts):
    idx = max(i for i, s in enumerate(starts) if s <= t + 1e-9)
    idx = min(idx, len(durs) - 1)
    local = t - starts[idx]
    sc = reel["scenes"][idx]
    bg = background(t, reel["theme"], reel["seed"])
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sc.fn(L, local, sc.dur, **sc.kw)
    fade = clamp((sc.dur - local) / 0.32)
    if idx == len(durs) - 1:
        fade = 1.0
    L.putalpha(L.getchannel("A").point([int(v * fade) for v in range(256)]))
    bg.alpha_composite(L)
    chrome(bg, t, reel, idx, local, durs)
    return bg.convert("RGB")


# ---------------------------------------------------------------- soundtrack
def soundtrack(path, starts, total, seed):
    sr = 44100
    n = int(total * sr) + sr
    tt = np.arange(n) / sr
    out = np.zeros(n)
    rnd = np.random.default_rng(seed)
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    progs = [
        [[50, 57, 62, 66, 69], [47, 54, 62, 66, 69], [43, 55, 59, 62, 66], [45, 52, 57, 61, 64]],
        [[45, 52, 57, 60, 64], [41, 53, 57, 60, 65], [48, 55, 60, 64, 67], [43, 55, 59, 62, 67]],
        [[52, 59, 64, 67, 71], [48, 55, 60, 64, 71], [45, 57, 60, 64, 69], [47, 54, 59, 63, 66]],
        [[48, 55, 60, 64, 67], [45, 52, 60, 64, 69], [41, 53, 57, 60, 65], [43, 50, 59, 62, 67]],
    ]
    prog = progs[(seed - 1) % 4]
    bar = 4.0
    for b in range(int(total / bar) + 2):
        t0 = b * bar
        chord = prog[b % 4]
        seg = (tt >= t0) & (tt < t0 + bar + 2.0)
        lt = tt[seg] - t0
        env = np.clip(lt / 1.4, 0, 1) * np.clip((bar + 2.0 - lt) / 2.0, 0, 1)
        for m in chord:
            f = hz(m)
            for det in (-0.12, 0.12):
                ph = rnd.uniform(0, 6.28)
                out[seg] += 0.05 * env * np.sin(2 * np.pi * (f + det) * lt + ph)
                out[seg] += 0.012 * env * np.sin(2 * np.pi * 2 * (f + det) * lt + ph)
        # soft pulse on each beat
        for beat in range(4):
            bt = t0 + beat
            s2 = (tt >= bt) & (tt < bt + 0.5)
            l2 = tt[s2] - bt
            out[s2] += 0.05 * np.exp(-l2 * 9) * np.sin(2 * np.pi * hz(chord[0] - 12) * l2)
    # bell on each scene change
    for i, s in enumerate(starts):
        seg = (tt >= s) & (tt < s + 2.5)
        lt = tt[seg] - s
        f = hz(prog[0][-1] + (12 if i % 2 else 7))
        out[seg] += 0.10 * np.exp(-lt * 2.6) * (np.sin(2 * np.pi * f * lt) + 0.3 * np.sin(2 * np.pi * f * 2.76 * lt))
    fade = np.clip((total - tt) / 1.5, 0, 1) * np.clip(tt / 0.4, 0, 1)
    out = out * fade
    out = out / (np.max(np.abs(out)) + 1e-9) * 0.7
    pcm = (out[: int(total * sr)] * 32767).astype(np.int16)
    with wave.open(path, "wb") as wv:
        wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(sr)
        wv.writeframes(pcm.tobytes())


# ---------------------------------------------------------------- render
def timing(reel):
    durs = [s.dur for s in reel["scenes"]]
    starts = list(np.cumsum([0] + durs[:-1]))
    return durs, starts, sum(durs)

def render_reel(n):
    reel = next(r for r in REELS if r["n"] == n)
    os.makedirs(OUT, exist_ok=True)
    durs, starts, total = timing(reel)
    wav = os.path.join(OUT, f".{reel['slug']}.wav")
    soundtrack(wav, starts, total, reel["seed"])
    mp4 = os.path.join(OUT, f"{reel['slug']}.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", mp4]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    frames = int(total * FPS)
    for i in range(frames):
        p.stdin.write(render_frame(reel, i / FPS, durs, starts).tobytes())
    p.stdin.close(); p.wait()
    os.remove(wav)
    # cover image: the hook at full reveal
    render_frame(reel, min(2.6, durs[0] - 0.4), durs, starts).save(
        os.path.join(OUT, f"{reel['slug']}-cover.jpg"), quality=90)
    return mp4, total

def preview(reel):
    d = os.path.join(HERE, "preview"); os.makedirs(d, exist_ok=True)
    durs, starts, _ = timing(reel)
    for i, (s, du) in enumerate(zip(starts, durs)):
        render_frame(reel, s + du * 0.8, durs, starts).save(os.path.join(d, f"{reel['slug']}-{i}.jpg"), quality=80)

if __name__ == "__main__":
    args = sys.argv[1:]
    want = [int(a) for a in args if a.isdigit()] or [r["n"] for r in REELS]
    reels = [r for r in REELS if r["n"] in want]
    if "--preview" in args:
        for r in reels:
            preview(r)
    else:
        with Pool(min(4, len(reels))) as pool:
            for mp4, total in pool.map(render_reel, [r["n"] for r in reels]):
                print(f"{os.path.relpath(mp4, HERE)}  {total:.1f}s")
