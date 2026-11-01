#!/usr/bin/env python3
"""Kameraschnitte in geplanten Clip-Segmenten finden, mit 10 fps, und je Schnitt ein Bild zum Pruefen.

    python3 check_camera_cuts.py TALK.mp4 --segment 3493.0-3499.0 --segment 2872.5-2888.0 --bilder pruefung/

Je Segment: alle Regie-Schnitte (Bilddifferenz zwischen Nachbarframes) auf 0,1 s genau, dazu ein Bild am Segmentanfang
und direkt nach jedem Schnitt. Erst die Bilder zeigen, welche Person dort steht. Die Kamerakarte (camera_map.py) kann
aehnliche Nahaufnahmen verwechseln, die Bilder nicht.

Wofuer: Ein Hochkant-Ausschnitt gilt immer nur fuer eine Kamera. Schneidet die Regie innerhalb eines Clips auf eine
andere Kamera, braucht dieses Stueck einen eigenen Ausschnitt, oder der Clip beginnt bzw. endet am Schnitt.
"""
import argparse
import subprocess
from pathlib import Path

import numpy as np

W, H = 48, 27


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--segment", action="append", required=True, help="von-bis in Sekunden, z. B. 3493.0-3499.0")
    ap.add_argument("--schwelle", type=float, default=0.05)
    ap.add_argument("--bilder", default="pruefung")
    a = ap.parse_args()
    ordner = Path(a.bilder)
    ordner.mkdir(parents=True, exist_ok=True)
    for seg in a.segment:
        von, bis = (float(x) for x in seg.split("-"))
        roh = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{von - 0.5:.2f}", "-t", f"{bis - von + 1.0:.2f}", "-i", a.video,
                              "-an", "-vf", f"fps=10,scale={W}:{H}:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True, check=True).stdout
        n = len(roh) // (W * H * 3)
        g = np.frombuffer(roh[: n * W * H * 3], dtype=np.uint8).reshape(n, H, W, 3).astype(np.float32) / 255
        diff = np.r_[0, np.abs(g[1:] - g[:-1]).mean(axis=(1, 2, 3))]
        t = von - 0.5 + np.arange(n) / 10
        schnitte = [round(float(t[i]), 1) for i in range(1, n) if diff[i] > a.schwelle and von - 0.3 <= t[i] <= bis + 0.3]
        pruef = [von + 0.2] + [s + 0.2 for s in schnitte]
        for p in pruef:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{p:.2f}", "-i", a.video, "-frames:v", "1", "-vf",
                            f"scale=320:-2,drawtext=text='{p:.1f}':x=6:y=6:fontsize=18:fontcolor=yellow:box=1:boxcolor=black",
                            str(ordner / f"{von:.1f}_{p:.1f}.jpg")], check=True)
        print(f"{von:.2f}-{bis:.2f}: Schnitte {schnitte or 'keine'}  Bilder: {len(pruef)} in {ordner}/")


if __name__ == "__main__":
    main()
