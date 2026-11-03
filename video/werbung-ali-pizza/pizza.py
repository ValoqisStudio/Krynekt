"""v2 renderer – creator-style edit for "Du hast dein Handy noch nie berührt".
Usage: python3 render2.py timing.json out.mp4 [audio.wav|mp3]
"""
import json, math, subprocess, sys
from functools import lru_cache
from multiprocessing import Pool

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
F_BLACK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
F_BOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
F_SEMI = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
F_EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

CYAN = np.array([0.25, 0.85, 1.0], np.float32)
ORANGE = np.array([1.0, 0.55, 0.2], np.float32)
YELLOW = np.array([1.0, 0.88, 0.1], np.float32)
RED = np.array([1.0, 0.18, 0.2], np.float32)
SKIN = np.array([0.90, 0.66, 0.52], np.float32)

timing = json.load(open(sys.argv[1]))
DUR = timing["duration"]
WORDS = timing["words"]
SC = timing["scenes"] + [DUR]


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


def back_out(x, s=1.7):
    x = min(1.0, max(0.0, x)) - 1
    return 1 + x * x * ((s + 1) * x + s)


def lerp(a, b, t):
    return a + (b - a) * t


# ------------------------------------------------------------------ sprites
def blit(dst, spr, cx, cy, op=1.0, add=False):
    h, w = spr.shape[:2]
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(dst.shape[1], x0 + w), min(dst.shape[0], y0 + h)
    if X0 >= X1 or Y0 >= Y1:
        return
    s = spr[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
    a = s[..., 3:4] * op
    d = dst[Y0:Y1, X0:X1]
    if add:
        d += s[..., :3] * a
    else:
        d *= (1 - a)
        d += s[..., :3] * a


def pil_to_f(img):
    return np.asarray(img.convert("RGBA"), np.float32) / 255.0


@lru_cache(maxsize=4096)
def txt(s, size, fill=(255, 255, 255), stroke=0, sfill=(0, 0, 0), font=F_BLACK, shadow=False):
    f = ImageFont.truetype(font, size)
    l, t, r, b = f.getbbox(s, stroke_width=stroke)
    pad = 30
    img = Image.new("RGBA", (r - l + pad * 2, b - t + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad - l + 4, pad - t + 8), s, font=f, fill=(0, 0, 0, 170), stroke_width=stroke, stroke_fill=(0, 0, 0, 170))
        arr = np.asarray(sh).copy()
        arr[..., 3] = cv2.GaussianBlur(arr[..., 3], (0, 0), 6)
        img = Image.fromarray(arr)
        d = ImageDraw.Draw(img)
    d.text((pad - l, pad - t), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
    return pil_to_f(img)


@lru_cache(maxsize=64)
def emoji(ch, size):
    f = ImageFont.truetype(F_EMOJI, 109)
    img = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((80, 80), ch, font=f, embedded_color=True, anchor="mm")
    img = img.crop(img.getbbox())
    m = max(img.size)
    sq = Image.new("RGBA", (m, m), (0, 0, 0, 0))
    sq.paste(img, ((m - img.size[0]) // 2, (m - img.size[1]) // 2))
    img = sq.resize((size, size), Image.LANCZOS)
    return pil_to_f(img)


@lru_cache(maxsize=512)
def sphere(r, col):
    col = np.array(col, np.float32)
    s = int(r * 2 + 4)
    y, x = np.mgrid[0:s, 0:s].astype(np.float32)
    dx, dy = (x + 0.5 - s / 2) / r, (y + 0.5 - s / 2) / r
    d2 = dx * dx + dy * dy
    a = np.clip((1 - np.sqrt(d2)) * r + 0.5, 0, 1)
    z = np.sqrt(np.clip(1 - d2, 0, 1))
    lx, ly = -0.45, -0.55
    lz = math.sqrt(1 - lx * lx - ly * ly)
    diff = np.clip(dx * lx + dy * ly + z * lz, 0, 1)
    spec = diff ** 40
    rim = (1 - z) ** 2.5
    c = col * (0.12 + 0.88 * diff)[..., None] + spec[..., None] * 0.9 + rim[..., None] * col * 0.7
    return np.dstack([np.clip(c, 0, 1), a]).astype(np.float32)


@lru_cache(maxsize=256)
def blob(r, col, k=3.0):
    s = int(r * 2)
    y, x = np.mgrid[0:s, 0:s].astype(np.float32)
    d2 = ((x - s / 2) ** 2 + (y - s / 2) ** 2) / (r * r)
    a = np.clip((np.exp(-d2 * k) - math.exp(-k)) / (1 - math.exp(-k)), 0, 1)
    return np.dstack([np.ones((s, s, 3), np.float32) * np.array(col, np.float32), a]).astype(np.float32)


def rounded_mask(w, h, r, ss=4):
    img = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(img).rounded_rectangle([0, 0, w * ss - 1, h * ss - 1], radius=r * ss, fill=255)
    return np.asarray(img.resize((w, h), Image.LANCZOS), np.float32) / 255.0


def make_finger(w=190, L=1300):
    Wc, Hc = w + 40, L
    y, x = np.mgrid[0:Hc, 0:Wc].astype(np.float32)
    cx, tipY = Wc / 2, Hc - 6
    tt = (tipY - y) / L
    hw = w / 2 * (0.88 + 0.12 * np.clip(tt * 3, 0, 1))
    r = w / 2 * 0.88
    ry = r * 1.2
    cy = tipY - ry
    below = y > cy
    ex, ey = (x - cx) / r, (y - cy) / ry
    tipd = (1 - np.sqrt(ex ** 2 + ey ** 2)) * r
    sd = np.where(below, tipd, hw - np.abs(x - cx))
    alpha = np.clip(sd + 0.5, 0, 1)
    u = np.clip((x - cx) / hw, -1, 1)
    nz = np.where(below, np.sqrt(np.clip(1 - ex ** 2 - ey ** 2, 0, 1)), np.sqrt(np.clip(1 - u ** 2, 0, 1)))
    lit = np.clip(0.25 + 0.75 * nz - 0.18 * u, 0, 1.1)
    col = SKIN[None, None] * lit[..., None] + np.array([0.55, 0.12, 0.08]) * ((1 - nz) ** 2 * 0.35)[..., None]
    rng = np.random.default_rng(3)
    noise = cv2.GaussianBlur(rng.normal(0, 1, (Hc, Wc)).astype(np.float32), (0, 0), 1.3) * 0.035
    col = col * (1 + noise[..., None])
    # knuckle creases
    for yc, amp in ((tipY - 390, 0.28), (tipY - 680, 0.33)):
        dd = np.exp(-(((y - yc - 22 * u ** 2) / 4.5) ** 2)) * amp * (np.abs(u) < 0.85)
        dd += np.exp(-(((y - yc - 14 - 22 * u ** 2) / 3.5) ** 2)) * amp * 0.6 * (np.abs(u) < 0.7)
        col = col * (1 - dd[..., None])
    # nail
    ny = tipY - 125
    nm = ((x - cx) / (r * 0.66)) ** 4 + ((y - ny) / 105) ** 4
    nail = np.clip((1 - nm) * 12, 0, 1)
    ncol = np.array([0.97, 0.78, 0.74]) * (0.55 + 0.5 * lit[..., None])
    free = np.clip((y - (tipY - 58)) / 14, 0, 1)[..., None]
    ncol = ncol * (1 - free) + np.array([1.0, 0.95, 0.9]) * free * (0.6 + 0.4 * lit[..., None])
    hl = np.exp(-((u + 0.3) / 0.09) ** 2)[..., None] * 0.35
    ncol = ncol + hl
    edge = np.clip((1 - nm) * 12, 0, 1) - np.clip((1 - nm) * 3, 0, 1)
    col = col * (1 - nail[..., None]) + ncol * nail[..., None]
    col = col * (1 - 0.25 * np.clip(edge, 0, 1)[..., None])
    return np.dstack([np.clip(col, 0, 1), alpha]).astype(np.float32)


def make_phone(w=540, h=1100):
    body = rounded_mask(w, h, 92)
    bez = np.pad(rounded_mask(w - 16, h - 16, 84), 8)
    scr = np.pad(rounded_mask(w - 44, h - 44, 70), 22)
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    fx = x / w
    metal = 0.42 + 0.35 * np.exp(-((fx - 0.08) / 0.05) ** 2) + 0.2 * np.exp(-((fx - 0.9) / 0.06) ** 2)
    col = np.dstack([metal * 0.78, metal * 0.80, metal * 0.86])
    col = col * (1 - bez[..., None]) + np.array([0.01, 0.01, 0.015]) * bez[..., None]
    # wallpaper
    fy = y / h
    wp = np.dstack([lerp(0.22, 0.02, fy), lerp(0.08, 0.04, fy), lerp(0.48, 0.18, fy)])
    for bx, by, br, bc in ((0.15, 0.7, 0.55, (0.95, 0.2, 0.6)), (0.9, 0.35, 0.5, (0.1, 0.65, 1.0)), (0.6, 0.95, 0.45, (1.0, 0.5, 0.15))):
        g = np.exp(-(((fx - bx) ** 2 + ((fy - by) * h / w) ** 2) / (br * br)) * 2.2)
        wp = wp + g[..., None] * np.array(bc) * 0.55
    wp = np.clip(wp, 0, 1)
    # lock screen text
    li = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dd = ImageDraw.Draw(li)
    dd.text((w / 2, h * 0.115), "Montag, 2. November", font=ImageFont.truetype(F_SEMI, 30), fill=(255, 255, 255, 230), anchor="mm")
    dd.text((w / 2, h * 0.205), "9:41", font=ImageFont.truetype(F_BOLD, 168), fill=(255, 255, 255, 245), anchor="mm")
    dd.rounded_rectangle([w / 2 - 82, 38, w / 2 + 82, 84], radius=23, fill=(0, 0, 0, 255))
    dd.rounded_rectangle([w * 0.33, h - 46, w * 0.67, h - 38], radius=4, fill=(255, 255, 255, 200))
    for i, cxp in enumerate((0.2, 0.8)):
        dd.ellipse([w * cxp - 44, h * 0.88 - 44, w * cxp + 44, h * 0.88 + 44], fill=(255, 255, 255, 50))
    la = np.asarray(li, np.float32) / 255
    wp = wp * (1 - la[..., 3:4]) + la[..., :3] * la[..., 3:4]
    refl = 0.08 * np.exp(-(((x * 0.75 - y * 0.42) - w * 0.05) / 70) ** 2)
    wp = np.clip(wp + refl[..., None], 0, 1)
    col = col * (1 - scr[..., None]) + wp * scr[..., None]
    emis = wp * scr[..., None]
    return np.dstack([col, body]).astype(np.float32), emis.astype(np.float32), scr


FINGER = make_finger()
PHONE, PHONE_EMIS, PHONE_SCR = make_phone()
PH_H, PH_W = PHONE.shape[:2]

# background with bokeh
_rng = np.random.default_rng(11)
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_r = np.sqrt(((_xx - W / 2) / W) ** 2 + ((_yy - H * 0.42) / H) ** 2)
BG = np.dstack([lerp(0.06, 0.008, _r * 1.6), lerp(0.05, 0.01, _r * 1.6), lerp(0.13, 0.03, _r * 1.6)]).clip(0, 1).astype(np.float32)
BOKEH = np.zeros((H * 2, W, 3), np.float32)
for _ in range(38):
    rr = _rng.uniform(20, 90)
    c = [CYAN, np.array([0.6, 0.3, 1.0]), ORANGE][_rng.integers(0, 3)] * _rng.uniform(0.05, 0.16)
    cv2.circle(BOKEH, (int(_rng.uniform(0, W)), int(_rng.uniform(0, 2 * H))), int(rr), c.tolist(), -1, cv2.LINE_AA)
BOKEH = cv2.GaussianBlur(BOKEH, (0, 0), 10)
VIGN = (1 - 0.62 * np.clip(_r * 1.25, 0, 1) ** 2.0)[..., None].astype(np.float32)
GRAIN = [(_rng.normal(0, 1, (H // 2, W // 2, 1)).astype(np.float32)) for _ in range(6)]
SKINTEX = None


def skin_band(h):
    rng = np.random.default_rng(5)
    n = cv2.GaussianBlur(rng.normal(0, 1, (h, W)).astype(np.float32), (0, 0), 2.5)
    pores = (rng.random((h, W)) > 0.996).astype(np.float32)
    pores = cv2.GaussianBlur(pores, (0, 0), 2.0) * 6
    lines = np.sin(_xx[:h] * 0.035 + np.sin(_yy[:h] * 0.02) * 3) * 0.5 + 0.5
    v = 0.62 + n * 0.06 - pores * 0.25 - lines[..., None][..., 0] * 0.06
    return (SKIN[None, None] * v[..., None]).astype(np.float32)


SKINBAND = skin_band(700)


# ------------------------------------------------------------------ drawing helpers
class Ctx:
    def __init__(self):
        self.img = BG.copy()
        self.glow = np.zeros((H, W, 3), np.float32)
        self.lines = np.zeros((H, W, 3), np.uint8)

    def line(self, pts, col, th=3):
        pts = np.round(np.array(pts) * 16).astype(np.int32)
        cv2.polylines(self.lines, [pts], False, [int(c * 255) for c in col], th, cv2.LINE_AA, shift=4)

    def arrow(self, x0, y0, x1, y1, col, th=10):
        cv2.arrowedLine(self.lines, (int(x0), int(y0)), (int(x1), int(y1)), [int(c * 255) for c in col], th, cv2.LINE_AA, tipLength=0.35)

    def circle(self, x, y, r, col, th=3):
        cv2.circle(self.lines, (int(x * 16), int(y * 16)), int(r * 16), [int(c * 255) for c in col], th, cv2.LINE_AA, shift=4)

    def flush_lines(self, glow=0.8):
        l = self.lines.astype(np.float32) / 255
        self.img += l
        self.glow += l * glow
        self.lines[:] = 0


def draw_phone(c, cx, cy):
    blit(c.img, PHONE, cx, cy)
    x0, y0 = int(cx - PH_W / 2), int(cy - PH_H / 2)
    sl = c.glow[max(0, y0):y0 + PH_H, max(0, x0):x0 + PH_W]
    sl += PHONE_EMIS[max(0, -y0):max(0, -y0) + sl.shape[0], max(0, -x0):max(0, -x0) + sl.shape[1]] * 0.22


def finger_shadow(c, tipx, tipy, surf_y, strength=1.0):
    d = max(0.0, surf_y - tipy)
    op = strength * np.clip(1 - d / 260, 0, 1) * 0.75
    r = 70 + d * 0.5
    sh = blob(int(r), (0, 0, 0), 2.2)
    blit(c.img, sh, tipx + 18 + d * 0.15, surf_y - 10 + d * 0.1, op)


def draw_finger(c, tipx, tipy):
    blit(c.img, FINGER, tipx, tipy - FINGER.shape[0] / 2 + 6)


NUC = []
_g = (1 + 5 ** 0.5) / 2
for i in range(13):
    z = 1 - 2 * (i + 0.5) / 13
    rr = math.sqrt(1 - z * z)
    th = 2 * math.pi * i / _g
    NUC.append((rr * math.cos(th), rr * math.sin(th), z, i % 2))


def atom(c, cx, cy, R, t, hue=CYAN, orbits=3, nuc=True, seed=0.0, label_alpha=0):
    if R < 4:
        return
    blit(c.img, blob(max(4, int(R * 1.15)), tuple(hue * 0.5), 2.6), cx, cy, 0.55, add=True)
    blit(c.glow, blob(max(4, int(R * 1.15)), tuple(hue * 0.4), 2.6), cx, cy, 0.5, add=True)
    rx, ry = R * 0.95, R * 0.34
    elec = []
    for k in range(orbits):
        a = math.radians(k * 180 / orbits + 20 + seed * 40)
        ca, sa = math.cos(a), math.sin(a)
        pts = []
        for j in range(65):
            th = j / 64 * 2 * math.pi
            px, py = rx * math.cos(th), ry * math.sin(th)
            pts.append((cx + px * ca - py * sa, cy + px * sa + py * ca))
        c.line(pts, hue * 0.32, 2)
        sp = 2.2 + 0.4 * k
        for tr in range(14):
            th = (t - tr * 0.018) * sp + k * 2.1 + seed * 5
            px, py = rx * math.cos(th), ry * math.sin(th)
            ex, ey = cx + px * ca - py * sa, cy + px * sa + py * ca
            if tr == 0:
                elec.append((ex, ey, math.sin(th)))
            else:
                c.circle(ex, ey, max(1, R * 0.03 * (1 - tr / 14)), hue * (0.8 * (1 - tr / 14)), -1)
    if nuc:
        rn = R * 0.16
        rot = t * 0.9 + seed
        pts = []
        for (x, y, z, kind) in NUC:
            X = x * math.cos(rot) + z * math.sin(rot)
            Z = -x * math.sin(rot) + z * math.cos(rot)
            pts.append((Z, X, y, kind))
        pts.sort()
        for Z, X, Y, kind in pts:
            col = (0.95, 0.25, 0.2) if kind else (0.55, 0.62, 0.75)
            blit(c.img, sphere(max(2, int(rn * 0.62)), col), cx + X * rn, cy + Y * rn)
        blit(c.glow, blob(max(4, int(rn * 2)), (1.0, 0.45, 0.2), 3), cx, cy, 0.6, add=True)
    for ex, ey, z in elec:
        er = max(3, int(R * 0.06))
        blit(c.glow, blob(er * 3, tuple(hue), 3), ex, ey, 1.0, add=True)
        blit(c.img, sphere(er, (0.85, 0.97, 1.0)), ex, ey)


def sticker(c, s, cx, cy, size, fill, stroke=12, sfill=(255, 255, 255), rot=0.0, scale=1.0, op=1.0):
    if scale < 0.05 or op <= 0:
        return
    spr = txt(s, size, fill, stroke, sfill, F_BLACK, True)
    if rot or scale != 1.0:
        h, w = spr.shape[:2]
        M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, scale)
        nw, nh = int(w * scale * 1.2), int(h * scale * 1.6)
        M[0, 2] += nw / 2 - w / 2
        M[1, 2] += nh / 2 - h / 2
        spr = cv2.warpAffine(spr, M, (nw, nh), flags=cv2.INTER_LINEAR)
    blit(c.img, spr, cx, cy, op)


def hud(c, label, lt):
    if int(lt * 2) % 2 == 0:
        blit(c.img, sphere(11, (1.0, 0.15, 0.15)), 86, 150)
    blit(c.img, txt("REC", 34, (255, 255, 255), 0, font=F_BOLD), 140, 150)
    blit(c.img, txt(label, 34, (255, 255, 255), 0, font=F_BOLD), W - 60 - txt(label, 34, (255, 255, 255), 0, font=F_BOLD).shape[1] / 2 + 30, 150)
    col = (0.85, 0.85, 0.85)
    for (x, y, dx, dy) in ((50, 110, 1, 1), (W - 50, 110, -1, 1), (50, 1290, 1, -1), (W - 50, 1290, -1, -1)):
        c.line([(x + dx * 60, y), (x, y), (x, y + dy * 60)], col, 4)


# ------------------------------------------------------------------ scenes
# each returns camera dict: scale, cx, cy, shake, extra post fx
FREEZE0, FREEZE1 = 1.25, 2.35


def s_hook(c, lt, p, t, dur):
    pcx, pcy = 540, 880
    surf = pcy - PH_H / 2 + 600
    tl = min(lt, FREEZE0)
    tip = lerp(-120, surf - 18, ease_out(tl / FREEZE0))
    if lt > FREEZE1:
        tip = surf - 18 - 6 * math.sin((lt - FREEZE1) * 4)
    draw_phone(c, pcx, pcy)
    finger_shadow(c, 560, tip, surf)
    draw_finger(c, 560, tip)
    cam = dict(scale=1.0 + 0.04 * p, cx=540, cy=900, shake=0.0, desat=0.0)
    if lt < 0.35:
        cam["scale"] = 1.0 + 0.18 * (1 - ease_out(lt / 0.35))
    if FREEZE0 <= lt < FREEZE1:
        k = (lt - FREEZE0)
        cam.update(scale=lerp(1.0, 1.55, ease_out(k / 0.18)), cx=560, cy=surf - 30, shake=max(0, 1 - k * 4) * 22, desat=0.75)
        prog = ease_out((k - 0.08) / 0.3)
        if prog > 0:
            pts = []
            for j in range(int(80 * prog) + 1):
                a = -math.pi / 2 + j / 80 * 2 * math.pi * 1.08
                rr = 170 + 10 * math.sin(a * 3) + j * 0.25
                pts.append((560 + rr * 1.15 * math.cos(a), surf - 30 + rr * 0.8 * math.sin(a)))
            c.line(pts, RED, 13)
        sparks(c, 560, surf - 20, k, 1, col=np.array([1.0, 0.35, 0.3], np.float32))
        if k > 0.3:
            sticker(c, "STOPP!", 735, surf - 215, 84, (255, 40, 50), 14, (255, 255, 255), rot=8, scale=back_out((k - 0.3) / 0.25))
    elif lt >= FREEZE1:
        cam.update(scale=lerp(1.55, 1.12, ease((lt - FREEZE1) / 0.5)), cx=560, cy=lerp(surf - 30, 820, ease((lt - FREEZE1) / 0.5)))
    return cam


def s_atoms(c, lt, p, t, dur):
    cam = dict(scale=1.0 + 0.05 * p, cx=540, cy=820, shake=0.0, desat=0.0)
    R = 360 * back_out(lt / 0.8, 1.2)
    # zoom-through skin
    if lt < 0.55:
        k = lt / 0.55
        sk = SKINBAND[:640]
        z = 1 + 4 * k ** 2
        M = cv2.getRotationMatrix2D((W / 2, 320), 0, z)
        M[1, 2] += 820 - 320
        warped = cv2.warpAffine(sk, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        c.img = c.img * k + warped * (1 - k)
    atom(c, 540, 820, R, t)
    if lt > 1.0:
        a = ease((lt - 1.0) * 2.5)
        c.line([(540, 820), (760, 560), (900, 560)], ORANGE * a, 4)
        blit(c.img, txt("KERN", 54, (255, 160, 70), 8, (0, 0, 0), F_BLACK, True), 900, 515, a)
    if lt > 1.6:
        a = ease((lt - 1.6) * 2.5)
        c.line([(540 - 300, 900), (300, 1120), (180, 1120)], CYAN * a, 4)
        blit(c.img, txt("ELEKTRONEN", 54, (80, 225, 255), 8, (0, 0, 0), F_BLACK, True), 250, 1170, a)
    hud(c, "1.000.000.000×", lt)
    return cam


def field_lines(c, p1, p2, R, alpha):
    for (sx, sy) in (p1, p2):
        for i in range(18):
            a = i / 18 * 2 * math.pi + 0.17
            x, y = sx + (R + 6) * math.cos(a), sy + (R + 6) * math.sin(a)
            pts = [(x, y)]
            for _ in range(60):
                ex = ey = 0.0
                for qx, qy in (p1, p2):
                    dx, dy = x - qx, y - qy
                    d3 = (dx * dx + dy * dy) ** 1.5 + 1e-3
                    ex += dx / d3
                    ey += dy / d3
                n = math.hypot(ex, ey) + 1e-9
                x += ex / n * 14
                y += ey / n * 14
                pts.append((x, y))
                if not (-50 < x < W + 50 and 150 < y < 1350):
                    break
            c.line(pts, CYAN * 0.45 * alpha, 3)


def s_repel(c, lt, p, t, dur):
    cam = dict(scale=1.0 + 0.04 * p, cx=540, cy=820, shake=0.0, desat=0.0)
    HIT = 1.35
    if lt < HIT:
        gap = lerp(360, 150, ease(lt / HIT) ** 1.6)
    else:
        k = lt - HIT
        gap = 150 + 230 * ease_out(k / 0.6) + 15 * math.sin(k * 9) * math.exp(-k * 3)
    y = 820
    R = 120 * back_out(lt / 0.4, 1.4)
    p1, p2 = (540 - gap, y), (540 + gap, y)
    field_lines(c, p1, p2, R, min(1, lt * 2))
    for (x, yy) in (p1, p2):
        blit(c.glow, blob(int(R * 2), tuple(CYAN), 2.5), x, yy, 0.8, add=True)
        blit(c.img, sphere(max(3, int(R)), (0.12, 0.55, 0.95)), x, yy)
        blit(c.img, txt("−", 150, (255, 255, 255), 6, (10, 60, 110), F_BLACK), x, yy - 12)
    if lt >= HIT:
        k = lt - HIT
        if k < 0.6:
            c.circle(540, y, 60 + k * 900, np.array([1, 1, 1]) * (1 - k / 0.6), int(14 * (1 - k / 0.6)) + 1)
            blit(c.glow, blob(220, (1, 1, 1), 2), 540, y, max(0, 1 - k * 4), add=True)
        cam["shake"] = max(0, 1 - k * 3.5) * 26
        sparks(c, 540, y, k, 2, n=60, col=CYAN, spd=1300)
        a = ease(k * 3)
        for x, sgn in ((p1[0], -1), (p2[0], 1)):
            c.arrow(x + sgn * (R + 20), y + 230, x + sgn * (R + 20 + 170 * a), y + 230, YELLOW, 12)
    blit(c.img, txt("−", 64, (255, 255, 255), 0, font=F_BLACK), 0, 0, 0)  # warm cache
    if lt > 0.3:
        a = ease((lt - 0.3) * 3)
        sticker(c, "GLEICHE LADUNG", 540, 400, 66, (255, 255, 255), 10, (0, 0, 0), rot=-3, op=a)
    return cam


def atom_row(c, y, t, hue, seed, R=78, n=5):
    for i in range(n):
        atom(c, 108 + i * 216, y, R, t, hue, orbits=2, nuc=True, seed=seed + i * 0.37)


def s_contact(c, lt, p, t, dur):
    cam = dict(scale=1.0 + 0.04 * p, cx=540, cy=800, shake=0.0, desat=0.0)
    ap = ease_out(lt / 2.0)
    top = lerp(330, 600, ap)
    bot = 1030
    jit = 4 * math.sin(lt * 47) if ap > 0.97 else 0
    # skin band
    sk = SKINBAND[-int(top - 100 + 1):] if top > 100 else SKINBAND[:1]
    hh = int(top - 95)
    if hh > 0:
        c.img[100:100 + hh] = c.img[100:100 + hh] * 0.15 + SKINBAND[-hh:] * 0.85
        blit(c.img, txt("FINGER", 46, (255, 225, 205), 8, (60, 30, 20), F_BLACK), 540, 230)
    atom_row(c, top + jit, t, np.array([1.0, 0.6, 0.35], np.float32), 0)
    atom_row(c, bot - jit, t, CYAN, 3)
    gl = c.img[bot + 85:1300]
    gy = np.linspace(0, 1, gl.shape[0])[:, None, None]
    c.img[bot + 85:1300] = gl * 0.2 + (np.array([0.05, 0.25, 0.4]) * (1 - gy * 0.6)) * 0.8
    blit(c.img, txt("DISPLAY", 46, (180, 240, 255), 8, (0, 30, 50), F_BLACK), 540, bot + 150)
    if ap > 0.85:
        a = ease((ap - 0.85) / 0.15)
        mid = (top + bot) / 2
        for k in range(4):
            pts = [(x, mid + (k - 1.5) * 26 + 10 * math.sin(x * 0.03 + t * 9 + k)) for x in range(0, W + 20, 20)]
            c.line(pts, YELLOW * 0.45 * a, 3)
        blit(c.glow, blob(420, (0.7, 0.55, 0.0), 1.6), 540, mid, a * 0.3, add=True)
        for i in range(5):
            x = 108 + i * 216
            c.arrow(x, mid - 30, x, mid - 30 - 70 * a, YELLOW, 8)
            c.arrow(x, mid + 30, x, mid + 30 + 70 * a, YELLOW, 8)
        sparks(c, 540, mid, lt - 2.0, 3, n=50)
        if lt > 2.3:
            sticker(c, "KEIN KONTAKT!", 540, mid, 76, (255, 40, 50), 12, (255, 255, 255), rot=-4, scale=back_out((lt - 2.3) / 0.25))
    hud(c, "SLOW-MO", lt)
    return cam


def s_force(c, lt, p, t, dur):
    cam = dict(scale=1.0 + 0.05 * p, cx=540, cy=800, shake=0.0, desat=0.0)
    bx, by = 760, 600
    fx, ftip = 320, 1120
    # display slab
    slab = c.img[ftip + 6:ftip + 90]
    c.img[ftip + 6:ftip + 90] = slab * 0.3 + np.array([0.05, 0.25, 0.4]) * 0.7
    c.line([(0, ftip + 6), (W, ftip + 6)], CYAN * 0.9, 4)
    draw_finger(c, fx, ftip)
    # nerve: up inside the finger, then across to the brain
    ctrl = [(fx, ftip - 90), (fx, 700), (fx + 40, 420), (bx - 120, by + 40)]
    pts = []
    for i in range(41):
        q = i / 40
        x = (1-q)**3*ctrl[0][0] + 3*(1-q)**2*q*ctrl[1][0] + 3*(1-q)*q*q*ctrl[2][0] + q**3*ctrl[3][0]
        y = (1-q)**3*ctrl[0][1] + 3*(1-q)**2*q*ctrl[1][1] + 3*(1-q)*q*q*ctrl[2][1] + q**3*ctrl[3][1]
        pts.append((x, y))
    c.line(pts, np.array([0.75, 0.45, 1.0]) * 0.8, 8)
    arrive = 0.0
    for k in range(3):
        q = (lt * 0.8 + k / 3) % 1.0
        for tr in range(9):
            qq = max(0, q - tr * 0.012) * 40
            j0 = int(qq)
            tx = lerp(pts[j0][0], pts[min(j0 + 1, 40)][0], qq - j0)
            ty = lerp(pts[j0][1], pts[min(j0 + 1, 40)][1], qq - j0)
            c.circle(tx, ty, 15 * (1 - tr / 9), YELLOW * (1 - tr / 9), -1)
            if tr == 0:
                blit(c.glow, blob(60, tuple(YELLOW), 3), tx, ty, 1.0, add=True)
        if q > 0.88:
            arrive = max(arrive, (q - 0.88) / 0.12)
    sc = 1 + 0.1 * arrive
    blit(c.glow, blob(260, (0.9, 0.35, 0.6), 2.2), bx, by, 0.35 + 0.65 * arrive, add=True)
    blit(c.img, emoji("\U0001F9E0", int(300 * sc)), bx, by)
    if arrive > 0.3:
        blit(c.img, emoji("\u26A1", 110), bx + 150, by - 150, arrive)
    if lt > 0.2:
        a = ease((lt - 0.2) * 3)
        sticker(c, "BERÜHRUNG", 760, 230, 64, (255, 255, 255), 10, (0, 0, 0), rot=-4, op=a)
        if lt > 0.8:
            s_ = ease((lt - 0.8) / 0.3)
            c.line([(585, 248), (585 + 350 * s_, 212)], RED, 12)
        if lt > 1.3:
            sticker(c, "KRAFT!", 760, 340, 96, (255, 225, 30), 12, (0, 0, 0), rot=5, scale=back_out((lt - 1.3) / 0.25))
    return cam


def s_hover(c, lt, p, t, dur):
    cam = dict(scale=1.0 + 0.05 * p, cx=540, cy=850, shake=0.0, desat=0.0)
    pcx, pcy = 540, 1010
    surf = pcy - PH_H / 2 + 620
    tipx = 400
    tip = surf - 14 + 5 * math.sin(lt * 3)
    draw_phone(c, pcx, pcy)
    finger_shadow(c, tipx, tip, surf)
    draw_finger(c, tipx, tip)
    # loupe
    a = back_out((lt - 0.4) / 0.4)
    if lt > 0.4:
        lx, ly, lr = 760, 420, int(215 * min(1, a))
        if lr > 10:
            c.flush_lines()
            sub = Ctx()
            sub.img[:] = 0.02
            for i in range(3):
                atom(sub, 330 + i * 210, 270, 92, t, np.array([1.0, 0.6, 0.35], np.float32), 2, True, i * 0.4)
                atom(sub, 330 + i * 210, 490, 92, t, CYAN, 2, True, 1 + i * 0.4)
            sub.arrow(540, 380, 540, 300, YELLOW, 8)
            sub.arrow(540, 380, 540, 460, YELLOW, 8)
            sub.flush_lines()
            sub.img += sub.glow * 0.5
            crop = sub.img[380 - 230:380 + 230, 540 - 230:540 + 230]
            crop = cv2.resize(crop, (lr * 2, lr * 2))
            mask = np.zeros((lr * 2, lr * 2), np.float32)
            cv2.circle(mask, (lr, lr), lr - 2, 1.0, -1, cv2.LINE_AA)
            spr = np.dstack([crop, mask])
            c.line([(tipx + 60, tip + 10), (lx - lr * 0.6, ly + lr * 0.75)], (0.9, 0.9, 0.9), 4)
            blit(c.img, spr, lx, ly)
            c.circle(lx, ly, lr, (0.85, 0.88, 0.95), 14)
            c.circle(lx - lr * 0.35, ly - lr * 0.35, lr * 0.28, (0.25, 0.25, 0.3), 3)
            if lt > 0.9:
                blit(c.img, txt("0,0000000001 m", 46, (255, 225, 30), 9, (0, 0, 0), F_BLACK, True), lx, ly - lr - 50, ease((lt - 0.9) * 3))
    return cam


def s_cta(c, lt, p, t, dur):
    cam = dict(scale=1.0 + 0.04 * p, cx=540, cy=800, shake=0.0, desat=0.0)
    s = back_out(lt / 0.4)
    blit(c.glow, blob(330, (1.0, 0.75, 0.1), 2.2), 540, 470, 0.7, add=True)
    blit(c.img, emoji("🤯", max(8, int(360 * s * (1 + 0.04 * math.sin(lt * 6))))), 540, 470)
    if lt > 1.0:
        k = ease_out((lt - 1.0) / 0.35)
        y = 880 + (1 - k) * 80
        box = np.dstack([np.ones((150, 860, 3), np.float32) * np.array([0.12, 0.12, 0.16]), rounded_mask(860, 150, 75) * 0.92])
        blit(c.img, box, 540, y, k)
        blit(c.img, sphere(40, (0.6, 0.4, 1.0)), 175, y, k)
        msg = "Nein, noch nie! 🤯"[: int(max(0, lt - 1.4) * 14)]
        msg = msg.replace("🤯", "")
        if msg:
            blit(c.img, txt(msg, 46, (255, 255, 255), 0, font=F_BOLD), 240 + txt(msg, 46, (255, 255, 255), 0, font=F_BOLD).shape[1] / 2 - 30, y, k)
        if int(lt * 3) % 2 == 0 and lt < 2.6:
            blit(c.img, txt("|", 50, (255, 255, 255), 0, font=F_SEMI), 250 + (txt(msg, 46, font=F_BOLD).shape[1] - 60 if msg else 0), y, k)
        blit(c.img, emoji("👇", 130), 540, y + 150 + 18 * math.sin(lt * 8), k)
    return cam


def s_end(c, lt, p, t, dur):
    cam = dict(scale=1.0 + 0.03 * p, cx=540, cy=800, shake=0.0, desat=0.0)
    s = back_out(lt / 0.5, 1.3)
    atom(c, 540, 640, 300 * s, t)
    if lt > 0.25:
        k = back_out((lt - 0.25) / 0.3)
        sticker(c, "UNSICHTBAR", 540, 1060, 120, (255, 255, 255), 12, (0, 0, 0), scale=k)
    if lt > 0.4:
        k = back_out((lt - 0.4) / 0.3)
        sticker(c, "ERKLÄRT", 540, 1190, 120, (255, 226, 26), 12, (0, 0, 0), scale=k)
    if lt > 0.8:
        a = ease((lt - 0.8) * 3)
        blit(c.img, txt("Folgen für mehr", 56, (220, 230, 255), 8, (0, 0, 0), F_BLACK, True), 500, 1330, a)
        blit(c.img, emoji("\U0001F92F", 80), 790, 1325, a)
    return cam


SCENES = [s_hook, s_atoms, s_repel, s_contact, s_force, s_hover, s_cta, s_end]
exec(open("scenes_pizza.py").read())


# ------------------------------------------------------------------ captions
CHUNKS = []
_cur = []
for _w in WORDS:
    _cur.append(_w)
    if len(_cur) == 3 or _w["text"].rstrip().endswith((".", "?", ":", ",", "!")):
        CHUNKS.append(_cur)
        _cur = []
if _cur:
    CHUNKS.append(_cur)


def captions(img, t):
    for ch in CHUNKS:
        if ch[0]["start"] - 0.04 <= t <= ch[-1]["end"] + 0.12:
            words = [w["text"].upper().strip(",.:!„“\"") for w in ch]
            act = 0
            for i, w in enumerate(ch):
                if t >= w["start"] - 0.03:
                    act = i
            sprs = []
            for i, s in enumerate(words):
                col = (255, 226, 26) if i == act else (255, 255, 255)
                spr = txt(s, 98, col, 11, (0, 0, 0), F_BLACK, True)
                if i == act:
                    k = ease_out((t - ch[i]["start"]) / 0.12)
                    sc = lerp(1.22, 1.0, k)
                    if abs(sc - 1) > 0.01:
                        spr = cv2.resize(spr, None, fx=sc, fy=sc, interpolation=cv2.INTER_LINEAR)
                sprs.append(spr)
            gap = -30
            maxw = W - 90
            for i, sp in enumerate(sprs):
                if sp.shape[1] > maxw:
                    f = maxw / sp.shape[1]
                    sprs[i] = cv2.resize(sp, None, fx=f, fy=f)
            widths = [sp.shape[1] for sp in sprs]
            lines, cur, cw = [], [], 0
            for i, wdt in enumerate(widths):
                add = wdt + (gap if cur else 0)
                if cur and cw + add > maxw:
                    lines.append(cur)
                    cur, cw = [], 0
                    add = wdt
                cur.append(i)
                cw += add
            lines.append(cur)
            y0 = 1440 - (len(lines) - 1) * 58
            for li, line in enumerate(lines):
                lw = sum(widths[i] for i in line) + gap * (len(line) - 1)
                x = W / 2 - lw / 2
                for i in line:
                    blit(img, sprs[i], x + widths[i] / 2, y0 + li * 116)
                    x += widths[i] + gap
            return



def sparks(c, ox, oy, k, seed, n=46, col=YELLOW, spd=900):
    """burst of glowing streaks; k = seconds since burst"""
    if k < 0 or k > 0.9:
        return
    rng = np.random.default_rng(seed)
    ang = rng.uniform(0, 2 * math.pi, n)
    v = rng.uniform(0.35, 1.0, n) * spd
    fade = 1 - k / 0.9
    for a, vv in zip(ang, v):
        d = vv * (1 - math.exp(-k * 4)) / 4
        x, y = ox + math.cos(a) * d, oy + math.sin(a) * d + 220 * k * k
        L = 0.06 * vv * fade
        x0, y0 = x - math.cos(a) * L, y - math.sin(a) * L
        c.line([(x0, y0), (x, y)], col * fade, 4)
    blit(c.glow, blob(160, tuple(col), 2), ox, oy, max(0, 1 - k * 5), add=True)


EMOJI_MAP = {"10!": "\U0001F4AF", "angebot:": "\U0001F525"}
POPS = []
for _w in WORDS:
    _k = _w["text"].lower().strip("„“\"")
    if _k in EMOJI_MAP:
        POPS.append((_w["start"], EMOJI_MAP.pop(_k)))


def emoji_pops(img, t):
    for i, (st, e) in enumerate(POPS):
        k = t - st
        if 0 <= k < 1.1:
            sc = back_out(k / 0.22, 2.2) * (1 - ease((k - 0.85) / 0.25))
            if sc <= 0.02:
                continue
            spr = emoji(e, 150)
            h, w = spr.shape[:2]
            rot = 12 * (1 if i % 2 else -1) * (1 - ease(k / 0.3)) + (6 if i % 2 else -6)
            M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, sc)
            M[0, 2] += 40; M[1, 2] += 40
            spr = cv2.warpAffine(spr, M, (w + 80, h + 80))
            x = 180
            blit(img, spr, x, 1130 - 20 * math.sin(k * 6))


def light_leak(img, t):
    for b in SC[1:-1]:
        d = t - b
        if abs(d) < 0.35:
            a = (1 - abs(d) / 0.35) ** 1.5
            x = 540 + d * 1800
            for (ox, oy, r, col) in ((x, 600, 520, (1.0, 0.45, 0.15)), (x + 300, 1100, 420, (1.0, 0.2, 0.55))):
                blit(img, blob(r, col, 1.8), ox, oy, 0.55 * a, add=True)


HOOK_TITLE = None
HOOK_TEXT = None

WM = txt("@unsichtbar.erklaert", 36, (255, 255, 255), 4, (0, 0, 0), F_BOLD)

# ------------------------------------------------------------------ frame
def scene_at(t):
    si = 0
    for i in range(len(SC) - 1):
        if t >= SC[i]:
            si = i
    return si


def render_scene(t):
    si = scene_at(t)
    st, en = SC[si], SC[si + 1]
    lt, dur = t - st, en - st
    c = Ctx()
    off = int((t * 14) % H)
    c.img += BOKEH[off:off + H]
    cam = SCENES[si](c, lt, lt / max(0.01, dur), t, dur)
    c.flush_lines()
    # bloom
    small = cv2.resize(c.glow, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    b = cv2.GaussianBlur(small, (0, 0), 5) * 0.9 + cv2.GaussianBlur(small, (0, 0), 16) * 1.1
    img = c.img + cv2.resize(b, (W, H), interpolation=cv2.INTER_LINEAR)
    if cam["desat"] > 0:
        g = img.mean(axis=2, keepdims=True)
        img = img * (1 - cam["desat"]) + g * cam["desat"] * np.array([1.0, 0.92, 0.85])
    # camera
    s = cam["scale"]
    rng = np.random.default_rng(int(t * FPS))
    sx, sy = (rng.uniform(-1, 1, 2) * cam["shake"]) if cam["shake"] else (0, 0)
    sx += 4 * math.sin(t * 1.3) + 2 * math.sin(t * 3.1 + 1)
    sy += 4 * math.sin(t * 1.7 + 2) + 2 * math.sin(t * 2.6)
    M = cv2.getRotationMatrix2D((cam["cx"], cam["cy"]), sx * 0.06 + 0.25 * math.sin(t * 0.9), s)
    M[0, 2] += W / 2 - cam["cx"] + sx
    M[1, 2] += 820 - cam["cy"] + sy
    img = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return img, si


def frame(i):
    t = i / FPS
    img, si = render_scene(t)
    # whip transition around cuts
    for b in SC[1:-1]:
        d = t - b
        if abs(d) < 0.13:
            k = 1 - abs(d) / 0.13
            shift = int((-1 if d < 0 else 1) * k * k * 420)
            Mw = np.float32([[1, 0, 0], [0, 1, shift]])
            img = cv2.warpAffine(img, Mw, (W, H), borderMode=cv2.BORDER_CONSTANT, borderValue=(0.02, 0.02, 0.05))
            ks = int(k * 110) | 1
            img = cv2.blur(img, (1, ks))
            img = img + k * k * 0.25
    light_leak(img, t)
    if HOOK_TEXT and t < 4.4:
        a = ease(t * 4) * (1 - ease((t - 4.1) / 0.3))
        ht = txt(HOOK_TEXT, 58, (20, 20, 20), 0, font=F_BLACK)
        bw = ht.shape[1] + 130
        pill = np.dstack([np.ones((120, bw, 3), np.float32) * np.array([1.0, 0.88, 0.1]), rounded_mask(bw, 120, 60)])
        sc_ = back_out(t / 0.3, 1.8)
        if sc_ > 0.05:
            blit(img, cv2.resize(pill, None, fx=sc_, fy=sc_), 500, 150, a)
            blit(img, cv2.resize(ht, None, fx=sc_, fy=sc_), 500 - 40 * sc_, 150, a)
            blit(img, emoji("\U0001F92F", int(86 * sc_) + 1), 500 + (bw / 2 - 60) * sc_, 150, a)
    if "MASCOT" in globals():
        MASCOT(img, t)
    emoji_pops(img, t)
    captions(img, t)
    if t < SC[-2]:
        blit(img, WM, W - 40 - WM.shape[1] / 2 + 20, 1700, 0.55)
    img *= VIGN
    g = cv2.resize(GRAIN[i % 6], (W, H), interpolation=cv2.INTER_NEAREST)[..., None]
    img += g * 0.022
    # subtle chromatic aberration
    img[..., 0] = np.roll(img[..., 0], 2, axis=1)
    img[..., 2] = np.roll(img[..., 2], -2, axis=1)
    # filmic tone
    img = np.clip(img, 0, None)
    img = img / (1 + img * 0.12) * 1.1
    return (np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes()


if __name__ == "__main__":
    out = sys.argv[2]
    audio = sys.argv[3] if len(sys.argv) > 3 else None
    only = sys.argv[4] if len(sys.argv) > 4 else None
    if only:  # stills: comma list of times
        for k, tt in enumerate(only.split(",")):
            arr = np.frombuffer(frame(int(float(tt) * FPS)), np.uint8).reshape(H, W, 3)
            Image.fromarray(arr).save(f"{out}_{k}.png")
        sys.exit()
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if audio:
        cmd += ["-i", audio, "-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = int(DUR * FPS)
    with Pool(4) as pool:
        for fb in pool.imap(frame, range(n), chunksize=4):
            proc.stdin.write(fb)
    proc.stdin.close()
    proc.wait()
    print("done", out, n)
