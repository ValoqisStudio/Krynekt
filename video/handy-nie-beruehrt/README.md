# Kurzvideo: „Du hast dein Handy noch nie berührt“

9:16-Kurzvideo (TikTok/Reels/Shorts), komplett per Code gerendert.

- `est_timing.py` – erzeugt `timing_est.json` (geschätztes Wort-Timing, bis die echte Sprachaufnahme da ist)
- `sfx.py timing.json sfx.wav` – Sounddesign (Whooshes, Impacts, Ambient-Pad)
- `render2.py timing.json out.mp4 [audio]` – rendert das Video (benötigt `numpy`, `Pillow`, `opencv-python-headless`, `ffmpeg`)

Mit echter Stimme: Wort-Timings aus der Transkription in `timing.json` schreiben, Stimme + `sfx.wav` mischen und als Audio übergeben.
