# video-skills

Videoschnitt-Handwerk fuer Claude Code, das in jedem Projekt gleich ist: Transkripte mit
Wortzeiten, Schnittgrenzen als Bildindex, Bild/Ton-Synchronitaet, Bildausschnitte aus
fertigen Renders zurueckmessen, Mehrkamera-Material clustern, framegenau schneiden.

Der Look bleibt im jeweiligen Projekt-Repo. Faustregel: Was bei einer anderen Produktion
wortgleich waere, gehoert hierher. Was Geschmack oder Kundenfreigabe abbildet, nicht.

Entstanden aus der Praxis: Reel-Produktion aus langen Interview-Aufzeichnungen.

## Installation

```
/plugin marketplace add thefke/video-skills
/plugin install video-skills@thefke-video-skills
```

## Voraussetzungen

`ffmpeg` (Version 9 getestet), Python mit `faster-whisper`, `numpy`, `Pillow`.
