#!/usr/bin/env python3
"""Time a card script to a voice-over, the way Apple's recaps are cut (the edit follows the voice).

  python vo_cards.py cards.json --voice public/vo.wav [--words words.json] [--bpm 120] [--fps 30] -o cards_timed.json

cards.json: {"bpm": 120, "cards": [...]}  - the Card list of Recap.tsx, where a card may carry
  "onWord": "search"      the card starts when this word is spoken (next occurrence after the previous anchor),
                          shifted by VO.typeLeadFrames (measured: Apple's type lands ~2 frames before the word)
  "afterPhrase": true     alternatively, start the card at the next pause after the previous anchor
Cards without an anchor share the time between anchors in proportion to their `beats`.
Word timestamps come from --words (a list of {"word", "start", "end"} in seconds) or, if omitted, from
faster-whisper (pip install faster-whisper). Output: the same cards with fractional `beats` (the card
engine rounds start frames from the running total, so nothing drifts), plus a printed timeline and the
number of bars to generate the music bed with.
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

TYPE_LEAD_FRAMES = -2  # VO.typeLeadFrames in tokens.ts (median over 45 measured type/word pairs)
PAUSE_S = 0.15


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def transcribe(path):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("no --words given and faster-whisper is not installed (pip install faster-whisper)")
    import os
    model = WhisperModel("small.en", device="cpu", compute_type="int8", download_root=os.environ.get("WHISPER_DIR"))
    segs, _ = model.transcribe(str(path), language="en", word_timestamps=True, vad_filter=True)
    return [{"word": w.word.strip(), "start": w.start, "end": w.end} for s in segs for w in (s.words or [])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cards")
    ap.add_argument("--voice")
    ap.add_argument("--words")
    ap.add_argument("--bpm", type=float)
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--tail-beats", type=float, default=None, help="beats of the last card (default: its own beats)")
    ap.add_argument("--lead-in", default="auto",
                    help="seconds of picture/music before the voice starts; 'auto' = the nominal beats of the cards "
                         "before the first anchored card, rounded up to a whole bar")
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    doc = json.loads(Path(a.cards).read_text())
    cards = doc["cards"]
    bpm = a.bpm or doc.get("bpm", 120)
    beat_f = 60 / bpm * a.fps
    words = json.loads(Path(a.words).read_text()) if a.words else transcribe(a.voice)
    if a.words is None and a.voice:
        Path(a.out).with_suffix(".words.json").write_text(json.dumps(words, indent=1))
    first_anchor = next((i for i, c in enumerate(cards) if c.get("onWord") or c.get("afterPhrase")), len(cards))
    if a.lead_in == "auto":
        lead_beats = sum(c["beats"] for c in cards[:first_anchor])
        lead_s = math.ceil(lead_beats / 4) * 4 * 60 / bpm if lead_beats else 0.0
    else:
        lead_s = float(a.lead_in)
    # everything below works on the composition timeline: voice time + lead-in
    words = [{**w, "start": w["start"] + lead_s, "end": w["end"] + lead_s} for w in words]
    pauses = [(w0["end"], w1["start"]) for w0, w1 in zip(words[:-1], words[1:]) if w1["start"] - w0["end"] >= PAUSE_S]

    # anchors: card index -> start frame
    anchors = {0: 0.0}
    wi, t_prev = 0, 0.0
    for i, c in enumerate(cards):
        if c.get("onWord"):
            key = norm(c["onWord"])
            hit = next((k for k in range(wi, len(words)) if norm(words[k]["word"]) == key and words[k]["start"] >= t_prev), None)
            if hit is None:
                sys.exit(f"card {i}: word '{c['onWord']}' not found after {t_prev:.2f} s")
            wi = hit + 1
            t_prev = words[hit]["start"]
            anchors[i] = max(0.0, words[hit]["start"] * a.fps + TYPE_LEAD_FRAMES)
        elif c.get("afterPhrase"):
            p = next(((s, e) for s, e in pauses if s >= t_prev), None)
            if p is None:
                sys.exit(f"card {i}: no pause after {t_prev:.2f} s")
            t_prev = p[1]
            anchors[i] = p[0] * a.fps + 0.5 * (p[1] - p[0]) * a.fps  # cut in the middle of the pause
    speech_end = words[-1]["end"] * a.fps if words else 0
    last = len(cards) - 1
    end_f = max(speech_end + 0.5 * a.fps, max(anchors.values()) + (a.tail_beats or cards[last]["beats"]) * beat_f)
    anchors[len(cards)] = end_f

    # distribute un-anchored cards between anchors by their nominal beats
    idx = sorted(anchors)
    starts = [0.0] * (len(cards) + 1)
    for a0, a1 in zip(idx[:-1], idx[1:]):
        span = anchors[a1] - anchors[a0]
        weights = [max(0.25, cards[k]["beats"]) for k in range(a0, a1)]
        tot = sum(weights)
        t = anchors[a0]
        for k, wgt in zip(range(a0, a1), weights):
            starts[k] = t
            t += span * wgt / tot
    starts[len(cards)] = end_f
    out = []
    print(f"{'card':>4} {'start f':>8} {'start s':>7} {'beats':>6}  content")
    for i, c in enumerate(cards):
        b = (starts[i + 1] - starts[i]) / beat_f
        c2 = {k: v for k, v in c.items() if k not in ("onWord", "afterPhrase")}
        c2["beats"] = round(b, 4)
        out.append(c2)
        what = c.get("lines") or c.get("spec", {}).get("value") or ("device" if c.get("device") else "") or ""
        print(f"{i:>4} {starts[i]:8.1f} {starts[i] / a.fps:7.2f} {b:6.2f}  {what} {('<- ' + c['onWord']) if c.get('onWord') else ''}")
    total_beats = sum(c["beats"] for c in out)
    bars = math.ceil(total_beats / 4)
    doc2 = dict(doc)
    doc2["cards"] = out
    doc2["bpm"] = bpm
    doc2["voiceFromFrames"] = round(lead_s * a.fps)
    Path(a.out).write_text(json.dumps(doc2, indent=1, ensure_ascii=False))
    print(f"\n{len(words)} words; voice starts at {lead_s:.2f} s (RecapProps.voiceFrom = {round(lead_s * a.fps)}), speech ends "
          f"{speech_end / a.fps:.2f} s; video {end_f / a.fps:.2f} s = {total_beats:.2f} beats.")
    print(f"Music: synth_audio.py public --bpm {bpm:g} --bars {max(8, bars)}  (the bed's hit then lands on beat {4 * max(8, bars)};"
          f" with a voice-over the hit is optional - set musicFadeOutFrames if the bed runs past the end)")


if __name__ == "__main__":
    main()
