#!/usr/bin/env python3
"""Schnittgrenzen eines fertigen Reels als BILDINDEX bestimmen.

    python3 find_cuts.py REEL.mp4

Warum Bildindex und nicht Sekunden: Umschneiden ueber Zeitfenster laesst an
jeder Grenze ein Bild durchrutschen (siehe Skill video-schnitt). Mit dem Index schneidest du
ueber `trim=start_frame=` exakt.

Achtung: Das erste Bild liegt nicht zwingend bei 0, bei unserem Reel bei
0,021029 s. Die Zeit eines Bildes ist also pts[0] + n/fps, nicht n/fps.
"""
import subprocess, sys, numpy as np, glob, os, tempfile
from PIL import Image

datei = sys.argv[1]
schwelle = float(sys.argv[2]) if len(sys.argv) > 2 else 18.0

r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                    "-show_entries", "frame=pts_time", "-of", "csv=p=0", datei],
                   capture_output=True, text=True)
pts = [float(x.strip().rstrip(",")) for x in r.stdout.split() if x.strip().rstrip(",")]
print(f"{len(pts)} Bilder | erstes pts {pts[0]:.6f} | Abstand {pts[1]-pts[0]:.6f}")

d = tempfile.mkdtemp()
subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", datei,
                "-vf", "scale=160:-1", "-fps_mode", "passthrough", d + "/%05d.png"], check=True)
fs = sorted(glob.glob(d + "/*.png"))
prev = None
print("\nSchnitte:")
for i, f in enumerate(fs):
    im = np.asarray(Image.open(f).convert("L"), dtype=np.float32)
    if prev is not None and np.abs(im - prev).mean() > schwelle:
        print(f"  Bildindex {i:5d}   pts {pts[i]:9.6f} s")
    prev = im
    os.unlink(f)
