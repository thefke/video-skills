---
name: video-bildcheck
description: >
  Pruefen, ob in einem gerenderten Video Begriffe stehen, die nicht ins Bild duerfen: Namen,
  Interna, IDs, Links, Mailadressen, Betraege. Liest jedes Bild per OCR und die Texte aus einer
  JSON-Datei. Nutze das vor jeder Freigabe eines Videos mit nachgebauten Oberflaechen, Screenshots
  oder Tafeln, bei "ist da was Vertrauliches drin", "darf das raus", "pruef die Bilder".
user-invocable: true
argument-hint: "--liste <verboten.txt> [--json texte.json] --video <render.mp4>"
license: MIT
---

# Bilder gegen eine Verbotsliste pruefen

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bildcheck.py" --liste VERBOTEN.txt --json TEXTE.json --video RENDER.mp4
```

Zwei Pruefungen, beide ohne Modell:

1. Daten: jede Zeichenkette der JSON-Datei, exakt. Schluessel mit `_` am Anfang zaehlen nicht.
2. Bild: ffmpeg zerlegt das Video (Standard 2 Bilder je Sekunde), tesseract liest jedes Bild,
   jeder Begriff wird gesucht, exakt, ohne Leerzeichen und unscharf ab 6 Zeichen.

Dazu feste Muster ohne Liste: Session-, Trigger- und Umgebungs-IDs, Artifact-Links, Mailadressen,
Eurobetraege, IBAN, lange IDs wie bei Drive.

Exit 0 heisst keine Treffer, Exit 1 Treffer, Exit 2 fehlt ein Werkzeug oder eine Liste.

## Warum zweimal gelesen wird

tesseract liest weisse Schrift auf farbiger Flaeche nicht. In einem Reel mit Hook und Schlussfrage
als weisse Versalien auf roter Tafel blieben beide Stellen leer, das Skript haette dort nichts
gefunden. Seitdem liest es jedes Bild zweimal: normal als verstreuter Text (`--psm 11`) und
invertiert als Seite (`--psm 3`). Erst die invertierte Lesart findet Weiss auf Rot und farbige
Uhrzeiten.

**Vor dem ersten Einsatz eine Gegenprobe.** Ein Testbild mit einem verbotenen Begriff in der
schwierigsten Darstellung des Videos (etwa Weiss auf der Akzentfarbe) muss Exit 1 liefern.
Ein Pruefskript, das nie etwas findet, ist nicht geprueft.

```bash
python3 -c "from PIL import Image, ImageDraw, ImageFont; im=Image.new('RGB',(1080,1920),'#f9f9f9'); d=ImageDraw.Draw(im); d.rectangle([80,300,1000,420],fill='#b7102a'); d.text((100,320),'BEGRIFF',fill='white',font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',64)); im.save('probe.png')"
ffmpeg -v error -y -loop 1 -i probe.png -t 1 -pix_fmt yuv420p probe.mp4
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bildcheck.py" --liste VERBOTEN.txt --video probe.mp4
```

## Listen

Ein Begriff je Zeile, `#` fuer Kommentare. Mehrere Listen mit mehrfachem `--liste`. Fehlt eine
angegebene Liste, bricht das Skript ab. Die Listen gehoeren ins Projekt, nie in dieses Plugin:
Namen von Kunden und Interna sind keine Technik.

`--nur-muster` prueft ohne Liste. Das muss ausdruecklich gesetzt werden, damit ein vergessener
Pfad nicht als "keine Treffer" durchgeht.

## Grenzen

- Was tesseract gar nicht liest (sehr kleine Schrift, starke Bewegungsunschaerfe), findet das Skript
  nicht. `--text` zeigt, was je Bild gelesen wurde, damit laesst sich das stichprobenartig pruefen.
- Gesprochenes prueft es nicht. Dafuer das Transkript (`video-transkript`) gegen dieselbe Liste
  laufen lassen.
- Laufzeit: etwa 1 s je Bild auf einem Container mit zwei Kernen. Lange Videos mit `--fps 1`.

## Voraussetzungen

`ffmpeg`, `tesseract-ocr` mit `tesseract-ocr-deu`, Python mit `Pillow`.
