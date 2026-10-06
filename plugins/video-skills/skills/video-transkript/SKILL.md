---
name: video-transkript
description: >
  Transkript mit Wortzeiten aus Video oder Audio ziehen, als Grundlage fuer
  Schnittgrenzen. Nutze das, wenn jemand "Transkript", "was wird gesagt",
  "Clip-Kandidaten", "Zitat finden" oder "wo endet der Satz" sagt.
user-invocable: true
argument-hint: "[datei] [--start s] [--dauer s]"
license: MIT
---

# Transkript mit Wortzeiten

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/transcribe_words.py" VIDEO.mp4 --start 294 --dauer 14 --modell medium
```

Braucht `faster-whisper` und `ffmpeg`.

## Regeln

- **Immer Wortzeiten, nie nur Segmente.** Ohne Wortende kannst du nicht pruefen, ob ein
  Clip mitten im Wort endet. Genau das ist der haeufigste Korrekturgrund.
- `vad_filter=False` beim Pruefen von Schnittgrenzen. Mit VAD verschluckt die Erkennung
  Pausen und die Zeiten verschieben sich.
- `small` reicht zum Sichten, fuer Schnittgrenzen `medium`. Zwischen beiden lagen in der
  Praxis bis zu 0,3 s bei einzelnen Wortenden.
- Whisper streut an den Raendern eines Suchfensters. Wenn ein Wortende wichtig ist, miss
  zusaetzlich die Huellkurve: Sprache endet dort, wo der Pegel in die Pause faellt.
  Das ist belastbarer als der Zeitstempel des Modells.
- Laufzeit grob: `small` auf CPU etwa 1,8-fache Echtzeit. Eine Stunde Material also
  rund 35 Minuten. Lange Transkripte im Hintergrund laufen lassen und mitschreiben.

## Danach

Schnittgrenzen gegen den Text pruefen: Ein Clip endet am Satzende. Faengt die Person
danach einen neuen Satz an, wird vor dessen erstem Wort geschnitten.
