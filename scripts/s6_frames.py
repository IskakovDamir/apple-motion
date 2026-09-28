#!/usr/bin/env python3
"""STEP 6: frames + contact sheets -> data/<slug>/frames/, data/<slug>/contact_sheets/

frames/shots/shotNNN_{first,mid,last}_fFFFFF.png   full-res first/middle/last frame of every shot
frames/entries/eNNN_filmstrip.png                   every frame of every text entry (appear-1 .. full+1)
                                                    in one labelled filmstrip (crop of the event region padded
                                                    to 16:9, 480 px per frame, 8 frames per row) - one file per
                                                    event instead of one per frame (the USB drive drops out
                                                    under bursts of small-file writes)
contact_sheets/sheet_NN_<kind>.png                  4x4 tiles, 1600 px wide, each tile labelled
                                                    "f<frame> s<shot>" (+ event id); max 12 sheets
contact_sheets/index.json                           what is on each sheet + every subsampling decision
Sheets: up to 3 'shots' sheets (middle frame per shot) then 'entries' sheets (8 tiles per event,
two events per sheet), typography events first, round-robin across entry styles.
"""
import sys
from collections import defaultdict

import cv2
import numpy as np

from common import DATA, iter_frames, load_json, meta, read_shots, save_json, shot_of

TW, TH = 400, 225
MAX_SHEETS = 12
HEADER = 36


def crop169(img, box, W, H, pad=0.35):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    w, h = w * (1 + 2 * pad), h * (1 + 2 * pad)
    if w / h < 16 / 9:
        w = h * 16 / 9
    else:
        h = w * 9 / 16
    w, h = min(w, W), min(h, H)
    x0 = int(np.clip(cx - w / 2, 0, W - w)); y0 = int(np.clip(cy - h / 2, 0, H - h))
    return img[y0:y0 + int(h), x0:x0 + int(w)]


def tile(img, label, sub=None):
    t = cv2.resize(img, (TW, TH), interpolation=cv2.INTER_AREA)
    cv2.rectangle(t, (0, TH - 26), (TW, TH), (0, 0, 0), -1)
    cv2.putText(t, label, (6, TH - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    if sub:
        cv2.rectangle(t, (0, 0), (TW, 22), (0, 0, 0), -1)
        cv2.putText(t, sub[:48], (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA)
    return t


def sheet(tiles, title):
    canvas = np.zeros((HEADER + 4 * TH, 4 * TW, 3), np.uint8)
    cv2.putText(canvas, title[:120], (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
    for i, t in enumerate(tiles[:16]):
        r, c = divmod(i, 4)
        canvas[HEADER + r * TH:HEADER + (r + 1) * TH, c * TW:(c + 1) * TW] = t
    return canvas


def write_strip(path, frames, e, shots):
    per_row = 8
    rows = int(np.ceil(len(frames) / per_row))
    canvas = np.zeros((rows * 270 + 30, per_row * 480, 3), np.uint8)
    cv2.putText(canvas, f"e{e['id']} '{e['text'][:60]}' appear {e['appear_frame']} full {e['full_frame']}",
                (8, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    for i, (f, im) in enumerate(frames):
        r, c = divmod(i, per_row)
        t = im.copy()
        cv2.rectangle(t, (0, 244), (480, 270), (0, 0, 0), -1)
        cv2.putText(t, f"f{f} s{shot_of(f, shots)}", (6, 263), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
        canvas[30 + r * 270:30 + (r + 1) * 270, c * 480:(c + 1) * 480] = t
    cv2.imwrite(str(path), canvas)


def evenly(seq, k):
    if len(seq) <= k:
        return list(seq)
    idx = np.linspace(0, len(seq) - 1, k).round().astype(int)
    return [seq[i] for i in idx]


def run(slug):
    m = meta(slug)
    W, H = m["width"], m["height"]
    shots = read_shots(slug)
    te = load_json(DATA / slug / "text_events.json")["events"]
    ta = {a["id"]: a for a in load_json(DATA / slug / "text_anim.json")["events"]} \
        if (DATA / slug / "text_anim.json").exists() else {}
    fd = DATA / slug / "frames"
    (fd / "shots").mkdir(parents=True, exist_ok=True)
    (fd / "entries").mkdir(parents=True, exist_ok=True)
    csd = DATA / slug / "contact_sheets"
    csd.mkdir(exist_ok=True)
    for old in csd.glob("sheet_*.png"):
        old.unlink()

    log = {"subsampling": []}
    # ---- plan shot sheets
    mids = [((s["start_frame"] + s["end_frame"]) // 2, s["index"]) for s in shots]
    shot_sheets = min(3, int(np.ceil(len(mids) / 16)))
    shot_pick = evenly(mids, shot_sheets * 16)
    if len(shot_pick) < len(mids):
        log["subsampling"].append(f"shots: {len(mids)} shots -> {len(shot_pick)} tiles (evenly spaced middle frames)")
    # ---- plan entry sheets
    ent_slots = (MAX_SHEETS - shot_sheets) * 2
    cand = [e for e in te if e["entry_frames"] >= 2]
    typo = [e for e in cand if e.get("role") == "typography"]
    rest = [e for e in cand if e.get("role") != "typography"]
    by_style = defaultdict(list)
    for e in sorted(typo, key=lambda e: -e["entry_frames"]):
        by_style[ta.get(e["id"], {}).get("entry_style", "?")].append(e)
    order = []
    while any(by_style.values()):
        for k in list(by_style):
            if by_style[k]:
                order.append(by_style[k].pop(0))
    order += sorted(rest, key=lambda e: -e["entry_frames"])
    ent_pick = order[:ent_slots]
    if len(order) > ent_slots:
        log["subsampling"].append(f"entries: {len(order)} animated entries -> {len(ent_pick)} on sheets "
                                  f"(typography first, round-robin over entry styles, longest first)")
    # frames needed
    need = defaultdict(list)
    for s in shots:
        mid = (s["start_frame"] + s["end_frame"]) // 2
        for tag, f in (("first", s["start_frame"]), ("mid", mid), ("last", s["end_frame"])):
            need[f].append(("shot", s["index"], tag))
    for e in te:
        for f in range(max(0, e["appear_frame"] - 1), e["full_frame"] + 2):
            need[f].append(("entry", e["id"], None))
    ent_frames = {}
    for e in ent_pick:
        fr = list(range(max(0, e["appear_frame"] - 1), e["full_frame"] + 2))
        pick = evenly(fr, 8)
        if len(pick) < len(fr):
            log["subsampling"].append(f"event {e['id']}: entry frames {fr[0]}-{fr[-1]} ({len(fr)}) -> 8 tiles {pick}")
        ent_frames[e["id"]] = set(pick)
    ev_by_id = {e["id"]: e for e in te}
    shot_tiles = {}
    ent_tiles = defaultdict(dict)
    shot_pick_set = {f for f, _ in shot_pick}
    n_png = 0
    strips = defaultdict(list)
    for f, img in iter_frames(slug, min(need), max(need) + 1):
        if f not in need:
            continue
        for kind, idx, tag in need[f]:
            if kind == "shot":
                cv2.imwrite(str(fd / "shots" / f"shot{idx:03d}_{tag}_f{f:06d}.png"), img)
                n_png += 1
                if tag == "mid" and f in shot_pick_set:
                    shot_tiles[f] = tile(img, f"f{f} s{idx}")
            else:
                e = ev_by_id[idx]
                b = e["bbox_ref"]
                box = (b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"])
                c = crop169(img, box, W, H)
                strips[idx].append((f, cv2.resize(c, (480, 270), interpolation=cv2.INTER_AREA)))
                if f == e["full_frame"] + 1 or f == max(need):
                    write_strip(fd / "entries" / f"e{idx:03d}_filmstrip.png", strips.pop(idx), e, shots)
                    n_png += 1
                if idx in ent_frames and f in ent_frames[idx]:
                    style = ta.get(idx, {}).get("entry_style", "")
                    ent_tiles[idx][f] = tile(c, f"f{f} s{shot_of(f, shots)} e{idx}", f"{e['text'][:28]} | {style}")
    sheets = []
    tl = [shot_tiles[f] for f, _ in shot_pick if f in shot_tiles]
    for i in range(0, len(tl), 16):
        sheets.append(("shots", tl[i:i + 16], [f for f, _ in shot_pick][i:i + 16]))
    pairs = [ent_pick[i:i + 2] for i in range(0, len(ent_pick), 2)]
    for pr in pairs:
        tiles, ids = [], []
        for e in pr:
            ts = [ent_tiles[e["id"]][f] for f in sorted(ent_tiles[e["id"]])]
            ts += [np.zeros((TH, TW, 3), np.uint8)] * (8 - len(ts))
            tiles += ts[:8]
            ids.append(e["id"])
        sheets.append(("entries", tiles, ids))
    sheets = sheets[:MAX_SHEETS]
    index = []
    for i, (kind, tiles, what) in enumerate(sheets):
        name = f"sheet_{i + 1:02d}_{kind}.png"
        title = f"{slug} | {kind} | " + (f"shot middle frames" if kind == "shots" else
                                         " + ".join(f"e{j}: {ev_by_id[j]['text'][:30]}" for j in what))
        cv2.imwrite(str(csd / name), sheet(tiles, title))
        index.append({"file": name, "kind": kind, "items": what})
    save_json(csd / "index.json", {"sheets": index, "tile": [TW, TH], "grid": [4, 4], **log})
    print(f"[{slug}] {n_png} pngs, {len(index)} contact sheets", flush=True)


if __name__ == "__main__":
    for s in sys.argv[1:]:
        run(s)
