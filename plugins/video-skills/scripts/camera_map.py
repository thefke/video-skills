#!/usr/bin/env python3
"""Kamerakarte fuer einen Mehrkamera-Talk: wann steht welche Einstellung im Bild, und wo laeuft die Zielperson.

    python3 camera_map.py TALK.mp4 --ref 3400,4000,1880 --gruppen 9 --out kameras.json

Ablauf:
1. Mini-Frames 48x27 mit 2 fps (ffmpeg, rohe RGB-Daten, eine Stunde Material dauert ein paar Minuten).
2. Schnitte der Regie per Bilddifferenz, daraus Einstellungen.
3. k-means ueber die Mittelbilder der Einstellungen, gewichtet nach Dauer, mehrere Starts.
4. Die Cluster an den Referenzzeiten (Stellen, an denen die Zielperson sicher im Bild ist) gelten als Zielperson.
   Aendert sich das Licht im Lauf der Aufzeichnung, landet dieselbe Kamera oft in zwei Clustern. Das ist in Ordnung.
5. Jedes Frame einzeln dem naechsten Cluster zuordnen, glaetten, zu Bloecken zusammenfassen.
6. Je Cluster vier Beispielbilder in einem Kontaktbogen: Die Zuordnung immer am Bild pruefen.

Ausgabe: JSON mit Einstellungen, Clustern, Dauer je Cluster und den Bloecken der Zielperson, dazu `<out>-cluster.jpg`.

Zweiter Lauf: Zeigt der Kontaktbogen die Zielperson auch in anderen Clustern, mit --ziel 2,3 wiederholen (derselbe
Seed liefert dieselben Cluster). Mischt ein Cluster zwei Personen, mit mehr --gruppen wiederholen.

Grenzen: Zwei Nahaufnahmen mit aehnlichem Bild (zwei Personen in weissem Shirt vor hellem Grund) verwechselt k-means.
Die Bloecke sind eine Vorauswahl. Vor dem Schnitt jede Clipgrenze mit check_camera_cuts.py und am Standbild pruefen.
"""
import argparse
import json
import subprocess
from pathlib import Path

import numpy as np

W, H = 48, 27


def mini_frames(video, fps):
    roh = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-an", "-vf", f"fps={fps},scale={W}:{H}:flags=area",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    n = len(roh) // (W * H * 3)
    return np.frombuffer(roh[: n * W * H * 3], dtype=np.uint8).reshape(n, H, W, 3).astype(np.float32) / 255


def kmeans(vek, gew, k, starts=8, seed=1):
    rng = np.random.default_rng(seed)
    best = None
    for _ in range(starts):
        zent = vek[rng.choice(len(vek), k, replace=False, p=gew / gew.sum())]
        for _ in range(80):
            lab = ((vek[:, None] - zent[None]) ** 2).sum(-1).argmin(1)
            neu = np.stack([np.average(vek[lab == j], axis=0, weights=gew[lab == j]) if (lab == j).any() else zent[j]
                            for j in range(k)])
            if np.allclose(neu, zent):
                break
            zent = neu
        kosten = (((vek - zent[lab]) ** 2).sum(-1) * gew).sum()
        if best is None or kosten < best[0]:
            best = (kosten, lab.copy(), zent.copy())
    return best[1], best[2]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--ref", required=True, help="Sekunden mit der Zielperson im Bild, kommagetrennt")
    ap.add_argument("--ziel", help="Cluster der Zielperson nach Blick auf den Kontaktbogen, kommagetrennt; ersetzt --ref")
    ap.add_argument("--gruppen", type=int, default=9)
    ap.add_argument("--fps", type=float, default=2.0)
    ap.add_argument("--min", type=float, default=12.0, help="Bloecke ab dieser Laenge auflisten")
    ap.add_argument("--out", default="kameras.json")
    a = ap.parse_args()

    f = mini_frames(a.video, a.fps)
    n = len(f)
    diff = np.abs(f[1:] - f[:-1]).mean(axis=(1, 2, 3))
    schnitt = np.where(diff > max(0.06, np.percentile(diff, 97)))[0] + 1
    grenzen = [0] + [int(x) for x in schnitt] + [n]
    shots = [(s, e) for s, e in zip(grenzen[:-1], grenzen[1:]) if e > s]
    vek = np.stack([f[s:e].mean(axis=0)[::3, ::3].ravel() for s, e in shots])
    gew = np.array([e - s for s, e in shots], dtype=np.float32)
    lab, zent = kmeans(vek, gew, a.gruppen)

    def shot_bei(t):
        i = int(t * a.fps)
        return next(j for j, (s, e) in enumerate(shots) if s <= i < e)

    ziel = sorted({int(lab[shot_bei(float(t))]) for t in a.ref.split(",")})
    if a.ziel:
        ziel = sorted(int(x) for x in a.ziel.split(","))

    # Frames einzeln zuordnen (Einstellungen koennen zwei Kameras zusammenfassen, wenn ein Schnitt weich ist)
    fv = f[:, ::3, ::3].reshape(n, -1)
    pf = ((fv[:, None] - zent[None]) ** 2).sum(-1).argmin(1)
    treffer = np.isin(pf, ziel).astype(int)
    treffer = (np.convolve(treffer, np.ones(3), "same") >= 2).astype(int)
    bloecke, i = [], 0
    while i < n:
        if treffer[i]:
            j = i
            while j < n and treffer[j]:
                j += 1
            if bloecke and i / a.fps - bloecke[-1][1] <= 0.5:
                bloecke[-1][1] = j / a.fps
            else:
                bloecke.append([i / a.fps, j / a.fps])
            i = j
        else:
            i += 1

    dauer = {int(c): float(gew[lab == c].sum() / a.fps) for c in range(a.gruppen)}
    out = {"fps": a.fps, "ziel_cluster": ziel, "dauer_s": dauer,
           "shots": [{"von": s / a.fps, "bis": e / a.fps, "cluster": int(c)} for (s, e), c in zip(shots, lab)],
           "bloecke": [[round(x, 2), round(y, 2)] for x, y in bloecke]}
    Path(a.out).write_text(json.dumps(out, indent=1))

    # Kontaktbogen: je Cluster vier Einstellungen, damit die Zuordnung am Bild geprueft wird
    tmp = Path(a.out).with_suffix("")
    bilder = []
    rng = np.random.default_rng(2)
    for c in range(a.gruppen):
        kand = [(s, e) for (s, e), l in zip(shots, lab) if l == c and (e - s) / a.fps > 3]
        wahl = sorted(rng.choice(len(kand), min(4, len(kand)), replace=False)) if kand else []
        for k in range(4):
            datei = f"{tmp}-c{c}-{k}.jpg"
            if k < len(wahl):
                s, e = kand[wahl[k]]
                t = (s + e) / 2 / a.fps
                text = f"c{c} {int(t // 60)}\\:{int(t % 60):02d}" + (" Ziel" if c in ziel else "")
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.1f}", "-i", a.video, "-frames:v", "1", "-vf",
                                f"scale=320:180,drawtext=text='{text}':x=6:y=6:fontsize=18:fontcolor=yellow:box=1:boxcolor=black",
                                datei], check=True)
            else:
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=320x180", "-frames:v", "1", datei], check=True)
            bilder.append(datei)
    ins = [x for b in bilder for x in ("-i", b)]
    zeilen = "".join("".join(f"[{r * 4 + k}]" for k in range(4)) + f"hstack=4[r{r}];" for r in range(a.gruppen))
    stapel = "".join(f"[r{r}]" for r in range(a.gruppen)) + (f"vstack={a.gruppen}" if a.gruppen > 1 else "null")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", zeilen + stapel, f"{tmp}-cluster.jpg"], check=True)
    for b in bilder:
        Path(b).unlink(missing_ok=True)

    print(f"{n} Frames, {len(shots)} Einstellungen, Zielperson in Cluster {ziel}")
    for c in sorted(dauer, key=lambda c: -dauer[c]):
        print(f"  Cluster {c}: {dauer[c] / 60:.1f} min" + ("  <- Ziel" if c in ziel else ""))
    gesamt = sum(y - x for x, y in bloecke)
    lang = [b for b in bloecke if b[1] - b[0] >= a.min]
    print(f"Zielperson: {gesamt / 60:.1f} min in {len(bloecke)} Bloecken, {len(lang)} ab {a.min:.0f} s")
    for x, y in lang:
        print(f"  {int(x // 60):02d}:{x % 60:04.1f} - {int(y // 60):02d}:{y % 60:04.1f}  {y - x:5.1f} s")
    print(f"Kontaktbogen: {tmp}-cluster.jpg")


if __name__ == "__main__":
    main()
