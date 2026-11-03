import json, wave, numpy as np
SR=44100
import sys
tm=json.load(open(sys.argv[1])); NARR=sys.argv[2] if len(sys.argv)>2 and sys.argv[2]!="none" else None; OUT=sys.argv[3] if len(sys.argv)>3 else "audio.wav"; DUR=tm["duration"]; sc=tm["scenes"]+[DUR]
n=int(DUR*SR); L=np.zeros(n); R=np.zeros(n); rng=np.random.default_rng(3)
def put(sig,t,gl=1.0,gr=1.0):
    i=int(t*SR); m=min(len(sig),n-i)
    if i<0 or m<=0: return
    L[i:i+m]+=sig[:m]*gl; R[i:i+m]+=sig[:m]*gr
def lp(x,a):
    a=np.broadcast_to(np.asarray(a,float),x.shape); y=np.zeros_like(x); s=0.0
    for i in range(len(x)): s+=a[i]*(x[i]-s); y[i]=s
    return y
tt=lambda d: np.arange(int(d*SR))/SR
def kick():
    t=tt(0.35); f=45+90*np.exp(-t*30); return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*9)*0.9
def snare():
    t=tt(0.22); nz=rng.normal(0,1,len(t)); nz=nz-lp(nz,0.08); return (nz*0.5+np.sin(2*np.pi*190*t)*0.4)*np.exp(-t*18)*0.55
def hat():
    t=tt(0.05); nz=rng.normal(0,1,len(t)); nz=nz-lp(nz,0.5); return nz*np.exp(-t*90)*0.18
def bass(f,d):
    t=tt(d); return (np.sin(2*np.pi*f*t)+0.3*np.sin(4*np.pi*f*t))*np.minimum(1,t*40)*np.exp(-t*1.5)*0.35
def pop():
    t=tt(0.09); f=500+1500*t/t[-1]; return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*45)*0.5
def whoosh(d=0.45):
    k=int(d*SR); x=rng.normal(0,1,k); u=np.linspace(0,1,k)
    y=lp(x,0.02+0.35*np.sin(np.pi*u)**2); y=y-lp(y,0.01)
    return y*np.sin(np.pi*u**0.7)**2*0.9
def impact():
    t=tt(1.2); f=55*np.exp(-t*1.5)+32
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*3.2)*0.9+lp(rng.normal(0,1,len(t)),0.25)*np.exp(-t*40)*0.6
def ding():
    t=tt(1.2); return (np.sin(2*np.pi*880*t)+0.5*np.sin(2*np.pi*1320*t))*np.exp(-t*4)*0.3
def sizzle(d):
    t=tt(d); nz=rng.normal(0,1,len(t)); nz=nz-lp(nz,0.3)
    cr=(rng.random(len(t))>0.997)*rng.normal(0,2,len(t))
    return (nz*0.08+cr*0.3)*np.minimum(1,t*4)*np.minimum(1,(d-t)*4)
# --- beat 100 bpm
bpm=100; beat=60/bpm; music=np.zeros(n); musR=np.zeros(n)
roots=[55.0,43.65,65.41,49.0]
b=0; t0=0.0
while t0<DUR-0.5:
    bar=int(b//4); pos=b%4
    def mput(sig,t,g=1.0):
        i=int(t*SR); m=min(len(sig),n-i)
        if m>0: music[i:i+m]+=sig[:m]*g; musR[i:i+m]+=sig[:m]*g
    if pos in (0,2): mput(kick(),t0)
    if pos==2: mput(kick(),t0+beat*0.5,0.6)
    if pos in (1,3): mput(snare(),t0)
    mput(hat(),t0); mput(hat(),t0+beat/2,0.7)
    if pos==0: mput(bass(roots[bar%4],beat*4),t0)
    b+=1; t0+=beat
# duck music under Ali's voice (his clip already carries music)
tv=np.arange(n)/SR
g=np.full(n,0.8)
for w in tm["words"]:
    g[int(max(0,w["start"]-0.1)*SR):int((w["end"]+0.15)*SR)]=0.3
g=np.convolve(g,np.ones(4410)/4410,'same')
L+=music*g*0.5; R+=musR*g*0.5
# --- Ali voice
ali=wave.open("ali_full.wav"); raw=np.frombuffer(ali.readframes(ali.getnframes()),np.int16).reshape(-1,2)/32768
def seg(a,b_,at):
    x=raw[int(a*SR):int(b_*SR)].copy(); k=len(x); f=np.ones(k); fl=int(0.04*SR); f[:fl]=np.linspace(0,1,fl); f[-fl:]=np.linspace(1,0,fl)
    i=int(at*SR); m=min(k,n-i); L[i:i+m]+=x[:m,0]*f[:m]*1.0; R[i:i+m]+=x[:m,1]*f[:m]*1.0
seg(0.55,5.35,0.0); seg(32.55,37.75,tm.get('ali2_at',sc[2]))
# --- sfx
for bnd in sc[1:4]: put(whoosh(),bnd-0.3,0.8,1.0)
TEN=[w["start"] for w in tm["words"] if w["text"].startswith("10!")][0]
PRICE=[w["start"] for w in tm["words"] if w["text"].startswith("9,90")][0]
put(impact(),TEN,0.8,0.8); put(impact()*1.1,PRICE)
put(ding(),PRICE+0.15)
KEYS=["salami","champignons","peperoni","oliven","mais","burrata","stracciatella","honey"]
cues=[]; prev=sc[1]
for k in KEYS:
    v=[w["start"] for w in tm["words"] if w["text"].lower().strip(".,!?:…").startswith(k) and w["start"]>=prev]
    if v: cues.append(v[0]); prev=v[0]
for cu in cues[:-1]:
    put(impact()[:int(0.25*SR)]*0.6,cu); put(pop(),cu+0.05,0.7,1.0)
HON=cues[-1] if cues else sc[1]+9
put(sizzle(2.5),HON); put(impact()*0.8,HON)
put(impact()*0.7,sc[3])
if NARR:
    nw=wave.open(NARR); nr=np.frombuffer(nw.readframes(nw.getnframes()),np.int16).reshape(-1,nw.getnchannels())/32768
    if nr.shape[1]==1: nr=np.repeat(nr,2,1)
    for (a_,b_,at) in tm.get("narr_segments",[]):
        x=nr[int(a_*SR):int(b_*SR)]; i=int(at*SR); m=min(len(x),n-i); L[i:i+m]+=x[:m,0]; R[i:i+m]+=x[:m,1]
st=np.stack([L,R],1); st=st/np.abs(st).max()*0.89
with wave.open(OUT,"wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st*32767).astype(np.int16).tobytes())
print("audio ok", TEN, PRICE)
