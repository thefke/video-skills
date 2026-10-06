---
name: video-schnitt
description: >
  Framegenau schneiden und Segmente ersetzen mit ffmpeg, ohne dass an den Grenzen Bilder
  durchrutschen. Nutze das bei "Segment austauschen", "umschneiden", "Einstellung
  ersetzen", "Clip verlaengern" oder "concat".
user-invocable: true
license: MIT
---

# Framegenau schneiden

## Grundregel

Segmente ueber `trim=start_frame=` und `concat` ersetzen, **nie** ueber `overlay` mit
`enable='between(t,...)'`. Das Overlay greift gegenueber den Bildzeitstempeln um ein Bild
versetzt: Am Anfang bleibt ein Bild der alten Einstellung stehen, am Ende rutscht eines
ins Folgesegment. Beides sieht man im Abspielen kaum und ist trotzdem falsch.

```
[0:v]split=2[s1][s2];
[s1]trim=start_frame=105:end_frame=685,setpts=PTS-STARTPTS,setsar=1[b1];
[s2]trim=start_frame=1661,setpts=PTS-STARTPTS,setsar=1[b2];
[1:v]crop=1215:2160:1620:0,scale=1080:1920,setsar=1,fps=30,trim=end_frame=258,setpts=PTS-STARTPTS[v1];
[b1][v1][b2]concat=n=3:v=1:a=0[vc]
```

## Fallen

- **`setsar=1` nach jedem `scale`.** Ein Crop, der nicht exakt 9:16 ist, kippt die
  Pixelform. 1800 mal 9/16 ergibt 1012,5, der ganzzahlige Crop erzeugt SAR 1214:1215 und
  `concat` bricht ab.
- **Quelle nie innerhalb einer Einstellung wechseln.** Derselbe Moment sieht aus einem
  alten 1080p-Render anders aus als frisch aus dem 4K-Master skaliert: gemessen 4,0
  mittlere Abweichung, waehrend zwei echte Nachbarbilder nur 1,61 auseinanderliegen. Der
  Wechsel ist also staerker als die Bewegung und wird als Huepfen sichtbar. Wird ein Teil
  neu gebaut, kommt die ganze Einstellung aus dem Master, damit der Wechsel auf den
  Schnitt faellt.
- **Bildzahl gegenpruefen.** Stimmt sie nicht, ist der Ton gegen das Bild verschoben.
- **ffmpeg 9 kennt `-vsync` nicht mehr.** Ersatz ist `-fps_mode passthrough`. Ohne das
  schreibt ffmpeg gar nichts und der Fehler geht leicht unter.

## Verlaengern

Bevor du einen Clip hinten verlaengerst, pruefe im Rohmaterial, ob die Person weiterredet.
Wenn ja, zeigt echtes Material tonlos bewegte Lippen. Dann das letzte Bild halten statt
Material anzuhaengen.

## Abnahme

1. Bildzahl stimmt
2. Grenzen stichprobenhaft Bild fuer Bild gegen die Basis vergleichen
3. Kontaktbogen ansehen:
   `ffmpeg -v error -y -i OUT.mp4 -vf "fps=1/2.2,scale=150:-1,tile=10x4" -frames:v 1 check.png`
   Kacheln nicht unter 300 px, wenn es um Bildraender geht. Leere Kacheln am Ende sind
   schwarz, das ist kein schwarzes Bild im Video.
4. Synchronitaet pruefen, siehe Skill `video-sync`
