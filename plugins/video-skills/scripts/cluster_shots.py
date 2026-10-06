#!/usr/bin/env python3
"""Mehrkamera-Material nach Einstellungen gruppieren.

    python3 cluster_shots.py VIDEO.mp4 --gruppen 8 --takt 5

Legt `shots/` mit Stichproben an, gruppiert sie und schreibt `kameras.csv`
(Startsekunde, Endsekunde, Gruppe) plus je Gruppe ein Beispielbild.

Wofuer: In einem Talk mit mehreren Kameras ist nicht jede inhaltlich gute Stelle
auch als Hochkant-Clip brauchbar. Waehrend einer Totale mit mehreren Personen gibt
es keinen 9:16-Ausschnitt auf eine Person. Erst die Kamerakarte, dann die Auswahl.

Wer wer ist, steht nicht im Bild: Gruppen anhand des Transkripts zuordnen. Wenn
jemand antwortet, schneidet die Regie in aller Regel auf ihn.
"""
import argparse, subprocess, glob, os, numpy as np
from PIL import Image

p = argparse.ArgumentParser()
p.add_argument("datei")
p.add_argument("--gruppen", type=int, default=8)
p.add_argument("--takt", type=int, default=5, help="Sekunden zwischen den Stichproben")
p.add_argument("--outdir", default="shots")
a = p.parse_args()

os.makedirs(a.outdir, exist_ok=True)
for f in glob.glob(a.outdir + "/*.png"): os.remove(f)
subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", a.datei,
                "-vf", f"fps=1/{a.takt},scale=64:36", "-fps_mode", "passthrough",
                a.outdir + "/%05d.png"], check=True)
fs = sorted(glob.glob(a.outdir + "/*.png"))
X = np.stack([np.asarray(Image.open(f).convert("RGB"), dtype=np.float32).ravel() / 255 for f in fs])
print(f"{len(X)} Stichproben, Takt {a.takt} s")

rng = np.random.RandomState(0)
C = [X[rng.randint(len(X))]]
for _ in range(a.gruppen - 1):                       # k-means++ Start
    d = np.min(((X[:, None, :] - np.array(C)[None])**2).sum(2), axis=1)
    C.append(X[int(np.argmax(d))])
C = np.array(C)
for it in range(60):
    zu = np.argmin(((X[:, None, :] - C[None])**2).sum(2), axis=1)
    neu = np.array([X[zu == k].mean(0) if (zu == k).any() else C[k] for k in range(a.gruppen)])
    if np.allclose(neu, C): break
    C = neu
zu = np.argmin(((X[:, None, :] - C[None])**2).sum(2), axis=1)

bloecke, start = [], 0
for i in range(1, len(zu) + 1):
    if i == len(zu) or zu[i] != zu[start]:
        bloecke.append((start * a.takt, i * a.takt, int(zu[start]))); start = i
with open("kameras.csv", "w") as f:
    f.write("start_s,ende_s,gruppe\n")
    for s, e, k in bloecke: f.write(f"{s},{e},{k}\n")

for k in range(a.gruppen):
    idx = np.where(zu == k)[0]
    if not len(idx): continue
    rep = int(idx[np.argmin(((X[idx] - C[k])**2).sum(1))]) * a.takt
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", str(rep), "-i", a.datei,
                    "-frames:v", "1", "-vf", "scale=320:-1", f"{a.outdir}/gruppe_{k}.jpg"], check=True)
    print(f"  Gruppe {k}: {len(idx)*a.takt/60:5.1f} min in "
          f"{len([b for b in bloecke if b[2]==k]):3d} Bloecken, Beispiel bei {rep//60}:{rep%60:02d}")
print(f"\nkameras.csv geschrieben, Beispielbilder in {a.outdir}/gruppe_*.jpg")
