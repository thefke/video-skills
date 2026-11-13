#!/usr/bin/env python3
"""Prüft Texte und gerenderte Bilder eines Videos gegen Verbotslisten.

Zwei Prüfungen, beide ohne Modell:
1. Daten: jede Zeichenkette einer JSON-Datei (die Texte, die ins Bild sollen), exakt.
2. Bild: ein Video wird mit ffmpeg in Einzelbilder zerlegt (Standard 2 je Sekunde), tesseract liest
   den Text zweimal (normal und invertiert), jeder Begriff der Listen wird gesucht, auch unscharf
   (OCR-Fehler) und ohne Leerzeichen.

Listen: eine oder mehrere Textdateien, ein Begriff je Zeile, # für Kommentare. Fehlt eine angegebene
Liste, bricht das Skript ab, statt ohne sie „grün“ zu melden. Dazu feste Muster: Session-, Trigger-
und Umgebungs-IDs, Artifact-Links, Mailadressen, Eurobeträge, IBAN, lange IDs wie bei Drive.

Aufruf:
    python3 bildcheck.py --liste verboten.txt --json texte.json --video render.mp4
    python3 bildcheck.py --liste a.txt --liste b.txt --video render.mp4 --fps 4
    python3 bildcheck.py --liste a.txt --video render.mp4 --text      # gelesenen Text je Bild ausgeben
    python3 bildcheck.py --nur-muster --video render.mp4               # ohne Liste, nur feste Muster

Exit 0: nichts gefunden. Exit 1: Treffer (Liste auf stdout). Exit 2: Werkzeug oder Liste fehlt.
Braucht ffmpeg, tesseract (apt-get install -y tesseract-ocr tesseract-ocr-deu) und Pillow.
"""
import argparse
import difflib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageOps


MUSTER = {
    "Session-ID": r"\b(session|cse)_[A-Za-z0-9]{8,}",
    "Trigger-ID": r"\btrig_[A-Za-z0-9]{8,}",
    "Umgebungs-ID": r"\benv_[A-Za-z0-9]{8,}",
    "Artifact-Link": r"claude\.ai/(artifact|code)",
    "Mailadresse": r"[\w.+-]+@[\w-]+\.[a-z]{2,}",
    "Eurobetrag": r"\d[\d.,]*\s?(€|eur\b)|€\s?\d",
    "IBAN": r"\bde\d{2}\s?(\d{4}\s?){4}\d{2}\b",
    "lange ID": r"\b(?=[A-Za-z0-9_-]*\d)(?=[A-Za-z0-9_-]*[A-Za-z])[A-Za-z0-9_-]{28,}\b",
}
UNSCHARF_AB = 6  # Begriffe ab dieser Länge auch unscharf suchen
SCHWELLE = 0.86


def norm(s: str) -> str:
    """Kleinschreibung, alles außer Buchstaben und Ziffern wird Leerzeichen."""
    return " " + re.sub(r"[^0-9a-zäöüß]+", " ", s.casefold()).strip() + " "


def kompakt(s: str) -> str:
    return re.sub(r"[^0-9a-zäöüß]", "", s.casefold())


def liste_lesen(pfad: Path) -> list[str]:
    return [z.strip() for z in pfad.read_text(encoding="utf-8").splitlines() if z.strip() and not z.lstrip().startswith("#")]


def treffer(text: str, begriffe: list[str]) -> list[tuple[str, str]]:
    """Liefert (Begriff oder Muster, Fundstelle). text ist roh, Begriffe werden normalisiert gesucht."""
    funde = []
    n = norm(text)
    k = kompakt(text)
    woerter = n.split()
    for b in begriffe:
        bn = norm(b)
        bk = kompakt(b)
        if not bk:
            continue
        if bn in n or (len(bk) >= UNSCHARF_AB and bk in k):
            funde.append((b, "exakt"))
            continue
        if len(bk) < UNSCHARF_AB:
            continue
        laenge = len(bn.split())
        for i in range(len(woerter) - laenge + 1):
            stueck = "".join(woerter[i : i + laenge])
            if abs(len(stueck) - len(bk)) <= 2 and difflib.SequenceMatcher(None, stueck, bk).ratio() >= SCHWELLE:
                funde.append((b, f"unscharf: {' '.join(woerter[i:i + laenge])}"))
                break
    for name, rx in MUSTER.items():
        m = re.search(rx, text, flags=re.IGNORECASE)
        if m:
            funde.append((name, m.group(0)))
    return funde


def strings(obj, pfad=""):
    if isinstance(obj, dict):
        for key, wert in obj.items():
            if str(key).startswith("_"):
                continue
            yield from strings(wert, f"{pfad}.{key}" if pfad else str(key))
    elif isinstance(obj, list):
        for i, wert in enumerate(obj):
            yield from strings(wert, f"{pfad}[{i}]")
    elif isinstance(obj, str):
        yield pfad, obj


def json_pruefen(pfad: Path, begriffe: list[str]) -> list[str]:
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    aus = []
    for wo, s in strings(daten):
        for b, fund in treffer(s, begriffe):
            if fund == "exakt" or not fund.startswith("unscharf"):
                aus.append(f"Daten {wo}: {b} ({fund})")
    return aus


def video_pruefen(video: Path, begriffe: list[str], fps: float, text_zeigen: bool) -> list[str]:
    aus = []
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            ["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps={fps}", f"{tmp}/b%05d.png"],
            check=True,
        )
        bilder = sorted(Path(tmp).glob("b?????.png"))
        for i, bild in enumerate(bilder):
            sek = i / fps
            # Zweimal lesen: normal als verstreuter Text (psm 11) und invertiert als Seite (psm 3).
            # Weiße Schrift auf Rot (Hook, Tafeln) und rote Uhrzeiten findet nur die invertierte Lesart,
            # getestet an einem Reel mit Tafeln in Weiß auf Rot und an einem Probebild (13.11.2026).
            invers = bild.with_name(bild.stem + "-inv.png")
            ImageOps.invert(Image.open(bild).convert("L")).save(invers)
            text = "\n".join(
                subprocess.run(
                    ["tesseract", str(b), "stdout", "-l", "deu+eng", "--psm", psm],
                    capture_output=True,
                    text=True,
                ).stdout
                for b, psm in ((bild, "11"), (invers, "3"))
            )
            if text_zeigen:
                print(f"--- {sek:6.1f} s: {' '.join(text.split())}")
            for b, fund in treffer(text, begriffe):
                aus.append(f"Bild {sek:6.1f} s: {b} ({fund})")
        print(f"{len(bilder)} Bilder gelesen ({fps} je Sekunde)", file=sys.stderr)
    return aus


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", type=Path, help="JSON mit den Texten fürs Bild")
    ap.add_argument("--video", type=Path, help="gerendertes Video")
    ap.add_argument("--fps", type=float, default=2.0, help="Bilder je Sekunde für die OCR, Standard 2")
    ap.add_argument("--liste", type=Path, action="append", default=[], help="Verbotsliste, mehrfach möglich")
    ap.add_argument("--nur-muster", action="store_true", help="ohne Liste prüfen, nur die festen Muster")
    ap.add_argument("--text", action="store_true", help="gelesenen Text je Bild ausgeben")
    a = ap.parse_args()

    if not a.json and not a.video:
        ap.error("--json oder --video angeben")
    if not a.liste and not a.nur_muster:
        ap.error("mindestens eine --liste angeben oder ausdrücklich --nur-muster")
    fehlt = [str(l) for l in a.liste if not l.exists()]
    if fehlt:
        print(f"Verbotsliste fehlt: {', '.join(fehlt)}", file=sys.stderr)
        return 2
    listen = a.liste
    begriffe = sorted({b for l in listen for b in liste_lesen(l)})
    if a.video and (not shutil.which("ffmpeg") or not shutil.which("tesseract")):
        print("ffmpeg oder tesseract fehlt: apt-get install -y ffmpeg tesseract-ocr tesseract-ocr-deu", file=sys.stderr)
        return 2

    funde = []
    if a.json:
        funde += json_pruefen(a.json, begriffe)
    if a.video:
        funde += video_pruefen(a.video, begriffe, a.fps, a.text)

    print(f"{len(begriffe)} Begriffe aus {len(listen)} Listen, {len(MUSTER)} Muster", file=sys.stderr)
    if funde:
        print(f"{len(funde)} Treffer:")
        for f in funde:
            print(" ", f)
        return 1
    print("Keine Treffer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
