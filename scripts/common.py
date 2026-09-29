"""Shared helpers for the extraction scripts. Import after sourcing scripts/env.sh."""
import csv
import json
import os
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(os.environ.get("PROJECT_ROOT", Path(__file__).resolve().parents[1]))
DATA = ROOT / "data"
SRC = DATA / "_src"

_req = os.environ.get("AM_REQUIRE_PREFIX", "")
if _req and not str(ROOT).startswith(_req):
    sys.exit(f"PROJECT_ROOT must live under {_req}, got {ROOT}")
if not os.environ.get("TMPDIR", "").startswith(str(ROOT)):
    sys.exit("source scripts/env.sh first (TMPDIR is not inside the project)")

cv2.setNumThreads(int(os.environ.get("CV_THREADS", 3)))


def slugs(include_renders=False):
    out = sorted(p.parent.name for p in DATA.glob("*/meta.json"))
    return out if include_renders else [s for s in out if not s.startswith("render-")]


def meta(slug):
    return json.loads((DATA / slug / "meta.json").read_text())


def video_path(slug):
    """Source video. If VIDEO_CACHE_DIR (a RAM disk) holds a copy, read that instead: the USB HDD
    drops off the bus under concurrent reads; outputs are still written to the project on Transcend."""
    cache = os.environ.get("VIDEO_CACHE_DIR")
    if cache and (Path(cache) / f"{slug}.mp4").exists():
        return Path(cache) / f"{slug}.mp4"
    return SRC / f"{slug}.mp4"


def out_dir(slug):
    d = DATA / slug
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_json(path, obj):
    path = Path(path)
    path.write_text(json.dumps(obj, indent=1, default=_np_default))


def load_json(path):
    return json.loads(Path(path).read_text())


def _np_default(o):
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return None if not np.isfinite(o) else round(float(o), 5)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, np.bool_):
        return bool(o)
    raise TypeError(type(o))


def iter_frames(slug, start=0, end=None, scale=None, gray=False):
    """Yield (index, frame) sequentially. Seeks once, then decodes linearly (frame accurate)."""
    cap = cv2.VideoCapture(str(video_path(slug)))
    if start:
        cap.set(cv2.CAP_PROP_POS_FRAMES, start)
    i = start
    while True:
        if end is not None and i >= end:
            break
        ok, f = cap.read()
        if not ok:
            break
        if scale:
            f = cv2.resize(f, scale, interpolation=cv2.INTER_AREA)
        if gray:
            f = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        yield i, f
        i += 1
    cap.release()


class FrameCache:
    """Random access to decoded frames via sequential decode of a window (avoids seek drift)."""

    def __init__(self, slug):
        self.slug = slug
        self.cache = {}

    def load_range(self, a, b, scale=None):
        a = max(0, a)
        missing = [i for i in range(a, b) if i not in self.cache]
        if not missing:
            return
        # decode from a keyframe-safe start: seek to a then read linearly
        for i, f in iter_frames(self.slug, a, b, scale=scale):
            self.cache[i] = f

    def get(self, i):
        return self.cache.get(i)

    def clear(self):
        self.cache.clear()


def read_shots(slug):
    rows = []
    with open(DATA / slug / "shots.csv") as fh:
        for r in csv.DictReader(fh):
            rows.append({k: (int(v) if k in ("index", "start_frame", "end_frame", "length_frames") else v)
                         for k, v in r.items()})
    return rows


def shot_of(frame, shots):
    for s in shots:
        if s["start_frame"] <= frame <= s["end_frame"]:
            return s["index"]
    return shots[-1]["index"] if shots else 0


def hexcol(bgr):
    b, g, r = [int(round(float(x))) for x in bgr]
    return f"#{r:02x}{g:02x}{b:02x}"


def luminance(bgr):
    b, g, r = [float(x) for x in bgr]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b
