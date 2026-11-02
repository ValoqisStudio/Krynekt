"""Procedural sound design: whooshes on cuts, impacts, ambient pad. Usage: sfx.py timing.json out.wav"""
import json, sys, wave
import numpy as np
SR = 44100
tm = json.load(open(sys.argv[1])); dur = tm["duration"]; sc = tm["scenes"]
n = int(dur * SR) + SR
L = np.zeros(n); R = np.zeros(n)
rng = np.random.default_rng(1)

def lp(x, a):
    y = np.zeros_like(x); s = 0.0
    for i, v in enumerate(x):
        s += a[i] * (v - s); y[i] = s
    return y

def put(sig, t, gl=1.0, gr=1.0):
    i = int(t * SR); m = min(len(sig), n - i)
    if i < 0 or m <= 0: return
    L[i:i+m] += sig[:m] * gl; R[i:i+m] += sig[:m] * gr

def whoosh(d=0.45):
    k = int(d * SR); x = rng.normal(0, 1, k); tt = np.linspace(0, 1, k)
    cut = 0.02 + 0.35 * np.sin(np.pi * tt) ** 2
    y = lp(x, cut); y = y - lp(y, np.full(k, 0.01))
    env = np.sin(np.pi * tt ** 0.7) ** 2
    return y * env * 0.9

def impact():
    k = int(1.4 * SR); tt = np.arange(k) / SR
    f = 55 * np.exp(-tt * 1.5) + 32
    ph = 2 * np.pi * np.cumsum(f) / SR
    sub = np.sin(ph) * np.exp(-tt * 3.2)
    cl = lp(rng.normal(0, 1, k), np.full(k, 0.25)) * np.exp(-tt * 40)
    return sub * 0.9 + cl * 0.6

def ding():
    k = int(1.2 * SR); tt = np.arange(k) / SR
    return (np.sin(2*np.pi*880*tt) + 0.5*np.sin(2*np.pi*1320*tt) + 0.25*np.sin(2*np.pi*1760*tt)) * np.exp(-tt * 4) * 0.25

def riser(d):
    k = int(d * SR); tt = np.linspace(0, 1, k)
    y = lp(rng.normal(0, 1, k), 0.01 + 0.3 * tt ** 2)
    return y * tt ** 2 * 0.5

for b in sc[1:]:
    w = whoosh(); put(w, b - 0.3, 0.8, 1.0)
def pop():
    k = int(0.09 * SR); tt = np.arange(k) / SR
    f = 500 + 1400 * tt / tt[-1]
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 45) * 0.45
def tick():
    k = int(0.03 * SR); tt = np.arange(k) / SR
    return np.sin(2 * np.pi * 2400 * tt) * np.exp(-tt * 300) * 0.5
def crackle(d=0.5):
    k = int(d * SR); x = (rng.random(k) > 0.993) * rng.normal(0, 1, k)
    return lp(x, np.full(k, 0.6)) * np.exp(-np.arange(k) / SR * 5) * 3
EM = {"jetzt","nicht.","uns.","weiter.","dunkel.","all.","zwei."}
for w in tm["words"]:
    k = w["text"].lower().strip("„“\"")
    if k in EM:
        EM.discard(k); put(pop(), w["start"], 0.7, 1.0)
put(impact(), sc[1] - 0.7); put(crackle(), sc[1] - 0.7)
x = sc[2]
while x < sc[3] - 0.2:
    put(tick(), x, 1.0, 0.7); x += 0.5
off = sc[4] + (sc[5] - sc[4]) * 0.55
x = sc[4]
while x < off - 0.1:
    put(tick() * 1.3, x, 1.0, 0.7); x += 0.33
put(impact() * 1.1, off)
put(riser(1.0), off - 1.0)
put(ding(), sc[6] + 1.0)
put(impact() * 0.7, sc[7]); put(ding() * 1.2, sc[7] + 0.45)
# ambient pad (A minor-ish), very quiet
tt = np.arange(n) / SR
pad = np.zeros(n)
for f, a in ((55, 0.5), (110, 0.35), (130.81, 0.18), (164.81, 0.2), (220, 0.1)):
    pad += a * np.sin(2 * np.pi * f * tt + np.sin(2 * np.pi * 0.11 * tt) * 0.8)
pad *= (0.6 + 0.4 * np.sin(2 * np.pi * 0.2 * tt)) * np.clip(tt / 2, 0, 1) * np.clip((dur + 0.5 - tt) / 2, 0, 1)
L += pad * 0.06; R += pad * 0.06
# soft heartbeat during freeze-ish tension in the hover scene
for k in range(8):
    t0 = sc[5] + k * 0.85
    if t0 < sc[6]:
        hb = impact()[: int(0.35 * SR)] * 0.35
        put(hb, t0); put(hb * 0.6, t0 + 0.22)
mx = max(np.abs(L).max(), np.abs(R).max())
st = np.stack([L, R], 1) / mx * 0.7
with wave.open(sys.argv[2], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st[: int(dur * SR)] * 32767).astype(np.int16).tobytes())
print("sfx ok")
