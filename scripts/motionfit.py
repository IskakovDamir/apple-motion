"""Fitting helpers: exact port of Remotion's spring() and a cubic-bezier easing fitter.

Remotion (packages/core/src/spring): the spring is advanced frame by frame with the closed-form
solution of a damped oscillator. With zeta = damping / (2*sqrt(stiffness*mass)):
  zeta <  1  under-damped closed form
  zeta >= 1  Remotion uses the *critically damped* closed form with omega0 = sqrt(k/m), i.e.
             damping above 2*sqrt(k*m) has no further effect in Remotion.
durationInFrames stretches time so that the natural settle duration (measureSpring, threshold
0.005, must stay settled for 20 frames) maps onto durationInFrames.
"""
import numpy as np
from scipy.optimize import least_squares


def _advance(cur, vel, to, dt_ms, damping, stiffness, mass):
    c, m, k = damping, mass, stiffness
    v0 = -vel
    x0 = to - cur
    zeta = c / (2 * np.sqrt(k * m))
    omega0 = np.sqrt(k / m)
    t = dt_ms / 1000
    if zeta < 1:
        omega1 = omega0 * np.sqrt(1 - zeta ** 2)
        sin1, cos1 = np.sin(omega1 * t), np.cos(omega1 * t)
        env = np.exp(-zeta * omega0 * t)
        frag1 = env * (sin1 * ((v0 + zeta * omega0 * x0) / omega1) + x0 * cos1)
        pos = to - frag1
        speed = zeta * omega0 * frag1 - env * (cos1 * (v0 + zeta * omega0 * x0) - omega1 * x0 * sin1)
    else:
        env = np.exp(-omega0 * t)
        pos = to - env * (x0 + (v0 + omega0 * x0) * t)
        speed = env * (v0 * (t * omega0 - 1) + t * x0 * omega0 * omega0)
    return pos, speed


def spring_calc(frame, fps, damping=10, stiffness=100, mass=1, velocity=0.0):
    """Remotion springCalculation: from 0 to 1."""
    cur, vel, last = 0.0, velocity, 0.0
    frame = max(0.0, float(frame))
    uneven = frame % 1
    for f in range(0, int(np.floor(frame)) + 1):
        ff = f + uneven if f == int(np.floor(frame)) else f
        now = ff / fps * 1000
        cur, vel = _advance(cur, vel, 1.0, min(now - last, 64), damping, stiffness, mass)
        last = now
    return cur


def spring_curve(frames, fps, damping, stiffness, mass=1.0):
    """Vectorised closed form (identical to stepping, see test_spring_port)."""
    t = np.maximum(0, np.asarray(frames, np.float64)) / fps
    zeta = damping / (2 * np.sqrt(stiffness * mass))
    w0 = np.sqrt(stiffness / mass)
    if zeta < 1:
        w1 = w0 * np.sqrt(1 - zeta ** 2)
        return 1 - np.exp(-zeta * w0 * t) * (np.cos(w1 * t) + (zeta * w0 / w1) * np.sin(w1 * t))
    return 1 - np.exp(-w0 * t) * (1 + w0 * t)


from functools import lru_cache


@lru_cache(maxsize=4096)
def _measure_spring_cached(fps, damping, stiffness, mass, threshold):
    f = np.arange(0, 3000, dtype=np.float64)
    diff = np.abs(spring_curve(f, fps, damping, stiffness, mass) - 1)
    idx = np.nonzero(diff >= threshold)[0]
    return int(idx.max() + 1) if len(idx) else 0


def measure_spring(fps, damping, stiffness, mass=1.0, threshold=0.005):
    """Remotion measureSpring: frames until the spring stays within threshold
    (vectorised: one past the last frame whose distance to the target is >= threshold)."""
    return _measure_spring_cached(float(fps), round(float(damping), 4), round(float(stiffness), 4),
                                  round(float(mass), 4), float(threshold))


def _measure_spring_loop(fps, damping, stiffness, mass=1.0, threshold=0.005):
    """Literal port of Remotion's loop, kept for the equivalence test."""
    frame = 0
    diff = lambda f: abs(spring_curve([f], fps, damping, stiffness, mass)[0] - 1)
    while diff(frame) >= threshold:
        frame += 1
    finished = frame
    i = 0
    while i < 20:
        frame += 1
        if diff(frame) >= threshold:
            i = 0
            finished = frame + 1
        else:
            i += 1
    return finished


def spring_with_duration(frames, fps, damping, stiffness, mass, duration):
    nat = measure_spring(fps, damping, stiffness, mass)
    f = np.asarray(frames, np.float64) / (duration / nat)
    out = spring_curve(f, fps, damping, stiffness, mass)
    out[np.asarray(frames) > duration] = 1.0
    return out


def test_spring_port():
    for d, k, m in [(10, 100, 1), (200, 100, 1), (26, 170, 1), (8, 300, 0.6), (15, 80, 2)]:
        a = np.array([spring_calc(f, 30, d, k, m) for f in range(0, 40)])
        b = spring_curve(np.arange(40), 30, d, k, m)
        assert np.max(np.abs(a - b)) < 1e-9, (d, k, m, np.max(np.abs(a - b)))
        assert abs(measure_spring(30, d, k, m) - _measure_spring_loop(30, d, k, m)) <= 1
    return True


DAMP_GRID = np.geomspace(3, 80, 36)
STIFF_GRID = np.geomspace(15, 1500, 44)
OFFSETS = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])


def fit_spring(frames_rel, p, fps):
    """Fit Remotion spring (mass fixed at 1) to progress p(frames_rel). frames_rel = frame - appear.
    Returns config, time offset, rmse, overshoot, natural durationInFrames."""
    frames_rel = np.asarray(frames_rel, np.float64)
    p = np.asarray(p, np.float64)
    best = (np.inf, None)
    for d in DAMP_GRID:
        for k in STIFF_GRID:
            zeta = d / (2 * np.sqrt(k))
            if zeta > 1.6:     # beyond critical Remotion is identical to critical; skip redundant grid
                continue
            for o in OFFSETS:
                y = spring_curve(frames_rel - o, fps, d, k)
                e = float(np.mean((y - p) ** 2))
                if e < best[0]:
                    best = (e, (d, k, o))
    d, k, o = best[1]

    def res(x):
        return spring_curve(frames_rel - x[2], fps, x[0], x[1]) - p
    try:
        r = least_squares(res, [d, k, o], bounds=([0.5, 1, -2], [400, 5000, 2]))
        d, k, o = r.x
    except Exception:
        pass
    y = spring_curve(frames_rel - o, fps, d, k)
    rmse = float(np.sqrt(np.mean((y - p) ** 2)))
    zeta = d / (2 * np.sqrt(k))
    dense = spring_curve(np.linspace(0, 120, 1201), fps, d, k)
    return {"damping": round(float(d), 2), "stiffness": round(float(k), 1), "mass": 1,
            "durationInFrames": int(measure_spring(fps, d, k)),
            "time_offset_frames": round(float(o), 2), "zeta": round(float(zeta), 3),
            "overshoot_pct": round(float(max(0, dense.max() - 1) * 100), 2),
            "rmse": round(rmse, 4), "n_points": int(len(p))}


def fit_spring_duration(frames_rel, p, fps, duration):
    """Idiomatic Remotion: spring({config: {damping}, durationInFrames}) with stiffness 100, mass 1.
    durationInFrames is fitted too (the visible settle is much shorter than Remotion's 0.5% settle)."""
    frames_rel = np.asarray(frames_rel, np.float64)
    best = (np.inf, None)
    durs = sorted(set(int(x) for x in np.unique(np.round(np.geomspace(max(2, duration), max(6, 5 * duration + 10), 14)))))
    for D in durs:
        for d in np.geomspace(4, 60, 30):
            for o in OFFSETS:
                y = spring_with_duration(frames_rel - o, fps, d, 100, 1, D)
                e = float(np.mean((y - p) ** 2))
                if e < best[0]:
                    best = (e, (d, o, D))
    d, o, D = best[1]
    return {"damping": round(float(d), 2), "stiffness": 100, "mass": 1, "durationInFrames": int(D),
            "time_offset_frames": round(float(o), 2), "rmse": round(float(np.sqrt(best[0])), 4)}


def effective_spring(damping, stiffness, mass, duration, fps):
    """Remotion spring stretched by durationInFrames == an unstretched spring with time scaled by
    c = natural/duration: stiffness * c^2, damping * c (zeta unchanged)."""
    c = measure_spring(fps, damping, stiffness, mass) / duration
    return damping * c, stiffness * c * c


def bezier_y_of_x(x, x1, y1, x2, y2):
    """Cubic bezier easing (CSS/Remotion Easing.bezier): y for given x in [0,1]."""
    x = np.clip(np.asarray(x, np.float64), 0, 1)
    t = x.copy()
    for _ in range(12):
        bx = 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t ** 2 * x2 + t ** 3
        dx = 3 * (1 - t) ** 2 * x1 + 6 * (1 - t) * t * (x2 - x1) + 3 * t ** 2 * (1 - x2)
        step = np.where(np.abs(dx) > 1e-6, (bx - x) / np.where(np.abs(dx) > 1e-6, dx, 1), 0)
        t = np.clip(t - step, 0, 1)
    return 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t ** 2 * y2 + t ** 3


NAMED = {
    "linear": (0, 0, 1, 1), "ease": (0.25, 0.1, 0.25, 1), "ease-in": (0.42, 0, 1, 1),
    "ease-out": (0, 0, 0.58, 1), "ease-in-out": (0.42, 0, 0.58, 1),
    "easeOutCubic": (0.33, 1, 0.68, 1), "easeOutQuart": (0.25, 1, 0.5, 1), "easeOutQuint": (0.22, 1, 0.36, 1),
    "easeOutExpo": (0.16, 1, 0.3, 1), "easeOutCirc": (0, 0.55, 0.45, 1), "easeInOutCubic": (0.65, 0, 0.35, 1),
    "easeInOutQuart": (0.76, 0, 0.24, 1), "easeInOutExpo": (0.87, 0, 0.13, 1), "easeOutBack": (0.34, 1.56, 0.64, 1),
    "easeInCubic": (0.32, 0, 0.67, 0), "easeInExpo": (0.7, 0, 0.84, 0),
}


def fit_bezier(xn, p):
    """xn = normalised time 0..1, p = progress. Returns best cubic-bezier + nearest named curve."""
    xn = np.asarray(xn, np.float64)
    p = np.asarray(p, np.float64)

    def res(c):
        return bezier_y_of_x(xn, *c) - p
    best = None
    for start in list(NAMED.values()):
        try:
            r = least_squares(res, start, bounds=([0, -1, 0, -1], [1, 2.5, 1, 2.5]))
            e = float(np.sqrt(np.mean(r.fun ** 2)))
            if best is None or e < best[0]:
                best = (e, r.x)
        except Exception:
            continue
    e, c = best
    named = min(NAMED, key=lambda n: float(np.sqrt(np.mean((bezier_y_of_x(xn, *NAMED[n]) - p) ** 2))))
    ne = float(np.sqrt(np.mean((bezier_y_of_x(xn, *NAMED[named]) - p) ** 2)))
    return {"bezier": [round(float(v), 3) for v in c], "rmse": round(e, 4),
            "nearest_named": named, "nearest_named_bezier": list(NAMED[named]), "nearest_named_rmse": round(ne, 4)}
