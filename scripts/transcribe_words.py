#!/usr/bin/env python3
"""Transkript mit Wortzeiten. Basis fuer jede Schnittgrenze.

    python3 transcribe_words.py video.mp4 --start 59 --dauer 8 --modell medium

Ohne Wortzeiten kannst du nicht pruefen, ob ein Clip mitten im Wort endet.
Das 'small'-Modell reicht zum Sichten, fuer Schnittgrenzen 'medium' nehmen:
small lag in dieser Session bei einzelnen Wortenden bis zu 0,3 s daneben.
"""
import argparse, subprocess, tempfile, os
from faster_whisper import WhisperModel

p = argparse.ArgumentParser()
p.add_argument("datei")
p.add_argument("--start", type=float, default=0.0)
p.add_argument("--dauer", type=float, default=None)
p.add_argument("--modell", default="medium")
p.add_argument("--sprache", default="de")
a = p.parse_args()

wav = tempfile.mktemp(suffix=".wav")
cmd = ["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", str(a.start)]
if a.dauer: cmd += ["-t", str(a.dauer)]
cmd += ["-i", a.datei, "-ac", "1", "-ar", "16000", wav]
subprocess.run(cmd, check=True)

m = WhisperModel(a.modell, device="cpu", compute_type="int8")
segs, _ = m.transcribe(wav, language=a.sprache, vad_filter=False, word_timestamps=True)
for s in segs:
    for w in s.words:
        print(f"{a.start + w.start:8.2f} - {a.start + w.end:8.2f}   {w.word}")
os.unlink(wav)
