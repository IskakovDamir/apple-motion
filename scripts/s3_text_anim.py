#!/usr/bin/env python3
"""STEP 3: text animation fitting -> data/<slug>/text_anim.json

Per event, from text_measure.json (per-frame scale, dx/dy, opacity, blur, reveal, word/letter mass):
  entry window [appear-2, full+2], exit window [exit_start-2, gone+2]
  - which channels actually animate (range above significance) and their start/end values
  - combined 0->1 progress = mean of significant channels' normalised progress
  - fit (a) Remotion spring (damping, stiffness, mass=1, natural durationInFrames) and
        (a') idiomatic spring({config:{damping}, durationInFrames}) with stiffness 100
        (b) closest cubic-bezier over [appear, full] (+ nearest named easing)
  - entry style: per-letter, per-word pop, slide up with mask, scale down from large, scale up,
    blur in, counter/number roll, swap in place, slide, fade, cut on
Fit error is RMSE in progress units (0..1).
"""
import sys

import numpy as np

import motionfit as mf
from common import DATA, load_json, meta, save_json

SIG = {"scale": 0.04, "dy": 0.004, "dx": 0.004, "opacity": 0.15, "blur_px": 1.5, "reveal": 0.15}


def channel_values(pts, ch):
    return np.array([p[ch] if p[ch] is not None else np.nan for p in pts], np.float64)


def analyse_window(series, a, b, direction, fps, cap_px=None, limit=None):
    """direction +1 entry: progress 0 at appear -> 1 when settled, time = f - appear.
    direction -1 exit:  progress 0 at exit start (settled) -> 1 when gone, time = f - exit_start."""
    sig = dict(SIG)
    if cap_px:
        sig["blur_px"] = max(SIG["blur_px"], 0.04 * cap_px)
    # fit window: the spring tail after the perceptual settle carries most of the shape information
    # (calibration on our own renders: a 12-frame Remotion spring looks settled after ~3-5 frames)
    tail = max(12, 2 * (b - a))
    lo, hi = (a - 3, b + tail) if direction > 0 else (a - tail // 2, b + 3)
    if limit is not None:   # never let the entry window run into the exit (or the exit into the entry)
        hi = min(hi, limit) if direction > 0 else hi
        lo = max(lo, limit) if direction < 0 else lo
    pts = [p for p in series if lo <= p["f"] <= hi]
    if len(pts) < 2:
        return None
    fr = np.array([p["f"] for p in pts], np.float64)
    mass = channel_values(pts, "mass")
    # geometric channels are only trustworthy where some ink is visible
    ok = mass >= 0.15
    settled_i = int(np.argmin(np.abs(fr - (b if direction > 0 else a))))
    moving_i = int(np.argmin(np.abs(fr - (a if direction > 0 else b))))
    chans, progress, prog_by = {}, [], {}
    for ch in ("scale", "dy", "dx", "opacity", "blur_px", "reveal"):
        v = channel_values(pts, ch)
        if ch == "opacity":
            v = np.where(np.isfinite(v), np.clip(v, 0, 1.3), np.clip(mass, 0, 1.3))
        valid = np.isfinite(v) & (ok | (ch == "opacity"))
        if valid.sum() < 2:
            continue
        # settled value = median of the settled side of the window (not the single 'full' frame,
        # which the settle tolerance allows to be a few % off -> fake overshoot in the fit)
        side = (fr >= b) if direction > 0 else (fr <= a)
        sv = v[side & valid]
        v_end = float(np.median(sv)) if len(sv) else (v[settled_i] if valid[settled_i] else v[valid][-1 if direction > 0 else 0])
        # start value: first valid sample on the moving side
        idx = np.where(valid)[0]
        v_start = v[idx[0]] if direction > 0 else v[idx[-1]]
        if ch == "opacity":
            v_start = 0.0 if mass[moving_i] < 0.05 else v_start
        rng = v_end - v_start
        is_sig = abs(rng) >= sig[ch]
        # start/end = moving side / settled side; from/to = chronological order
        entry = {"start": round(float(v_start), 4), "end": round(float(v_end), 4), "animated": bool(is_sig),
                 "from": round(float(v_start if direction > 0 else v_end), 4),
                 "to": round(float(v_end if direction > 0 else v_start), 4)}
        if ch in ("dy", "dx"):
            entry["start_pct_h"] = round(float(v_start) * 100, 2)
        chans[ch] = entry
        if is_sig:
            pr = (v - v_start) / rng
            progress.append(np.where(valid, pr, np.nan))
            prog_by[ch] = np.where(valid, pr, np.nan)
    if not progress:
        # cut on/off: presence is the only signal
        pr = np.clip(mass, 0, 1)
        progress.append(pr if direction > 0 else pr)
    # the spring is fitted to ONE leading channel: geometry is driven linearly by the spring, while
    # opacity usually has its own faster ramp (calibration: averaging channels made springs ~2x too fast).
    # Masked slides: the visible fraction (reveal) is the clean signal.
    primary = None
    # calibration: under a mask the tracked y offset follows the spring exactly (0.49/0.76/0.93 vs
    # 0.49/0.76/0.93 predicted), while the reveal fraction runs ~10% ahead -> prefer geometry
    order = ("dy", "scale", "dx", "reveal", "blur_px", "opacity") if ("reveal" in prog_by and chans["reveal"]["from"] < 0.8) \
        else ("scale", "dy", "dx", "blur_px", "reveal", "opacity")
    for ch in order:
        if ch in prog_by and np.isfinite(prog_by[ch]).sum() >= 3:
            primary = ch
            break
    P = prog_by[primary] if primary else np.nanmean(np.vstack(progress), axis=0)  # 0 moving side, 1 settled
    if direction < 0:
        P = 1 - P                                   # exit: 0 settled -> 1 gone
    fr_rel = fr - a
    good = np.isfinite(P)
    return {"frames_rel": fr_rel[good], "progress": np.clip(P[good], -0.5, 1.8), "channels": chans,
            "frames": fr[good], "primary_channel": primary or "presence"}


def stagger(series, a, b, key):
    """Half-mass frame of each unit (word/letter) inside the entry window."""
    pts = [p for p in series if a - 2 <= p["f"] <= b + 2 and p.get(key)]
    if len(pts) < 2:
        return None
    n = len(pts[0][key])
    if n < 2:
        return None
    halves = []
    for u in range(n):
        vals = [(p["f"], p[key][u]) for p in pts if len(p[key]) == n and p[key][u] is not None]
        t = next((f for f, v in vals if v >= 0.5), None)
        halves.append(t)
    if any(h is None for h in halves):
        return None
    h = np.array(halves, np.float64)
    order = np.arange(n)
    rho = float(np.corrcoef(order, h)[0, 1]) if np.ptp(h) > 0 else 0.0
    d = np.diff(h)
    return {"n_units": n, "half_frames": [int(x) for x in h], "spread_frames": int(np.ptp(h)),
            "median_step_frames": float(np.median(d)) if len(d) else 0.0, "order_corr": round(rho, 3)}


def classify_entry(ev, win, words, letters):
    if ev["entry_frames"] <= 1:
        return "cut on"
    if ev.get("numeric") and len(ev.get("ocr_distinct_texts", [])) >= 3:
        return "counter/number roll"
    if ev.get("replaces_event") is not None and ev["entry_frames"] <= 4:
        return "swap in place"
    # per-letter only when letters of the same word appear at different times; a per-word entry
    # also staggers letters, but in word-sized groups
    if letters and letters["n_units"] >= 4 and letters["spread_frames"] >= 3 and letters["order_corr"] > 0.7:
        distinct = len(set(letters["half_frames"]))
        n_words = words["n_units"] if words else 1
        if distinct > n_words + 1:
            return "per-letter"
    if words and words["n_units"] >= 2 and words["spread_frames"] >= 2 and words["order_corr"] > 0.7:
        return "per-word pop"
    ch = win["channels"] if win else {}
    rev = ch.get("reveal", {})
    dy = ch.get("dy", {})
    sc = ch.get("scale", {})
    bl = ch.get("blur_px", {})
    if rev.get("animated") and rev.get("start", 1) < 0.8 and dy.get("animated"):
        return "slide up with mask" if dy["start"] > dy["end"] else "slide down with mask"
    # the first measurable frame is already ~half-way through a fast spring: 1.03 / 0.97 thresholds
    if sc.get("animated") and sc["start"] > 1.03:
        return "scale down from large"
    if sc.get("animated") and sc["start"] < 0.97:
        return "scale up from small"
    if bl.get("animated") and bl["start"] > 2.0:
        return "blur in"
    if dy.get("animated") or ch.get("dx", {}).get("animated"):
        return "slide"
    if ch.get("opacity", {}).get("animated"):
        return "fade"
    # nothing measurable changed during the 'entry': the text is simply there from its first frame
    # (the settle window was stretched by background noise, e.g. footage moving behind the type)
    return "cut on (no measurable animation)"


def classify_exit(ev, win):
    if ev["exit_kind"] == "cut" or ev["exit_frames"] <= 1:
        return "cut off"
    ch = win["channels"] if win else {}
    if ch.get("scale", {}).get("animated"):
        return "scale out (up)" if ch["scale"]["start"] > ch["scale"]["end"] else "scale out (down)"
    if ch.get("blur_px", {}).get("animated"):
        return "blur out"
    if ch.get("dy", {}).get("animated") or ch.get("dx", {}).get("animated"):
        return "slide out"
    if ch.get("opacity", {}).get("animated"):
        return "fade out"
    return "other"


def fit_window(win, fps, dur):
    fr, p = win["frames_rel"], win["progress"]
    out = {"spring": mf.fit_spring(fr, p, fps),
           "spring_idiomatic": mf.fit_spring_duration(fr, p, fps, max(1, dur))}
    inside = (fr >= 0) & (fr <= max(1, dur))
    if inside.sum() >= 3 and dur >= 2:
        out["bezier"] = mf.fit_bezier(fr[inside] / max(1, dur), p[inside])
    else:
        out["bezier"] = {"bezier": None, "rmse": None, "note": "entry shorter than 2 frames"}
    out["samples"] = [[int(a), round(float(b), 3)] for a, b in zip(fr, p)]
    return out


def run(slug):
    m = meta(slug)
    fps = m["fps"]
    te = load_json(DATA / slug / "text_events.json")
    ms = load_json(DATA / slug / "text_measure.json")
    anims = []
    for ev in te["events"]:
        series = ms[str(ev["id"])]["series"]
        a, full, xs, g = ev["appear_frame"], ev["full_frame"], ev["exit_start_frame"], ev["gone_frame"]
        cap = ev.get("cap_height_px")
        ent = analyse_window(series, a, full, +1, fps, cap, limit=xs)
        ext = analyse_window(series, xs, g, -1, fps, cap, limit=full) if ev["exit_frames"] > 1 else None
        words = stagger(series, a, full, "word_mass")
        letters = stagger(series, a, full, "letter_mass")
        style = classify_entry(ev, ent, words, letters)
        entry_frames = ev["entry_frames"]
        if style.startswith("cut on (no"):
            style, entry_frames = "cut on", 0
        rec = {"id": ev["id"], "text": ev["text"], "role": ev.get("role"),
               "appear_frame": a, "full_frame": full, "exit_start_frame": xs, "gone_frame": g,
               "entry_frames": entry_frames, "entry_frames_measured": ev["entry_frames"], "exit_frames": ev["exit_frames"],
               "entry_style": style,
               "exit_style": classify_exit(ev, ext),
               "word_stagger": words, "letter_stagger": letters}
        if ent is not None and len(ent["progress"]) >= 2:
            rec["entry"] = {"channels": ent["channels"], "primary_channel": ent["primary_channel"], **fit_window(ent, fps, full - a)}
        else:
            rec["entry"] = {"channels": {}, "spring": None, "note": "no samples"}
        if ext is not None and len(ext["progress"]) >= 2:
            rec["exit"] = {"channels": ext["channels"], "primary_channel": ext["primary_channel"], **fit_window(ext, fps, g - xs)}
        else:
            rec["exit"] = {"note": "cut off or no samples", "spring": None}
        if rec["entry"].get("spring") is None:
            # still record a (degenerate) spring for instant entries: step from 0 to 1 at frame 0
            fr = np.array([-1, 0, 1, 2]); p = np.array([0, 1, 1, 1.0])
            rec["entry"]["spring"] = {**mf.fit_spring(fr, p, fps), "degenerate": True}
        if rec["entry_frames"] <= 1:
            rec["entry"]["spring"] = rec["entry"].get("spring") or {}
            rec["entry"]["spring"]["degenerate"] = True
        anims.append(rec)
    save_json(DATA / slug / "text_anim.json", {"slug": slug, "fps": fps, "significance": SIG, "events": anims})
    from collections import Counter
    print(f"[{slug}] {len(anims)} fitted; entry styles {dict(Counter(a['entry_style'] for a in anims))}", flush=True)


if __name__ == "__main__":
    for s in sys.argv[1:]:
        run(s)
