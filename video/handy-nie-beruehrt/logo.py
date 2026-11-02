import sys, numpy as np, cv2
sys.argv = ["render2.py", "timing_est.json", "x"]
exec(open("render2.py").read().split('if __name__ == "__main__":')[0])
from PIL import Image
S = 1080
def make(t, label):
    c = Ctx()
    c.img = c.img[:S] * 0 + np.array([0.02, 0.025, 0.06])
    c.glow = c.glow[:S]; c.lines = c.lines[:S]
    atom(c, S/2, S/2, 340, t)
    c.flush_lines()
    small = cv2.resize(c.glow, (S//4, S//4), interpolation=cv2.INTER_AREA)
    b = cv2.GaussianBlur(small, (0,0), 5)*0.9 + cv2.GaussianBlur(small, (0,0), 16)*1.1
    img = c.img + cv2.resize(b, (S, S))
    yy, xx = np.mgrid[0:S, 0:S]
    r = np.sqrt((xx-S/2)**2 + (yy-S/2)**2)/S
    img *= (1 - 0.8*np.clip(r*1.3, 0, 1)**2)[..., None]
    img = np.clip(img/(1+img*0.12)*1.1, 0, 1)
    Image.fromarray((img*255).astype(np.uint8)).save(label)
make(1.3, "profilbild_unsichtbar_erklaert.png")
# banner / intro card 1080x1920 with name
c = Ctx(); atom(c, 540, 760, 330, 2.0); c.flush_lines()
small = cv2.resize(c.glow, (W//4, H//4), interpolation=cv2.INTER_AREA)
img = c.img + cv2.resize(cv2.GaussianBlur(small,(0,0),5)*0.9+cv2.GaussianBlur(small,(0,0),16)*1.1, (W, H))
blit(img, txt("UNSICHTBAR", 132, (255,255,255), 12, (0,0,0), F_BLACK, True), 540, 1260)
blit(img, txt("ERKLÄRT", 132, (255,226,26), 12, (0,0,0), F_BLACK, True), 540, 1400)
blit(img, txt("Dinge, die dein Gehirn kaputt machen", 44, (200,215,255), 0, font=F_SEMI), 540, 1530)
img *= VIGN
Image.fromarray((np.clip(img/(1+img*0.12)*1.1,0,1)*255).astype(np.uint8)).save("intro_karte_unsichtbar_erklaert.png")
