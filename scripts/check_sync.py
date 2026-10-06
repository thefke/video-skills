#!/usr/bin/env python3
"""Pruefen, ob ein fertiger Schnitt lippensynchron ist.

    python3 check_sync.py RENDER.mp4 12.5 MASTER.mp4 437.0

Misst zweimal unabhaengig, an welcher Stelle des Masters der Render gerade ist:
einmal ueber den Ton (Kreuzkorrelation), einmal ueber das Bild (Bildkorrelation).
Stimmen beide nicht ueberein, laeuft der Ton gegen das Bild.

Warum das noetig ist: Ein Schnitt kann Bild fuer Bild sauber sein und trotzdem
unbrauchbar, wenn Ton und Bild gegeneinander laufen. Bild gegen Bild zu pruefen
findet das nie. In einem freigegebenen Reel steckte so ein Fehler von 379 ms, der
ueber die Laufzeit anwuchs - er faellt erst auf, wenn man genau diese Messung macht.

Richtwerte: unter 45 ms faellt nicht auf, ab 125 ms stoert es deutlich.
"""
import subprocess, sys, numpy as np, wave
from PIL import Image

render, t_render, master, t_master = sys.argv[1], float(sys.argv[2]), sys.argv[3], float(sys.argv[4])
crop = sys.argv[5] if len(sys.argv) > 5 else None      # z.B. "1215:2160:702:0"
SR = 16000

def ton(pfad, ss=None, dauer=None):
    out = "/tmp/_sync.wav"
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-y"]
    if ss is not None: cmd += ["-ss", str(ss)]
    if dauer is not None: cmd += ["-t", str(dauer)]
    cmd += ["-i", pfad, "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", out]
    subprocess.run(cmd, check=True)
    w = wave.open(out)
    return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768

def bild(pfad, t, vf=None):
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{t:.5f}", "-i", pfad, "-frames:v", "1"]
    if vf: cmd += ["-vf", vf]
    cmd += ["/tmp/_sync.png"]
    subprocess.run(cmd, check=True)
    return np.asarray(Image.open("/tmp/_sync.png").convert("L"), dtype=np.float32)

norm = lambda x: (x - x.mean()) / (x.std() + 1e-9)

# --- Ton: wo im Master liegt das, was hier zu hoeren ist?
FENSTER, SUCHE = 1.5, 0.6
ref = ton(render, t_render, FENSTER)
such = ton(master, t_master - SUCHE, FENSTER + 2 * SUCHE)
ref, such = ref - ref.mean(), such - such.mean()
k = np.correlate(such, ref, "valid")
k /= (np.sqrt(np.convolve(such**2, np.ones(len(ref)), "valid")) * np.sqrt((ref**2).sum()) + 1e-9)
i = int(np.argmax(k)); ton_versatz = (i / SR - SUCHE) * 1000
print(f"Ton   passt bei Master {t_master + ton_versatz/1000:9.3f} s  ({ton_versatz:+7.1f} ms, Guete {k[i]:.3f})")

# --- Bild: dasselbe ueber Bildkorrelation, in Schritten von 1/30 s
vf_r = "scale=270:480"
vf_m = (f"crop={crop},scale=270:480" if crop else "scale=270:480")
r = norm(bild(render, t_render + FENSTER/2, vf_r))
best = (-9.0, 0.0)
for s in range(-20, 21):
    dt = s / 30.0
    c = float((norm(bild(master, t_master + FENSTER/2 + dt, vf_m)) * r).mean())
    if c > best[0]: best = (c, dt)
bild_versatz = best[1] * 1000
print(f"Bild  passt bei Master {t_master + bild_versatz/1000:9.3f} s  ({bild_versatz:+7.1f} ms, Korrelation {best[0]:.4f})")

ab = abs(bild_versatz - ton_versatz)
urteil = "unauffaellig" if ab < 45 else ("grenzwertig" if ab < 125 else "STOEREND")
print(f"\nBild gegen Ton: {ab:.1f} ms  -> {urteil}")
if not crop and best[0] < 0.9:
    print("Hinweis: niedrige Bildkorrelation. Bei beschnittenem Bild den Crop als 5. Argument angeben.")
