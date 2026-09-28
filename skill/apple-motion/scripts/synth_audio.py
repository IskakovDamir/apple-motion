#!/usr/bin/env python3
"""Generate a royalty-free (CC0, synthesized from scratch) upbeat music bed + SFX kit.

  music.wav   BPM-locked electronic bed (four-on-the-floor kick, clap 2&4, 8th hats, pulsing bass,
              supersaw chords, pluck arpeggio) with an intro, build, drop, break and final hit
  sfx/whoosh.wav, sfx/swish.wav, sfx/click.wav, sfx/hit.wav, sfx/riser.wav

Usage: synth_audio.py OUT_DIR [--bpm 120] [--bars 16] [--seed 7]
Loudness: normalise the result with ffmpeg loudnorm to the measured Apple target
(see references/audio.md), e.g. -16 LUFS integrated, -1.5 dBTP.
Only numpy + stdlib wave are needed.
"""
import argparse
import wave
from pathlib import Path

import numpy as np

SR = 48000


def write_wav(path, x):
    x = np.asarray(x, np.float64)
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    peak = np.abs(x).max()
    if peak > 0.98:
        x = x / peak * 0.98
    data = (x * 32767).astype("<i2")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


def env_exp(n, decay_s):
    t = np.arange(n) / SR
    return np.exp(-t / decay_s)


def onepole_lp(x, fc):
    a = np.exp(-2 * np.pi * np.asarray(fc) / SR)
    y = np.zeros_like(x)
    acc = 0.0
    a = np.broadcast_to(a, x.shape)
    for i in range(len(x)):
        acc = (1 - a[i]) * x[i] + a[i] * acc
        y[i] = acc
    return y


def hp(x, fc):
    return x - onepole_lp(x, fc)


def saw(freq, n, phase=0.0):
    t = np.arange(n) / SR
    return 2 * ((t * freq + phase) % 1.0) - 1


def kick(n=int(0.35 * SR)):
    t = np.arange(n) / SR
    f = 45 + 95 * np.exp(-t / 0.035)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * env_exp(n, 0.16)
    click = np.random.randn(n) * env_exp(n, 0.004) * 0.3
    return (body + click) * 0.95


def clap(rng, n=int(0.25 * SR)):
    x = np.zeros(n)
    for k, off in enumerate((0, 0.011, 0.022)):
        i = int(off * SR)
        m = int(0.009 * SR)
        x[i:i + m] += rng.standard_normal(m) * (0.7 - 0.15 * k)
    tail = rng.standard_normal(n) * env_exp(n, 0.07) * 0.5
    x += tail
    x = hp(x, 900) - hp(x, 5000) * 0.5
    return x * 0.45


def hat(rng, open_=False):
    n = int((0.16 if open_ else 0.04) * SR)
    x = hp(rng.standard_normal(n), 7000) * env_exp(n, 0.05 if open_ else 0.012)
    return x * (0.22 if open_ else 0.16)


def pluck(freq, n=int(0.22 * SR)):
    t = np.arange(n) / SR
    x = np.sign(np.sin(2 * np.pi * freq * t)) * 0.5 + np.sin(2 * np.pi * 2 * freq * t) * 0.3
    return onepole_lp(x * env_exp(n, 0.07), 3500) * 0.22


def supersaw(freq, n):
    x = sum(saw(freq * d, n, phase=i * 0.17) for i, d in enumerate((0.991, 0.996, 1.0, 1.004, 1.009)))
    return x / 5


NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def hz(name, octave):
    return 440.0 * 2 ** ((NOTE[name] + 12 * (octave + 1) - 69) / 12)


def music(bpm=120, bars=16, seed=7):
    rng = np.random.default_rng(seed)
    beat = 60 / bpm
    total = int((bars * 4 * beat + 2.5) * SR)
    L = np.zeros(total)
    R = np.zeros(total)
    drums = np.zeros(total)
    kick_times = []
    prog = [("C", ["C", "E", "G"]), ("G", ["G", "B", "D"]), ("A", ["A", "C", "E"]), ("F", ["F", "A", "C"])]

    def add(buf, x, t, gain=1.0):
        i = int(t * SR)
        j = min(len(buf), i + len(x))
        if i < len(buf):
            buf[i:j] += x[: j - i] * gain

    # sections (bars): intro 0-1, build 2-3, main 4-11, break 12-13, final 14-15
    for bar in range(bars):
        t0 = bar * 4 * beat
        root, chord = prog[(bar // 2) % 4] if bar >= 2 else prog[0]
        intro, build, brk = bar < 2, 2 <= bar < 4, 12 <= bar < 14
        for b in range(4):
            tb = t0 + b * beat
            if not intro and not brk:
                add(drums, kick(), tb)
                kick_times.append(tb)
            if not intro and not brk and b in (1, 3):
                add(drums, clap(rng), tb)
            for h in range(2):
                if not (intro and h == 0):
                    add(drums, hat(rng, open_=(h == 1 and not intro)), tb + h * beat / 2)
        # chords: one stab every beat in main, sustained pad elsewhere
        n_bar = int(4 * beat * SR)
        pad = sum(supersaw(hz(nm, 4), n_bar) for nm in chord) / 3
        cut = 900 if (intro or brk) else 2400
        pad = onepole_lp(pad, np.linspace(cut * 0.6, cut, n_bar)) * (0.16 if (intro or brk) else 0.12)
        add(L, pad * 0.9, t0)
        add(R, pad * 1.0, t0)
        if not intro:
            # bass: 8th-note pulse on the chord root
            for e in range(8):
                n = int(beat / 2 * SR * 0.9)
                x = onepole_lp(saw(hz(root, 2), n), 500) * env_exp(n, 0.18) * 0.35
                add(L, x, t0 + e * beat / 2)
                add(R, x, t0 + e * beat / 2)
        if not (intro or build or brk):
            arp = chord + [chord[0]]
            for s in range(16):
                nm = arp[s % 4]
                x = pluck(hz(nm, 5 + (s // 8) % 2))
                pan = 0.35 if s % 2 else -0.35
                add(L, x * (1 - pan), t0 + s * beat / 4)
                add(R, x * (1 + pan), t0 + s * beat / 4)
    # riser into the final section and a closing hit
    riser_t = 12 * 4 * beat
    rn = int(8 * beat * SR)
    rsig = sfx_riser(rn, rng) * 0.5
    add(L, rsig, riser_t)
    add(R, rsig, riser_t)
    end_t = bars * 4 * beat
    h = sfx_hit(rng) * 0.9
    add(L, h, end_t)
    add(R, h, end_t)
    # sidechain ducking from the kick
    duck = np.ones(total)
    for kt in kick_times:
        i = int(kt * SR)
        n = int(0.22 * SR)
        j = min(total, i + n)
        duck[i:j] = np.minimum(duck[i:j], 1 - 0.55 * env_exp(n, 0.07)[: j - i])
    L = L * duck + drums
    R = R * duck + drums
    x = np.stack([L, R], 1)
    x = np.tanh(x * 1.4) / np.tanh(1.4)
    fade = int(1.5 * SR)
    x[-fade:] *= np.linspace(1, 0, fade)[:, None]
    return x


def sfx_riser(n, rng):
    t = np.arange(n) / SR
    f = 200 * (10 ** (t / t[-1]))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.3
    noise = hp(rng.standard_normal(n), 2000) * 0.4
    return (tone + noise) * (t / t[-1]) ** 2


def sfx_whoosh(rng, dur=0.45, peak=0.55):
    n = int(dur * SR)
    t = np.arange(n) / SR
    envl = np.where(t < peak * dur, (t / (peak * dur)) ** 2, np.exp(-(t - peak * dur) / (0.25 * dur)))
    fc = 300 + 2700 * np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    x = onepole_lp(rng.standard_normal(n), fc)
    x = hp(x, 150) * envl
    pan = np.linspace(-0.7, 0.7, n)
    return np.stack([x * (1 - pan), x * (1 + pan)], 1) * 0.8


def sfx_click():
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * 2600 * t) * env_exp(n, 0.006) * 0.6


def sfx_hit(rng):
    n = int(1.6 * SR)
    t = np.arange(n) / SR
    f = 40 + 80 * np.exp(-t / 0.05)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 0.45)
    crack = hp(rng.standard_normal(n), 1500) * env_exp(n, 0.03) * 0.5
    tail = onepole_lp(rng.standard_normal(n), 2500) * env_exp(n, 0.5) * 0.15
    return sub * 0.9 + crack + tail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--bpm", type=float, default=120)
    ap.add_argument("--bars", type=int, default=16)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    out = Path(a.out)
    rng = np.random.default_rng(a.seed)
    write_wav(out / "music_raw.wav", music(a.bpm, a.bars, a.seed))
    write_wav(out / "sfx" / "whoosh.wav", sfx_whoosh(rng, 0.45))
    write_wav(out / "sfx" / "swish.wav", sfx_whoosh(rng, 0.22, 0.6) * 0.6)
    write_wav(out / "sfx" / "click.wav", sfx_click())
    write_wav(out / "sfx" / "hit.wav", sfx_hit(rng))
    write_wav(out / "sfx" / "riser.wav", sfx_riser(int(2 * SR), rng))
    print(f"wrote {out}/music_raw.wav and sfx/*.wav ({a.bpm} BPM, {a.bars} bars)")


if __name__ == "__main__":
    main()
