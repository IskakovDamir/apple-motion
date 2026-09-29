#!/usr/bin/env python3
"""STEP 7: audio forensics -> data/<slug>/audio.json + audio/spectrogram.png

mix.wav (ffmpeg) -> demucs htdemucs stems (drums, bass, other, vocals).
music = drums+bass+other: BPM, beat + downbeat frames, bar length, energy curve, sections.
SFX candidates = transients in the non-vocal stems that the music grid does not explain
(off the 1/8-note grid, or noise-like), plus the demucs reconstruction residual.
Voice: faster-whisper word timestamps on the vocals stem (run in s7b_asr.py, separate
process: PyAV and OpenCV ship clashing libavdevice builds).
Loudness: ffmpeg ebur128 integrated LUFS, LRA, true peak.
No OpenCV import here on purpose.
"""
import csv
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(os.environ["PROJECT_ROOT"])
DATA = ROOT / "data"
SR = 22050


def meta(slug):
    return json.loads((DATA / slug / "meta.json").read_text())


def cuts(slug):
    with open(DATA / slug / "shots.csv") as fh:
        return [int(r["start_frame"]) for r in csv.DictReader(fh)][1:]


def sh(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def extract(slug, ad):
    mix = ad / "mix.wav"
    if not mix.exists():
        sh(["ffmpeg", "-y", "-v", "error", "-i", str(DATA / "_src" / f"{slug}.mp4"), "-vn", "-ac", "2",
            "-ar", "44100", "-c:a", "pcm_s16le", str(mix)])
    stems = ad / "stems"
    if not (stems / "vocals.wav").exists():
        subprocess.run([sys.executable, "-m", "demucs", "-n", "htdemucs", "-d", "cpu", "-j", "4",
                        "-o", str(ad / "_demucs"), "--filename", "{stem}.{ext}", str(mix)], check=True)
        stems.mkdir(exist_ok=True)
        for p in (ad / "_demucs" / "htdemucs").glob("[!.]*.wav"):
            p.rename(stems / p.name)
    return mix, stems


def loudness(mix):
    r = subprocess.run(["ffmpeg", "-nostats", "-i", str(mix), "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    txt = r.stderr[r.stderr.rfind("Summary:"):]
    g = lambda pat: float(re.search(pat, txt).group(1))
    return {"integrated_lufs": g(r"I:\s+(-?[\d.]+) LUFS"), "lra_lu": g(r"LRA:\s+(-?[\d.]+) LU"),
            "true_peak_dbtp": g(r"Peak:\s+(-?[\d.inf]+) dBFS")}


def load(p):
    y, sr = sf.read(str(p), always_2d=True)
    y = y.mean(1)
    return librosa.resample(y, orig_sr=sr, target_sr=SR) if sr != SR else y


def to_frame(t, fps):
    return int(round(t * fps))


def downbeat_phase(beats_t, low_env, chroma_nov, times):
    """Pick the beat phase (4/4) whose beats carry the most low-end onset + harmonic change."""
    if len(beats_t) < 8:
        return 0, 0.0
    idx = np.clip(np.searchsorted(times, beats_t), 0, len(times) - 1)
    lo = low_env[idx]
    hn = chroma_nov[idx]
    lo = lo / (lo.max() + 1e-9)
    hn = hn / (hn.max() + 1e-9)
    s = lo + hn
    scores = [float(s[p::4].mean()) for p in range(4)]
    order = np.argsort(scores)[::-1]
    conf = (scores[order[0]] - scores[order[1]]) / (scores[order[0]] + 1e-9)
    return int(order[0]), round(float(conf), 3)


def sections(music, fps, n_frames):
    hop = 512
    chroma = librosa.feature.chroma_cqt(y=music, sr=SR, hop_length=hop)
    mfcc = librosa.feature.mfcc(y=music, sr=SR, hop_length=hop, n_mfcc=13)
    rms = librosa.feature.rms(y=music, hop_length=hop)
    feat = np.vstack([librosa.util.normalize(chroma, axis=1), librosa.util.normalize(mfcc, axis=1),
                      librosa.util.normalize(rms, axis=1)])
    # smooth over ~2 s so sections are musical, not per-note
    w = int(2 * SR / hop)
    feat = np.apply_along_axis(lambda r: np.convolve(r, np.ones(w) / w, mode="same"), 1, feat)
    dur = len(music) / SR
    k = int(np.clip(round(dur / 25), 3, 10))
    bounds = librosa.segment.agglomerative(feat, k)
    bt = librosa.frames_to_time(bounds, sr=SR, hop_length=hop)
    bt = sorted(set([0.0] + [float(t) for t in bt if t > 0.5]))
    rms_full = librosa.feature.rms(y=music, hop_length=hop)[0]
    tt = librosa.frames_to_time(np.arange(len(rms_full)), sr=SR, hop_length=hop)
    out = []
    for i, t0 in enumerate(bt):
        t1 = bt[i + 1] if i + 1 < len(bt) else dur
        m = (tt >= t0) & (tt < t1)
        e = float(20 * np.log10(rms_full[m].mean() + 1e-9)) if m.any() else -90.0
        out.append({"start_frame": to_frame(t0, fps), "end_frame": min(n_frames - 1, to_frame(t1, fps) - 1),
                    "start_s": round(t0, 2), "end_s": round(t1, 2), "rms_db": round(e, 1)})
    es = [s["rms_db"] for s in out]
    lo, hi = np.percentile(es, 33), np.percentile(es, 66)
    for s in out:
        s["energy"] = "low" if s["rms_db"] <= lo else ("high" if s["rms_db"] > hi else "mid")
    return out


def sfx(stems, beats_t, bpm, fps):
    """Transient candidates the music grid does not explain."""
    drums, other, bass, vocals = stems["drums"], stems["other"], stems["bass"], stems["vocals"]
    nonvocal = drums + other + bass
    hop = 256
    env = librosa.onset.onset_strength(y=nonvocal, sr=SR, hop_length=hop)
    # onset_detect normalises the envelope to max 1, so delta is in normalised units
    ons = librosa.onset.onset_detect(onset_envelope=env, sr=SR, hop_length=hop, backtrack=False,
                                     delta=0.08, wait=int(0.08 * SR / hop))
    if len(ons) == 0:
        return []
    thr = np.percentile(env[ons], 50)
    ons = [o for o in ons if env[o] >= thr]
    # 1/8-note grid from beats
    grid = []
    for a, b in zip(beats_t[:-1], beats_t[1:]):
        grid += [a, (a + b) / 2]
    grid = np.array(grid + list(beats_t[-1:])) if len(beats_t) else np.array([])
    S = np.abs(librosa.stft(nonvocal, n_fft=1024, hop_length=hop))
    freqs = librosa.fft_frequencies(sr=SR, n_fft=1024)
    cent = librosa.feature.spectral_centroid(S=S, sr=SR)[0]
    flat = librosa.feature.spectral_flatness(S=S)[0]
    rms = librosa.feature.rms(S=S, frame_length=1024)[0]
    rms_db = 20 * np.log10(rms + 1e-9)
    out = []
    for o in ons:
        t = librosa.frames_to_time(o, sr=SR, hop_length=hop)
        off_grid_ms = float(np.min(np.abs(grid - t)) * 1000) if len(grid) else 999.0
        # pre-roll: how long energy has been rising into the onset (whoosh/riser signature)
        k = o
        while k > 0 and rms_db[k - 1] < rms_db[k] - 0.2 and (o - k) * hop / SR < 1.5:
            k -= 1
        pre_ms = (o - k) * hop / SR * 1000
        # decay: time until -20 dB from peak
        pk = o + int(np.argmax(rms_db[o:o + 20])) if o + 1 < len(rms_db) else o
        j = pk
        while j < len(rms_db) - 1 and rms_db[j] > rms_db[pk] - 20 and (j - pk) * hop / SR < 2.0:
            j += 1
        decay_ms = (j - pk) * hop / SR * 1000
        c = float(np.median(cent[max(0, o - 2):o + 6]))
        fl = float(np.median(flat[max(0, o - 2):o + 6]))
        low_share = float(S[freqs < 200, o:o + 6].sum() / (S[:, o:o + 6].sum() + 1e-9))
        if pre_ms >= 150 and fl > 0.05:
            cls = "whoosh/riser"
        elif decay_ms < 80 and c > 2500:
            cls = "click/tick"
        elif low_share > 0.45 and decay_ms > 150:
            cls = "hit/boom"
        elif fl > 0.2:
            cls = "noise burst"
        else:
            cls = "tonal hit"
        musical = off_grid_ms <= 45 and fl < 0.2 and cls in ("tonal hit", "hit/boom")
        out.append({"t": round(float(t), 3), "frame": to_frame(t, fps), "class": cls,
                    "off_grid_ms": round(off_grid_ms, 1), "pre_roll_ms": round(pre_ms), "decay_ms": round(decay_ms),
                    "centroid_hz": round(c), "flatness": round(fl, 3), "low_share": round(low_share, 2),
                    "strength": round(float(env[o]), 2), "likely_music": bool(musical)})
    return out


MAGMA = np.array([[0, 0, 4], [28, 16, 68], [79, 18, 123], [129, 37, 129], [181, 54, 122],
                  [229, 80, 100], [251, 135, 97], [254, 194, 135], [252, 253, 191]], np.float32)


def colormap(x):
    x = np.clip(x, 0, 1) * (len(MAGMA) - 1)
    i = np.floor(x).astype(int).clip(0, len(MAGMA) - 2)
    f = (x - i)[..., None]
    return (MAGMA[i] * (1 - f) + MAGMA[i + 1] * f).astype(np.uint8)


def spectrogram_png(mix, fps, n_frames, cut_frames, beats_f, downbeats_f, secs, sfx_list, out):
    hop = 512
    M = librosa.feature.melspectrogram(y=mix, sr=SR, n_fft=2048, hop_length=hop, n_mels=160, fmax=11000)
    D = librosa.power_to_db(M, ref=np.max, top_db=80)
    img = colormap((D + 80) / 80)[::-1]
    W, H = 2400, 420
    im = Image.fromarray(img).resize((W, H - 60), Image.BILINEAR)
    canvas = Image.new("RGB", (W, H), (0, 0, 0))
    canvas.paste(im, (0, 0))
    d = ImageDraw.Draw(canvas)
    x = lambda f: int(f / n_frames * W)
    for f in cut_frames:
        d.line([(x(f), 0), (x(f), H - 60)], fill=(255, 255, 255), width=1)
    for f in beats_f:
        d.line([(x(f), H - 58), (x(f), H - 48)], fill=(120, 200, 255), width=1)
    for f in downbeats_f:
        d.line([(x(f), H - 58), (x(f), H - 40)], fill=(0, 255, 160), width=2)
    for s in sfx_list:
        if not s["likely_music"] and not s.get("on_word_onset"):
            d.ellipse([x(s["frame"]) - 3, H - 34, x(s["frame"]) + 3, H - 28], fill=(255, 90, 60))
    for s in secs:
        d.line([(x(s["start_frame"]), H - 24), (x(s["start_frame"]), H)], fill=(255, 220, 0), width=2)
        d.text((x(s["start_frame"]) + 3, H - 22), s["energy"], fill=(255, 220, 0))
    for sec in range(0, int(n_frames / fps) + 1, 10):
        d.text((x(sec * fps) + 2, H - 12), f"{sec}s", fill=(160, 160, 160))
    d.text((6, 4), "white=cuts  blue=beats  green=downbeats  red=SFX candidates  yellow=sections",
           fill=(255, 255, 255))
    canvas.save(out)


def run(slug):
    m = meta(slug)
    fps, n_frames = m["fps"], m["nb_frames"]
    ad = DATA / slug / "audio"
    ad.mkdir(exist_ok=True)
    mix_p, stem_dir = extract(slug, ad)
    mix = load(mix_p)
    st = {k: load(stem_dir / f"{k}.wav") for k in ("drums", "bass", "other", "vocals")}
    L = min(len(mix), *(len(v) for v in st.values()))
    mix = mix[:L]
    st = {k: v[:L] for k, v in st.items()}
    music = st["drums"] + st["bass"] + st["other"]
    residual = mix - (music + st["vocals"])

    e = lambda y: float(np.sqrt(np.mean(y ** 2)) + 1e-12)
    stem_share = {k: round(e(v) / e(mix), 3) for k, v in st.items()}
    stem_share["residual"] = round(e(residual) / e(mix), 4)

    # beats on the music stem; drums-weighted onset envelope when drums carry the groove
    # hop 128 (5.8 ms): librosa's tempo estimate is quantised to 60*sr/(hop*lag); at hop 512 the
    # neighbouring bins around 120 BPM are 117.45 and 123.05 (measured on our own 120 BPM render).
    # BPM is therefore taken from a line fit of beat time vs beat index, not from the tempo bin.
    hop = 128
    perc_src = st["drums"] + 0.5 * st["bass"] if stem_share["drums"] > 0.15 else music
    oenv = librosa.onset.onset_strength(y=perc_src, sr=SR, hop_length=hop)
    tempo, beats = librosa.beat.beat_track(onset_envelope=oenv, sr=SR, hop_length=hop, start_bpm=110, tightness=100)
    beats_t = librosa.frames_to_time(beats, sr=SR, hop_length=hop)
    bpm_bin = float(np.atleast_1d(tempo)[0])
    if len(beats_t) >= 8:
        ibi = np.diff(beats_t)
        med = np.median(ibi)
        keep = np.abs(ibi - med) < 0.15 * med
        idx = np.concatenate([[0], np.cumsum(np.round(ibi / med))]).astype(int)
        slope = np.polyfit(idx, beats_t, 1)[0] if keep.sum() >= 6 else med
        bpm = float(60 / slope)
    else:
        bpm = bpm_bin
    hop = 512
    # low-end onset env + harmonic novelty for downbeats
    low = librosa.onset.onset_strength(y=st["bass"] + st["drums"], sr=SR, hop_length=hop, fmax=200, n_mels=32)
    chroma = librosa.feature.chroma_cqt(y=music, sr=SR, hop_length=hop)
    cn = np.concatenate([[0], np.linalg.norm(np.diff(chroma, axis=1), axis=0)])
    times = librosa.frames_to_time(np.arange(len(low)), sr=SR, hop_length=hop)
    phase, dconf = downbeat_phase(beats_t, low, cn[:len(low)], times)
    down_t = beats_t[phase::4]
    ibi = np.diff(beats_t)
    beat_period_s = float(np.median(ibi)) if len(ibi) else 60 / max(bpm, 1)

    # energy curve per video frame (music and mix), dBFS
    fh = SR / fps
    nfr = int(L / fh)
    def per_frame_db(y):
        r = np.array([np.sqrt(np.mean(y[int(i * fh):int((i + 1) * fh)] ** 2) + 1e-12) for i in range(nfr)])
        return np.round(20 * np.log10(r), 1)
    energy_music = per_frame_db(music)
    energy_mix = per_frame_db(mix)
    secs = sections(music, fps, n_frames)
    sfx_list = sfx(st, beats_t, bpm, fps)

    # voice
    voc_frames = per_frame_db(st["vocals"])
    voiced = float((voc_frames > (energy_mix - 12)).mean())
    asr_path = DATA / slug / "audio" / "asr.json"
    voice = {"vocals_stem_share": stem_share["vocals"], "voiced_frame_share": round(voiced, 3),
             "present": bool(stem_share["vocals"] > 0.12 and voiced > 0.1)}
    if voice["present"]:
        if not asr_path.exists():
            subprocess.run([sys.executable, str(ROOT / "scripts" / "s7b_asr.py"), slug], check=True)
        asr = json.loads(asr_path.read_text())
        words = asr["words"]
        speech_s = sum(s["end"] - s["start"] for s in asr["segments"])
        voice.update({"words": [{"w": w["word"].strip(), "start_frame": to_frame(w["start"], fps),
                                 "end_frame": to_frame(w["end"], fps), "p": round(w["probability"], 2)} for w in words],
                      "n_words": len(words), "speech_seconds": round(speech_s, 2),
                      "words_per_second_speaking": round(len(words) / speech_s, 2) if speech_s else None,
                      "words_per_second_overall": round(len(words) / (L / SR), 2),
                      "transcript": asr["text"], "language_prob": asr.get("language_probability"),
                      "note": "vocals stem may contain sung lyrics; check transcript"})

    # flag SFX candidates that coincide with a spoken word onset (likely voice bleed into other stems)
    word_on = np.array([w["start_frame"] for w in voice.get("words", [])])
    for c in sfx_list:
        c["on_word_onset"] = bool(len(word_on) and np.min(np.abs(word_on - c["frame"])) <= 2)
    loud = loudness(mix_p)
    cf = cuts(slug)
    beats_f = [to_frame(t, fps) for t in beats_t]
    down_f = [to_frame(t, fps) for t in down_t]
    spectrogram_png(mix, fps, n_frames, cf, beats_f, down_f, secs, sfx_list, ad / "spectrogram.png")
    out = {
        "fps": fps, "duration_s": round(L / SR, 3), "sr_analysis": SR,
        "stem_rms_share": stem_share,
        "bpm": round(bpm, 2), "bpm_librosa_bin": round(bpm_bin, 2), "beat_period_frames": round(60 / bpm * fps, 3),
        "beat_frames": beats_f, "beat_times_s": [round(float(t), 3) for t in beats_t],
        "downbeat_frames": down_f, "downbeat_phase": phase, "downbeat_confidence": dconf,
        "meter_assumed": "4/4", "bar_length_frames": round(4 * 60 / bpm * fps, 3),
        "energy_db_per_frame": {"music": energy_music.tolist(), "mix": energy_mix.tolist()},
        "sections": secs,
        "sfx": {"method": "onsets in drums+bass+other stems; class from pre-roll/decay/centroid/flatness; "
                          "likely_music = on 1/8 grid (<=45 ms) and tonal",
                "candidates": sfx_list,
                "n_non_music": sum(1 for s in sfx_list if not s["likely_music"] and not s["on_word_onset"])},
        "voice": voice,
        "loudness": loud,
        "files": {"mix": str(mix_p), "stems": str(stem_dir), "spectrogram": str(ad / "spectrogram.png")},
    }
    (DATA / slug / "audio.json").write_text(json.dumps(out, indent=1))
    print(f"[{slug}] bpm {bpm:.1f} beats {len(beats_f)} downbeat phase {phase} (conf {dconf}) "
          f"sections {len(secs)} sfx {out['sfx']['n_non_music']}/{len(sfx_list)} voice {voice['present']} "
          f"LUFS {loud['integrated_lufs']} TP {loud['true_peak_dbtp']}", flush=True)


if __name__ == "__main__":
    for s in sys.argv[1:] or sorted(p.parent.name for p in DATA.glob("*/meta.json")):
        run(s)
