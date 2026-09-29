#!/usr/bin/env python3
"""Re-derive event timing (appear / full / exit_start / gone and everything that depends on it) from
the per-frame measurements already in text_measure.json, without re-measuring pixels.
Use after changing timing() or settle_distance() in s2b_text_events.py. Labels are kept."""
import sys

import numpy as np

import s2b_text_events as S
from common import DATA, load_json, meta, read_shots, save_json


def run(slug):
    m = meta(slug)
    fps = m["fps"]
    shots = read_shots(slug)
    te = load_json(DATA / slug / "text_events.json")
    ms = load_json(DATA / slug / "text_measure.json")
    frames_ocr, _ = S.load_ocr(slug, m["height"])
    changed = 0
    for e in te["events"]:
        series = ms[str(e["id"])]["series"]
        for x in series:  # json nulls -> nan so the numpy maths behaves like in s2b
            for k in ("scale", "dx", "dy", "opacity", "blur_px", "reveal", "mass", "ncc"):
                if x.get(k) is None:
                    x[k] = np.nan
        b = e["bbox_ref"]
        p = {"first": e["ocr_first_frame"], "last": e["ocr_last_frame"],
             "shot_first": e["shot_index"], "shot_last": e["shot_index_last"],
             "box": [b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"]],
             "lo": min(x["f"] for x in series), "hi": max(x["f"] for x in series)}
        p["foreign"] = S.foreign_frames(p, frames_ocr, " ".join(e["lines"]))
        a, f, xs, g, ak, ek = S.timing(series, e["ref_frame"], shots, p, e["cap_height_px"])
        if (a, f, xs, g) != (e["appear_frame"], e["full_frame"], e["exit_start_frame"], e["gone_frame"]):
            changed += 1
        e.update({"appear_frame": a, "full_frame": f, "exit_start_frame": xs, "gone_frame": g,
                  "entry_frames": f - a, "hold_frames": xs - f, "exit_frames": g - xs,
                  "appear_kind": ak, "exit_kind": ek, "hold_drift": S.drift(series, f, xs, fps)})
        bb, last = [], None
        for x in series:
            if x.get("bbox") and a <= x["f"] < g and (last is None or max(abs(u - v) for u, v in zip(x["bbox"], last)) > 1):
                bb.append([x["f"]] + x["bbox"])
                last = x["bbox"]
        e["bbox_over_time"] = bb
    te["retimed"] = True
    save_json(DATA / slug / "text_events.json", te)
    print(f"[{slug}] retimed {changed}/{len(te['events'])} events", flush=True)


if __name__ == "__main__":
    for s in sys.argv[1:]:
        run(s)
