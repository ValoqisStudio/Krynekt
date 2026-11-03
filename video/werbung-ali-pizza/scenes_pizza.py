# Promo: Stiftung-Ali-Test-Pizza @ The Pizzary – exec'd inside pizza.py (render4 core)

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


exec(open("mascot_part.py").read().replace("x = 935", "x = 975").replace("y = 1165 +", "y = 185 +"))
TEN_AT = next(w["start"] for w in WORDS if w["text"].startswith("10!")) - SC[0]
PRICE_AT = next(w["start"] for w in WORDS if w["text"].startswith("9,90")) - SC[2]
MOODS = ["shock", "happy", "cool", "happy"]

PR = 360           # pizza radius
PS = PR * 2 + 40   # sprite size
_yy, _xx = np.mgrid[0:PS, 0:PS].astype(np.float32)
_dd = np.sqrt((_xx - PS / 2) ** 2 + (_yy - PS / 2) ** 2)
_ang = np.arctan2(_yy - PS / 2, _xx - PS / 2)


def blit4(dst, spr, cx, cy, op=1.0):
    """alpha-over onto an RGBA float canvas"""
    h, w = spr.shape[:2]
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(dst.shape[1], x0 + w), min(dst.shape[0], y0 + h)
    if X0 >= X1 or Y0 >= Y1:
        return
    s = spr[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
    a = s[..., 3:4] * op
    d = dst[Y0:Y1, X0:X1]
    da = d[..., 3:4]
    oa = a + da * (1 - a)
    d[..., :3] = (s[..., :3] * a + d[..., :3] * da * (1 - a)) / np.maximum(oa, 1e-6)
    d[..., 3:4] = oa


def _rgba(col, a):
    return np.dstack([np.clip(col, 0, 1), np.clip(a, 0, 1)]).astype(np.float32)


def make_base():
    edge = PR * (1 + 0.025 * np.sin(_ang * 7) + 0.015 * np.sin(_ang * 13 + 1))
    a = np.clip(edge - _dd + 0.5, 0, 1)
    n = _fbm(PS, PS, 3, 6)
    # crust: golden ring with char spots
    u = np.clip((_dd - PR * 0.80) / (PR * 0.2), 0, 1)
    puff = np.sin(u * math.pi)
    crust = np.array([0.86, 0.60, 0.30]) * (0.65 + 0.45 * puff)[..., None] * (0.85 + 0.3 * n)[..., None]
    char = (n > 0.78) * (u > 0.2)
    crust = crust * (1 - 0.55 * char[..., None])
    # sauce
    sr = PR * (0.82 + 0.02 * np.sin(_ang * 9))
    sa = np.clip(sr - _dd, 0, 1)
    sauce = np.array([0.72, 0.12, 0.06]) * (0.75 + 0.4 * n)[..., None]
    col = crust * (1 - sa[..., None]) + sauce * sa[..., None]
    # cheese
    cn = _fbm(PS, PS, 11, 6)
    ca = np.clip((cn - 0.32) * 6, 0, 1) * np.clip(PR * 0.8 - _dd, 0, 1)
    brown = np.clip((cn - 0.82) * 6, 0, 1)
    cheese = np.array([1.0, 0.93, 0.68]) * (0.85 + 0.2 * cn)[..., None] * (1 - 0.35 * brown[..., None]) + np.array([0.6, 0.35, 0.1]) * 0.35 * brown[..., None]
    col = col * (1 - ca[..., None]) + cheese * ca[..., None]
    # light from top-left
    lit = 1.05 - 0.15 * ((_xx + _yy) / (2 * PS))
    return _rgba(col * lit[..., None], a)


def item(size, fn, seed=0):
    s = int(size)
    y, x = np.mgrid[0:s, 0:s].astype(np.float32)
    return fn(x - s / 2 + 0.5, y - s / 2 + 0.5, s / 2, np.random.default_rng(seed))


def salami(x, y, r, rng):
    d = np.sqrt(x * x + y * y)
    rr = r * 0.92
    a = np.clip(rr - d, 0, 1)
    n = rng.random(x.shape).astype(np.float32)
    fat = cv2.GaussianBlur((n > 0.965).astype(np.float32), (0, 0), 1.6) * 3
    col = np.array([0.62, 0.08, 0.07]) * (0.8 + 0.25 * (1 - d / rr))[..., None]
    col = col * (1 - np.clip(fat, 0, 1)[..., None]) + np.array([0.95, 0.75, 0.7]) * np.clip(fat, 0, 1)[..., None]
    rim = np.clip((d - rr * 0.85) / (rr * 0.15), 0, 1)
    col = col * (1 - 0.45 * rim[..., None])
    hl = np.exp(-(((x + rr * 0.3) ** 2 + (y + rr * 0.35) ** 2) / (rr * 0.25) ** 2)) * 0.35
    return _rgba(col + hl[..., None], a)


def mushroom(x, y, r, rng):
    cap = np.clip((1 - (x / (r * 0.9)) ** 2 - ((y + r * 0.05) / (r * 0.55)) ** 2) * r * 0.5, 0, 1) * (y < r * 0.1)
    stem = ((np.abs(x) < r * 0.28) & (y >= -r * 0.05) & (y < r * 0.75)).astype(np.float32)
    stem = cv2.GaussianBlur(stem, (0, 0), 0.8)
    a = np.clip(cap + stem, 0, 1)
    col = np.array([0.93, 0.86, 0.74]) * np.ones_like(x)[..., None]
    edge = np.clip(1 - (x / (r * 0.9)) ** 2 - ((y + r * 0.05) / (r * 0.55)) ** 2, 0, 1)
    col = col * (0.75 + 0.25 * np.clip(edge * 4, 0, 1))[..., None]
    col = col * (1 - (cap > 0)[..., None] * (edge < 0.12)[..., None] * 0.45) + np.array([0.35, 0.2, 0.08]) * ((cap > 0) & (edge < 0.12))[..., None] * 0.6
    return _rgba(col, a)


def ring(x, y, r, rng, outer=(0.25, 0.55, 0.15), inner=(0.75, 0.85, 0.5), hole=0.55, seeds=True):
    d = np.sqrt(x * x + y * y)
    ro = r * 0.92
    a = np.clip(ro - d, 0, 1)
    col = np.array(outer) * (0.8 + 0.3 * (1 - d / ro))[..., None]
    hi = np.clip(ro * hole - d, 0, 1)
    col = col * (1 - hi[..., None]) + np.array(inner) * hi[..., None]
    if seeds:
        for k in range(5):
            ang = k * 1.26 + rng.uniform(0, 0.3)
            sx, sy = math.cos(ang) * ro * 0.28, math.sin(ang) * ro * 0.28
            sd = np.sqrt((x - sx) ** 2 + (y - sy) ** 2)
            sm = np.clip(ro * 0.08 - sd, 0, 1)
            col = col * (1 - sm[..., None]) + np.array([0.97, 0.95, 0.8]) * sm[..., None]
    hl = np.exp(-(((x + ro * 0.35) ** 2 + (y + ro * 0.4) ** 2) / (ro * 0.22) ** 2)) * 0.4
    return _rgba(col + hl[..., None], a)


def olive(x, y, r, rng):
    d = np.sqrt(x * x + y * y)
    ro = r * 0.9
    a = np.clip(ro - d, 0, 1) * (1 - np.clip(ro * 0.45 - d, 0, 1))
    col = np.array([0.06, 0.05, 0.06]) * np.ones_like(x)[..., None]
    hl = np.exp(-(((x + ro * 0.35) ** 2 + (y + ro * 0.45) ** 2) / (ro * 0.2) ** 2)) * 0.55
    return _rgba(col + hl[..., None], a)


def corn(x, y, r, rng):
    a = np.clip((1 - (x / (r * 0.8)) ** 2 - (y / (r * 0.95)) ** 2) * r * 0.6, 0, 1)
    col = np.array([1.0, 0.82, 0.15]) * (0.8 + 0.3 * np.clip(-y / r, 0, 1))[..., None]
    hl = np.exp(-(((x + r * 0.25) ** 2 + (y + r * 0.35) ** 2) / (r * 0.25) ** 2)) * 0.5
    return _rgba(col + hl[..., None], a)


def burrata(x, y, r, rng):
    d = np.sqrt(x * x + (y * 1.08) ** 2)
    ro = r * 0.9
    wob = 1 + 0.06 * np.sin(np.arctan2(y, x) * 5)
    a = np.clip(ro * wob - d, 0, 1)
    z = np.sqrt(np.clip(1 - (d / ro) ** 2, 0, 1))
    col = np.array([0.98, 0.97, 0.93]) * (0.72 + 0.3 * z)[..., None]
    hl = np.exp(-(((x + ro * 0.32) ** 2 + (y + ro * 0.38) ** 2) / (ro * 0.2) ** 2)) * 0.6
    knot = np.exp(-((x ** 2 + (y + ro * 0.5) ** 2) / (ro * 0.15) ** 2)) * 0.15
    return _rgba(col + hl[..., None] - knot[..., None], a)


def stracci(x, y, r, rng):
    m = np.zeros(x.shape, np.float32)
    s = x.shape[0]
    for k in range(9):
        p = rng.uniform(s * 0.2, s * 0.8, 2)
        q = p + rng.uniform(-s * 0.3, s * 0.3, 2)
        cv2.line(m, (int(p[0]), int(p[1])), (int(q[0]), int(q[1])), 1.0, int(rng.uniform(3, 7)), cv2.LINE_AA)
    m = cv2.GaussianBlur(m, (0, 0), 1.2)
    a = np.clip(m * 1.5, 0, 1)
    col = np.array([1.0, 0.98, 0.92]) * (0.8 + 0.2 * m)[..., None]
    return _rgba(col, a)


rng0 = np.random.default_rng(21)


def scatter(n, rmin, rmax, minsep, seed):
    rng = np.random.default_rng(seed)
    pts = []
    tries = 0
    while len(pts) < n and tries < 5000:
        tries += 1
        a, rr = rng.uniform(0, 2 * math.pi), math.sqrt(rng.uniform((rmin / PR) ** 2, (rmax / PR) ** 2)) * PR
        p = (rr * math.cos(a), rr * math.sin(a))
        if all((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 > minsep ** 2 for q in pts):
            pts.append(p)
    return pts


GROUPS = []   # (label, emoji, [(sprite, x, y)], start_lt)


def _mk(label, emo, fn, n, size, rmin, rmax, sep, seed, rot=True):
    pts = scatter(n, rmin, rmax, sep, seed)
    rng = np.random.default_rng(seed)
    items = []
    for i, (x, y) in enumerate(pts):
        spr = item(size * rng.uniform(0.9, 1.1), fn, seed * 100 + i)
        if rot:
            h, w = spr.shape[:2]
            M = cv2.getRotationMatrix2D((w / 2, h / 2), rng.uniform(0, 360), 1)
            spr = cv2.warpAffine(spr, M, (w, h))
        items.append((spr, x, y))
    return (label, emo, items)


GROUPS = [
    _mk("SALAMI", "\U0001F355", salami, 9, 104, 40, 260, 110, 1),
    _mk("CHAMPIGNONS", "\U0001F344", mushroom, 9, 78, 30, 270, 70, 2),
    _mk("PEPERONI", "\U0001F336️", ring, 11, 50, 20, 270, 50, 3),
    _mk("OLIVEN", "\U0001FAD2", olive, 13, 36, 20, 270, 40, 4),
    _mk("MAIS", "\U0001F33D", corn, 34, 20, 10, 275, 22, 5),
    _mk("BURRATA", "\U0001F9C0", burrata, 3, 140, 60, 190, 170, 6, rot=False),
    _mk("STRACCIATELLA", "\U0001F95B", stracci, 10, 90, 30, 250, 60, 7),
]
STARTS = [0.7, 1.95, 3.2, 4.45, 5.7, 6.95, 8.2]
HONEY_START = 9.45
BASE = make_base()


def honey_layer(prog):
    """golden drizzle drawn up to prog (0..1)"""
    lay = np.zeros((PS, PS, 4), np.float32)
    m = np.zeros((PS, PS), np.float32)
    pts = []
    for i in range(400):
        u = i / 399
        y = -PR * 0.68 + u * PR * 1.36 + 10 * math.sin(u * 53)
        x = math.sin(u * 17 + 0.6 * math.sin(u * 5)) * PR * 0.6 * math.sqrt(max(0, 1 - (y / (PR * 0.76)) ** 2)) + 22 * math.sin(u * 9 + 1)
        pts.append((x + PS / 2, y + PS / 2))
    k = int(len(pts) * prog)
    if k > 2:
        cv2.polylines(m, [np.int32(np.array(pts[:k]) * 4)], False, 1.0, 6, cv2.LINE_AA, shift=2)
        for j in range(0, k, 37):
            cv2.circle(m, (int(pts[j][0]), int(pts[j][1])), 7, 1.0, -1, cv2.LINE_AA)
    m = cv2.GaussianBlur(m, (0, 0), 1.0)
    hl = cv2.GaussianBlur(m, (0, 0), 0.6) - cv2.GaussianBlur(m, (0, 0), 2.5)
    col = np.array([0.9, 0.48, 0.05]) * np.ones((PS, PS, 1)) + np.clip(hl, 0, 1)[..., None] * 1.4
    lay = _rgba(col, m * 0.78)
    # chili flakes
    rng = np.random.default_rng(9)
    for i in range(int(60 * prog)):
        a, rr = rng.uniform(0, 6.28), math.sqrt(rng.uniform(0, 1)) * PR * 0.78
        cx, cy = int(PS / 2 + rr * math.cos(a)), int(PS / 2 + rr * math.sin(a))
        cv2.circle(lay, (cx, cy), 3, (0.75, 0.08, 0.04, 1.0), -1, cv2.LINE_AA)
    return lay


HONEY_FULL = honey_layer(1.0)


def compose_pizza(lt_build, full=False):
    """returns RGBA pizza sprite with toppings landed up to lt_build"""
    pz = BASE.copy()
    for gi, (label, emo, items) in enumerate(GROUPS):
        st = STARTS[gi]
        for ii, (spr, x, y) in enumerate(items):
            t0 = st + ii * (0.5 / max(1, len(items)))
            k = 1.0 if full else (lt_build - t0) / 0.28
            if k <= 0:
                continue
            k = min(1.0, k)
            sc = lerp(2.2, 1.0, ease_out(k))
            op = min(1.0, k * 2.5)
            dy = -(1 - ease_out(k)) * 160
            s = spr if abs(sc - 1) < 0.01 else cv2.resize(spr, None, fx=sc, fy=sc)
            if k < 1:
                # drop shadow while falling
                blit4(pz, blob(int(spr.shape[0] * 0.5), (0, 0, 0), 2.5), PS / 2 + x + 10, PS / 2 + y + 14, 0.35 * op)
            blit4(pz, s, PS / 2 + x, PS / 2 + y + dy, op)
            if k >= 1:
                pass
    hp = 1.0 if full else ease((lt_build - HONEY_START) / 1.4)
    if hp > 0:
        lay = HONEY_FULL if hp >= 1 else honey_layer(hp)
        blit4(pz, lay, PS / 2, PS / 2)
    pz[..., 3] = np.maximum(pz[..., 3], BASE[..., 3])
    return pz


PIZZA_FULL = compose_pizza(0, full=True)


def make_board():
    R = PR + 70
    s = R * 2 + 20
    y, x = np.mgrid[0:s, 0:s].astype(np.float32)
    d = np.sqrt((x - s / 2) ** 2 + (y - s / 2) ** 2)
    a = np.clip(R - d, 0, 1)
    grain = np.sin((x * 0.06 + np.sin(y * 0.01) * 6)) * 0.5 + 0.5
    n = _fbm(s, s, 17, 5)
    col = np.array([0.55, 0.34, 0.17]) * (0.75 + 0.15 * grain + 0.2 * n)[..., None]
    rim = np.clip((d - (R - 18)) / 18, 0, 1)
    col = col * (1 - 0.35 * rim[..., None])
    return _rgba(col, a)


BOARD = make_board()


def draw_pizza(c, cx, cy, sprite, rot, t, steam=True):
    blit(c.img, blob(PR + 140, (0, 0, 0), 2.2), cx + 25, cy + 40, 0.7)
    h, w = BOARD.shape[:2]
    blit(c.img, BOARD, cx, cy)
    M = cv2.getRotationMatrix2D((sprite.shape[1] / 2, sprite.shape[0] / 2), rot, 1.0)
    sp = cv2.warpAffine(sprite, M, (sprite.shape[1], sprite.shape[0]), flags=cv2.INTER_LINEAR)
    blit(c.img, blob(PR + 30, (0, 0, 0), 3), cx + 10, cy + 16, 0.5)
    blit(c.img, sp, cx, cy)
    blit(c.glow, blob(PR + 80, (1.0, 0.55, 0.2), 2.5), cx, cy, 0.25, add=True)
    if steam:
        for k in range(6):
            ph = (t * 0.35 + k / 6) % 1.0
            x0 = cx - 220 + k * 85
            pts = [(x0 + 22 * math.sin(ph * 9 + j * 0.5 + k), cy - 80 - ph * 420 - j * 14) for j in range(12)]
            c.line(pts, np.array([1, 1, 1]) * 0.12 * math.sin(ph * math.pi), 10)


def price_tag(c, cx, cy, sc, rot=-8):
    if sc < 0.05:
        return
    w, h = 620, 300
    tag = np.dstack([np.ones((h, w, 3), np.float32) * np.array([0.95, 0.12, 0.15]), rounded_mask(w, h, 40)])
    tag[..., :3] *= np.linspace(1.15, 0.8, h)[:, None, None]
    t1 = txt("NUR", 54, (255, 255, 255), 0, font=F_BLACK)
    t2 = txt("9,90 €", 150, (255, 230, 40), 10, (90, 0, 0), F_BLACK)
    blit4(tag, t1, w / 2, 58)
    blit4(tag, t2, w / 2, 190)
    tag[..., 3] = np.maximum(tag[..., 3], 0)
    M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, sc)
    M[0, 2] += 80; M[1, 2] += 120
    sp = cv2.warpAffine(tag, M, (w + 160, h + 240))
    blit(c.img, blob(300, (1.0, 0.2, 0.1), 2), cx, cy, 0.4 * min(1, sc), add=True)
    blit(c.img, sp, cx, cy)


def badge(c, s, cx, cy, size, bg, fg=(255, 255, 255), op=1.0, sc=1.0):
    if sc < 0.05 or op <= 0:
        return
    tt = txt(s, size, fg, 0, font=F_BLACK)
    w, h = tt.shape[1] + 30, int(size * 1.55)
    p = np.dstack([np.ones((h, w, 3), np.float32) * np.array(bg), rounded_mask(w, h, h // 2)])
    blit4(p, tt, w / 2, h / 2)
    if sc != 1:
        p = cv2.resize(p, None, fx=sc, fy=sc)
    blit(c.img, p, cx, cy, op)


def werbung(c):
    blit(c.img, txt("WERBUNG", 30, (255, 255, 255), 5, (0, 0, 0), F_BOLD), 110, 112, 0.85)


def s_p_hook(c, lt, p, t, dur):
    cam = dict(scale=1.0 + 0.05 * p, cx=540, cy=820, shake=0.0, desat=0.0)
    if lt < 0.3:
        cam["scale"] = 1.0 + 0.18 * (1 - ease_out(lt / 0.3))
    draw_pizza(c, 540, 860, PIZZA_FULL, lt * 12, t)
    badge(c, "STIFTUNG ALI TEST", 540, 300, 58, (0.05, 0.05, 0.08), (255, 226, 26), ease(lt * 4))
    badge(c, "HAT SEINE EIGENE PIZZA", 540, 395, 50, (1.0, 0.25, 0.25), op=ease((lt - 0.25) * 4))
    k = lt - TEN_AT
    if k > 0:
        sticker(c, "10/10", 790, 600, 150, (255, 226, 26), 14, (0, 0, 0), rot=-10, scale=back_out(k / 0.25, 2.2))
        sparks(c, 790, 600, k, 5, n=50, col=YELLOW, spd=1300)
        cam["shake"] = max(0, 1 - k * 4) * 18
    werbung(c)
    return cam


def s_p_build(c, lt, p, t, dur):
    cam = dict(scale=1.0 + 0.03 * p, cx=540, cy=820, shake=0.0, desat=0.0)
    pz = compose_pizza(lt)
    draw_pizza(c, 540, 860, pz, lt * 4, t, steam=lt > HONEY_START)
    blit(c.img, txt("DAS IST DRAUF", 70, (255, 255, 255), 10, (0, 0, 0), F_BLACK, True), 540, 230, ease(lt * 3))
    cur = None
    for gi, (label, emo, items) in enumerate(GROUPS):
        if lt >= STARTS[gi]:
            cur = (gi, label, emo, lt - STARTS[gi])
    if lt >= HONEY_START:
        cur = (7, "HOT HONEY", "\U0001F36F", lt - HONEY_START)
    if cur:
        gi, label, emo, k = cur
        s = back_out(k / 0.22, 2.0)
        colr = [(255, 120, 110), (240, 220, 190), (140, 230, 110), (200, 200, 210), (255, 220, 60), (255, 255, 255), (255, 255, 240), (255, 170, 40)][gi]
        sticker(c, label, 560, 345, 84, colr, 12, (0, 0, 0), rot=(-4 if gi % 2 else 4), scale=s)
        blit(c.img, emoji(emo, max(8, int(110 * min(1, s)))), 95, 345)
        if k < 0.2:
            cam["shake"] = 6
    # progress dots
    for i in range(8):
        on = lt >= (STARTS[i] if i < 7 else HONEY_START)
        c.circle(330 + i * 60, 1290, 12, (YELLOW if on else np.array([0.3, 0.3, 0.35])), -1)
    werbung(c)
    return cam


def s_p_price(c, lt, p, t, dur):
    cam = dict(scale=1.0 + 0.04 * p, cx=540, cy=820, shake=0.0, desat=0.0)
    draw_pizza(c, 540, 900, PIZZA_FULL, lt * 10, t)
    badge(c, "ANGEBOT", 540, 280, 66, (1.0, 0.25, 0.25), sc=back_out(lt / 0.3))
    k = lt - PRICE_AT
    if k > 0:
        price_tag(c, 560, 640, back_out(k / 0.25, 2.0))
        cam["shake"] = max(0, 1 - k * 4) * 22
        sparks(c, 560, 640, k, 8, n=60, col=YELLOW, spd=1400)
    werbung(c)
    return cam


def s_p_end(c, lt, p, t, dur):
    cam = dict(scale=1.0 + 0.03 * p, cx=540, cy=820, shake=0.0, desat=0.0)
    draw_pizza(c, 540, 700, PIZZA_FULL, t * 10, t)
    items = [("THE PIZZARY", 110, (255, 255, 255), 1110, 0.1),
             ("BERLIN", 70, (255, 226, 26), 1215, 0.25)]
    for s_, size, col, y, d in items:
        if lt > d:
            sticker(c, s_, 540, y, size, col, 12, (0, 0, 0), scale=back_out((lt - d) / 0.25))
    if lt > 0.45:
        badge(c, "AB 03.11.", 540, 260, 64, (1.0, 0.25, 0.25), sc=back_out((lt - 0.45) / 0.25))
    if lt > 0.8:
        blit(c.img, txt("@stiftung.ali.test", 52, (220, 230, 255), 8, (0, 0, 0), F_BLACK, True), 540, 1320, ease((lt - 0.8) * 3))
    werbung(c)
    return cam


SCENES = [s_p_hook, s_p_build, s_p_price, s_p_end]
