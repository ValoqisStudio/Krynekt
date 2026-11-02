import json
S = ["Du bestehst fast nur aus Nichts.",
"Jedes Atom in deinem Körper ist zu über 99,9999% leer.",
"Stell dir vor, der Atomkern wäre so groß wie eine Erbse. Dann wäre das ganze Atom so groß wie ein Fußballstadion.",
"Und dazwischen? Nichts.",
"Jetzt pressen wir den leeren Raum aus allen acht Milliarden Menschen heraus.",
"Die gesamte Menschheit… passt in einen Zuckerwürfel.",
"Ein einziger Würfel. So schwer wie alle Menschen zusammen.",
"Also: Bist du mehr Nichts als Etwas? Schreib's in die Kommentare."]
t=0.15; words=[]; scenes=[]
for s in S:
    scenes.append(max(0,t-0.15))
    for w in s.split():
        d=0.1+0.05*len(w) if "%" not in w else 2.2
        words.append({"text":w,"start":t,"end":t+d}); t+=d+0.05
        if w.endswith(('.','?',':','…')): t+=0.3
    t+=0.25
scenes.append(t)
json.dump({"duration":t+2.4,"words":words,"scenes":scenes},open("timing_nichts_est.json","w"),ensure_ascii=False)
print(round(t,2), [round(x,2) for x in scenes])
