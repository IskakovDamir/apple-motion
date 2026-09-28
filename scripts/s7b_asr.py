#!/usr/bin/env python3
"""Word timestamps on the demucs vocals stem with faster-whisper (separate process: PyAV vs OpenCV)."""
import json
import os
import sys
from pathlib import Path

from faster_whisper import WhisperModel

ROOT = Path(os.environ["PROJECT_ROOT"])
slug = sys.argv[1]
ad = ROOT / "data" / slug / "audio"
model = WhisperModel("small.en", device="cpu", compute_type="int8",
                     download_root=str(Path(os.environ["HF_HOME"]) / "faster-whisper"))
segs, info = model.transcribe(str(ad / "stems" / "vocals.wav"), language="en", word_timestamps=True,
                              vad_filter=True, beam_size=5)
segments, words = [], []
for s in segs:
    segments.append({"start": s.start, "end": s.end, "text": s.text})
    for w in s.words or []:
        words.append({"word": w.word, "start": w.start, "end": w.end, "probability": w.probability})
(ad / "asr.json").write_text(json.dumps({"text": " ".join(s["text"].strip() for s in segments),
                                         "segments": segments, "words": words,
                                         "language_probability": info.language_probability}, indent=1))
print(f"[{slug}] asr: {len(words)} words")
