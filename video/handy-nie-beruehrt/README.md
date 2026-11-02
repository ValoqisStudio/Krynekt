# Kurzvideo: „Du hast dein Handy noch nie berührt“

9:16-Kurzvideo (TikTok/Reels/Shorts), komplett per Code gerendert.

- `est_timing.py` – erzeugt `timing_est.json` (geschätztes Wort-Timing, bis die echte Sprachaufnahme da ist)
- `sfx.py timing.json sfx.wav` – Sounddesign (Whooshes, Impacts, Ambient-Pad)
- `render2.py timing.json out.mp4 [audio]` – rendert das Video (benötigt `numpy`, `Pillow`, `opencv-python-headless`, `ffmpeg`)

Mit echter Stimme: Wort-Timings aus der Transkription in `timing.json` schreiben, Stimme + `sfx.wav` mischen und als Audio übergeben.

## Version 3
- `timing_v3.json`: echte Wort-Timings der ElevenLabs-Stimme (Adrian, eleven_v4, 41,3 s)
- Rendern: `python3 sfx.py timing_v3.json sfx_v3.wav && python3 render2.py timing_v3.json v3_bild.mp4 sfx_v3.wav`
- Stimme draufmischen:
  `ffmpeg -i v3_bild.mp4 -i voice.mp3 -filter_complex "[1:a]volume=1.0[v];[0:a]volume=0.45[s];[v][s]amix=inputs=2:duration=longest:normalize=0[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k v3_final.mp4`
