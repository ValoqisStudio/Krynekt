import json, subprocess
# speech regions from silencedetect (start,end)
sil = [(0.845,1.494),(3.213,3.756),(7.274,7.632),(9.723,10.408),(11.229,11.653),(14.202,14.897),(18.244,18.743),(19.526,20.268),(20.728,21.262),(21.840,22.351),(26.637,27.241),(27.898,28.377),(29.655,30.362),(30.936,31.280),(32.722,33.308),(34.477,35.089),(37.289,37.968),(38.721,39.368),(39.839,40.311),(42.339,42.938),(44.535,45.035)]
regs = []; prev = 0.0
for s,e in sil:
    regs.append((prev, s)); prev = e
cuts = [(0.0,1.40),(19.95,21.0),(26.95,28.15),(30.0,31.1),(37.6,39.1)]
END = 44.70
keep=[]; p=0.0
for a,b in cuts:
    if a>p: keep.append((p,a))
    p=b
keep.append((p,END))
def newt(x):
    o=0.0
    for a,b in keep:
        if x<a: return o
        if x<=b: return o+(x-a)
        o+=b-a
    return o
# build cleaned audio
parts=[]; fc=""
for i,(a,b) in enumerate(keep):
    fc+=f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={b-a-0.012:.3f}:d=0.012[p{i}];"
fc+="".join(f"[p{i}]" for i in range(len(keep)))+f"concat=n={len(keep)}:v=0:a=1[o]"
subprocess.run(["ffmpeg","-y","-loglevel","error","-i","voice2.mp3","-filter_complex",fc,"-map","[o]","-ar","44100","voice2_clean.wav"],check=True)
# spoken units per (kept) region index -> display words
T = {1:"Du bestehst fast nur aus Nichts.",
     2:"Jedes Atom in deinem Körper ist zu über |neunundneunzig Komma",
     3:"|neun neun neun neun Prozent leer.",
     4:"Stell dir vor,",5:"der Atomkern wäre so groß wie eine Erbse.",
     6:"Dann wäre das ganze Atom so groß wie ein Fußballstadion.",7:"Und dazwischen?",9:"Nichts.",
     10:"Jetzt pressen wir den leeren Raum aus allen acht Milliarden Menschen heraus.",12:"Die gesamte Menschheit…",
     14:"passt in einen Zuckerwürfel.",15:"Ein einziger Würfel.",16:"So schwer wie alle Menschen zusammen.",
     18:"Also:",19:"Bist du mehr Nichts als Etwas?",20:"Schreib's in die Kommentare."}
words=[]; sent_starts=[]
pct=None
for ri in sorted(T):
    a,b = regs[ri]; a,b = newt(a+0.02), newt(b)
    toks = T[ri].split()
    wts = [len(t.strip("|"))+2 for t in toks]; tot=sum(wts); x=a
    for tok,wt in zip(toks,wts):
        d=(b-a)*wt/tot; s,e=x,x+d*0.92; x+=d
        if tok.startswith("|") or (pct is not None and ri in (2,3) and tok in ("Komma","neun","Prozent")):
            if pct is None:
                pct={"text":"99,9999%","start":s,"end":e}; words.append(pct)
            else: pct["end"]=e
            continue
        words.append({"text":tok,"start":round(s,3),"end":round(e,3)})
starts = {w["text"]:w["start"] for w in words[::-1]}
def st(word, after=0):
    for w in words:
        if w["text"]==word and w["start"]>=after: return w["start"]
sc=[0, st("Jedes"), st("Stell"), st("Und"), st("Jetzt"), st("Die",20), st("Ein",25), st("Also:"), words[-1]["end"]+0.35]
sc=[0]+[max(0,x-0.12) for x in sc[1:-1]]+[sc[-1]]
dur = newt(END)+2.6
json.dump({"duration":round(dur,2),"words":words,"scenes":[round(x,3) for x in sc]},open("timing_nichts.json","w"),ensure_ascii=False)
print("dur",round(dur,2),"scenes",[round(x,2) for x in sc])
print(" ".join(f'{w["text"]}@{w["start"]:.2f}' for w in words))
