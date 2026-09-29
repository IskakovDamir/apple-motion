#!/usr/bin/env python3
"""Aggregate every per-video extraction into the style fingerprint the skill is built from.

  skill/apple-motion/references/fingerprint.json   machine-readable (per video + pooled)
  reports/extraction_report.md                      the report table + storage check

Typography statistics use reviewed labels (role == 'typography'); good spring fits only
(entry >= 2 frames and rmse <= 0.15) enter the spring/bezier medians.
"""
import json
import os
import subprocess
import sys
from collections import Counter

import numpy as np
from pathlib import Path

from common import DATA, ROOT, load_json, meta, read_shots

OUT_JSON = ROOT / "skill" / "apple-motion" / "references" / "fingerprint.json"
OUT_MD = ROOT / "reports" / "extraction_report.md"


def q(xs, ps=(10, 25, 50, 75, 90), nd=2):
    xs = [float(x) for x in xs if x is not None and np.isfinite(x)]
    if not xs:
        return None
    return {f"p{p}": round(float(np.percentile(xs, p)), nd) for p in ps} | {"n": len(xs), "mean": round(float(np.mean(xs)), nd)}


def med(xs, nd=2):
    xs = [float(x) for x in xs if x is not None and np.isfinite(x)]
    return round(float(np.median(xs)), nd) if xs else None


def shares(counter):
    tot = sum(counter.values())
    return {k: round(v / tot, 3) for k, v in counter.most_common()} if tot else {}


def video(slug):
    m = meta(slug)
    fps, n = m["fps"], m["nb_frames"]
    dur = n / fps
    shots = read_shots(slug)
    te = load_json(DATA / slug / "text_events.json")["events"]
    ta = {a["id"]: a for a in load_json(DATA / slug / "text_anim.json")["events"]}
    mo = load_json(DATA / slug / "motion.json")
    cl = load_json(DATA / slug / "color_layout.json")
    au = load_json(DATA / slug / "audio.json")
    sy = load_json(DATA / slug / "sync.json")["summary"]
    typo = [e for e in te if e.get("role") == "typography"]
    capt = [e for e in te if e.get("role") == "caption"]
    tA = [ta[e["id"]] for e in typo if e["id"] in ta]
    anim = [a for a in tA if a["entry_frames"] >= 2 and a["entry"].get("spring") and not a["entry"]["spring"].get("degenerate")]
    good = [a for a in anim if a["entry"]["spring"]["rmse"] <= 0.15]
    exits = [a for a in tA if a.get("exit", {}).get("spring")]

    def ch_start(ch, key="start"):
        return [a["entry"]["channels"][ch][key] for a in anim if a["entry"]["channels"].get(ch, {}).get("animated")]

    lens = [s["length_frames"] for s in shots]
    # structure: pace across the video, montage runs, where type sits in time
    q4 = [[s["length_frames"] for s in shots if k * n / 4 <= s["start_frame"] < (k + 1) * n / 4] for k in range(4)]
    runs, cur = [], 0
    for L_ in lens:
        if L_ <= 10:
            cur += 1
        else:
            if cur >= 4:
                runs.append(cur)
            cur = 0
    if cur >= 4:
        runs.append(cur)
    structure = {"first_shot_frames": lens[0], "last_shot_frames": lens[-1],
                 "median_shot_by_quarter": [med(x, 1) for x in q4],
                 "montage_runs": len(runs), "montage_run_lengths": runs,
                 "typography_by_quarter": [sum(1 for e in typo if k * n / 4 <= e["appear_frame"] < (k + 1) * n / 4) for k in range(4)]}
    v = {
        "slug": slug, "source": m["source"], "fps": round(fps, 3), "duration_s": round(dur, 2), "frames": n,
        "structure": structure,
        "shots": {"count": len(shots), "length_frames": q(lens, nd=1), "cuts_per_10s": round((len(shots) - 1) / dur * 10, 2),
                  "transitions": dict(Counter(s["transition"] for s in shots[1:]))},
        "text": {"events_total": len(te), "roles": dict(Counter(e.get("role") for e in te)),
                 "typography_count": len(typo), "typography_per_10s": round(len(typo) / dur * 10, 2),
                 "caption_count": len(capt), "all_events_per_10s": round(len(te) / dur * 10, 2),
                 "hold_frames_all": q([e["hold_frames"] for e in te], nd=1)},
        "typography": {
            "cap_height_pct": q([e["cap_height_pct"] for e in typo]),
            "stroke_to_cap": q([e.get("stroke_to_cap") for e in typo], nd=3),
            "x_height_ratio": q([e.get("x_height_ratio") for e in typo], nd=3),
            "line_pitch_to_cap": q([e.get("line_pitch_to_cap") for e in typo]),
            "line_count": dict(Counter(e["line_count"] for e in typo)),
            "alignment": dict(Counter(e["alignment"] for e in typo)),
            "grid_cell": dict(Counter(e["grid_cell"] for e in typo)),
            "center_pct": [e["center_pct"] for e in typo],
            "color_hex": dict(Counter(e["color_hex"] for e in typo)),
            "background_hex": dict(Counter(e["background_hex"] for e in typo)),
            "background_type": dict(Counter(e["background_type"] for e in typo)),
            "hold_frames": q([e["hold_frames"] for e in typo], nd=1),
            "on_screen_frames": q([e["gone_frame"] - e["appear_frame"] for e in typo], nd=1),
            "entry_frames": q([a["entry_frames"] for a in tA], nd=1),
            "entry_frames_animated": q([a["entry_frames"] for a in anim], nd=1),
            "exit_frames": q([a["exit_frames"] for a in tA], nd=1),
            "appear_kind": dict(Counter(e["appear_kind"] for e in typo)),
            "exit_kind": dict(Counter(e["exit_kind"] for e in typo)),
            "entry_style": dict(Counter(a["entry_style"] for a in tA)),
            "exit_style": dict(Counter(a["exit_style"] for a in tA)),
            "entry_spring": {k: med([a["entry"]["spring"][k] for a in good]) for k in ("damping", "stiffness", "durationInFrames", "zeta", "overshoot_pct", "rmse")} | {"mass": 1, "n": len(good)},
            "entry_spring_idiomatic": {k: med([a["entry"]["spring_idiomatic"][k] for a in good]) for k in ("damping", "durationInFrames", "rmse")} | {"stiffness": 100, "mass": 1},
            "entry_bezier": [med([a["entry"]["bezier"]["bezier"][i] for a in anim if a["entry"].get("bezier", {}).get("bezier")], 3) for i in range(4)],
            "entry_bezier_named": dict(Counter(a["entry"]["bezier"]["nearest_named"] for a in anim if a["entry"].get("bezier", {}).get("nearest_named"))),
            "exit_spring": {k: med([a["exit"]["spring"][k] for a in exits]) for k in ("damping", "stiffness", "durationInFrames", "rmse")} | {"n": len(exits)},
            "exit_bezier": [med([a["exit"]["bezier"]["bezier"][i] for a in exits if a["exit"].get("bezier", {}).get("bezier")], 3) for i in range(4)],
            "entry_channels": dict(Counter(k for a in anim for k, c in a["entry"]["channels"].items() if c.get("animated"))),
            "entry_start": {"scale": q(ch_start("scale")), "dy_pct_h": q(ch_start("dy", "start_pct_h")),
                            "dx_pct_h": q(ch_start("dx", "start_pct_h")), "blur_px": q(ch_start("blur_px")),
                            "opacity": q(ch_start("opacity"))},
            "word_stagger_frames": q([a["word_stagger"]["median_step_frames"] for a in tA if a.get("word_stagger") and a["entry_style"] == "per-word pop"]),
            "hold_drift_scale_pct_per_s": q([e["hold_drift"]["scale_pct_per_s"] for e in typo if e.get("hold_drift")]),
            "hold_drift_dy_pct_h_per_s": q([e["hold_drift"]["dy_pct_h_per_s"] for e in typo if e.get("hold_drift")]),
            "examples": [{"text": e["text"], "appear": e["appear_frame"], "entry": ta.get(e["id"], {}).get("entry_style"),
                          "entry_frames": e["entry_frames"], "hold": e["hold_frames"], "cap_pct": e["cap_height_pct"],
                          "color": e["color_hex"], "bg": e["background_hex"]} for e in typo],
        },
        "motion": {"dominant_move": dict(Counter(r["dominant_move"] for r in mo["shots"])),
                   "camera_spring": {k: med([r["spring"][k] for r in mo["shots"] if r.get("spring") and r["dominant_move"] in ("push", "pull", "pan", "tilt")]) for k in ("damping", "stiffness", "rmse")},
                   "cum_zoom_pct_push_pull": q([r["cum_zoom_pct"] for r in mo["shots"] if r["dominant_move"] in ("push", "pull")]),
                   "element_entries_per_s": mo["element_entries_per_s"]},
        "color": {"frame_share_by_class": cl["frame_share_by_class"],
                  "shot_background_hex": dict(Counter(r.get("background_hex") for r in cl["shots"]).most_common(8)),
                  "accent_hex": dict(Counter(a["hex"] for r in cl["shots"] for a in r["accents"][:1]).most_common(8))},
        "audio": {"bpm": au["bpm"], "beat_period_frames": au["beat_period_frames"], "bar_length_frames": au["bar_length_frames"],
                  "downbeat_confidence": au["downbeat_confidence"],
                  "loudness": au["loudness"], "stem_rms_share": au["stem_rms_share"],
                  "sections": [{"start_s": s["start_s"], "end_s": s["end_s"], "energy": s["energy"], "rms_db": s["rms_db"]} for s in au["sections"]],
                  "voice": {k: au["voice"].get(k) for k in ("present", "n_words", "words_per_second_speaking", "words_per_second_overall", "speech_seconds")},
                  "sfx_non_music": au["sfx"]["n_non_music"], "sfx_per_10s": round(au["sfx"]["n_non_music"] / dur * 10, 2),
                  "sfx_classes": dict(Counter(c["class"] for c in au["sfx"]["candidates"] if not c["likely_music"] and not c.get("on_word_onset")))},
        "sync": sy,
    }
    return v


def calibration():
    """Speed bias of the spring fit, from our own calibration render (known springs measured back).
    Returns {'time_scale': c, 'n': n} with fitted stiffness ~ true * c^2, damping ~ true * c."""
    import re
    import motionfit as mf
    tr = ROOT / "demo" / "out" / "calibration.truth.json"
    an = DATA / "render-cal" / "text_anim.json"
    if not (tr.exists() and an.exists()):
        return None
    TT = load_json(tr)
    T = TT["cards"]
    A = load_json(an)["events"]
    td, tk = TT["text_in_spring"]["damping"], TT["text_in_spring"]["stiffness"]  # spring used at render time
    ratios, zetas = [], []
    for c in T:
        if c["entry"] not in ("scaleDown", "scaleUp", "slideUp", "slideUpMask", "fade") or not c["entry_frames"]:
            continue
        cand = [a for a in A if abs(a["appear_frame"] - c["start"]) <= 6 and a["entry"].get("spring")]
        if not cand:
            continue
        a = min(cand, key=lambda a: abs(a["appear_frame"] - c["start"]))
        ed, ek = mf.effective_spring(td, tk, 1, c["entry_frames"], 30)
        sp = a["entry"]["spring"]
        ratios.append(float(np.sqrt(sp["stiffness"] / ek)))
        zetas.append((sp["damping"] / (2 * np.sqrt(sp["stiffness"]))) / (ed / (2 * np.sqrt(ek))))
    if len(ratios) < 3:
        return None
    return {"time_scale": round(float(np.median(ratios)), 3), "zeta_ratio": round(float(np.median(zetas)), 3),
            "n": len(ratios), "ratios": [round(r, 3) for r in ratios],
            "note": "fitted springs are this much faster than the truth; calibrated = fitted / c (damping), / c^2 (stiffness)"}


def weight_calibration():
    """stroke/cap measured on our render of SF Pro Display at known weights -> interpolation table."""
    p = DATA / "render-cal" / "text_events.json"
    if not p.exists():
        return None
    import re
    pts = []
    for e in load_json(p)["events"]:
        m = re.match(r"Weight (\d+)", e["text"])
        if m and e.get("stroke_to_cap"):
            pts.append((e["stroke_to_cap"], int(m.group(1))))
    pts.sort()
    return pts if len(pts) >= 3 else None


def to_weight(sc, table):
    if sc is None or not table:
        return None
    xs, ys = [p[0] for p in table], [p[1] for p in table]
    return int(round(float(np.interp(sc, xs, ys)) / 50) * 50)


def camera(slugs):
    """Per-shot camera/global motion rates from motion.json (pooled)."""
    zoom, pan, fps_ = [], [], 30.0
    for s in slugs:
        mo = load_json(DATA / s / "motion.json")
        fps_ = mo.get("fps", 30.0)
        for r in mo["shots"]:
            n = r["end_frame"] - r["start_frame"] + 1
            if n < 6:
                continue
            if r["dominant_move"] in ("push", "pull"):
                zoom.append(abs(r["cum_zoom_pct"]) / (n / fps_))
            if r["dominant_move"] in ("pan", "tilt"):
                pan.append(float(np.hypot(*r["cum_translation_pct"])) / (n / fps_))
    return {"zoom_pct_per_s": q(zoom), "pan_pct_per_s": q(pan)}


def pool(videos, slugs):
    """Pooled distributions over all videos (typography events pooled, not averaged)."""
    allty, allan, alllen = [], [], []
    for s in slugs:
        te = load_json(DATA / s / "text_events.json")["events"]
        ta = {a["id"]: a for a in load_json(DATA / s / "text_anim.json")["events"]}
        ty = [e for e in te if e.get("role") == "typography"]
        allty += ty
        allan += [ta[e["id"]] for e in ty if e["id"] in ta]
        alllen += [x["length_frames"] for x in read_shots(s)]
    anim = [a for a in allan if a["entry_frames"] >= 2 and a["entry"].get("spring") and not a["entry"]["spring"].get("degenerate")]
    good = [a for a in anim if a["entry"]["spring"]["rmse"] <= 0.15]

    def cs(ch, key="start"):
        return [a["entry"]["channels"][ch][key] for a in anim if a["entry"]["channels"].get(ch, {}).get("animated")]
    cal = calibration()
    esp = {k: med([a["entry"]["spring"][k] for a in good]) for k in ("damping", "stiffness", "durationInFrames", "zeta", "overshoot_pct", "rmse")} | {"mass": 1, "n": len(good)}
    esp_cal = None
    if cal and esp["damping"] and esp["stiffness"]:
        import motionfit as mf
        c = cal["time_scale"]
        esp_cal = {"damping": round(esp["damping"] / c, 2), "stiffness": round(esp["stiffness"] / c ** 2, 1), "mass": 1}
        esp_cal["durationInFrames"] = mf.measure_spring(30, esp_cal["damping"], esp_cal["stiffness"], 1)
    # pooled on-beat test: observed hits vs expected hits under each video's chance rate
    k_hit = sum(round(v["sync"]["cuts_on_beat"] * n) for v, n in ((v, v["shots"]["count"] - 1) for v in videos) if v["sync"]["cuts_on_beat"] is not None)
    n_tot = sum(v["shots"]["count"] - 1 for v in videos if v["sync"]["cuts_on_beat"] is not None)
    exp = sum(v["sync"]["chance_on_beat"] * (v["shots"]["count"] - 1) for v in videos if v["sync"]["cuts_on_beat"] is not None)
    from scipy.stats import norm
    var = sum(v["sync"]["chance_on_beat"] * (1 - v["sync"]["chance_on_beat"]) * (v["shots"]["count"] - 1) for v in videos if v["sync"]["cuts_on_beat"] is not None)
    z = (k_hit - exp) / np.sqrt(var) if var else 0
    return {
        "calibration": cal, "entry_spring_calibrated": esp_cal,
        "cuts_on_beat_pooled": {"hits": int(k_hit), "cuts": int(n_tot), "expected_by_chance": round(exp, 1),
                                "z": round(float(z), 2), "p_one_sided": round(float(1 - norm.cdf(z)), 4)},
        "videos": len(slugs), "duration_s": round(sum(v["duration_s"] for v in videos), 1),
        "frames": sum(v["frames"] for v in videos),
        "shot_length_frames": q(alllen, nd=1),
        "median_shot_by_quarter": [med([v["structure"]["median_shot_by_quarter"][k] for v in videos], 1) for k in range(4)],
        "first_shot_frames": q([v["structure"]["first_shot_frames"] for v in videos], nd=0),
        "last_shot_frames": q([v["structure"]["last_shot_frames"] for v in videos], nd=0),
        "montage_runs_per_minute": q([v["structure"]["montage_runs"] / (v["duration_s"] / 60) for v in videos]),
        "typography_share_by_quarter": [round(sum(v["structure"]["typography_by_quarter"][k] for v in videos) /
                                              max(1, sum(sum(v["structure"]["typography_by_quarter"]) for v in videos)), 3) for k in range(4)],
        "cuts_per_10s": q([v["shots"]["cuts_per_10s"] for v in videos]),
        "transitions": shares(sum((Counter(v["shots"]["transitions"]) for v in videos), Counter())),
        "typography_count": len(allty),
        "typography_per_10s": q([v["text"]["typography_per_10s"] for v in videos]),
        "cap_height_pct": q([e["cap_height_pct"] for e in allty]),
        "stroke_to_cap": q([e.get("stroke_to_cap") for e in allty], nd=3),
        "weight_calibration": weight_calibration(),
        "font_weight_estimate": q([to_weight(e.get("stroke_to_cap"), weight_calibration()) for e in allty], nd=0),
        "x_height_ratio": q([e.get("x_height_ratio") for e in allty], nd=3),
        "line_pitch_to_cap": q([e.get("line_pitch_to_cap") for e in allty]),
        "line_count": shares(Counter(e["line_count"] for e in allty)),
        "alignment": shares(Counter(e["alignment"] for e in allty)),
        "grid_cell": shares(Counter(e["grid_cell"] for e in allty)),
        "color_hex": dict(Counter(e["color_hex"] for e in allty).most_common(10)),
        "background_type": shares(Counter(e["background_type"] for e in allty)),
        "hold_frames": q([e["hold_frames"] for e in allty], nd=1),
        "on_screen_frames": q([e["gone_frame"] - e["appear_frame"] for e in allty], nd=1),
        "entry_frames": q([a["entry_frames"] for a in allan], nd=1),
        "entry_frames_animated": q([a["entry_frames"] for a in anim], nd=1),
        "exit_frames": q([a["exit_frames"] for a in allan], nd=1),
        "appear_kind": shares(Counter(e["appear_kind"] for e in allty)),
        "exit_kind": shares(Counter(e["exit_kind"] for e in allty)),
        "entry_style": shares(Counter(a["entry_style"] for a in allan)),
        "exit_style": shares(Counter(a["exit_style"] for a in allan)),
        "entry_spring": esp,
        "entry_spring_q": {k: q([a["entry"]["spring"][k] for a in good]) for k in ("damping", "stiffness", "durationInFrames")},
        "entry_spring_idiomatic": {k: med([a["entry"]["spring_idiomatic"][k] for a in good]) for k in ("damping", "durationInFrames", "rmse")} | {"stiffness": 100, "mass": 1},
        "entry_bezier": [med([a["entry"]["bezier"]["bezier"][i] for a in anim if a["entry"].get("bezier", {}).get("bezier")], 3) for i in range(4)],
        "entry_bezier_named": dict(Counter(a["entry"]["bezier"]["nearest_named"] for a in anim if a["entry"].get("bezier", {}).get("nearest_named")).most_common()),
        "exit_bezier": [med([a["exit"]["bezier"]["bezier"][i] for a in allan if a.get("exit", {}).get("bezier", {}).get("bezier")], 3) for i in range(4)],
        "entry_channels": shares(Counter(k for a in anim for k, c in a["entry"]["channels"].items() if c.get("animated"))),
        "entry_start_scale_down": q([x for x in cs("scale") if x > 1.0]),
        "entry_start_scale_up": q([x for x in cs("scale") if x < 1.0]),
        "entry_start": {"scale": q(cs("scale")), "dy_pct_h": q(cs("dy", "start_pct_h")), "blur_px": q(cs("blur_px")),
                        "opacity": q(cs("opacity"))},
        "hold_drift_scale_pct_per_s": q([e["hold_drift"]["scale_pct_per_s"] for e in allty if e.get("hold_drift")]),
        "bpm": q([v["audio"]["bpm"] for v in videos], nd=1),
        "lufs": q([v["audio"]["loudness"]["integrated_lufs"] for v in videos], nd=1),
        "true_peak_dbtp": q([v["audio"]["loudness"]["true_peak_dbtp"] for v in videos], nd=1),
        "lra_lu": q([v["audio"]["loudness"]["lra_lu"] for v in videos], nd=1),
        "vo_words_per_s_speaking": q([v["audio"]["voice"]["words_per_second_speaking"] for v in videos if v["audio"]["voice"]["present"]]),
        "sfx_per_10s": q([v["audio"]["sfx_per_10s"] for v in videos]),
        "cuts_on_beat": q([v["sync"]["cuts_on_beat"] for v in videos], nd=3),
        "chance_on_beat": q([v["sync"]["chance_on_beat"] for v in videos], nd=3),
        "cuts_near_word_onset": q([v["sync"]["cuts_near_word_onset"] for v in videos], nd=3),
        "chance_near_word_onset": q([v["sync"]["chance_near_word_onset"] for v in videos], nd=3),
        "typography_vo_offset_frames": q(sum((v["sync"]["typography_vo_offsets"] for v in videos), []), nd=1),
        "frame_share_by_class": {k: round(float(np.mean([v["color"]["frame_share_by_class"].get(k, 0) for v in videos])), 3)
                                 for k in {k for v in videos for k in v["color"]["frame_share_by_class"]}},
        "dominant_move": shares(sum((Counter(v["motion"]["dominant_move"]) for v in videos), Counter())),
        "camera": camera(slugs),
        "element_entries_per_s": q([v["motion"]["element_entries_per_s"] for v in videos]),
    }


def fmt(x, key="p50"):
    if x is None:
        return "n/a"
    if isinstance(x, dict):
        return f"{x.get(key)}"
    return str(x)


def storage():
    lines = []
    du = subprocess.run(["du", "-sh", str(ROOT)], capture_output=True, text=True).stdout.split()[0]
    vols = [v for v in ("/", "/System/Volumes/Data", str(ROOT)) if os.path.exists(v)]
    df = subprocess.run(["df", "-h", *vols], capture_output=True, text=True).stdout
    lines.append(f"- Project size (du -sh {ROOT}): {du}")
    lines.append("```")
    lines += df.strip().splitlines()
    lines.append("```")
    base = ROOT / ".cache" / "df_baseline_rerun.txt"
    if base.exists():
        b = base.read_text().split("\n")[1].split()
        now = subprocess.run(["df", "-k", "/System/Volumes/Data"], capture_output=True, text=True).stdout.splitlines()[1].split()
        used0, used1 = int(b[2]), int(now[2])
        lines.append(f"- Internal Data volume used: {used0 / 1e6:.2f} GB at baseline ({base.read_text().splitlines()[0]}) -> "
                     f"{used1 / 1e6:.2f} GB now: {(used1 - used0) / 1024:+.0f} MB. This counts everything on the Mac "
                     "(other apps, browsers, other Claude sessions, caches), not just this project.")
    home = Path.home()
    own = [home / ".claude" / "projects" / "-Volumes-Transcend-dev-apple-motion",
           home / ".claude" / "projects" / "-Users-damir-dev-apple-motion",
           Path("/private/tmp/claude-501/-Volumes-Transcend-dev-apple-motion")]
    tot = 0
    for p_ in own:
        if p_.exists():
            kb = int(subprocess.run(["du", "-sk", str(p_)], capture_output=True, text=True).stdout.split()[0])
            tot += kb
            lines.append(f"  - this project's files on the internal disk: {p_} {kb / 1024:.1f} MB")
    lines.append(f"- This project's own internal-disk footprint (session transcript + scratchpad + the ~/dev symlink): "
                 f"{tot / 1024:.0f} MB {'(<= 200 MB: OK)' if tot / 1024 <= 200 else '(> 200 MB)'}")
    old = home / "dev" / "apple-motion.internal-old-20260928"
    if old.exists():
        lines.append(f"- Left on the internal disk from the earlier aborted attempt (moved aside, not deleted): {old} "
                     "(1.5 GB; safe to delete by hand)")
    return lines


def report(videos, P):
    L = ["# apple-motion extraction report", "",
         f"{P['videos']} videos, {P['duration_s']} s, {P['frames']} frames. All numbers measured by `scripts/` "
         "(see README). 'text' = every tracked text block (UI, products, chrome, legal included); 'typo' = "
         "reviewed designer typography only. 'On beat' = within +-2 frames of a tracked beat; chance = 5 / beat period.", "",
         "| video | fps | dur s | shots | median shot fr | BPM | text ev /10s | typo /10s | median hold fr text / typo | "
         "most common typo entry | median entry spring d/k/m (n) | cuts on beat (chance) | text / typo on beat | LUFS |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for v in videos:
        t = v["typography"]
        es = t["entry_style"]
        top = max(es, key=es.get) if es else "n/a"
        sp = t["entry_spring"]
        L.append(f"| {v['slug']} | {v['fps']} | {v['duration_s']} | {v['shots']['count']} | {fmt(v['shots']['length_frames'])} | "
                 f"{v['audio']['bpm']} | {v['text']['all_events_per_10s']} | {v['text']['typography_per_10s']} | "
                 f"{fmt(v['text'].get('hold_frames_all'))} / {fmt(t['hold_frames'])} | {top} | "
                 f"{sp['damping']}/{sp['stiffness']}/1 ({sp['n']}) | {v['sync']['cuts_on_beat']} ({v['sync']['chance_on_beat']}) | "
                 f"{v['sync']['text_on_beat']} / {v['sync']['typography_on_beat']} | {v['audio']['loudness']['integrated_lufs']} |")
    cal = P.get("calibration") or {}
    pb = P.get("cuts_on_beat_pooled") or {}
    L += ["", f"Pooled cuts on beat: {pb.get('hits')}/{pb.get('cuts')} vs {pb.get('expected_by_chance')} expected by chance "
          f"(z={pb.get('z')}, p={pb.get('p_one_sided')}).",
          f"Spring-fit calibration (known springs rendered and measured back): fitted springs are {cal.get('time_scale')}x too fast "
          f"(n={cal.get('n')}, damping ratio preserved x{cal.get('zeta_ratio')}); calibrated pooled entry spring: "
          f"{P.get('entry_spring_calibrated')}.",
          f"Font weight calibration (stroke/cap of SF Pro Display rendered at known weights): {P.get('weight_calibration')}.", ""]
    L += ["## Storage", ""] + storage()
    return "\n".join(L) + "\n"


def main():
    slugs = sorted(p.parent.name for p in DATA.glob("*/meta.json") if not p.parent.name.startswith("render-"))
    ready = [s for s in slugs if all((DATA / s / f).exists() for f in ("text_anim.json", "motion.json", "color_layout.json", "audio.json", "sync.json"))]
    videos = [video(s) for s in ready]
    P = pool(videos, ready)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps({"generated_from": ready, "pooled": P, "videos": videos}, indent=1, default=str))
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(report(videos, P))
    print(f"fingerprint over {len(ready)}/{len(slugs)} videos -> {OUT_JSON}")


if __name__ == "__main__":
    main()
