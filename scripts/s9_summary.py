#!/usr/bin/env python3
"""STEP 9: data/<slug>/summary.md - 20 to 40 lines of measured facts (no interpretation)."""
import sys
from collections import Counter

import numpy as np

from common import DATA, load_json, meta, read_shots


def med(xs, nd=1):
    xs = [x for x in xs if x is not None and np.isfinite(x)]
    return round(float(np.median(xs)), nd) if xs else None


def pct(a, b):
    return f"{a / b * 100:.0f}%" if b else "n/a"


def stats(slug):
    m = meta(slug)
    fps, n = m["fps"], m["nb_frames"]
    dur = n / fps
    shots = read_shots(slug)
    te = load_json(DATA / slug / "text_events.json")["events"]
    ta = load_json(DATA / slug / "text_anim.json")["events"]
    mo = load_json(DATA / slug / "motion.json")
    cl = load_json(DATA / slug / "color_layout.json")
    au = load_json(DATA / slug / "audio.json")
    sy = load_json(DATA / slug / "sync.json")["summary"]
    typo_ids = {e["id"] for e in te if e.get("role") == "typography"}
    typo = [e for e in te if e["id"] in typo_ids]
    typo_a = [a for a in ta if a["id"] in typo_ids]
    animated = [a for a in typo_a if a["entry_frames"] >= 2 and a["entry"].get("spring")]
    sp = [a["entry"]["spring"] for a in animated]
    lens = [s["length_frames"] for s in shots]
    return dict(m=m, fps=fps, n=n, dur=dur, shots=shots, lens=lens, te=te, ta=ta, typo=typo, typo_a=typo_a,
                animated=animated, sp=sp, mo=mo, cl=cl, au=au, sy=sy)


def run(slug):
    S = stats(slug)
    m, fps, dur = S["m"], S["fps"], S["dur"]
    lens, shots, typo, typo_a, sp, au, sy = S["lens"], S["shots"], S["typo"], S["typo_a"], S["sp"], S["au"], S["sy"]
    tr = Counter(s["transition"] for s in shots[1:])
    st = Counter(a["entry_style"] for a in typo_a)
    ex = Counter(a["exit_style"] for a in typo_a)
    holds = [e["hold_frames"] for e in typo]
    entries = [a["entry_frames"] for a in S["animated"]]
    lines = [
        f"# {slug} - measured facts",
        "",
        f"- Source: {m['source']} ({m.get('via', 'download')}), {m['width']}x{m['height']} {m['vcodec']}, "
        f"{m['fps_rational']} = {fps:.3f} fps, {S['n']} frames, {dur:.2f} s.",
        f"- Shots: {len(shots)}; length median {med(lens, 0)} fr, p10 {np.percentile(lens, 10):.0f}, "
        f"p90 {np.percentile(lens, 90):.0f}, min {min(lens)}, max {max(lens)} fr.",
        f"- Cuts per 10 s: {(len(shots) - 1) / dur * 10:.1f}. Transitions: "
        + ", ".join(f"{k} {v}" for k, v in tr.most_common()) + ".",
        f"- Text events: {len(S['te'])} total, {len(typo)} typography "
        f"({len(typo) / dur * 10:.2f} per 10 s); roles: "
        + ", ".join(f"{k} {v}" for k, v in Counter(e.get('role') for e in S['te']).most_common()) + ".",
        f"- Typography hold: median {med(holds, 0)} fr ({(med(holds, 0) or 0) / fps:.2f} s), "
        f"p10 {np.percentile(holds, 10):.0f}, p90 {np.percentile(holds, 90):.0f} fr." if holds else "- Typography hold: n/a.",
        f"- Typography entry duration (animated only, n={len(entries)}): median {med(entries, 0)} fr, "
        f"p90 {np.percentile(entries, 90):.0f} fr." if entries else "- Typography entry duration: n/a.",
        "- Entry styles (typography): " + (", ".join(f"{k} {v}" for k, v in st.most_common()) or "n/a") + ".",
        "- Exit styles (typography): " + (", ".join(f"{k} {v}" for k, v in ex.most_common()) or "n/a") + ".",
    ]
    if sp:
        lines.append(f"- Entry spring fit (median of {len(sp)}): damping {med([s['damping'] for s in sp])}, "
                     f"stiffness {med([s['stiffness'] for s in sp])}, mass 1, durationInFrames "
                     f"{med([s['durationInFrames'] for s in sp], 0)}, overshoot {med([s['overshoot_pct'] for s in sp])}%, "
                     f"rmse {med([s['rmse'] for s in sp], 3)}.")
        bz = [a["entry"]["bezier"]["bezier"] for a in S["animated"] if a["entry"].get("bezier", {}).get("bezier")]
        if bz:
            b = np.median(np.array(bz), 0)
            nn = Counter(a["entry"]["bezier"]["nearest_named"] for a in S["animated"] if a["entry"].get("bezier", {}).get("nearest_named"))
            lines.append(f"- Entry bezier (median control points): ({b[0]:.2f}, {b[1]:.2f}, {b[2]:.2f}, {b[3]:.2f}); "
                         f"nearest named: " + ", ".join(f"{k} {v}" for k, v in nn.most_common(3)) + ".")
        ch = Counter(k for a in S["animated"] for k, v in a["entry"]["channels"].items() if v.get("animated"))
        lines.append("- Animated channels in typography entries: " + ", ".join(f"{k} {v}" for k, v in ch.most_common()) + ".")
        sc0 = [a["entry"]["channels"]["scale"]["start"] for a in S["animated"] if a["entry"]["channels"].get("scale", {}).get("animated")]
        dy0 = [a["entry"]["channels"]["dy"]["start_pct_h"] for a in S["animated"] if a["entry"]["channels"].get("dy", {}).get("animated")]
        bl0 = [a["entry"]["channels"]["blur_px"]["start"] for a in S["animated"] if a["entry"]["channels"].get("blur_px", {}).get("animated")]
        lines.append(f"- Entry start values: scale median {med(sc0, 2)} (n={len(sc0)}), y-offset median {med(dy0, 2)}% of height "
                     f"(n={len(dy0)}), blur median {med(bl0, 1)} px (n={len(bl0)}).")
    if typo:
        lines.append(f"- Cap height (typography): median {med([e['cap_height_pct'] for e in typo], 2)}% of frame height, "
                     f"p10 {np.percentile([e['cap_height_pct'] for e in typo], 10):.2f}%, p90 {np.percentile([e['cap_height_pct'] for e in typo], 90):.2f}%.")
        lines.append("- Typography lines: " + ", ".join(f"{k} line(s) {v}" for k, v in sorted(Counter(e['line_count'] for e in typo).items()))
                     + "; alignment: " + ", ".join(f"{k} {v}" for k, v in Counter(e['alignment'] for e in typo).most_common()) + ".")
        lines.append("- Typography position (3x3): " + ", ".join(f"{k} {v}" for k, v in Counter(e['grid_cell'] for e in typo).most_common(5)) + ".")
        lines.append("- Typography colour: " + ", ".join(f"{k} {v}" for k, v in Counter(e['color_hex'] for e in typo).most_common(4))
                     + "; background type: " + ", ".join(f"{k} {v}" for k, v in Counter(e['background_type'] for e in typo).most_common()) + ".")
        drift = [e["hold_drift"]["scale_pct_per_s"] for e in typo if e.get("hold_drift")]
        if drift:
            lines.append(f"- Hold drift (typography): scale median {med(drift, 2)}%/s (n={len(drift)}).")
    mo, cl = S["mo"], S["cl"]
    lines.append("- Camera/global motion per shot: " + ", ".join(f"{k} {v}" for k, v in Counter(r['dominant_move'] for r in mo['shots']).most_common())
                 + f"; element entries {mo['element_entries_per_s']}/s.")
    ws = [r["spring"] for r in mo["shots"] if r.get("spring") and r["dominant_move"] in ("push", "pull", "pan", "tilt", "whip")]
    if ws:
        lines.append(f"- Camera move spring (median of {len(ws)}): damping {med([s['damping'] for s in ws])}, stiffness "
                     f"{med([s['stiffness'] for s in ws])}; accel {med([r.get('accel_frames') for r in mo['shots'] if r.get('spring')], 0)} fr, "
                     f"decel {med([r.get('decel_frames') for r in mo['shots'] if r.get('spring')], 0)} fr.")
    lines.append("- Frame classes (share of frames): " + ", ".join(f"{k} {v * 100:.0f}%" for k, v in sorted(cl['frame_share_by_class'].items(), key=lambda kv: -kv[1])) + ".")
    bgs = Counter(r.get("background_hex") for r in cl["shots"])
    lines.append("- Most common shot backgrounds: " + ", ".join(f"{k} {v}" for k, v in bgs.most_common(4)) + ".")
    acc = Counter(a["hex"] for r in cl["shots"] for a in r["accents"][:1])
    if acc:
        lines.append("- Dominant accent per shot (top): " + ", ".join(f"{k} {v}" for k, v in acc.most_common(4)) + ".")
    lines.append(f"- Music: {au['bpm']} BPM (beat {au['beat_period_frames']} fr, bar {au['bar_length_frames']} fr, "
                 f"4/4 assumed, downbeat confidence {au['downbeat_confidence']}); {len(au['sections'])} sections: "
                 + ", ".join(f"{s['start_s']:.0f}-{s['end_s']:.0f}s {s['energy']}" for s in au['sections']) + ".")
    lo = au["loudness"]
    lines.append(f"- Loudness: {lo['integrated_lufs']} LUFS integrated, LRA {lo['lra_lu']} LU, true peak {lo['true_peak_dbtp']} dBTP.")
    lines.append(f"- Stems RMS share of mix: " + ", ".join(f"{k} {v}" for k, v in au["stem_rms_share"].items()) + ".")
    v = au["voice"]
    if v.get("present"):
        lines.append(f"- Voice-over: {v['n_words']} words, {v['words_per_second_speaking']} words/s while speaking, "
                     f"{v['words_per_second_overall']} words/s overall, {v['speech_seconds']} s of speech.")
    else:
        lines.append("- Voice-over: none detected (vocals stem share %.2f)." % v["vocals_stem_share"])
    lines.append(f"- SFX candidates (non-music, off word onsets): {au['sfx']['n_non_music']} "
                 f"({au['sfx']['n_non_music'] / dur * 10:.1f} per 10 s); classes: "
                 + ", ".join(f"{k} {c}" for k, c in Counter(c['class'] for c in au['sfx']['candidates'] if not c['likely_music'] and not c.get('on_word_onset')).most_common()) + ".")
    lines.append(f"- Sync (+-2 fr): cuts on beat {sy['cuts_on_beat']} vs chance {sy['chance_on_beat']}; on downbeat "
                 f"{sy['cuts_on_downbeat']} vs {sy['chance_on_downbeat']}; typography on beat {sy['typography_on_beat']}.")
    if sy.get("cuts_near_word_onset") is not None:
        lines.append(f"- Cuts within 2 fr of a word onset {sy['cuts_near_word_onset']} (chance {sy['chance_near_word_onset']}), "
                     f"of a word end {sy['cuts_near_word_end']}; typography vs same spoken word: median offset "
                     f"{sy['typography_vo_median_offset']} fr (n={len(sy['typography_vo_offsets'])}).")
    lines.append(f"- Cuts with an SFX candidate within 2 fr: {sy['cuts_with_sfx']}; typography entries with SFX: {sy['typography_with_sfx']}.")
    (DATA / slug / "summary.md").write_text("\n".join(lines) + "\n")
    print(f"[{slug}] summary.md {len(lines)} lines", flush=True)
    return len(lines)


if __name__ == "__main__":
    for s in sys.argv[1:]:
        run(s)
