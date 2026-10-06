#!/usr/bin/env python3
"""Welcher 9:16-Ausschnitt aus dem 4K-Master steckt in einem fertigen Reel?

    python3 match_crop.py REEL.mp4 62.0 MASTER.mp4 297.412

Braucht man, wenn die Build-Befehle verloren sind oder wenn ein Segment
nachgeschnitten wird und der neue Ausschnitt zum alten passen muss.

Sucht ueber die Normierte Kreuzkorrelation in einer Dimension: Der Look ist
1215x2160 ueber die volle Hoehe, also ist nur x unbekannt. Treffer liegen bei
corr > 0.99; alles darunter heisst, das Segment wurde anders gebaut
(bei unserem Opener 0.375, da steckte ein Querformat-Kasten drin).
"""
import subprocess, sys, numpy as np
from PIL import Image

reel, t_reel, master, t_master = sys.argv[1], float(sys.argv[2]), sys.argv[3], float(sys.argv[4])
BREITE, HOEHE = 1215, 2160
TW, TH = 96, 170

def bild(pfad, t, w, h, out):
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", str(t), "-i", pfad,
                    "-frames:v", "1", "-vf", f"scale={w}:{h},format=gray", out], check=True)
    return np.asarray(Image.open(out), dtype=np.float32)

def norm(a):
    a = a - a.mean(); s = a.std()
    return a / s if s > 1e-6 else a

def probe(img, x0, w):
    cx = (x0 + (np.arange(TW) + 0.5) * w / TW).astype(np.int32)
    cy = ((np.arange(TH) + 0.5) * HOEHE / TH).astype(np.int32)
    return img[np.ix_(cy, cx)]

ref = norm(probe(bild(reel, t_reel, BREITE, HOEHE, "/tmp/_ref.png"), 0, BREITE))
gross = bild(master, t_master, 3840, 2160, "/tmp/_master.png")
corr, x = max((float((norm(probe(gross, x, BREITE)) * ref).mean()), x)
              for x in range(0, 3840 - BREITE + 1))
print(f"crop={BREITE}:{HOEHE}:{x}:0   Korrelation {corr:.4f}")
