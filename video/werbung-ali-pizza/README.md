# Werbung: Stiftung-Ali-Test-Pizza @ The Pizzary (ab 03.11.)

- Stimme: nur Alis zwei Sätze aus dem Referenz-Video (0,55–5,35 s und 32,55–37,75 s), Rest eigene Animation + Beat
- `audio_pizza.py` erwartet `ali_full.wav` (Ton des Referenz-Videos, 44,1 kHz Stereo)
- Rendern: `python3 audio_pizza.py && ffmpeg -i audio_pizza.wav -af loudnorm=I=-14:TP=-1.2 audio_pizza_norm.wav && python3 pizza.py timing_pizza.json out.mp4 audio_pizza_norm.wav`
- Benötigt `render4.py`-Kern (pizza.py ist eine Kopie davon) und `mascot_part.py`
