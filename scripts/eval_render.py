#!/usr/bin/env python3
"""Measure a rendered video with the SAME pipeline used on the Apple videos and score it against
the Apple fingerprint. This is the training loop for the skill: render -> measure -> compare ->
adjust tokens/templates -> render again.

  python eval_render.py demo/out/recap.mp4 --name demo-v1 [--truth demo/out/recap.truth.json]

- ingests the render as data/render-<name>/ (all text in our renders is designer typography,
  so every event is labelled 'typography' automatically)
- runs steps 1, 2a, 2b, 3, 4, 5, 7, 8, 9
- writes reports/eval/<name>.md: every metric next to Apple's pooled p10/p50/p90 and whether it
  falls inside; with --truth also measured vs. ground-truth timing/springs (pipeline calibration)
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

from common import DATA, ROOT, load_json

PY = sys.executable
STEPS = ["s1_shots", "s2a_ocr", "s2b_text_events", "s3_text_anim", "s4_motion", "s7_audio", "s5_color_layout",
         "s8_sync", "s9_summary"]


def sh(args, log):
    with open(log, "a") as fh:
        r = subprocess.run(args, cwd=ROOT / "scripts", stdout=fh, stderr=subprocess.STDOUT)
    if r.returncode:
        raise SystemExit(f"{args} failed, see {log}")


def ingest(video, slug):
    src = DATA / "_src" / f"{slug}.mp4"
    shutil.copyfile(video, src)
    d = DATA / slug
    d.mkdir(parents=True, exist_ok=True)
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format",
                                    str(src)], capture_output=True, text=True, check=True).stdout)
    v = next(s for s in pr["streams"] if s["codec_type"] == "video")
    a = next((s for s in pr["streams"] if s["codec_type"] == "audio"), None)
    num, den = map(int, v["r_frame_rate"].split("/"))
    meta = {"slug": slug, "source": str(video), "via": "render", "title": slug, "width": v["width"], "height": v["height"],
            "vcodec": v["codec_name"], "fps": num / den, "fps_rational": v["r_frame_rate"],
            "nb_frames": int(v.get("nb_frames", 0)), "duration_s": float(pr["format"]["duration"]),
            "acodec": a["codec_name"] if a else None, "path": str(src)}
    (d / "meta.json").write_text(json.dumps(meta, indent=1))


def label_all(slug):
    te = load_json(DATA / slug / "text_events.json")
    out = {"slug": slug, "reviewer": "auto: every text in our own renders is typography", "typography": [], "caption": []}
    for e in te["events"]:
        b = e["bbox_ref"]
        out["typography"].append({"id_at_review": e["id"], "text": e["text"], "ref_frame": e["ref_frame"],
                                  "cx": b["x"] + b["w"] / 2, "cy": b["y"] + b["h"] / 2})
    p = ROOT / "reference" / "labels" / f"{slug}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1))


def inside(v, q):
    if v is None or not q:
        return None
    return q["p10"] <= v <= q["p90"]


def scorecard(slug, truth):
    sys.path.insert(0, str(ROOT / "scripts"))
    from build_fingerprint import video
    P = load_json(ROOT / "skill" / "apple-motion" / "references" / "fingerprint.json")["pooled"]
    V = video(slug)
    t = V["typography"]
    sp = t["entry_spring"]
    rows = [
        ("median shot length (frames)", V["shots"]["length_frames"]["p50"] if V["shots"]["length_frames"] else None, P["shot_length_frames"]),
        ("cuts per 10 s", V["shots"]["cuts_per_10s"], P["cuts_per_10s"]),
        ("typography per 10 s", V["text"]["typography_per_10s"], P["typography_per_10s"]),
        ("cap height % (median)", (t["cap_height_pct"] or {}).get("p50"), P["cap_height_pct"]),
        ("stroke / cap (weight)", (t["stroke_to_cap"] or {}).get("p50"), P["stroke_to_cap"]),
        ("typography hold frames (median)", (t["hold_frames"] or {}).get("p50"), P["hold_frames"]),
        ("entry frames, animated (median)", (t["entry_frames_animated"] or {}).get("p50"), P["entry_frames_animated"]),
        ("entry spring damping", sp.get("damping"), P["entry_spring_q"]["damping"]),
        ("entry spring stiffness", sp.get("stiffness"), P["entry_spring_q"]["stiffness"]),
        ("BPM", V["audio"]["bpm"], P["bpm"]),
        ("integrated LUFS", V["audio"]["loudness"]["integrated_lufs"], P["lufs"]),
        ("true peak dBTP", V["audio"]["loudness"]["true_peak_dbtp"], P["true_peak_dbtp"]),
        ("cuts on beat (share)", V["sync"]["cuts_on_beat"], P["cuts_on_beat"]),
    ]
    L = [f"# eval: {slug}", "", f"Measured with the extraction pipeline; Apple = pooled over {P['videos']} videos.", "",
         "| metric | render | Apple p10 | p50 | p90 | inside |", "|---|---|---|---|---|---|"]
    n_in = n_tot = 0
    for name, v, q in rows:
        ok = inside(v, q)
        if ok is not None:
            n_tot += 1
            n_in += ok
        L.append(f"| {name} | {v if v is not None else 'n/a'} | {q['p10'] if q else ''} | {q['p50'] if q else ''} | "
                 f"{q['p90'] if q else ''} | {'yes' if ok else ('no' if ok is not None else '-')} |")
    L += ["", f"**{n_in}/{n_tot} metrics inside Apple's p10-p90 range.**", ""]
    L += ["Entry styles measured: " + ", ".join(f"{k} {v}" for k, v in t["entry_style"].items()), ""]
    if truth:
        T = load_json(truth)
        te = load_json(DATA / slug / "text_events.json")["events"]
        ta = {a["id"]: a for a in load_json(DATA / slug / "text_anim.json")["events"]}
        L += ["## Pipeline calibration (measured vs. ground truth)", "",
              "| card | text | true appear | measured appear | true entry fr | measured entry fr | true style | measured style | true effective d/k | fitted d/k | idiomatic fit (damping, durationInFrames) |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
        import re as _re
        import motionfit as mf
        if "text_in_spring" in T:
            td, tk = T["text_in_spring"]["damping"], T["text_in_spring"]["stiffness"]
        else:
            tok = (ROOT / "skill" / "apple-motion" / "templates" / "remotion" / "tokens.ts").read_text()
            m_ = _re.search(r"textIn: \{damping: ([\d.]+), stiffness: ([\d.]+)", tok)
            td, tk = float(m_.group(1)), float(m_.group(2))
        errs = []
        for c in T["cards"]:
            if not c.get("lines"):
                continue
            cand = [e for e in te if abs(e["appear_frame"] - c["start"]) <= 20]
            if not cand:
                L.append(f"| {c['i']} | {' / '.join(c['lines'])} | {c['start']} | missed | | | {c.get('entry')} | | |")
                continue
            e = min(cand, key=lambda e: abs(e["appear_frame"] - c["start"]))
            a = ta.get(e["id"], {})
            s = (a.get("entry") or {}).get("spring") or {}
            errs.append(e["appear_frame"] - c["start"])
            ef = c.get("entry_frames") or 0
            te_ = mf.effective_spring(td, tk, 1, ef, 30) if ef >= 2 else (None, None)
            idi = (a.get("entry") or {}).get("spring_idiomatic") or {}
            L.append(f"| {c['i']} | {' / '.join(c['lines'])[:30]} | {c['start']} | {e['appear_frame']} | {ef} | "
                     f"{e['entry_frames']} | {c.get('entry')} | {a.get('entry_style')} | "
                     f"{'%.0f/%.0f' % te_ if te_[0] else '-'} | {s.get('damping')}/{s.get('stiffness')} | "
                     f"{idi.get('damping')}, {idi.get('durationInFrames')} |")
        if errs:
            L += ["", f"Appear-frame error: median {np.median(errs):+.1f} fr, max |err| {np.max(np.abs(errs))} fr (n={len(errs)})."]
    out = ROOT / "reports" / "eval" / f"{slug}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n")
    print("\n".join(L))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--name", required=True)
    ap.add_argument("--truth")
    ap.add_argument("--skip", default="", help="comma list of steps already done")
    ap.add_argument("--oracle", action="store_true", help="use s2a_oracle (truth-seeded boxes) instead of GPU OCR")
    a = ap.parse_args()
    slug = f"render-{a.name}"
    log = ROOT / ".cache" / "logs" / f"eval_{slug}.log"
    skip = set(a.skip.split(",")) if a.skip else set()
    if "ingest" not in skip:
        ingest(Path(a.video).resolve(), slug)
    for step in STEPS:
        if step in skip:
            continue
        if step == "s2a_ocr" and a.oracle:
            sh([PY, "s2a_oracle.py", slug, "--truth", str(Path(a.truth).resolve())], log)
            continue
        sh([PY, f"{step}.py", slug], log)
        if step == "s2b_text_events":
            label_all(slug)
            sh([PY, "relabel.py", slug], log)
    scorecard(slug, a.truth)


if __name__ == "__main__":
    main()
