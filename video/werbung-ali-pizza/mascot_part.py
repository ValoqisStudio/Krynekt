@lru_cache(maxsize=256)
def mascot_face(R, mood, blink, lx, ly):
    ss = 4
    S = int(R * 2.2) * ss
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c0 = S / 2
    r = R * ss
    def E(x, y, rx, ry, fill):
        d.ellipse([c0 + x - rx, c0 + y - ry, c0 + x + rx, c0 + y + ry], fill=fill)
    ex, ey = 0.34 * r, -0.12 * r
    big = 1.3 if mood in ("shock", "scared") else 1.0
    if mood == "cool":
        for sg in (-1, 1):
            d.rounded_rectangle([c0 + sg * ex - 0.3 * r, c0 + ey - 0.17 * r, c0 + sg * ex + 0.3 * r, c0 + ey + 0.2 * r], radius=0.1 * r, fill=(10, 10, 15, 255))
            d.ellipse([c0 + sg * ex - 0.18 * r, c0 + ey - 0.1 * r, c0 + sg * ex - 0.05 * r, c0 + ey - 0.0 * r], fill=(255, 255, 255, 120))
        d.line([c0 - ex + 0.28 * r, c0 + ey - 0.05 * r, c0 + ex - 0.28 * r, c0 + ey - 0.05 * r], fill=(10, 10, 15, 255), width=int(0.06 * r))
    elif mood == "happy" or blink:
        for sg in (-1, 1):
            d.arc([c0 + sg * ex - 0.17 * r, c0 + ey - 0.14 * r, c0 + sg * ex + 0.17 * r, c0 + ey + 0.16 * r], 200, 340, fill=(15, 15, 25, 255), width=int(0.07 * r))
    else:
        for sg in (-1, 1):
            E(sg * ex, ey, 0.17 * r * big, 0.21 * r * big, (255, 255, 255, 255))
            pr = 0.09 * r * (0.75 if mood in ("shock", "scared") else 1.0)
            px, py = sg * ex + lx * 0.06 * r, ey + ly * 0.07 * r
            E(px, py, pr, pr, (15, 15, 25, 255))
            E(px - pr * 0.35, py - pr * 0.4, pr * 0.32, pr * 0.32, (255, 255, 255, 255))
    # brows
    bw = int(0.06 * r)
    brow = {"shock": (-0.42, -0.42, 0), "scared": (-0.40, -0.46, 1), "worried": (-0.36, -0.42, 1), "think": (-0.36, -0.46, 2), "cold": (-0.38, -0.40, 1)}
    if mood in brow:
        y1, y2, kind = brow[mood]
        for sg in (-1, 1):
            if kind == 1:
                d.line([c0 + sg * (ex + 0.15 * r), c0 + y1 * r, c0 + sg * (ex - 0.15 * r), c0 + y2 * r], fill=(15, 15, 25, 255), width=bw)
            elif kind == 2 and sg == 1:
                d.arc([c0 + ex - 0.17 * r, c0 + y2 * r, c0 + ex + 0.17 * r, c0 + y2 * r + 0.2 * r], 200, 340, fill=(15, 15, 25, 255), width=bw)
            elif kind == 2:
                d.line([c0 - ex - 0.15 * r, c0 + y1 * r, c0 - ex + 0.15 * r, c0 + y1 * r], fill=(15, 15, 25, 255), width=bw)
            else:
                d.arc([c0 + sg * ex - 0.17 * r, c0 + y1 * r, c0 + sg * ex + 0.17 * r, c0 + y1 * r + 0.2 * r], 200, 340, fill=(15, 15, 25, 255), width=bw)
    # mouth
    my = 0.32 * r
    dark = (20, 10, 20, 255)
    if mood == "shock":
        E(0, my, 0.12 * r, 0.16 * r, dark)
    elif mood == "happy":
        d.chord([c0 - 0.28 * r, c0 + my - 0.25 * r, c0 + 0.28 * r, c0 + my + 0.2 * r], 0, 180, fill=dark)
        E(0, my + 0.1 * r, 0.11 * r, 0.06 * r, (240, 90, 110, 255))
    elif mood == "cool":
        d.arc([c0 - 0.22 * r, c0 + my - 0.2 * r, c0 + 0.12 * r, c0 + my + 0.08 * r], 20, 150, fill=dark, width=bw)
    elif mood == "cold":
        d.rounded_rectangle([c0 - 0.24 * r, c0 + my - 0.08 * r, c0 + 0.24 * r, c0 + my + 0.1 * r], radius=0.05 * r, fill=(250, 250, 250, 255), outline=dark, width=int(0.03 * r))
        for k in range(1, 4):
            xx = c0 - 0.24 * r + k * 0.12 * r
            d.line([xx, c0 + my - 0.08 * r, xx, c0 + my + 0.1 * r], fill=dark, width=int(0.025 * r))
    elif mood == "think":
        d.line([c0 - 0.05 * r, c0 + my + 0.02 * r, c0 + 0.2 * r, c0 + my - 0.03 * r], fill=dark, width=bw)
    else:  # worried / scared: wavy
        pts = [(c0 + (-0.2 + 0.4 * i / 8) * r, c0 + my + 0.04 * r * math.sin(i * 1.6)) for i in range(9)]
        d.line(pts, fill=dark, width=bw)
    im = im.resize((S // ss, S // ss), Image.LANCZOS)
    return pil_to_f(im)


MOODS = ["shock", "cool", "worried", "think", "scared", "cold", "happy", "happy"]


def MASCOT(img, t):
    si = scene_at(t)
    lt = t - SC[si]
    mood = MOODS[min(si, len(MOODS) - 1)]
    R = 72
    pop = back_out(lt / 0.3, 2.0)
    x = 935 + (math.sin(t * 40) * 4 if mood in ("cold", "scared") else 0)
    y = 1165 + 8 * math.sin(t * 2.2)
    col = {"cold": (0.45, 0.65, 1.0), "scared": (0.12, 0.25, 0.35), "cool": (1.0, 0.75, 0.3)}.get(mood, (0.25, 0.8, 1.0))
    Rs = max(4, int(R * (0.85 + 0.15 * pop)))
    if mood != "scared":
        blit(img, blob(int(Rs * 1.8), col, 2.5), x, y, 0.45, add=True)
    # electron rings
    patch = np.zeros((Rs * 4, Rs * 4, 3), np.uint8)
    for k in range(2):
        ang = 25 + k * 110
        cv2.ellipse(patch, (Rs * 2, Rs * 2), (int(Rs * 1.55), int(Rs * 0.45)), ang, 0, 360, tuple(int(v * 140) for v in col), 3, cv2.LINE_AA)
        th = t * (2.5 + k) + k
        a = math.radians(ang)
        px = Rs * 1.55 * math.cos(th)
        py = Rs * 0.45 * math.sin(th)
        ex_, ey_ = int(Rs * 2 + px * math.cos(a) - py * math.sin(a)), int(Rs * 2 + px * math.sin(a) + py * math.cos(a))
        cv2.circle(patch, (ex_, ey_), max(3, Rs // 9), (255, 255, 255), -1, cv2.LINE_AA)
    x0, y0 = int(x - Rs * 2), int(y - Rs * 2)
    sl = img[max(0, y0):y0 + Rs * 4, max(0, x0):x0 + Rs * 4]
    sl += patch[: sl.shape[0], : sl.shape[1]].astype(np.float32) / 255 * (0.35 if mood == "scared" else 0.9)
    blit(img, sphere(Rs, col), x, y)
    blink = (t % 3.7) < 0.12
    look = {"worried": (-0.3, -1.0), "think": (-0.8, -0.9), "scared": (math.sin(t * 9) * 0.8, 0)}.get(mood, (0, 0))
    face = mascot_face(Rs, mood, blink, round(look[0], 1), round(look[1], 1))
    blit(img, face, x, y)
    if mood == "cold":
        blit(img, emoji("\u2744\uFE0F", 44), x - Rs, y - Rs, 0.9)


