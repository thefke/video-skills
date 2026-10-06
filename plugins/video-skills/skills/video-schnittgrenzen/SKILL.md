---
name: video-schnittgrenzen
description: >
  Die Schnittgrenzen eines fertigen Videos als Bildindex bestimmen, um einzelne
  Einstellungen gezielt zu ersetzen. Nutze das bei "wo sind die Schnitte",
  "Segment austauschen", "Einstellung neu schneiden" oder "umschneiden".
user-invocable: true
argument-hint: "[datei] [schwelle]"
license: MIT
---

# Schnittgrenzen als Bildindex

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/find_cuts.py" REEL.mp4
```

## Warum Bildindex und nicht Sekunden

Das erste Bild liegt nicht zwingend bei 0. In einem real geschnittenen Reel lag es bei
0,021029 s, danach exakt 1/30 s Abstand. Die Zeit eines Bildes ist also `pts[0] + n/fps`,
nicht `n/fps`. Wer in Sekunden rechnet, liegt an jeder Grenze daneben.

Die Szenenerkennung von ffmpeg (`select='gt(scene,0.12)'`) findet dieselben Stellen,
liefert aber nur Zeiten. Fuer den Schnitt brauchst du den Index.

## Gegenpruefen

Nach dem Umschneiden Basis gegen Ergebnis Bild fuer Bild vergleichen, nicht nur
stichprobenhaft hinsehen. Ein einzelnes durchgerutschtes Bild ist im Abspielen kaum zu
sehen, aber es ist da: In einem Fall blieb genau ein Bild der alten Einstellung stehen,
inklusive der Hand, die eigentlich rausgeschnitten werden sollte.
