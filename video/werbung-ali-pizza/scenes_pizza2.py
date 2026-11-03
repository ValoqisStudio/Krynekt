# "Krass" promo v2: dialog (Ali + second speaker), no channel branding, fire + slams
exec(open("scenes_pizza.py").read())
if "MASCOT" in globals():
    del MASCOT

RED = np.array([1.0, 0.16, 0.12], np.float32)

# ---------- background: dark red radial pulse + halftone
_yy2, _xx2 = np.mgrid[0:H, 0:W].astype(np.float32)
_rad = np.sqrt(((_xx2 - W / 2) / W) ** 2 + ((_yy2 - H * 0.45) / H) ** 2)
BG_RED = np.dstack([0.22 * np.exp(-_rad * 3.2) + 0.02, 0.03 * np.exp(-_rad * 3.2) + 0.008, 0.02 * np.exp(-_rad * 3) + 0.01]).astype(np.float32)
_half = ((np.sin(_xx2 * 0.35) * np.sin(_yy2 * 0.35)) > 0.6).astype(np.float32) * np.clip(1 - _rad * 1.6, 0, 1) * 0.035
BG_RED += _half[..., None] * np.array([1.0, 0.4, 0.2], np.float32)
BOKEH = np.zeros((H * 2, W, 3), np.float32)   # disable bokeh drift
BG[:] = BG_RED

# ---------- fire
_FH, _FW = 200, 270
FIRE_NOISE = _fbm(_FH * 4, _FW, 77, 6)


def fire(c, t, strength=1.0, y_base=H):
    if strength <= 0:
        return
    off = int((t * 220) % (_FH * 3))
    n = FIRE_NOISE[off:off + _FH]
    yy = np.linspace(0, 1, _FH)[:, None]  # 0 top .. 1 bottom
    xx = np.linspace(-1, 1, _FW)[None, :]
    flame = np.clip(n * 1.25 - (1 - yy) * (1.25 - 0.35 * np.cos(xx * 3.0)) + 0.1, 0, 1) ** 1.5
    col = np.dstack([np.clip(flame * 3, 0, 1), np.clip(flame * 2 - 0.35, 0, 1), np.clip(flame * 2.2 - 1.3, 0, 1)]).astype(np.float32)
    big = cv2.resize(col, (W, int(H * 0.42)), interpolation=cv2.INTER_CUBIC) * strength
    y0 = int(y_base - big.shape[0])
    c.img[y0:y_base] += big
    c.glow[y0:y_base] += big * 0.6


def speed_lines(c, t, op=1.0, cx=540, cy=860):
    rng = np.random.default_rng(int(t * 30))
    for i in range(26):
        a = rng.uniform(0, 2 * math.pi)
        r0 = rng.uniform(520, 640)
        L = rng.uniform(150, 420)
        c.line([(cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + (r0 + L) * math.cos(a), cy + (r0 + L) * math.sin(a))], np.array([1, 0.9, 0.8]) * 0.55 * op, 4)


def slam(c, word, k, col=(255, 226, 26), size=150, rot=-6, y=430):
    if k < 0 or k > 1.2:
        return
    sc = lerp(2.3, 1.0, ease_out(k / 0.12)) if k < 0.12 else 1.0 + 0.04 * (k - 0.12)
    op = 1.0 if k < 0.95 else max(0, 1 - (k - 0.95) / 0.25)
    sticker(c, word, 540, y, size, col, 16, (0, 0, 0), rot=rot, scale=sc, op=op)


def lower_third(c, name, handle, k):
    if k <= 0:
        return
    x = lerp(-700, 0, ease_out(min(1, k / 0.35)))
    w, h = 720, 120
    p = np.dstack([np.ones((h, w, 3), np.float32) * np.array([0.05, 0.05, 0.07]), rounded_mask(w, h, 22) * 0.92])
    p[:, :16, :3] = RED
    blit4(p, txt(name, 54, (255, 255, 255), 0, font=F_BLACK), 40 + txt(name, 54, (255, 255, 255), 0, font=F_BLACK).shape[1] / 2, 44)
    blit4(p, txt(handle, 34, (255, 226, 26), 0, font=F_BOLD), 40 + txt(handle, 34, (255, 226, 26), 0, font=F_BOLD).shape[1] / 2, 92)
    blit(c.img, p, 60 + w / 2 + x, 1235)


def neon(c, s, cx, cy, size, t, col=(1.0, 0.25, 0.45)):
    flick = 0.55 if (int(t * 13) % 17 == 0) else 1.0
    spr = txt(s, size, (255, 255, 255), 0, font=F_BLACK)
    blit(c.glow, spr * np.array([*col, 1.0], np.float32), cx, cy, 1.6 * flick, add=True)
    blit(c.img, spr * np.array([*(np.array(col) * 0.6 + 0.4), 1.0], np.float32), cx, cy, flick)


def _wstart(key, after=0.0):
    for w in WORDS:
        if w["text"].lower().strip(".,!?:…„“\"").startswith(key) and w["start"] >= after:
            return w["start"]
    return None


# topping cue times (absolute) from narrator words
TOP_KEYS = ["salami", "champignons", "peperoni", "oliven", "mais", "burrata", "stracciatella", "honey"]
TOP_T = []
_prev = SC[1]
for k_ in TOP_KEYS:
    v = _wstart(k_, _prev)
    TOP_T.append(v if v is not None else _prev + 0.7)
    _prev = TOP_T[-1]
OWN_T = _wstart("eigene", SC[1]) or SC[1] + 2
ASK_T = _wstart("ali,", SC[1] + 3) or (SC[2] - 1.4)
HEUTE_T = _wstart("heute", SC[3]) or SC[3] + 0.3
HOLT_T = _wstart("holt", SC[3]) or SC[3] + 2.5
# map build-schedule to narrator cues
STARTS = [x - SC[1] for x in TOP_T[:7]]
HONEY_START = TOP_T[7] - SC[1]
TOP_LABEL = ["SALAMI", "CHAMPIGNONS", "PEPERONI", "OLIVEN", "MAIS", "BURRATA", "STRACCIATELLA", "HOT HONEY"]
TOP_COL = [(255, 110, 100), (240, 220, 190), (140, 235, 110), (210, 210, 220), (255, 220, 60), (255, 255, 255), (255, 255, 240), (255, 170, 40)]


def k2_hook(c, lt, p, t, dur):
    cam = dict(scale=1.0 + 0.06 * p, cx=540, cy=860, shake=0.0, desat=0.0)
    if lt < 0.3:
        cam["scale"] = 1.0 + 0.2 * (1 - ease_out(lt / 0.3))
    draw_pizza(c, 540, 860, PIZZA_FULL, lt * 14, t)
    fire(c, t, 0.55)
    badge(c, "STIFTUNG ALI TEST", 540, 230, 62, (0.04, 0.04, 0.05), (255, 226, 26), sc=back_out(lt / 0.3))
    badge(c, "HAT JETZT SEINE EIGENE PIZZA", 540, 330, 48, tuple(RED), sc=back_out((lt - 0.2) / 0.3))
    k = lt - TEN_AT
    if k > 0:
        speed_lines(c, t, max(0, 1 - k * 2))
        sticker(c, "10/10", 780, 600, 170, (255, 226, 26), 16, (0, 0, 0), rot=-10, scale=back_out(k / 0.2, 2.4))
        sparks(c, 780, 600, k, 5, n=60, col=YELLOW, spd=1400)
        cam["shake"] = max(0, 1 - k * 4) * 24
    lower_third(c, "STIFTUNG ALI TEST", "@stiftung.ali.test", lt - 0.4)
    werbung(c)
    return cam


def k2_build(c, lt, p, t, dur):
    cam = dict(scale=1.0, cx=540, cy=860, shake=0.0, desat=0.0)
    # last cue that fired
    cur, kk = None, 0
    for i, tt_ in enumerate(TOP_T):
        if t >= tt_:
            cur, kk = i, t - tt_
    if cur is None:
        # intro: neon sign "THE PIZZARY" + EIGENE PIZZA slam
        pz = compose_pizza(-1)
        draw_pizza(c, 540, 900, pz, lt * 6, t, steam=False)
        neon(c, "THE PIZZARY", 540, 300, 120, t)
        slam(c, "EIGENE PIZZA!", t - OWN_T, (255, 255, 255), 110, -5, 470)
        if 0 <= t - OWN_T < 0.25:
            cam["shake"] = 14
    else:
        pz = compose_pizza(lt)
        draw_pizza(c, 540, 900, pz, lt * 6, t, steam=cur == 7)
        punch = max(0.0, 1 - kk / 0.18)
        cam["scale"] = 1.0 + 0.09 * punch
        cam["shake"] = 10 * punch
        if kk < 0.35:
            speed_lines(c, t, 1 - kk / 0.35, 540, 900)
        slam(c, TOP_LABEL[cur], kk, TOP_COL[cur], 128 if len(TOP_LABEL[cur]) < 11 else 100, -6 if cur % 2 else 5, 330)
        if cur == 7:
            fire(c, t, min(1.0, kk * 2))
            blit(c.img, emoji("\U0001F525", 150), 160, 520)
            blit(c.img, emoji("\U0001F36F", 150), 920, 540)
        # progress row
        for i in range(8):
            on = i <= cur
            c.circle(330 + i * 60, 1330, 13, (YELLOW if on else np.array([0.3, 0.3, 0.35])), -1)
    k = t - ASK_T
    if k > 0:
        sticker(c, "WAS KOSTET SIE?", 540, 470, 96, (255, 255, 255), 14, (0, 0, 0), rot=4, scale=back_out(k / 0.2, 2.0))
    werbung(c)
    return cam


def k2_price(c, lt, p, t, dur):
    cam = dict(scale=1.0 + 0.05 * p, cx=540, cy=860, shake=0.0, desat=0.0)
    draw_pizza(c, 540, 930, PIZZA_FULL, lt * 12, t)
    k = lt - PRICE_AT
    fire(c, t, 0.4 + (0.6 if k > 0 else 0))
    badge(c, "ANGEBOT", 540, 260, 70, tuple(RED), sc=back_out(lt / 0.3))
    if k > 0:
        speed_lines(c, t, max(0, 1 - k * 2), 540, 650)
        price_tag(c, 560, 650, back_out(k / 0.22, 2.2))
        cam["shake"] = max(0, 1 - k * 4) * 28
        sparks(c, 560, 650, k, 8, n=70, col=YELLOW, spd=1500)
        for i in range(10):
            ph = (k * 0.7 + i / 10) % 1.0
            blit(c.img, emoji("\U0001F4B8", 90), 80 + i * 105, -60 + ph * 1500, 0.9)
    lower_third(c, "STIFTUNG ALI TEST", "@stiftung.ali.test", lt - 0.2)
    werbung(c)
    return cam


def k2_end(c, lt, p, t, dur):
    cam = dict(scale=1.0 + 0.04 * p, cx=540, cy=860, shake=0.0, desat=0.0)
    draw_pizza(c, 540, 760, PIZZA_FULL, t * 12, t)
    fire(c, t, 0.85)
    kh = t - HEUTE_T
    if kh > -0.2:
        badge(c, "AB HEUTE · 03.11.", 540, 250, 70, tuple(RED), sc=back_out((kh + 0.2) / 0.25))
    neon(c, "THE PIZZARY", 540, 1150, 130, t)
    if lt > 0.6:
        blit(c.img, txt("BERLIN", 70, (255, 226, 26), 10, (0, 0, 0), F_BLACK, True), 540, 1260, ease((lt - 0.6) * 3))
    kk = t - HOLT_T
    if kk > 0:
        slam(c, "HOLT SIE EUCH!", min(kk, 0.9), (255, 255, 255), 120, -5, 470)
        if kk < 0.25:
            cam["shake"] = 18
    werbung(c)
    return cam


SCENES = [k2_hook, k2_build, k2_price, k2_end]
