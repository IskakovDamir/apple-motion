#!/usr/bin/env python3
"""Apply reference/labels/<slug>.json to an existing text_events.json (no re-measurement)."""
import sys

from common import DATA, load_json, save_json
from review_sheet import apply_labels

for slug in sys.argv[1:]:
    p = DATA / slug / "text_events.json"
    d = load_json(p)
    print(f"[{slug}] {apply_labels(slug, d['events'])}")
    save_json(p, d)
    ap = DATA / slug / "text_anim.json"
    if ap.exists():
        a = load_json(ap)
        roles = {e["id"]: e["role"] for e in d["events"]}
        for x in a["events"]:
            x["role"] = roles.get(x["id"], x.get("role"))
        save_json(ap, a)
