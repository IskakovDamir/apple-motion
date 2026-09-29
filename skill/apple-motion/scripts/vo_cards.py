#!/usr/bin/env python3
"""Time a card script to a voice-over, the way Apple's recaps are cut (the edit follows the voice).

  python vo_cards.py cards.json --voice public/vo.wav [--words words.json] [--bpm 120] [--fps 30] -o cards_timed.json

cards.json: {"bpm": 120, "cards": [...]} - the Card list of Recap.tsx. A card may carry ONE anchor:
  "onWord": "search"        start when this word is spoken (next occurrence after the previous anchor; fuzzy
                            match, so ASR spellings like "Pasquis" still find "Passkeys")
  "afterWord": "password"   start in the pause right after this word
  "afterPhrase": true       start in the next pause after the previous anchor
Cards WITH type (lines / spec / counter / swap / typing) start VO.typeLeadFrames (-2, measured) before
their word; picture-only cards cut in the pause before the word when there is one within 0.5 s.
Cards without an anchor share the time between anchors in proportion to their `beats`.

Word timings: from --words (list of {"word","start","end"} in seconds, voice time) or faster-whisper
(pip install faster-whisper; WHISPER_DIR chooses where the model is stored). Word starts and pauses are
then refined on the voice waveform (ASR boundaries are often 0.1-0.3 s off); --no-refine disables that.

Output: the cards with fractional `beats` (the engine rounds starts from the running total, no drift),
voiceFromFrames and voiceSpanFrames for RecapProps, and a --bpm/--bars suggestion that puts the music
bed's closing hit exactly on the last anchored card (the logo). Import in TSX as
  import data from './cards_timed.json';   cards: data.cards as Card[]
Measured context: Apple's voice starts 0-12.6 s into the video (median ~1.5 s), the picture holds
1.4-8.5 s after the last word (median ~6.7 s), speaking rate ~3 words/s.
"""
import argparse
import array
import difflib
import json
import math
import os
import re
import subprocess
import sys
import wave
from pathlib import Path

TYPE_LEAD_FRAMES = -2   # VO.typeLeadFrames in tokens.ts (median over 45 measured type/word pairs)
PAUSE_S = 0.15
TYPE_KEYS = ("lines", "spec", "counter", "swap", "typing")
BPM_RANGE = (88, 136)   # Apple p10..p90 widened by ~4 BPM


def fail(msg):
    print(f"vo_cards: {msg}", file=sys.stderr, flush=True)
    os._exit(2)  # hard exit: ctranslate2 can abort on interpreter teardown after an error


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def similar(a, b):
    a, b = norm(a), norm(b)
    return a == b or (len(a) > 2 and difflib.SequenceMatcher(None, a, b).ratio() >= 0.72)


def transcribe(path):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        fail("no --words given and faster-whisper is not installed (pip install faster-whisper)")
    model = WhisperModel("small.en", device="cpu", compute_type="int8", download_root=os.environ.get("WHISPER_DIR"))
    segs, _ = model.transcribe(str(path), language="en", word_timestamps=True, vad_filter=True)
    return [{"word": w.word.strip(), "start": w.start, "end": w.end} for s in segs for w in (s.words or [])]


def envelope(path, hop_s=0.01):
    """RMS envelope (dB) of the voice at 10 ms hops (ffmpeg -> 16 kHz mono wav, stdlib only)."""
    tmp = Path(os.environ.get("TMPDIR", "/tmp")) / "vo_cards_env.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-ac", "1", "-ar", "16000", str(tmp)], check=True)
    with wave.open(str(tmp)) as w:
        raw = w.readframes(w.getnframes())
    tmp.unlink(missing_ok=True)
    a = array.array("h", raw)
    hop = int(16000 * hop_s)
    env = []
    for i in range(0, len(a) - hop, hop):
        seg = a[i:i + hop]
        rms = math.sqrt(sum(x * x for x in seg) / len(seg)) / 32768 + 1e-9
        env.append(20 * math.log10(rms))
    return env, hop_s


def refine(words, env, hop_s):
    """Real pauses = energy 35 dB under the peak for >= 0.15 s; word starts snap to the end of a pause."""
    if not env:
        return words, []
    floor = max(env) - 35
    silent = [e < floor for e in env]
    pauses, i = [], 0
    while i < len(silent):
        if silent[i]:
            j = i
            while j < len(silent) and silent[j]:
                j += 1
            if (j - i) * hop_s >= PAUSE_S and i > 0 and j < len(silent):
                pauses.append((i * hop_s, j * hop_s))
            i = j
        else:
            i += 1
    out = []
    for w in words:
        s = w["start"]
        near = [p for p in pauses if abs(p[1] - s) <= 0.3]
        if near:
            s = min(near, key=lambda p: abs(p[1] - s))[1]
        out.append({**w, "start": s})
    return out, pauses


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cards")
    ap.add_argument("--voice")
    ap.add_argument("--words")
    ap.add_argument("--bpm", type=float)
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--tail-frames", type=int, default=45, help="RecapProps.tailFrames (default 45)")
    ap.add_argument("--lead-in", default="auto",
                    help="seconds of picture/music before the voice; 'auto' = nominal beats of the cards before the first "
                         "anchor, rounded up to a whole bar")
    ap.add_argument("--no-refine", action="store_true", help="trust the word timings as given")
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    doc = json.loads(Path(a.cards).read_text())
    cards = doc["cards"]
    bpm = a.bpm or doc.get("bpm", 120)
    beat_f = 60 / bpm * a.fps
    if a.words:
        words = json.loads(Path(a.words).read_text())
    elif a.voice:
        words = transcribe(a.voice)
        Path(a.out).with_suffix(".words.json").write_text(json.dumps(words, indent=1))
    else:
        fail("need --voice or --words")
    pauses = []
    if a.voice and not a.no_refine:
        env, hop = envelope(a.voice)
        words, pauses = refine(words, env, hop)
    if not pauses:
        pauses = [(w0["end"], w1["start"]) for w0, w1 in zip(words[:-1], words[1:]) if w1["start"] - w0["end"] >= PAUSE_S]

    first_anchor = next((i for i, c in enumerate(cards) if c.get("onWord") or c.get("afterWord") or c.get("afterPhrase")), len(cards))
    if a.lead_in == "auto":
        lead_beats = sum(c["beats"] for c in cards[:first_anchor])
        lead_s = math.ceil(lead_beats / 4) * 4 * 60 / bpm if lead_beats else 0.0
    else:
        lead_s = float(a.lead_in)

    def F(t_voice):  # voice time (s) -> composition frame
        return (t_voice + lead_s) * a.fps

    anchors = {0: 0.0}
    wi, t_prev = 0, 0.0
    for i, c in enumerate(cards):
        has_type = any(c.get(k) for k in TYPE_KEYS)
        target = c.get("onWord") or c.get("afterWord")
        if target:
            hit = next((k for k in range(wi, len(words)) if similar(words[k]["word"], target) and words[k]["start"] >= t_prev), None)
            if hit is None:
                heard = " ".join(w["word"] for w in words[wi:wi + 12])
                fail(f"card {i}: word '{target}' not found after {t_prev:.2f} s of the voice (voice time). "
                     f"Heard next: \"{heard}\". Fix the spelling in --words, or anchor to another word.")
            wi = hit + 1
            w = words[hit]
            if c.get("afterWord"):
                p = next((p for p in pauses if p[0] >= w["end"] - 0.05), None)
                t = (p[0] + p[1]) / 2 if p else w["end"]
                anchors[i] = F(t)
                t_prev = t
            else:
                t_prev = w["start"]
                if has_type:
                    anchors[i] = max(0.0, F(w["start"]) + TYPE_LEAD_FRAMES)
                else:
                    p = next((p for p in pauses if 0 <= w["start"] - p[1] <= 0.5), None)
                    anchors[i] = F((p[0] + p[1]) / 2) if p else F(w["start"])
        elif c.get("afterPhrase"):
            p = next(((s, e) for s, e in pauses if s >= t_prev), None)
            if p is None:
                fail(f"card {i}: no pause after {t_prev:.2f} s of the voice")
            t_prev = p[1]
            anchors[i] = F((p[0] + p[1]) / 2)
    speech_start, speech_end = F(words[0]["start"]), F(words[-1]["end"])
    last = len(cards) - 1
    end_f = max(speech_end + 0.5 * a.fps, max(anchors.values()) + cards[last]["beats"] * beat_f)
    anchors[len(cards)] = end_f
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
        c2 = {k: v for k, v in c.items() if k not in ("onWord", "afterWord", "afterPhrase")}
        c2["beats"] = round(b, 4)
        out.append(c2)
        what = c.get("lines") or (c.get("spec") or {}).get("value") or ("device" if c.get("device") else "") or ""
        anc = c.get("onWord") or c.get("afterWord") or ("pause" if c.get("afterPhrase") else "")
        print(f"{i:>4} {starts[i]:8.1f} {starts[i] / a.fps:7.2f} {b:6.2f}  {what} {('<- ' + anc) if anc else ''}")
    total_f = end_f + a.tail_frames
    doc2 = dict(doc, cards=out, bpm=bpm, voiceFromFrames=round(lead_s * a.fps),
                voiceSpanFrames=[round(speech_start), round(speech_end)])

    last_anchor = max((i for i in anchors if 0 < i < len(cards)), default=None)
    sugg = None
    if last_anchor is not None:
        t_hit = starts[last_anchor] / a.fps
        best = None
        for bars in range(8, 64):
            b = bars * 4 * 60 / t_hit
            if BPM_RANGE[0] <= b <= BPM_RANGE[1] and (best is None or abs(b - bpm) < best[0]):
                best = (abs(b - bpm), bars, b)
        if best:
            sugg = (best[2], best[1], t_hit)
    Path(a.out).write_text(json.dumps(doc2, indent=1, ensure_ascii=False))
    print(f"\n{len(words)} words. Voice starts at {lead_s:.2f} s (voiceFrom = {round(lead_s * a.fps)}), speech "
          f"{speech_start / a.fps:.2f}-{speech_end / a.fps:.2f} s (voiceSpan = [{round(speech_start)}, {round(speech_end)}]).")
    print(f"Video: {end_f / a.fps:.2f} s of cards + {a.tail_frames} tail frames = {total_f / a.fps:.2f} s.")
    speech_s = (speech_end - speech_start) / a.fps
    if total_f / a.fps > speech_s + lead_s + 8.5:
        print(f"Note: the voice covers {speech_s:.1f} s of {total_f / a.fps:.1f} s. Apple holds 1.4-8.5 s after the last word "
              f"(median 6.7 s): consider a shorter video or a longer voice-over (~3 words/s).")
    if sugg:
        print(f"Music: synth_audio.py public --bpm {sugg[0]:.2f} --bars {sugg[1]}  -> the bed's closing hit lands at {sugg[2]:.2f} s, "
              f"on card {last_anchor}. Re-run this script with --bpm {sugg[0]:.2f} so beats are counted at that tempo.")
    print(f"Speaking rate {len(words) / max(0.1, speech_s):.2f} words/s (Apple median ~3.0).")


if __name__ == "__main__":
    main()
