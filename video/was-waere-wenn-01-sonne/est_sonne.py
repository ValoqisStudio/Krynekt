import json
S = ["Was wäre, wenn die Sonne genau jetzt verschwindet?",
"Die Antwort: Du merkst es nicht.",
"Acht Minuten und zwanzig Sekunden lang scheint sie einfach weiter. Denn so lange braucht ihr Licht bis zu uns.",
"Und auch die Erde kreist weiter. Um eine Sonne, die es gar nicht mehr gibt. Denn auch die Schwerkraft ist nur so schnell wie das Licht.",
"Dann, ganz plötzlich… wird es dunkel.",
"Und die Erde fliegt geradeaus hinaus ins eiskalte All.",
"Und was danach mit uns passiert? Das zeige ich dir in Teil zwei. Willst du ihn sehen? Schreib „Teil zwei“ in die Kommentare."]
t=0.15; words=[]; scenes=[]
for s in S:
    scenes.append(max(0,t-0.15))
    for w in s.split():
        d=0.1+0.05*len(w); words.append({"text":w,"start":t,"end":t+d}); t+=d+0.05
        if w.endswith(('.','?',':','…',',')): t+=0.25
    t+=0.25
scenes.append(t)
json.dump({"duration":t+2.4,"words":words,"scenes":scenes},open("timing_sonne_est.json","w"),ensure_ascii=False)
print(round(t,2),[round(x,2) for x in scenes])
