#!/usr/bin/env python3
"""Write reviewed role labels for a slug from event ids seen on the review sheets.
Usage: label.py SLUG --typography 47,51 --caption 28,30   (stores frame+position, not ids)"""
import argparse
import json

from common import DATA, ROOT, load_json

ap = argparse.ArgumentParser()
ap.add_argument("slug")
ap.add_argument("--typography", default="")
ap.add_argument("--caption", default="")
a = ap.parse_args()
ev = {e["id"]: e for e in load_json(DATA / a.slug / "text_events.json")["events"]}
out = {"slug": a.slug, "reviewer": "visual review of data/<slug>/review/*.png",
       "rule": "typography = designer-set type over the picture; caption = small overlay pills/labels; "
               "everything else (UI screens, products, player timecodes, legal) is not labelled"}
for role in ("typography", "caption"):
    ids = [int(x) for x in getattr(a, role).split(",") if x.strip()]
    out[role] = []
    for i in ids:
        e = ev[i]
        b = e["bbox_ref"]
        out[role].append({"id_at_review": i, "text": e["text"], "ref_frame": e["ref_frame"],
                          "cx": round(b["x"] + b["w"] / 2), "cy": round(b["y"] + b["h"] / 2)})
p = ROOT / "reference" / "labels" / f"{a.slug}.json"
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(out, indent=1))
print(f"{p}: " + ", ".join(f"{r} {len(out[r])}" for r in ("typography", "caption")))
