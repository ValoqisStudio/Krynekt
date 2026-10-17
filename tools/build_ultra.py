"""Erzeugt Vortexia_ULTRA.html aus Vortexia.html: startet immer mit maximaler Grafik.

Unterschiede zur normalen Version:
  * Qualitätsstufe 'ultra' als Voreinstellung (statt automatischer Erkennung)
  * eigene gespeicherte Einstellungen (vx_set_ultra), damit die normale Version sie nicht überschreibt
  * Ultra-Stufe zusätzlich aufgedreht: 4096er-Schatten, mehr Schritte für die Lichtstrahlen
Die dynamische Auflösung bleibt aktiv: ruckelt es, rechnet das Spiel mit weniger Pixeln.
Aufruf: python3 tools/build_ultra.py
"""
from pathlib import Path

root = Path(__file__).resolve().parent.parent
src = (root / 'Vortexia.html').read_text(encoding='utf-8')

REPL = [
    ("this.set=Object.assign({q:'auto',", "this.set=Object.assign({q:'ultra',"),
    ("LS.get('vx_set',{})", "LS.get('vx_set_ultra',{})"),
    ("LS.set('vx_set',S_)", "LS.set('vx_set_ultra',S_)"),
    (" ultra:{n:'Ultra',pr:2,post:true,vol:true,steps:22,refl:true,rd:1,shadow:2048,",
     " ultra:{n:'Ultra',pr:2,post:true,vol:true,steps:30,refl:true,rd:1,shadow:4096,"),
    ('<title>VORTEXIA – VALOQIS STUDIO</title>', '<title>VORTEXIA ULTRA – VALOQIS STUDIO</title>'),
]
for old, new in REPL:
    n = src.count(old)
    if n != 1:
        raise SystemExit(f'Stelle nicht eindeutig gefunden ({n}x): {old[:60]}')
    src = src.replace(old, new)

(root / 'Vortexia_ULTRA.html').write_text(src, encoding='utf-8')
print('Vortexia_ULTRA.html geschrieben')
