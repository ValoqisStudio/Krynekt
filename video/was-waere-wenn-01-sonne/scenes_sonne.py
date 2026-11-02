# Scenes for "Was wäre wenn… Teil 1: Die Sonne verschwindet" – exec'd inside sonne.py (render4 core)

_r = np.random.default_rng(42)


def _fbm(h, w, seed, octaves=5):
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp = 1.0
    for o in range(octaves):
        sh, sw = max(2, h >> (octaves - o)), max(2, w >> (octaves - o))
        n = rng.random((sh, sw)).astype(np.float32)
        out += cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC) * amp
        amp *= 0.5
    out -= out.min()
    return out / out.max()


# Earth equirect texture (512x256)
_land = _fbm(1024, 2048, 7, 8)
_lat = np.abs(np.linspace(-1, 1, 1024))[:, None]
_lm = np.clip((_land - 0.55) * 30, 0, 1)[..., None]
_mount = np.clip((_land - 0.68) * 8, 0, 1)[..., None]
_landcol = np.array([0.16, 0.38, 0.14]) * (0.75 + 0.5 * _land[..., None]) * (1 - _mount) + np.array([0.45, 0.38, 0.25]) * _mount
_sea = np.array([0.02, 0.13, 0.40]) * (0.8 + 0.5 * _land[..., None])
EARTH_TEX = (_landcol * _lm + _sea * (1 - _lm)).astype(np.float32)
_ice = np.clip((_lat - 0.84) * 20, 0, 1)[..., None]
EARTH_TEX = (EARTH_TEX * (1 - _ice) + np.array([0.92, 0.95, 1.0]) * _ice).astype(np.float32)
CLOUDS = np.clip((_fbm(1024, 2048, 99, 8) - 0.52) * 3.2, 0, 1).astype(np.float32)
SUN_TEX = _fbm(512, 1024, 5, 8) ** 1.4


def render_globe(R, rot, light, tex, clouds=None, emissive=False, night=0.0, tint=None):
    """returns RGBA sprite of a textured sphere. light = (lx, ly) direction toward light in screen plane, None = unlit"""
    s = int(R * 2 + 4)
    y, x = np.mgrid[0:s, 0:s].astype(np.float32)
    dx, dy = (x + 0.5 - s / 2) / R, (y + 0.5 - s / 2) / R
    d2 = dx * dx + dy * dy
    a = np.clip((1 - np.sqrt(d2)) * R + 0.5, 0, 1)
    z = np.sqrt(np.clip(1 - d2, 0, 1))
    lon = (np.arctan2(dx, z) / (2 * np.pi) + rot) % 1.0
    lat = np.arcsin(np.clip(dy, -1, 1)) / np.pi + 0.5
    th, tw = tex.shape[:2]
    ui = (lon * (tw - 1)).astype(np.int32)
    vi = (lat * (th - 1)).astype(np.int32)
    col = tex[vi, ui] if tex.ndim == 3 else tex[vi, ui][..., None]
    if clouds is not None:
        cl = clouds[vi, (ui + int(rot * 40)) % tw][..., None]
        col = col * (1 - cl * 0.85) + cl * 0.95
    if emissive:
        limb = (0.55 + 0.45 * z)[..., None]
        col = col * limb
    elif light is not None:
        lx, ly = light
        lz = 0.25
        n = math.sqrt(lx * lx + ly * ly + lz * lz)
        diff = np.clip((dx * lx + dy * ly + z * lz) / n, 0, 1)
        col = col * (0.03 + 1.05 * diff ** 0.8)[..., None]
        rim = np.clip((1 - z) ** 3, 0, 1) * np.clip(diff * 2, 0, 1)
        col = col + rim[..., None] * np.array([0.3, 0.6, 1.0]) * 0.9
    if night > 0:
        col = col * (1 - night)
    if tint is not None:
        col = col * np.array(tint, np.float32)
    return np.dstack([np.clip(col, 0, 1.5), a]).astype(np.float32)


def draw_sun(c, cx, cy, R, t, op=1.0):
    if R < 2 or op <= 0:
        return
    tex = np.dstack([0.75 + 0.35 * SUN_TEX, 0.28 + 0.5 * SUN_TEX, 0.03 + 0.2 * SUN_TEX ** 2]).astype(np.float32)
    spr = render_globe(R, t * 0.03, None, tex, emissive=True)
    blit(c.glow, blob(int(R * 2.6), (1.0, 0.55, 0.12), 1.6), cx, cy, 0.6 * op, add=True)
    blit(c.img, blob(int(R * 1.6), (1.0, 0.5, 0.1), 2.4), cx, cy, 0.45 * op, add=True)
    blit(c.img, spr, cx, cy, op)
    blit(c.glow, spr, cx, cy, 0.22 * op, add=True)


def draw_earth(c, cx, cy, R, t, light=(-1.0, 0.0), night=0.0, frost=0.0):
    spr = render_globe(R, t * 0.02, light, EARTH_TEX, CLOUDS, night=night)
    if frost > 0:
        g = spr[..., :3].mean(axis=2, keepdims=True)
        spr[..., :3] = spr[..., :3] * (1 - frost) + (g * np.array([0.8, 0.9, 1.1]) + 0.15 * frost) * frost
    blit(c.glow, blob(int(R * 1.35), (0.3, 0.6, 1.0), 2.5), cx, cy, 0.35 * (1 - night * 0.8), add=True)
    blit(c.img, spr, cx, cy)


def series_badge(c, lt):
    a = ease(lt * 3)
    blit(c.img, txt("WAS WÄRE WENN…", 50, (255, 255, 255), 8, (0, 0, 0), F_BLACK, True), 540, 225, a)
    pill = np.dstack([np.ones((70, 220, 3), np.float32) * np.array([1.0, 0.25, 0.3]), rounded_mask(220, 70, 35)])
    blit(c.img, pill, 540, 300, a)
    blit(c.img, txt("TEIL 1", 44, (255, 255, 255), 0, font=F_BLACK), 540, 300, a)


def s3_hook(c, lt, p, t, dur):
    cam = dict(scale=1.0 + 0.05 * p, cx=540, cy=760, shake=0.0, desat=0.0)
    if lt < 0.3:
        cam["scale"] = 1.0 + 0.16 * (1 - ease_out(lt / 0.3))
    gone = dur - 0.7
    if lt < gone:
        R = 300 * (1 + 0.02 * math.sin(lt * 3))
        draw_sun(c, 540, 760, R, t)
    else:
        k = lt - gone
        R = 300 * max(0.0, 1 - k / 0.18)
        draw_sun(c, 540, 760, R, t)
        blit(c.glow, blob(500, (1, 0.9, 0.7), 1.5), 540, 760, max(0, 1 - k * 2.5) * 1.5, add=True)
        sparks(c, 540, 760, k, 77, n=70, col=np.array([1.0, 0.7, 0.3], np.float32), spd=1500)
        cam["shake"] = max(0, 1 - k * 3) * 26
    series_badge(c, lt)
    return cam


def s3_notice(c, lt, p, t, dur):
    cam = dict(scale=1.0 + 0.06 * p, cx=540, cy=760, shake=0.0, desat=0.0)
    # the sun "still" shines in the sky: we see old light
    draw_earth(c, 540, 1080, 520, t, light=(-0.6, -1.0))
    draw_sun(c, 300, 330, 110, t)
    blit(c.img, emoji("\U0001F60E", 150), 760, 470, ease(lt * 3))
    if lt > 1.0:
        sticker(c, "NICHTS PASSIERT?!", 540, 700, 74, (255, 226, 26), 11, (0, 0, 0), rot=-4, scale=back_out((lt - 1.0) / 0.25))
    return cam


def timer_text(sec):
    sec = max(0, sec)
    return f"{int(sec // 60):02d}:{int(sec % 60):02d}"


def s3_light(c, lt, p, t, dur):
    cam = dict(scale=1.0 + 0.04 * p, cx=540, cy=760, shake=0.0, desat=0.0)
    sx, ex = 150, 900
    y = 760
    # ghost of the sun
    c.circle(sx, y, 80, (1.0, 0.6, 0.2), 3)
    blit(c.img, txt("SONNE?", 40, (255, 170, 80), 6, (0, 0, 0), F_BLACK), sx, y + 130)
    draw_earth(c, ex, y, 90, t, light=(-1.0, 0.0))
    blit(c.img, txt("ERDE", 40, (120, 200, 255), 6, (0, 0, 0), F_BLACK), ex, y + 130)
    # dashed path
    for xx in range(sx + 90, ex - 100, 40):
        c.line([(xx, y), (xx + 18, y)], np.array([0.6, 0.6, 0.7]) * 0.6, 3)
    # last light packet travelling
    q = min(1.0, lt / max(1.0, dur - 0.5))
    lx = lerp(sx + 90, ex - 100, q)
    blit(c.glow, blob(70, (1.0, 0.85, 0.4), 2), lx, y, 1.0, add=True)
    blit(c.img, sphere(14, (1.0, 0.95, 0.7)), lx, y)
    for k in range(8):
        c.line([(lx - 30 - k * 25, y), (lx - 30 - k * 25 - 16, y)], YELLOW * (1 - k / 8), 4)
    # countdown 08:20 -> 00:00 mapped to scene
    remain = 500 * (1 - q)
    blit(c.img, txt(timer_text(remain), 170, (255, 226, 26), 14, (0, 0, 0), F_BLACK, True), 540, 420)
    blit(c.img, txt("BIS ES DUNKEL WIRD", 46, (255, 255, 255), 8, (0, 0, 0), F_BLACK, True), 540, 540)
    hud(c, "LICHT", lt)
    return cam


def s3_orbit(c, lt, p, t, dur):
    cam = dict(scale=1.0 + 0.04 * p, cx=540, cy=760, shake=0.0, desat=0.0)
    cx, cy, Ro = 540, 760, 360
    pts = [(cx + Ro * math.cos(a), cy + Ro * 0.62 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 140)]
    c.line(pts, np.array([0.5, 0.6, 0.8]) * 0.55, 3)
    c.circle(cx, cy, 60, (1.0, 0.6, 0.2), 3)
    blit(c.img, txt("?", 90, (255, 170, 80), 8, (0, 0, 0), F_BLACK), cx, cy)
    ang = -0.6 + lt * 0.55
    ex, ey = cx + Ro * math.cos(ang), cy + Ro * 0.62 * math.sin(ang)
    draw_earth(c, ex, ey, 70, t, light=(cx - ex, cy - ey))
    # gravity "wave" rings expanding from the sun position, same speed as light
    for k in range(4):
        rr = ((lt * 220 + k * 160) % 640)
        c.circle(cx, cy, rr, CYAN * 0.3 * (1 - rr / 640), 3)
    if lt > 0.6:
        sticker(c, "KREIST WEITER", 540, 1180, 74, (255, 255, 255), 11, (0, 0, 0), rot=-3, scale=back_out((lt - 0.6) / 0.25))
    if lt > dur * 0.6:
        k = lt - dur * 0.6
        blit(c.img, txt("SCHWERKRAFT = LICHTTEMPO", 52, (80, 225, 255), 9, (0, 0, 0), F_BLACK, True), 540, 330, ease(k * 3))
    return cam


def s3_dark(c, lt, p, t, dur):
    cam = dict(scale=1.0 + 0.08 * p, cx=540, cy=760, shake=0.0, desat=0.0)
    off = dur * 0.55
    night = 0.0 if lt < off else min(1.0, (lt - off) / 0.12)
    draw_earth(c, 540, 1080, 520, t, light=(-0.6, -1.0), night=night * 0.93)
    if lt < off:
        draw_sun(c, 300, 330, 110, t)
        blit(c.img, txt(timer_text(3 * (1 - lt / off)), 150, (255, 226, 26), 14, (0, 0, 0), F_BLACK, True), 540, 640)
    else:
        k = lt - off
        cam["shake"] = max(0, 1 - k * 3) * 22
        c.img *= max(0.18, 1 - k * 4)
        blit(c.img, txt("00:00", 150, (255, 60, 60), 14, (0, 0, 0), F_BLACK, True), 540, 640)
        blit(c.glow, blob(300, (1.0, 0.2, 0.2), 2), 540, 640, max(0, 0.6 - k), add=True)
    return cam


def s3_fly(c, lt, p, t, dur):
    cam = dict(scale=1.0 + 0.04 * p, cx=540, cy=760, shake=0.0, desat=0.0)
    cx, cy, Ro = 540, 820, 360
    pts = [(cx + Ro * math.cos(a), cy + Ro * 0.62 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 140)]
    for i in range(0, 139, 3):
        c.line(pts[i:i + 2], np.array([0.5, 0.6, 0.8]) * 0.35, 3)
    a0 = -math.pi / 2
    sx, sy = cx + Ro * math.cos(a0), cy + Ro * 0.62 * math.sin(a0)
    q = ease(lt / max(1.0, dur - 0.4))
    ex, ey = sx + q * 400, sy - q * 160
    c.line([(sx, sy), (ex, ey)], YELLOW * 0.7, 4)
    frost = min(1.0, q * 1.1)
    draw_earth(c, ex, ey, 95 * (1 - 0.45 * q), t, light=(-0.3, 0.2), night=0.55, frost=frost)
    if lt > 0.8:
        sticker(c, "AB INS ALL", 540, 1040, 80, (255, 255, 255), 11, (0, 0, 0), rot=3, scale=back_out((lt - 0.8) / 0.25))
    if q > 0.6:
        blit(c.img, emoji("\U0001F976", 170), 300, 420, ease((q - 0.6) * 4))
        blit(c.img, txt("EISKALT", 70, (170, 230, 255), 10, (0, 0, 0), F_BLACK, True), 300, 560, ease((q - 0.6) * 4))
    return cam


def s3_cta(c, lt, p, t, dur):
    cam = dict(scale=1.0 + 0.04 * p, cx=540, cy=800, shake=0.0, desat=0.0)
    draw_earth(c, 540, 620, 200, t, light=(-0.3, 0.2), night=0.6, frost=1.0)
    s = back_out(lt / 0.35)
    sticker(c, "TEIL 2?", 540, 330, 150, (255, 226, 26), 14, (0, 0, 0), rot=-5, scale=s)
    if lt > 1.0:
        k = ease_out((lt - 1.0) / 0.35)
        y = 980 + (1 - k) * 80
        box = np.dstack([np.ones((150, 860, 3), np.float32) * np.array([0.12, 0.12, 0.16]), rounded_mask(860, 150, 75) * 0.92])
        blit(c.img, box, 540, y, k)
        blit(c.img, sphere(40, (1.0, 0.5, 0.3)), 175, y, k)
        full = "Teil 2!!"
        msg = full[: int(max(0, lt - 1.4) * 10)]
        if msg:
            ts = txt(msg, 50, (255, 255, 255), 0, font=F_BOLD)
            blit(c.img, ts, 240 + ts.shape[1] / 2 - 30, y, k)
        if len(msg) == len(full):
            blit(c.img, emoji("\U0001F525", 56), 240 + txt(full, 50, font=F_BOLD).shape[1] - 10, y, k)
        blit(c.img, emoji("\U0001F447", 120), 540, y + 150 + 18 * math.sin(lt * 8), k)
    return cam


SCENES = [s3_hook, s3_notice, s3_light, s3_orbit, s3_dark, s3_fly, s3_cta, s_end]
