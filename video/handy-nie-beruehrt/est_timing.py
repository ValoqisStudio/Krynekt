import json
S = ["Du hast dein Handy noch nie berührt. Kein einziges Mal.",
"Alles besteht aus Atomen. Und ganz außen hat jedes Atom eine Wolke aus Elektronen.",
"Elektronen sind negativ geladen. Und gleiche Ladungen stoßen sich ab.",
"Wenn dein Finger also dein Display „berührt“, kommen sich die Elektronen so nah, dass sie sich gegenseitig wegdrücken.",
"Was du spürst, ist keine Berührung. Sondern diese Kraft. Deine Nerven melden sie nur an dein Gehirn.",
"Dein Finger schwebt also gerade über dem Bildschirm. Unvorstellbar knapp. Aber er schwebt.",
"Also: Hast du jemals irgendwas wirklich angefasst? Schreib's in die Kommentare."]
t=0.2; words=[]; scenes=[]
for s in S:
    scenes.append(max(0,t-0.2))
    for w in s.split():
        d=0.12+0.055*len(w); words.append({"text":w.replace("„","").replace("“",""),"start":t,"end":t+d}); t+=d+0.04
        if w.endswith(('.','?',':')): t+=0.25
    t+=0.3
json.dump({"duration":t+0.8,"words":words,"scenes":scenes},open("timing_est.json","w"),ensure_ascii=False)
print(t, scenes)
