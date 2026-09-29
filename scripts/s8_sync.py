#!/usr/bin/env python3
"""STEP 8: picture/sound sync -> data/<slug>/sync.json

For every cut (shot start > 0) and every text appear_frame:
  signed offset in frames to the nearest beat and nearest downbeat (event - beat; negative = early)
  SFX candidates (non-music) and any transient onset within +-2 frames
Shares "on beat" use |offset| <= 2 frames and are reported next to the chance rate: with a beat
period P frames, a random frame lands within +-2 of a beat with probability min(1, 5/P).
Typography-only shares are reported separately from all text events.
"""
import difflib
import re
import sys

import numpy as np

from common import DATA, load_json, meta, read_shots, save_json

WIN = 2


def nearest(f, grid):
    if not len(grid):
        return None
    g = np.asarray(grid)
    i = int(np.argmin(np.abs(g - f)))
    return int(f - g[i])


def run(slug):
    m = meta(slug)
    au = load_json(DATA / slug / "audio.json")
    shots = read_shots(slug)
    te = load_json(DATA / slug / "text_events.json")["events"]
    beats, downs = au["beat_frames"], au["downbeat_frames"]
    sfx = [c for c in au["sfx"]["candidates"]]
    sfx_nm = [c for c in sfx if not c["likely_music"] and not c.get("on_word_onset")]
    period = au["beat_period_frames"]
    bar = au["bar_length_frames"]
    chance_beat = min(1.0, (2 * WIN + 1) / period) if period else None
    chance_down = min(1.0, (2 * WIN + 1) / bar) if bar else None
    t0, t1 = (beats[0], beats[-1]) if beats else (0, 0)

    def item(kind, f, extra):
        ob, od = nearest(f, beats), nearest(f, downs)
        hits = [c for c in sfx_nm if abs(c["frame"] - f) <= WIN]
        anyon = [c for c in sfx if abs(c["frame"] - f) <= WIN]
        return {"kind": kind, "frame": f, **extra, "beat_offset": ob, "downbeat_offset": od,
                "in_music": bool(t0 <= f <= t1),
                "on_beat": ob is not None and abs(ob) <= WIN, "on_downbeat": od is not None and abs(od) <= WIN,
                "sfx": [{"frame": c["frame"], "class": c["class"], "offset": c["frame"] - f} for c in hits],
                "any_onset_within_2": len(anyon) > 0,
                "word_onset_offset": int(f - w_on[np.argmin(np.abs(w_on - f))]) if len(w_on) else None,
                "word_end_offset": int(f - w_off[np.argmin(np.abs(w_off - f))]) if len(w_off) else None}
    words = au.get("voice", {}).get("words", []) if au.get("voice", {}).get("present") else []
    w_on = np.array([w["start_frame"] for w in words]) if words else np.array([])
    w_off = np.array([w["end_frame"] for w in words]) if words else np.array([])
    norm = lambda t: re.sub(r"[^a-z0-9]", "", t.lower())

    def vo_match(text, f):
        """Spoken occurrence of the text's first word nearest to frame f -> (offset appear - word start)."""
        toks = [norm(t) for t in re.split(r"\s+", text) if norm(t)]
        if not toks or not words:
            return None
        best = None
        for w in words:
            r = difflib.SequenceMatcher(None, toks[0], norm(w["w"])).ratio()
            if r >= 0.8 and abs(w["start_frame"] - f) <= 90:
                d = f - w["start_frame"]
                if best is None or abs(d) < abs(best[0]):
                    best = (d, w["w"])
        return {"offset_frames": best[0], "word": best[1]} if best else None

    # VO pauses: gaps >= 0.15 s between consecutive words (breaths / phrase ends)
    pauses = []
    for w0, w1 in zip(words[:-1], words[1:]):
        if (w1["start_frame"] - w0["end_frame"]) / m["fps"] >= 0.15:
            pauses.append((w0["end_frame"], w1["start_frame"]))
    in_pause = lambda f: any(a - WIN <= f <= b + WIN for a, b in pauses)
    speech_span = (words[0]["start_frame"], words[-1]["end_frame"]) if words else (0, 0)
    pause_frames = sum(min(b + WIN, speech_span[1]) - max(a - WIN, speech_span[0]) + 1 for a, b in pauses)
    items = []
    for s in shots[1:]:
        items.append(item("cut", s["start_frame"], {"shot": s["index"], "transition": s["transition"]}))
    for e in te:
        it = item("text_appear", e["appear_frame"], {"event": e["id"], "role": e.get("role"),
                                                     "text": e["text"][:40]})
        it["vo_same_word"] = vo_match(e["text"], e["appear_frame"])
        items.append(it)

    def share(sel, key):
        sel = [i for i in sel if i["in_music"]]
        return round(sum(i[key] for i in sel) / len(sel), 3) if sel else None
    cuts = [i for i in items if i["kind"] == "cut"]
    txt = [i for i in items if i["kind"] == "text_appear"]
    typo = [i for i in txt if i.get("role") == "typography"]
    offs = [i["beat_offset"] for i in cuts if i["in_music"] and i["beat_offset"] is not None]
    summary = {
        "window_frames": WIN, "beat_period_frames": period, "bar_length_frames": bar,
        "chance_on_beat": round(chance_beat, 3) if chance_beat else None,
        "chance_on_downbeat": round(chance_down, 3) if chance_down else None,
        "cuts_on_beat": share(cuts, "on_beat"), "cuts_on_downbeat": share(cuts, "on_downbeat"),
        "text_on_beat": share(txt, "on_beat"), "text_on_downbeat": share(txt, "on_downbeat"),
        "typography_on_beat": share(typo, "on_beat"), "typography_on_downbeat": share(typo, "on_downbeat"),
        "cuts_with_sfx": round(sum(bool(i["sfx"]) for i in cuts) / len(cuts), 3) if cuts else None,
        "cuts_with_any_onset": round(sum(i["any_onset_within_2"] for i in cuts) / len(cuts), 3) if cuts else None,
        "typography_with_sfx": round(sum(bool(i["sfx"]) for i in typo) / len(typo), 3) if typo else None,
        "median_abs_cut_beat_offset": float(np.median(np.abs(offs))) if offs else None,
        "cuts_near_word_onset": round(sum(1 for i in cuts if i["word_onset_offset"] is not None and abs(i["word_onset_offset"]) <= WIN) / len(cuts), 3) if cuts and len(w_on) else None,
        "cuts_near_word_end": round(sum(1 for i in cuts if i["word_end_offset"] is not None and abs(i["word_end_offset"]) <= WIN) / len(cuts), 3) if cuts and len(w_on) else None,
        "chance_near_word_onset": round(min(1.0, (2 * WIN + 1) * len(w_on) / m["nb_frames"]), 3) if len(w_on) else None,
        "typography_vo_offsets": [i["vo_same_word"]["offset_frames"] for i in typo if i.get("vo_same_word")],
        "typography_vo_median_offset": float(np.median([i["vo_same_word"]["offset_frames"] for i in typo if i.get("vo_same_word")]))
            if any(i.get("vo_same_word") for i in typo) else None,
        "cuts_in_vo_pause": (round(sum(1 for i in cuts if speech_span[0] <= i["frame"] <= speech_span[1] and in_pause(i["frame"]))
                                   / max(1, sum(1 for i in cuts if speech_span[0] <= i["frame"] <= speech_span[1])), 3) if pauses else None),
        "chance_in_vo_pause": round(pause_frames / max(1, speech_span[1] - speech_span[0]), 3) if pauses else None,
        "n_vo_pauses": len(pauses),
        "cut_beat_offset_hist": {str(k): int(sum(1 for o in offs if o == k)) for k in range(-7, 8)},
    }
    # one-sided binomial tests against the chance rate (is the alignment more than coincidence?)
    from scipy.stats import binomtest
    def ptest(sel, key, chance):
        sel = [i for i in sel if i["in_music"]]
        k = sum(bool(i[key]) for i in sel)
        return round(float(binomtest(k, len(sel), chance, alternative="greater").pvalue), 4) if sel and chance else None
    summary["p_cuts_on_beat"] = ptest(cuts, "on_beat", chance_beat)
    summary["p_cuts_on_downbeat"] = ptest(cuts, "on_downbeat", chance_down)
    summary["p_typography_on_beat"] = ptest(typo, "on_beat", chance_beat)
    save_json(DATA / slug / "sync.json", {"slug": slug, "summary": summary, "items": items})
    print(f"[{slug}] cuts on beat {summary['cuts_on_beat']} (chance {summary['chance_on_beat']}), "
          f"typo on beat {summary['typography_on_beat']}", flush=True)


if __name__ == "__main__":
    for s in sys.argv[1:]:
        run(s)
