---
name: video-kameras
description: >
  Mehrkamera-Material nach Einstellungen gruppieren und Sprecher zuordnen, bevor Clips
  ausgewaehlt werden. Nutze das bei "Talk", "Podcast mit mehreren Gaesten", "wer ist wann
  im Bild", "Clip-Kandidaten aus einem langen Video", "Kamerakarte", "Hochkant-Ausschnitt
  je Kamera", "Frage und Antwort zwischen zwei Personen schneiden".
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

## Mehrkamera-Talk ohne Gesichtserkennung

Bewaehrt an einer 71-Minuten-Folge mit fuenf Kameras und zwei Personen in weissem Shirt.
Gesichtserkennung (Haar-Kaskaden) liegt bei Profilaufnahmen bis 250 px daneben, deshalb
arbeitet dieser Weg nur mit Bilddifferenz, Clustern und Sichtpruefung.

1. Kamerakarte fuer die ganze Aufzeichnung:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/camera_map.py" TALK.mp4 --ref 3400,4000,1880 --gruppen 9 --out kameras.json
   ```

   `--ref` sind Sekunden, an denen die Zielperson sicher im Bild ist (aus einem schon
   bekannten Clip oder dem Transkript). Das Skript schreibt die Einstellungen, die Cluster
   und die Bloecke der Zielperson, dazu einen Kontaktbogen mit vier Bildern je Cluster.
2. Kontaktbogen ansehen. Aendert sich im Lauf der Aufzeichnung das Licht, steht dieselbe
   Kamera in zwei Clustern. Mischt ein Cluster zwei Personen, mit mehr Gruppen wiederholen.
   Dann mit `--ziel 2,3` die richtigen Cluster festlegen.
3. Kandidaten nur aus Bloecken der Zielperson nehmen, Transkript dieser Bloecke mit `medium`.
4. Vor dem Schnitt jedes Segment auf Kameraschnitte pruefen, mit 10 fps und einem Bild je Schnitt:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_camera_cuts.py" TALK.mp4 --segment 3706.9-3749.6 --bilder pruefung/
   ```

   Die Bilder entscheiden, nicht die Karte. Die Karte hat zwei Nahaufnahmen mit weissem
   Shirt verwechselt. Aufgefallen ist das erst am Standbild des fertigen Clips.
   Auch Anfang und Ende pruefen, wenn ein Segment nachtraeglich verlaengert wurde.

### Ein Ausschnitt je Kamera

Ein 9:16-Ausschnitt gilt nur fuer eine Kamera. Schneidet die Regie innerhalb eines Segments
um, bekommt jedes Stueck seinen eigenen Ausschnitt, und der Wechsel sitzt framegenau auf
dem Schnitt der Regie. In einem ffmpeg-Aufruf, damit der Ton durchlaeuft:

```
[0:v]split=3[s0][s1][s2];
[s0]trim=start=0:end=7.1,setpts=PTS-STARTPTS,crop=608:1080:650:0,scale=1080:1920,fps=30,setsar=1[c0];
[s1]trim=start=7.1:end=12.9,setpts=PTS-STARTPTS,crop=608:1080:610:0,scale=1080:1920,fps=30,setsar=1[c1];
[s2]trim=start=12.9:end=15.3,setpts=PTS-STARTPTS,crop=608:1080:480:0,scale=1080:1920,fps=30,setsar=1[c2];
[c0][c1][c2]concat=n=3:v=1:a=0[v]
```

Mit `-ss` vor dem Eingang und `-map [v] -map 0:a`. Die Ausschnitte je Kamera einmal am Bild
festlegen (Sprecher mittig, Kopf nicht angeschnitten) und als Konstanten im Schnittskript halten.

Was Schnitte der Regie im Clip bedeuten:
- Frage und Antwort zwischen zwei Personen: Beide Kameras mit eigenem Ausschnitt, die Saetze
  der anderen Person in den Untertiteln abgesetzt (zum Beispiel hellgrau).
- Kurzer Zwischenschnitt auf das Gegenueber, waehrend die Zielperson weiterredet: drinlassen,
  das wirkt wie ein normaler Talk-Schnitt.
- Totale am Schluss: Ausschnitt auf die Zielperson in der Totale, als ruhiges Schlussbild brauchbar.
- Der Clip beginnt auf einer anderen Person: Start auf den ersten Satz verlegen, den die
  Zielperson im eigenen Bild sagt. Die Hook-Tafel gehoert auf ihren Koerper.

## Aufloesung

Pruefe ausserdem die Aufloesung der Quelle: Aus 1920x1080 ist ein 9:16-Ausschnitt 608x1080
und muss fuer 1080x1920 um Faktor 1,78 hoch. Brauchbar, aber sichtbar weicher als Material
aus 4K.
