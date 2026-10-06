---
name: video-sync
description: >
  Pruefen, ob ein geschnittenes Video lippensynchron ist, durch getrennte Messung von
  Ton und Bild gegen das Rohmaterial. Nutze das bei "wirkt unrund", "stimmt was nicht",
  "lippensynchron", "Ton passt nicht", oder vor jeder Abgabe eines Schnitts.
user-invocable: true
argument-hint: "[render] [zeit] [master] [master-zeit] [crop]"
license: MIT
---

# Bild gegen Ton pruefen

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_sync.py" REEL.mp4 12.5 MASTER.mp4 437.0 "1215:2160:702:0"
```

Misst zweimal unabhaengig, an welcher Stelle des Masters der Schnitt gerade ist: einmal
ueber den Ton per Kreuzkorrelation, einmal ueber das Bild. Die Differenz ist der Versatz.

## Warum das in die Abnahme gehoert

Ein Schnitt kann Bild fuer Bild fehlerfrei sein und trotzdem unbrauchbar. In einem bereits
freigegebenen Reel steckte ein Versatz, der mit der Laufzeit anwuchs: 33 ms am Anfang,
233 ms nach 42 Sekunden, 367 ms am Ende. Das Ergebnis fuehlte sich "unrund" an, ohne dass
jemand sagen konnte warum. Drei Korrekturrunden an den Schnittgrenzen haben daran nichts
geaendert, weil immer nur Bild gegen Bild geprueft wurde.

**Pruefe an mindestens drei Stellen: Anfang, Mitte, Ende.** Ein Versatz, der mitwaechst,
ist an einer einzelnen Stelle unsichtbar.

## Richtwerte

| Abweichung | Wirkung |
|---|---|
| unter 45 ms | faellt nicht auf |
| 45 bis 125 ms | grenzwertig |
| ueber 125 ms | stoert deutlich |

## Wenn es nicht stimmt

Nicht nachjustieren, sondern das Segment aus dem Master neu bauen: Bild und Ton aus
derselben Quelle am selben Timecode. Dann ist Synchronitaet bauartbedingt richtig
statt nachtraeglich hingeschoben.
