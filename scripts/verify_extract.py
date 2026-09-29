#!/usr/bin/env python3
"""Acceptance check for the extraction. Exit code 1 on any failure.

Per slug: every output file exists; every contact sheet opens; text_events.json has > 10 events;
text_anim.json has a spring fit (damping, stiffness, mass, durationInFrames) for every event.
Storage: project, data, cache, venv, every cache env var, the python prefix, ~/dev/apple-motion
and every file under data/ resolve under /Volumes/Transcend.
"""
import json
import os
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(os.environ.get("PROJECT_ROOT", Path(__file__).resolve().parents[1]))
DATA = ROOT / "data"
EXT = os.environ.get("AM_REQUIRE_PREFIX") or (os.path.realpath(ROOT) + "/")
REQUIRED = ["meta.json", "shots.csv", "text_events.json", "text_anim.json", "motion.json", "color_layout.json",
            "audio.json", "sync.json", "summary.md", "audio/spectrogram.png", "contact_sheets/index.json"]
fails, rows = [], []


def check(ok, what):
    if not ok:
        fails.append(what)
    return ok


def main():
    slugs = sorted(p.parent.name for p in DATA.glob("*/meta.json") if not p.parent.name.startswith("render-"))
    check(len(slugs) == 6, f"expected 6 slugs, found {len(slugs)}")
    for slug in slugs:
        d = DATA / slug
        miss = [f for f in REQUIRED if not (d / f).exists()]
        check(not miss, f"{slug}: missing {miss}")
        shots_png = list((d / "frames" / "shots").glob("*.png"))
        entries = list((d / "frames" / "entries").glob("e*_filmstrip.png"))
        check(len(shots_png) > 0, f"{slug}: no shot frames")
        sheets = sorted((d / "contact_sheets").glob("sheet_*.png"))
        check(0 < len(sheets) <= 12, f"{slug}: {len(sheets)} contact sheets (need 1..12)")
        bad = []
        for s in sheets:
            try:
                with Image.open(s) as im:
                    im.verify()
                with Image.open(s) as im:
                    im.load()
                    if im.size[0] != 1600:
                        bad.append(f"{s.name} width {im.size[0]}")
            except Exception as e:
                bad.append(f"{s.name}: {e}")
        check(not bad, f"{slug}: bad sheets {bad}")
        n_ev = n_fit = 0
        if (d / "text_events.json").exists() and (d / "text_anim.json").exists():
            te = json.loads((d / "text_events.json").read_text())["events"]
            ta = {a["id"]: a for a in json.loads((d / "text_anim.json").read_text())["events"]}
            n_ev = len(te)
            check(n_ev > 10, f"{slug}: only {n_ev} text events")
            for e in te:
                a = ta.get(e["id"])
                sp = (a or {}).get("entry", {}).get("spring")
                if sp and all(k in sp for k in ("damping", "stiffness", "mass", "durationInFrames")):
                    n_fit += 1
            check(n_fit == n_ev, f"{slug}: spring fits {n_fit}/{n_ev}")
            n_anim = sum(1 for e in te if e["full_frame"] + 1 >= e["appear_frame"])
            check(len(entries) >= n_anim, f"{slug}: {len(entries)} entry filmstrips for {n_anim} events")
        # storage
        outside = []
        for p in d.rglob("*"):
            if not os.path.realpath(p).startswith(EXT):
                outside.append(str(p))
        check(not outside, f"{slug}: {len(outside)} data paths outside Transcend, e.g. {outside[:2]}")
        rows.append((slug, "OK" if not miss else "MISSING", len(sheets), len(shots_png), len(entries), n_ev, n_fit))
    paths = {"project": ROOT, "data": DATA, "cache": ROOT / ".cache", "venv": ROOT / ".venv",
             "~/dev/apple-motion": Path.home() / "dev" / "apple-motion", "sys.prefix": Path(sys.prefix)}
    for var in ("PIP_CACHE_DIR", "TORCH_HOME", "HF_HOME", "XDG_CACHE_HOME", "TMPDIR", "EASYOCR_DIR"):
        v = os.environ.get(var)
        check(v is not None, f"env {var} not set (source scripts/env.sh)")
        if v:
            paths[f"${var}"] = Path(v)
    print(f"{'path':24} realpath")
    for k, p in paths.items():
        rp = os.path.realpath(p)
        ok = check(rp.startswith(EXT), f"{k} -> {rp} not on Transcend")
        print(f"{k:24} {rp} {'OK' if ok else 'FAIL'}")
    print()
    print(f"{'slug':22} {'files':8} {'sheets':>6} {'shotpng':>7} {'entrypng':>8} {'events':>6} {'springs':>7}")
    for r in rows:
        print(f"{r[0]:22} {r[1]:8} {r[2]:>6} {r[3]:>7} {r[4]:>8} {r[5]:>6} {r[6]:>7}")
    print()
    if fails:
        print("FAIL")
        for f in fails:
            print(" -", f)
        sys.exit(1)
    print("PASS: all acceptance checks")


if __name__ == "__main__":
    main()
