"""Per-frame pixel measurement of a text block against its settled reference.

Everything is measured on an "ink" map alpha in [0,1]: how text-coloured each pixel is,
given the settled text colour and the local background colour (alpha = 1 on glyphs,
0 on background). From alpha per frame:
  mass     sum(alpha) / settled sum              -> presence
  centroid (dx, dy) vs settled                   -> offset
  scale    sqrt(sx*sy / sx_ref*sy_ref) of alpha's second moments
  opacity  mass / scale^2 (mass of a scaled glyph grows with area)
  blur     Gaussian sigma (px @1080p) from the Dirichlet energy sum|grad alpha|^2,
           calibrated per event by blurring the settled glyphs (energy is scale-invariant)
  reveal   visible ink height / expected height; clip edge fixed across frames = mask
  ncc      normalised cross-correlation of the frame with the settled template at the
           measured scale/offset (1 = identical glyph shapes)
"""
import cv2
import numpy as np

SIGMAS = np.array([0, 0.5, 1, 1.5, 2, 3, 4, 6, 8, 12, 16, 24, 32], np.float32)


def kmeans2(pixels):
    """Two colour clusters (BGR float32). Returns centers, labels."""
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 0.5)
    _, labels, centers = cv2.kmeans(pixels.astype(np.float32), 2, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    return centers, labels.ravel()


def settle_colors(crop, box, ring=6):
    """Text and background colour of a settled crop. box = (x0,y0,x1,y1) inside crop."""
    x0, y0, x1, y1 = box
    inner = crop[y0:y1, x0:x1].reshape(-1, 3)
    centers, labels = kmeans2(inner)
    # background = cluster that dominates a ring just outside the box
    H, W = crop.shape[:2]
    rx0, ry0, rx1, ry1 = max(0, x0 - ring), max(0, y0 - ring), min(W, x1 + ring), min(H, y1 + ring)
    ringpix = np.concatenate([crop[ry0:y0, rx0:rx1].reshape(-1, 3), crop[y1:ry1, rx0:rx1].reshape(-1, 3),
                              crop[ry0:ry1, rx0:x0].reshape(-1, 3), crop[ry0:ry1, x1:rx1].reshape(-1, 3)])
    if len(ringpix) == 0:
        ringpix = inner
    d = [np.linalg.norm(ringpix - c, axis=1).mean() for c in centers]
    bg_i = int(np.argmin(d))
    bg, txt = centers[bg_i], centers[1 - bg_i]
    ring_med = np.median(ringpix, axis=0)
    ring_std = float(ringpix.std(axis=0).mean())
    return txt, bg, ring_med, ring_std


def alpha_map(crop, txt, bg):
    """Per-pixel text-likeness: projection of (pixel - bg) onto (txt - bg)."""
    v = (txt - bg).astype(np.float32)
    den = float((v * v).sum()) + 1e-6
    a = ((crop.astype(np.float32) - bg) @ v) / den
    return np.clip(a, 0, 1)


def moments(a):
    m = float(a.sum())
    if m < 1e-3:
        return m, np.nan, np.nan, np.nan, np.nan
    H, W = a.shape
    ys = np.arange(H, dtype=np.float32)
    xs = np.arange(W, dtype=np.float32)
    px = a.sum(0)
    py = a.sum(1)
    cx = float((px * xs).sum() / m)
    cy = float((py * ys).sum() / m)
    sx = float(np.sqrt(max(1e-6, (px * (xs - cx) ** 2).sum() / m)))
    sy = float(np.sqrt(max(1e-6, (py * (ys - cy) ** 2).sum() / m)))
    return m, cx, cy, sx, sy


def dirichlet(a):
    gx = cv2.Sobel(a, cv2.CV_32F, 1, 0, ksize=3) / 8
    gy = cv2.Sobel(a, cv2.CV_32F, 0, 1, ksize=3) / 8
    return float((gx * gx + gy * gy).sum())


def blur_calibration(a_ref):
    """Dirichlet energy of the settled glyphs blurred by SIGMAS (per unit mass)."""
    out = []
    m = a_ref.sum() + 1e-6
    for s in SIGMAS:
        b = a_ref if s == 0 else cv2.GaussianBlur(a_ref, (0, 0), float(s))
        out.append(dirichlet(b) / m)
    return np.array(out)


def sigma_from_energy(e_per_mass, calib):
    """Invert the monotone-decreasing calibration curve."""
    c = calib
    if e_per_mass >= c[0]:
        return 0.0
    if e_per_mass <= c[-1]:
        return float(SIGMAS[-1])
    # c decreasing: interpolate on reversed arrays
    return float(np.interp(e_per_mass, c[::-1], SIGMAS[::-1]))


def ink_bbox(a, thr=0.35):
    ys, xs = np.where(a > thr)
    if len(xs) < 4:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def ncc_at(frame_gray, tmpl_gray, scale, cx, cy):
    """NCC between frame and template scaled by `scale`, centred at (cx, cy); small local search."""
    if not np.isfinite(scale) or scale < 0.15 or scale > 6 or not np.isfinite(cx):
        return np.nan
    th, tw = tmpl_gray.shape
    nw, nh = max(4, int(round(tw * scale))), max(4, int(round(th * scale)))
    t = cv2.resize(tmpl_gray, (nw, nh), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)
    H, W = frame_gray.shape
    pad = max(3, int(0.05 * nh))
    x0 = int(round(cx - nw / 2)) - pad
    y0 = int(round(cy - nh / 2)) - pad
    x1, y1 = x0 + nw + 2 * pad, y0 + nh + 2 * pad
    if x0 < 0 or y0 < 0 or x1 > W or y1 > H:
        # clip template region to frame
        ox0, oy0 = max(0, x0), max(0, y0)
        ox1, oy1 = min(W, x1), min(H, y1)
        if ox1 - ox0 < nw or oy1 - oy0 < nh:
            return np.nan
        x0, y0, x1, y1 = ox0, oy0, ox1, oy1
    if t.std() < 1e-3:
        return np.nan
    r = cv2.matchTemplate(frame_gray[y0:y1, x0:x1], t, cv2.TM_CCOEFF_NORMED)
    return float(r.max())


def split_units(mask, axis_gap):
    """Split a binary glyph mask into column runs separated by gaps >= axis_gap px (words)."""
    col = mask.any(0)
    runs, start, gap = [], None, 0
    for x, v in enumerate(col):
        if v:
            if start is None:
                start = x
            gap = 0
            last = x
        else:
            if start is not None:
                gap += 1
                if gap >= axis_gap:
                    runs.append((start, last + 1))
                    start, gap = None, 0
    if start is not None:
        runs.append((start, last + 1))
    return runs


def letter_units(mask):
    """Column runs separated by any empty column (approximate letters/glyph clusters)."""
    return split_units(mask, 1)


def line_rows(mask, min_gap):
    row = mask.any(1)
    runs, start, gap = [], None, 0
    for y, v in enumerate(row):
        if v:
            if start is None:
                start = y
            gap = 0
            last = y
        else:
            if start is not None:
                gap += 1
                if gap >= min_gap:
                    runs.append((start, last + 1))
                    start, gap = None, 0
    if start is not None:
        runs.append((start, last + 1))
    return runs


def cap_height(mask):
    """Baseline minus cap/ascender line from connected components of one text line."""
    n, lab, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    if n <= 1:
        return None, None
    hs = stats[1:, cv2.CC_STAT_HEIGHT]
    keep = stats[1:][(hs > 0.4 * hs.max()) & (stats[1:, cv2.CC_STAT_AREA] > 4)]
    if len(keep) == 0:
        return None, None
    tops = keep[:, cv2.CC_STAT_TOP]
    bottoms = keep[:, cv2.CC_STAT_TOP] + keep[:, cv2.CC_STAT_HEIGHT]
    base = float(np.percentile(bottoms, 50))
    top = float(np.percentile(tops, 10))
    xh_top = float(np.percentile(tops, 60))
    return base - top, base - xh_top


# ---------------------------------------------------------------------------------------------
# Template tracker on text-likeness (alpha) maps: robust to moving footage behind the text.
# ---------------------------------------------------------------------------------------------
BLUR_GRID = np.array([0, 0.75, 1.5, 2.5, 4, 6, 9, 13, 18, 25], np.float32)


def _ncc(a, b):
    a = a - a.mean()
    b = b - b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d > 1e-9 else np.nan


class TextTracker:
    """Tracks a settled text template through frames of a fixed search region.

    Pose (scale, centre) comes from NCC template search on text-likeness (alpha) maps.
    Photometrics are measured only on the glyphs and a thin ring around them, at the tracked pose,
    so moving footage further away cannot leak in:
      opacity  (core colour - ring colour) projected on (settled text colour - ring colour)
      blur     sigma whose blurred template best matches the frame inside a glyph-hugging mask
      reveal   share of glyph rows whose local gain is present (mask wipes / clipped slides)
    """

    def __init__(self, a_ref, box, txt_bgr, units=(), letters=()):
        x0, y0, x1, y1 = box
        m = max(2, int(0.15 * (y1 - y0)))
        H, W = a_ref.shape
        self.bx = (max(0, x0 - m), max(0, y0 - m), min(W, x1 + m), min(H, y1 + m))
        bx = self.bx
        self.T = a_ref[bx[1]:bx[3], bx[0]:bx[2]].astype(np.float32)
        self.txt = np.asarray(txt_bgr, np.float32)
        glyph = (self.T > 0.5).astype(np.uint8)
        core = cv2.erode(glyph, np.ones((3, 3), np.uint8))
        self.glyph = glyph
        self.core = core if core.sum() >= 20 else glyph
        d1 = cv2.dilate(glyph, np.ones((3, 3), np.uint8))
        d3 = cv2.dilate(glyph, np.ones((9, 9), np.uint8))
        self.ring = (d3 > 0) & ~(d1 > 0)
        self.center_ref = ((bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2)
        self.units = [(r0 - bx[1], r1 - bx[1], c0 - bx[0], c1 - bx[0]) for (r0, r1, c0, c1) in units]
        self.letters = [(r0 - bx[1], r1 - bx[1], c0 - bx[0], c1 - bx[0]) for (r0, r1, c0, c1) in letters]
        self.ink_rows = self.T.max(1) > 0.5
        self.cache = {}
        self.mcache = {}

    def _tmpl(self, s):
        key = round(float(s), 3)
        if key not in self.cache:
            h, w = self.T.shape
            nw, nh = max(3, int(round(w * s))), max(3, int(round(h * s)))
            self.cache[key] = cv2.resize(self.T, (nw, nh), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
        return self.cache[key]

    def _masks(self, s):
        key = round(float(s), 3)
        if key not in self.mcache:
            th, tw = self._tmpl(s).shape
            rs = lambda mk: cv2.resize(mk.astype(np.uint8), (tw, th), interpolation=cv2.INTER_NEAREST) > 0
            self.mcache[key] = (rs(self.glyph), rs(self.core), rs(self.ring))
        return self.mcache[key]

    def _match(self, A, s):
        t = self._tmpl(s)
        if t.shape[0] >= A.shape[0] or t.shape[1] >= A.shape[1] or t.std() < 1e-4:
            return -1.0, None
        r = cv2.matchTemplate(A, t, cv2.TM_CCOEFF_NORMED)
        _, mx, _, loc = cv2.minMaxLoc(r)
        return float(mx), loc

    def track(self, A, crop_bgr, s_prior=None, units=True):
        if s_prior is None or not np.isfinite(s_prior):
            scales = np.geomspace(0.35, 3.0, 17)
        else:
            scales = s_prior * np.array([0.84, 0.9, 0.95, 1.0, 1.05, 1.11, 1.19])
        scales = scales[(scales > 0.2) & (scales < 4.0)]
        res = [(self._match(A, s), s) for s in scales]
        (best, loc), s = max(res, key=lambda r: r[0][0])
        if loc is None:
            return None
        for fs in (0.975, 1.025):
            (v, l), ss = self._match(A, s * fs), s * fs
            if v > best:
                best, loc, s = v, l, ss
        t = self._tmpl(s)
        th, tw = t.shape
        gm, cm, rm = self._masks(s)
        P = A[loc[1]:loc[1] + th, loc[0]:loc[0] + tw]
        Pc = crop_bgr[loc[1]:loc[1] + th, loc[0]:loc[0] + tw].astype(np.float32)
        # opacity from glyph cores vs the local ring, in colour
        opacity = np.nan
        if cm.any() and rm.any():
            core_c = np.median(Pc[cm], axis=0)
            ring_c = np.median(Pc[rm], axis=0)
            v = self.txt - ring_c
            den = float((v * v).sum())
            if den > 400:  # >= 20 levels of contrast between text and local background
                opacity = float(np.dot(core_c - ring_c, v) / den)
        # blur: masked NCC against blurred templates, mask hugs the glyphs (grows with sigma)
        best_b = (-2.0, 0.0)
        for sg in BLUR_GRID:
            tb = t if sg == 0 else cv2.GaussianBlur(t, (0, 0), float(sg))
            r = int(2 + 1.5 * sg)
            mk = cv2.dilate(gm.astype(np.uint8), np.ones((2 * r + 1, 2 * r + 1), np.uint8)) > 0
            if mk.sum() < 20:
                continue
            c = _ncc(P[mk], tb[mk])
            if np.isfinite(c) and c > best_b[0]:
                best_b = (c, float(sg))
        c, sg = best_b
        # reveal: row-wise presence of glyph cores (alpha) against the template rows
        rows_vis = rows_ink = 0
        clip_top = clip_bottom = False
        tr = cv2.resize(self.ink_rows.astype(np.float32)[:, None], (1, th), interpolation=cv2.INTER_NEAREST).ravel() > 0.5
        ink_idx = np.where(tr)[0]
        if len(ink_idx):
            row_vis = []
            for y in ink_idx:
                g = gm[y]
                row_vis.append(bool(g.any() and P[y][g].mean() > 0.35 * max(0.05, min(1.0, opacity if np.isfinite(opacity) else 1.0))))
            row_vis = np.array(row_vis)
            rows_ink = len(ink_idx)
            rows_vis = int(row_vis.sum())
            if 0 < rows_vis < rows_ink:
                fv, lv = ink_idx[row_vis][0], ink_idx[row_vis][-1]
                clip_top = fv > ink_idx[0] + 0.1 * rows_ink
                clip_bottom = lv < ink_idx[-1] - 0.1 * rows_ink
        cx = loc[0] + tw / 2
        cy = loc[1] + th / 2
        unit_g = [self._unit_gain(A, t, s, loc, *u) for u in self.units] if units else []
        let_g = [self._unit_gain(A, t, s, loc, *u) for u in self.letters] if units and len(self.letters) <= 40 else None
        return {"scale": float(s), "cx": float(cx), "cy": float(cy), "ncc": float(best), "ncc_blur": float(c),
                "blur": sg, "opacity": opacity, "reveal": rows_vis / rows_ink if rows_ink else np.nan,
                "clip": "top" if clip_top else ("bottom" if clip_bottom else None),
                "unit_gain": unit_g, "letter_gain": let_g}

    def _unit_gain(self, A, t, s, loc, r0, r1, c0, c1):
        """Presence of one word/letter near its settled place relative to the block pose
        (+-0.6 unit height vertically, +-0.3 width horizontally for independent motion)."""
        rr0, rr1, cc0, cc1 = [int(round(v * s)) for v in (r0, r1, c0, c1)]
        sub = t[max(0, rr0):rr1, max(0, cc0):cc1]
        if sub.size < 9 or sub.std() < 1e-4:
            return np.nan
        hh = rr1 - rr0
        ww = cc1 - cc0
        y0 = max(0, loc[1] + rr0 - int(0.6 * hh)); y1 = min(A.shape[0], loc[1] + rr1 + int(0.6 * hh))
        x0 = max(0, loc[0] + cc0 - int(0.3 * ww)); x1 = min(A.shape[1], loc[0] + cc1 + int(0.3 * ww))
        R = A[y0:y1, x0:x1]
        if R.shape[0] <= sub.shape[0] or R.shape[1] <= sub.shape[1]:
            return np.nan
        r = cv2.matchTemplate(R, sub, cv2.TM_CCOEFF_NORMED)
        _, mx, _, l = cv2.minMaxLoc(r)
        P = R[l[1]:l[1] + sub.shape[0], l[0]:l[0] + sub.shape[1]]
        tv = sub - sub.mean()
        g = float(((P - P.mean()) * tv).sum() / ((tv * tv).sum() + 1e-9))
        return g * float(np.clip(mx / 0.5, 0, 1))
