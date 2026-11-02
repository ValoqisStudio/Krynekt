# Scenes for video 2 "Du bestehst fast nur aus Nichts" – exec'd inside nichts.py (render4 core)

# ---- human made of light points
def _human_points(n=1600, seed=4):
    m = np.zeros((1000, 600), np.uint8)
    cv2.circle(m, (300, 110), 85, 255, -1)
    cv2.ellipse(m, (300, 230), (55, 30), 0, 0, 360, 255, -1)
    pts = np.array([[175, 250], [425, 250], [395, 560], [205, 560]], np.int32)
    cv2.fillPoly(m, [pts], 255)
    for sgn in (-1, 1):
        cv2.line(m, (300 + sgn * 120, 270), (300 + sgn * 185, 470), 255, 62)
        cv2.line(m, (300 + sgn * 185, 470), (300 + sgn * 205, 620), 255, 50)
        cv2.line(m, (300 + sgn * 55, 560), (300 + sgn * 75, 760), 255, 78)
        cv2.line(m, (300 + sgn * 75, 760), (300 + sgn * 85, 960), 255, 62)
    ys, xs = np.nonzero(m)
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(xs), n, replace=False)
    return np.stack([xs[idx] - 300.0, ys[idx] - 500.0], 1), rng.uniform(0, 6.28, n), rng.uniform(0.6, 1.0, n)


HUMAN, HPH, HBR = _human_points()


def draw_human(c, cx, cy, sc, spread, t, alpha=1.0, col=CYAN):
    """spread 0 = solid body of points, 1 = points far apart (empty space)"""
    for (x, y), ph, br in zip(HUMAN, HPH, HBR):
        jx = math.sin(t * 2 + ph) * 3 * (1 + spread * 6)
        jy = math.cos(t * 1.7 + ph) * 3 * (1 + spread * 6)
        px = cx + (x * (1 + spread * 0.9) + jx) * sc
        py = cy + (y * (1 + spread * 0.25) + jy) * sc
        r = max(1.0, 3.2 * sc * (1 - 0.55 * spread))
        c.circle(px, py, r, col * br * alpha, -1)
    blit(c.glow, blob(int(420 * sc), tuple(col * 0.5), 2), cx, cy, 0.5 * alpha * (1 - spread * 0.6), add=True)


def counter_text(v):
    return f"{v:,.4f}".replace(",", "X").replace(".", ",").replace("X", ".") + " %"


def s2_hook(c, lt, p, t, dur):
    cam = dict(scale=1.0 + 0.06 * p, cx=540, cy=800, shake=0.0, desat=0.0)
    if lt < 0.3:
        cam["scale"] = 1.0 + 0.16 * (1 - ease_out(lt / 0.3))
    spread = ease((lt - 1.0) / 1.2)
    draw_human(c, 540, 760, 1.05, spread, t)
    if lt > 1.3:
        sticker(c, "NICHTS?!", 540, 1180, 96, (255, 225, 30), 12, (0, 0, 0), rot=-5, scale=back_out((lt - 1.3) / 0.25))
        sparks(c, 540, 760, lt - 1.3, 11, n=40, col=CYAN, spd=1100)
    return cam


def s2_percent(c, lt, p, t, dur):
    cam = dict(scale=1.0 + 0.05 * p, cx=540, cy=760, shake=0.0, desat=0.0)
    R = 330 * back_out(lt / 0.7, 1.2) * (1 - 0.35 * ease((lt - 2.6) / 1.5))
    atom(c, 540, 600, R, t)
    v = 99.9999 * ease_out((lt - 0.6) / 2.6)
    if lt > 0.6:
        blit(c.img, txt(counter_text(v), 120, (255, 226, 26), 12, (0, 0, 0), F_BLACK, True), 540, 1020)
    if lt > 3.3:
        sticker(c, "LEER", 540, 1145, 92, (255, 255, 255), 12, (0, 0, 0), rot=4, scale=back_out((lt - 3.3) / 0.25))
    hud(c, "ATOM", lt)
    return cam


def draw_stadium(c, cx, cy, z, t):
    """top-down stadium; z = zoom factor (1 = whole stadium ~900px wide)"""
    def P(x, y):
        return (cx + x * z, cy + y * z)
    # stands (outer ring)
    for k in range(14):
        rr = 470 - k * 9
        col = np.array([0.25, 0.27, 0.36]) * (0.7 + 0.3 * (k % 2))
        pts = [P(rr * math.cos(a) * 0.95, rr * math.sin(a) * 1.25) for a in np.linspace(0, 2 * math.pi, 120)]
        c.line(pts, col * 0.6, max(1, min(int(6 * z), 10)))
    # field
    fw, fh = 300, 470
    x0, y0 = P(-fw / 2, -fh / 2)
    x1, y1 = P(fw / 2, fh / 2)
    X0, Y0, X1, Y1 = max(0, int(x0)), max(0, int(y0)), min(W, int(x1)), min(H, int(y1))
    if X1 > X0 and Y1 > Y0:
        yy = np.arange(Y0, Y1)[:, None]
        stripe = ((((yy - y0) / z) // 47) % 2).astype(np.float32)
        g = np.array([0.10, 0.42, 0.16], np.float32) * (0.85 + 0.15 * stripe)[..., None]
        c.img[Y0:Y1, X0:X1] = np.broadcast_to(g, (Y1 - Y0, X1 - X0, 3))
    wcol = np.array([0.9, 0.95, 0.9])
    lw = max(1, min(int(3 * z), 7))
    c.line([P(-fw / 2, -fh / 2), P(fw / 2, -fh / 2), P(fw / 2, fh / 2), P(-fw / 2, fh / 2), P(-fw / 2, -fh / 2)], wcol, lw)
    c.line([P(-fw / 2, 0), P(fw / 2, 0)], wcol, lw)
    c.circle(*P(0, 0), 45 * z, wcol, lw)
    for sgn in (-1, 1):
        c.line([P(-80, sgn * fh / 2), P(-80, sgn * (fh / 2 - 70)), P(80, sgn * (fh / 2 - 70)), P(80, sgn * fh / 2)], wcol, lw)
    # floodlights glow
    for (fx, fy) in ((-430, -560), (430, -560), (-430, 560), (430, 560)):
        blit(c.glow, blob(int(max(20, 90 * min(z, 3))), (1.0, 0.95, 0.8), 2), *P(fx, fy), 0.5, add=True)
    # the pea (atomic nucleus) – 1/100.000 would be invisible; drawn small but visible
    pr = max(1.5, 1.6 * z)
    blit(c.glow, blob(int(max(6, pr * 4)), (0.4, 1.0, 0.3), 2), *P(0, 0), 0.9, add=True)
    blit(c.img, sphere(max(2, int(pr)), (0.35, 0.85, 0.25)), *P(0, 0))


def s2_stadium(c, lt, p, t, dur):
    cam = dict(scale=1.0, cx=540, cy=760, shake=0.0, desat=0.0)
    z = 1.0 if lt < 4.0 else 1.0 + 24 * ease((lt - 4.0) / 2.2) ** 2
    draw_stadium(c, 540, 760, min(z, 25), t)
    if lt > 0.3 and lt < 4.2:
        sticker(c, "KERN = ERBSE", 540, 230, 70, (130, 255, 110), 11, (0, 0, 0), rot=-3, scale=back_out((lt - 0.3) / 0.25))
        c.arrow(540, 300, 540, 720, (0.5, 1.0, 0.4), 6)
    if 2.6 < lt < 4.3:
        sticker(c, "ATOM = STADION", 540, 1170, 72, (255, 255, 255), 11, (0, 0, 0), rot=3, scale=back_out((lt - 2.6) / 0.25))
    if lt > 5.4:
        blit(c.img, emoji("\U0001FADB", 120), 700, 600, ease((lt - 5.4) * 3))
    return cam


def s2_nothing(c, lt, p, t, dur):
    cam = dict(scale=1.0 + 0.08 * p, cx=540, cy=760, shake=0.0, desat=0.0)
    c.img *= 0.35
    rng = np.random.default_rng(9)
    for i in range(40):
        x, y = rng.uniform(0, W), rng.uniform(200, 1300)
        a = max(0.0, 1 - lt * 0.8) * rng.uniform(0.2, 0.6)
        c.circle(x, y, 2, CYAN * a, -1)
    if lt > 0.9:
        k = lt - 0.9
        flick = 1.0 if (int(k * 20) % 7) else 0.35
        gx = int(8 * math.sin(k * 50)) if k < 0.35 else 0
        a = min(1.0, k * 4) * flick
        blit(c.img, txt("NICHTS", 190, (255, 60, 70), 0, font=F_BLACK), 540 + gx + 6, 760, a * 0.6, add=True)
        blit(c.img, txt("NICHTS", 190, (60, 220, 255), 0, font=F_BLACK), 540 - gx - 6, 760, a * 0.6, add=True)
        blit(c.img, txt("NICHTS", 190, (255, 255, 255), 0, font=F_BLACK, shadow=True), 540, 760, a)
    else:
        blit(c.img, txt("?", 260, (255, 255, 255), 10, (0, 0, 0), F_BLACK, True), 540, 760, ease(lt * 3))
    return cam


def s2_press(c, lt, p, t, dur):
    cam = dict(scale=1.0 + 0.04 * p, cx=540, cy=760, shake=0.0, desat=0.0)
    k = ease((lt - 1.2) / (dur - 1.6)) if dur > 2 else 0
    gap = lerp(420, 40, k)
    cy = 780
    rows, cols = 6, 6
    for i in range(rows):
        for j in range(cols):
            x = 540 + (j - (cols - 1) / 2) * 150 * (1 - k * 0.9)
            y = cy + (i - (rows - 1) / 2) * 130 * (gap / 420)
            s = 110 * (1 - k * 0.85)
            if s > 8:
                blit(c.img, emoji("\U0001F9CD", int(s)), x, y)
    # press plates
    for sgn in (-1, 1):
        py = cy + sgn * (gap + 70)
        plate = np.dstack([np.ones((90, 980, 3), np.float32) * np.array([0.55, 0.58, 0.65]), rounded_mask(980, 90, 18)])
        plate[..., :3] *= np.linspace(1.25, 0.6, 90)[:, None, None]
        blit(c.img, plate, 540, py)
        ya, yb = sorted((int(py + sgn * 45), int(py + sgn * 900)))
        ya, yb = max(0, ya), min(H, yb)
        if yb > ya:
            c.img[ya:yb, 520:560] = np.linspace(0.65, 0.3, 40)[None, :, None] * np.array([0.8, 0.82, 0.9])
        for hx in (120, 960):
            c.line([(hx - 40, py), (hx + 40, py)], YELLOW * 0.8, 10)
    cnt = int(8_000_000_000 * ease_out(lt / 1.2))
    blit(c.img, txt(f"{cnt:,}".replace(",", "."), 84, (255, 226, 26), 11, (0, 0, 0), F_BLACK, True), 540, 120)
    blit(c.img, txt("MENSCHEN", 54, (255, 255, 255), 9, (0, 0, 0), F_BLACK, True), 540, 195)
    if k > 0.9:
        cam["shake"] = 14
        blit(c.glow, blob(200, (1, 1, 1), 2), 540, cy, (k - 0.9) * 10, add=True)
    return cam


def draw_cube(c, cx, cy, s, glow=1.0):
    """isometric sugar cube, s = edge length in px"""
    h = s * 0.5
    top = [(cx, cy - s), (cx + s * 0.87, cy - h), (cx, cy), (cx - s * 0.87, cy - h)]
    left = [(cx - s * 0.87, cy - h), (cx, cy), (cx, cy + s), (cx - s * 0.87, cy + h)]
    right = [(cx, cy), (cx + s * 0.87, cy - h), (cx + s * 0.87, cy + h), (cx, cy + s)]
    rng = np.random.default_rng(2)
    for poly, shade in ((left, 0.72), (right, 0.55), (top, 0.97)):
        m = np.zeros((H, W), np.uint8)
        cv2.fillPoly(m, [np.round(np.array(poly) * 16).astype(np.int32)], 255, cv2.LINE_AA, shift=4)
        a = (m.astype(np.float32) / 255)[..., None]
        ys, xs = np.nonzero(m)
        if len(xs) == 0:
            continue
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        grain = rng.random((y1 - y0, x1 - x0, 1)).astype(np.float32)
        col = np.array([1.0, 0.98, 0.95]) * shade * (0.85 + 0.15 * grain)
        sl = c.img[y0:y1, x0:x1]
        aa = a[y0:y1, x0:x1]
        c.img[y0:y1, x0:x1] = sl * (1 - aa) + col * aa
    for poly in (top, left, right):
        c.line(poly + [poly[0]], np.array([1, 1, 1]) * 0.25, 2)
    blit(c.glow, blob(int(s * 1.6), (0.7, 0.85, 1.0), 2), cx, cy, 0.45 * glow, add=True)


def s2_cube(c, lt, p, t, dur):
    cam = dict(scale=1.0 + 0.06 * p, cx=540, cy=760, shake=0.0, desat=0.0)
    reveal = 1.7
    if lt < reveal:
        pul = 0.6 + 0.4 * math.sin(lt * 9)
        blit(c.glow, blob(90, (1, 1, 1), 2), 540, 760, pul, add=True)
        blit(c.img, sphere(10, (1, 1, 1)), 540, 760)
    else:
        k = lt - reveal
        s = 210 * back_out(k / 0.35, 1.6)
        draw_cube(c, 540, 700 + 6 * math.sin(lt * 2), s)
        sparks(c, 540, 760, k, 21, n=50, col=np.array([0.8, 0.9, 1.0], np.float32), spd=1200)
        if k > 0.3:
            sticker(c, "ZUCKERWÜRFEL", 540, 1230, 84, (255, 255, 255), 11, (0, 0, 0), rot=-3, scale=back_out((k - 0.3) / 0.25))
        if k < 0.25:
            cam["shake"] = 16 * (1 - k / 0.25)
    return cam


def s2_weight(c, lt, p, t, dur):
    cam = dict(scale=1.0 + 0.04 * p, cx=540, cy=760, shake=0.0, desat=0.0)
    ground = 1000
    c.img[ground:1330] = c.img[ground:1330] * 0.3 + np.array([0.09, 0.08, 0.1]) * 0.7
    c.line([(0, ground), (W, ground)], np.array([0.5, 0.5, 0.6]), 4)
    drop = 0.45
    s = 190
    if lt < drop:
        y = lerp(-300, ground - s, (lt / drop) ** 2)
    else:
        y = ground - s
    finger_like = None
    draw_cube(c, 540, y, s)
    if lt >= drop:
        k = lt - drop
        cam["shake"] = max(0, 1 - k * 3) * 30
        sparks(c, 540, ground, k, 31, n=70, col=np.array([1.0, 0.7, 0.3], np.float32), spd=1400)
        rng = np.random.default_rng(5)
        grow = ease_out(k / 0.5)
        for i in range(9):
            a = rng.uniform(0, math.pi) if i % 2 else rng.uniform(-0.3, 0.3) + (0 if i % 4 else math.pi)
            pts = [(540, ground)]
            x, yy = 540.0, float(ground)
            for j in range(7):
                a += rng.uniform(-0.5, 0.5)
                L = rng.uniform(30, 70) * grow
                x += math.cos(a) * L
                yy += abs(math.sin(a)) * L * 0.5
                pts.append((x, yy))
            c.line(pts, np.array([0.9, 0.55, 0.2]) * 0.9, 5)
        if k > 0.4:
            ton = int(500_000_000 * ease_out((k - 0.4) / 1.4))
            blit(c.img, txt(f"≈ {ton:,}".replace(",", ".") + " t", 98, (255, 226, 26), 12, (0, 0, 0), F_BLACK, True), 540, 330)
            blit(c.img, txt("(500 MILLIONEN TONNEN)", 46, (255, 255, 255), 8, (0, 0, 0), F_BLACK, True), 540, 425, ease((k - 1.6) * 3))
    return cam


def s2_cta(c, lt, p, t, dur):
    cam = dict(scale=1.0 + 0.04 * p, cx=540, cy=800, shake=0.0, desat=0.0)
    s = back_out(lt / 0.4)
    draw_human(c, 540, 520, 0.5, 0.6 + 0.4 * math.sin(lt * 1.5) ** 2, t, alpha=0.9)
    blit(c.img, emoji("\U0001F914", max(8, int(170 * s))), 760, 330)
    if lt > 1.0:
        k = ease_out((lt - 1.0) / 0.35)
        y = 960 + (1 - k) * 80
        box = np.dstack([np.ones((150, 860, 3), np.float32) * np.array([0.12, 0.12, 0.16]), rounded_mask(860, 150, 75) * 0.92])
        blit(c.img, box, 540, y, k)
        blit(c.img, sphere(40, (0.3, 0.8, 1.0)), 175, y, k)
        full = "Definitiv mehr Nichts"
        msg = full[: int(max(0, lt - 1.4) * 14)]
        if msg:
            ts = txt(msg, 46, (255, 255, 255), 0, font=F_BOLD)
            blit(c.img, ts, 240 + ts.shape[1] / 2 - 30, y, k)
        if len(msg) == len(full):
            blit(c.img, emoji("\U0001F605", 56), 240 + txt(full, 46, font=F_BOLD).shape[1] - 10, y, k)
        blit(c.img, emoji("\U0001F447", 120), 540, y + 150 + 18 * math.sin(lt * 8), k)
    return cam


SCENES = [s2_hook, s2_percent, s2_stadium, s2_nothing, s2_press, s2_cube, s2_weight, s2_cta, s_end]
