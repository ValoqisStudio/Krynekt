"""Cut spoken tag-words out of a voice file and estimate word timings from pauses.
usage: align_generic.py config.json  (keys: src, out_wav, out_json, end, cuts, regions:{idx:text}, scene_words:[[word,after],...], silence_db, min_sil)"""
import json, subprocess, sys, re
cfg = json.load(open(sys.argv[1]))
out = subprocess.run(["ffmpeg","-i",cfg["src"],"-af",f"silencedetect=noise={cfg.get('silence_db',-38)}dB:d={cfg.get('min_sil',0.2)}","-f","null","-"],capture_output=True,text=True).stderr
ss=[float(x) for x in re.findall(r"silence_start: ([0-9.]+)",out)]; se=[float(x) for x in re.findall(r"silence_end: ([0-9.]+)",out)]
regs=[]; prev=0.0
for s,e in zip(ss,se):
    regs.append((prev,s)); prev=e
regs.append((prev,cfg["end"]))
cuts=cfg["cuts"]; END=cfg["end"]
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
fc=""
for i,(a,b) in enumerate(keep):
    fc+=f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={b-a-0.012:.3f}:d=0.012[p{i}];"
fc+="".join(f"[p{i}]" for i in range(len(keep)))+f"concat=n={len(keep)}:v=0:a=1[o]"
subprocess.run(["ffmpeg","-y","-loglevel","error","-i",cfg["src"],"-filter_complex",fc,"-map","[o]","-ar","44100",cfg["out_wav"]],check=True)
words=[]
for ri,text in sorted(cfg["regions"].items(), key=lambda kv:int(kv[0])):
    a,b=regs[int(ri)]; a,b=newt(a+0.02),newt(b)
    toks=text.split(); wts=[len(t)+2 for t in toks]; tot=sum(wts); x=a
    for tok,wt in zip(toks,wts):
        d=(b-a)*wt/tot; words.append({"text":tok,"start":round(x,3),"end":round(x+d*0.92,3)}); x+=d
def st(word, after=0):
    for w in words:
        if w["text"]==word and w["start"]>=after: return w["start"]
    raise SystemExit("word not found: "+word)
sc=[0]+[max(0,st(w,a)-0.12) for w,a in cfg["scene_words"]]+[words[-1]["end"]+0.35]
json.dump({"duration":round(newt(END)+2.6,2),"words":words,"scenes":[round(x,3) for x in sc]},open(cfg["out_json"],"w"),ensure_ascii=False)
print("regions:",len(regs),"scenes",[round(x,2) for x in sc],"dur",round(newt(END)+2.6,2))
