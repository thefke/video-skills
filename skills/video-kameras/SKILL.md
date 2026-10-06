---
name: video-kameras
description: >
  Mehrkamera-Material nach Einstellungen gruppieren und Sprecher zuordnen, bevor Clips
  ausgewaehlt werden. Nutze das bei "Talk", "Podcast mit mehreren Gaesten", "wer ist wann
  im Bild", "Clip-Kandidaten aus einem langen Video".
user-invocable: true
argument-hint: "[datei] [--gruppen n] [--takt s]"
license: MIT
---

# Kameras clustern und zuordnen

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cluster_shots.py" TALK.mp4 --gruppen 8 --takt 5
```

Schreibt `kameras.csv` (Startsekunde, Endsekunde, Gruppe) und je Gruppe ein Beispielbild.

## Zuordnung

Die Gruppen sind erstmal nur Nummern. Wer dahintersteckt, klaerst du ueber das Transkript:
Wenn jemand auf eine Frage antwortet, schneidet die Regie in aller Regel auf ihn. Nimm eine
Stelle, an der eine Person namentlich angesprochen wird und dann redet, und schau nach,
welche Gruppe dort steht. Das ist belastbarer als Raten anhand der Kleidung. In einem Fall
trugen zwei Personen Weiss.

## Warum vor der Clip-Auswahl

Nicht jede inhaltlich starke Stelle ist als Hochkant-Clip brauchbar. Waehrend einer Totale
mit mehreren Personen am Tisch gibt es keinen 9:16-Ausschnitt auf eine Person. Eine Stelle
ist nur Kandidat, wenn die Kamera auf der sprechenden Person steht.

Pruefe ausserdem die Aufloesung der Quelle: Aus 1920x1080 ist ein 9:16-Ausschnitt 608x1080
und muss fuer 1080x1920 um Faktor 1,78 hoch. Brauchbar, aber sichtbar weicher als Material
aus 4K.
