---
name: video-ausschnitt
description: >
  Den 9:16-Bildausschnitt aus einem fertigen Render zurueckmessen, wenn die
  Build-Parameter fehlen oder ein neuer Ausschnitt zum alten passen muss. Nutze das
  bei "welcher Crop", "Ausschnitt rekonstruieren", "Parameter verloren".
user-invocable: true
argument-hint: "[render] [zeit] [master] [master-zeit]"
license: MIT
---

# Bildausschnitt zurueckmessen

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/match_crop.py" REEL.mp4 62.0 MASTER.mp4 297.412
```

Sucht eindimensional ueber x, weil ein 9:16-Ausschnitt aus 16:9 die volle Hoehe nutzt.
Aus 3840x2160 ist das 1215x2160.

## Lesen der Werte

- **ueber 0,99**: Treffer, der Ausschnitt stimmt.
- **deutlich darunter**: Das Segment wurde anders gebaut. Ein Opener kam auf 0,375,
  weil dort ein eingebettetes Querformat steckte statt eines Ausschnitts.

## Dazu

Pruefe auch, ob eine Farbkorrektur auf dem Render liegt, bevor du frisch aus dem Master
schneidest: denselben Ausschnitt zum selben Zeitpunkt aus beiden ziehen, Mittelwert je
Kanal und Standardabweichung vergleichen. Liegen die beieinander, passt ein direkter
Crop farblich zu den Nachbarn. Nicht auf Einzelpixel schauen, die Abweichung durch
Bewegung und Kompression ist normal.
