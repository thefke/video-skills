# video-skills

Videoschnitt-Handwerk fuer Claude Code, das in jedem Projekt gleich ist: Transkripte mit
Wortzeiten, Schnittgrenzen als Bildindex, Bild/Ton-Synchronitaet, Bildausschnitte aus
fertigen Renders zurueckmessen, Mehrkamera-Material clustern, framegenau schneiden.

Der Look bleibt im jeweiligen Projekt-Repo. Faustregel: Was bei einer anderen Produktion
wortgleich waere, gehoert hierher. Was Geschmack oder Kundenfreigabe abbildet, nicht.

Entstanden aus der Praxis: Reel-Produktion aus langen Interview-Aufzeichnungen.

## Installation

Das Plugin haengt am Marketplace in `thefke/thomas-hefke-os`, zusammen mit `thomas-design`
und `bibliothek`. Einmal hinzufuegen, gilt in allen Repos:

```
/plugin marketplace add thefke/thomas-hefke-os
/plugin install video-skills@thomas-hefke-os
```

Dieses Repo ist die Quelle und wird hier gepflegt. Der Marketplace verweist per
`git-subdir` auf `plugins/video-skills`.

## Skills

| Skill | Wofuer |
|---|---|
| `video-transkript` | Transkript mit Wortzeiten, Modellwahl, Laufzeiten |
| `video-schnittgrenzen` | Schnitte eines Renders als Bildindex bestimmen |
| `video-sync` | Bild gegen Ton pruefen, gehoert in jede Abnahme |
| `video-ausschnitt` | 9:16-Crop aus einem fertigen Render zurueckmessen |
| `video-kameras` | Mehrkamera-Material clustern und Sprecher zuordnen |
| `video-schnitt` | Framegenau schneiden und Segmente ersetzen |

## Voraussetzungen

`ffmpeg` (Version 9 getestet), Python mit `faster-whisper`, `numpy`, `Pillow`.
