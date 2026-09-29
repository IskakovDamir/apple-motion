# Measurements

Pooled over 4 videos, 561.8 s, 16837 frames. Generated from fingerprint.json - numbers only. Frames at ~30 fps.

## Distributions (pooled)

| metric | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|
| shot length (frames) | 7.0 | 26.0 | 41.0 | 71.8 | 120.7 (n=282) |
| cuts per 10 s (per video) | 2.95 | 3.6 | 4.74 | 6.48 | 8.21 (n=4) |
| typography events per 10 s (per video) | 0.53 | 0.7 | 0.8 | 0.89 | 1.02 (n=4) |
| cap height (% of frame height) | 3.42 | 5.6 | 9.42 | 14.82 | 20.89 (n=47) |
| stroke / cap height (weight proxy) | 0.137 | 0.146 | 0.159 | 0.172 | 0.205 (n=47) |
| estimated SF Pro weight (calibrated) | 500.0 | 550.0 | 600.0 | 675.0 | 800.0 (n=47) |
| x-height / cap height | 0.739 | 0.752 | 0.8 | 0.98 | 0.989 (n=47) |
| line pitch / cap height | 1.12 | 1.45 | 1.57 | 2.36 | 2.41 (n=10) |
| typography hold (frames) | 3.0 | 11.5 | 20.0 | 34.5 | 48.8 (n=47) |
| typography on screen (frames) | 25.8 | 36.0 | 44.0 | 63.5 | 72.0 (n=47) |
| entry duration, all (frames) | 0.6 | 4.0 | 8.0 | 18.0 | 29.4 (n=47) |
| entry duration, animated only (frames) | 4.0 | 6.0 | 8.0 | 21.0 | 30.0 (n=41) |
| exit duration (frames) | 0.0 | 0.0 | 5.0 | 17.5 | 30.2 (n=47) |
| entry start scale | 0.77 | 0.91 | 0.94 | 1.05 | 1.1 (n=16) |
| entry start y offset (% of height) | -4.78 | -1.44 | 1.64 | 2.84 | 3.88 (n=22) |
| entry start blur (px @1080p) | 5.7 | 8.13 | 14.38 | 38.44 | 45.28 (n=18) |
| hold drift, scale (%/s) | -23.59 | -0.28 | -0.0 | 0.26 | 1.56 (n=40) |
| entry spring damping (good fits) | 2.84 | 5.82 | 17.83 | 55.22 | 118.91 (n=31) |
| entry spring stiffness (good fits) | 11.5 | 23.55 | 141.5 | 694.6 | 2299.1 (n=31) |
| entry spring durationInFrames | 5.0 | 9.0 | 21.0 | 56.0 | 113.0 (n=31) |
| music BPM (per video) | 89.0 | 95.5 | 109.4 | 121.5 | 124.9 (n=4) |
| integrated loudness LUFS (per video) | -20.2 | -18.1 | -16.9 | -16.6 | -16.6 (n=4) |
| true peak dBTP (per video) | -3.5 | -2.6 | -2.0 | -1.7 | -1.5 (n=4) |
| loudness range LU (per video) | 2.7 | 3.1 | 3.8 | 4.1 | 4.2 (n=4) |
| VO words/s while speaking (per video) | 2.64 | 2.71 | 3.05 | 3.39 | 3.46 (n=4) |
| SFX candidates per 10 s (per video) | 2.87 | 3.86 | 4.41 | 5.21 | 6.62 (n=4) |
| cuts on beat +-2 fr (per video) | 0.302 | 0.328 | 0.359 | 0.376 | 0.379 (n=4) |
| chance of on-beat (per video) | 0.247 | 0.266 | 0.304 | 0.338 | 0.347 (n=4) |
| cuts near a word onset +-2 fr | 0.257 | 0.262 | 0.324 | 0.411 | 0.465 (n=4) |
| chance near a word onset | 0.343 | 0.354 | 0.38 | 0.415 | 0.445 (n=4) |
| typography appear - same spoken word (frames) | -18.5 | -9.2 | -0.5 | 10.2 | 33.0 (n=30) |
| UI/graphic element entries per s | 3.37 | 3.47 | 3.54 | 3.65 | 3.82 (n=4) |
| first shot (frames) | 43.0 | 65.0 | 118.0 | 174.0 | 200.0 (n=4) |
| last shot (frames) | 12.0 | 28.0 | 124.0 | 245.0 | 308.0 (n=4) |
| montage runs (>=4 shots of <=10 fr) per minute | 0.0 | 0.0 | 0.0 | 0.32 | 0.88 (n=4) |

## Shares (pooled)

- Transitions: cut 91%, whip 6%, mask wipe 1%, match cut 1%, dissolve 0%, scale through 0%
- Typography entry styles: slide 17%, fade 15%, cut on 13%, blur in 11%, scale up from small 8%, per-letter 8%, slide up with mask 6%, other 4%
- Typography exit styles: cut off 34%, fade out 23%, slide out 17%, scale out (down) 15%, other 4%, blur out 4%
- Appear kind: animated 85%, cut 11%, instant 4%; exit kind: animated 43%, animated_then_cut 26%, cut 26%
- Animated channels in entries: opacity 29%, dy 18%, dx 15%, blur_px 14%, scale 13%, reveal 11%
- Entry spring (median of good fits): damping 17.83, stiffness 141.5, mass 1, durationInFrames 21.0, zeta 0.81, overshoot 1.21%, n=31
- Calibrated entry spring (pipeline speed bias removed, see calibration): {'damping': 14.98, 'stiffness': 99.9, 'mass': 1, 'durationInFrames': 22}; calibration {"time_scale": 1.19, "zeta_ratio": 1.032, "n": 5, "ratios": [1.171, 1.393, 1.19, 1.347, 1.121], "note": "fitted springs are this much faster than the truth; calibrated = fitted / c (damping), / c^2 (stiffness)"}
- Median shot length by quarter of the video: [57.5, 45.5, 41.5, 46.5] frames; share of typography per quarter: [0.277, 0.34, 0.149, 0.234]
- Cuts on the beat, pooled: {"hits": 95, "cuts": 278, "expected_by_chance": 82.1, "z": 1.7, "p_one_sided": 0.0444}
- Idiomatic form: spring({config: {damping: 17.88}, durationInFrames: 10.0}) (stiffness 100, mass 1)
- Entry cubic-bezier (median control points): [0.362, 0.374, 0.521, 0.731]; nearest named: linear 8, ease-in 6, easeOutExpo 5, easeInExpo 4
- Exit cubic-bezier (median): [0.51, 0.199, 0.575, 0.329]
- Line count: 1 79%, 2 13%, 4 6%, 3 2%; alignment: center 64%, right 17%, left 11%, ragged 8%
- Position (3x3 grid): middle-center 49%, bottom-center 36%, middle-right 6%, top-center 4%, bottom-left 2%, bottom-right 2%
- Typography colour (most frequent hex): #080808, #0e0e0e, #0f0f0f, #0a0a0a, #090909, #0b0b0b
- Background behind typography: solid 57%, image 28%, gradient 15%
- Frame classes (mean share of frames): footage 42%, pure white 22%, ui screenshot 16%, pure black 11%, product 8%, gradient 2%
- Global motion per shot: static 42%, pull 18%, push 16%, tilt 10%, local 7%, pan 4%, whip 2%

## Per video

| video | dur s | shots | median shot fr | cuts/10s | typo/10s | median hold fr | top entry | BPM | LUFS | cuts on beat (chance) |
|---|---|---|---|---|---|---|---|---|---|---|
| sept26-event-recap | 95.09 | 90 | 22.5 | 9.36 | 0.42 | 26.5 | fade | 127.2 | -17.0 | 0.38 (0.354) |
| wwdc22-day1-recap | 179.51 | 72 | 66.0 | 3.96 | 1.11 | 29.5 | cut on | 99.18 | -16.5 | 0.343 (0.276) |
| wwdc23-17things | 135.1 | 35 | 66.0 | 2.52 | 0.81 | 20.0 | slide down with mask | 119.57 | -16.7 | 0.375 (0.332) |
| wwdc25-welcome | 152.09 | 85 | 41.0 | 5.52 | 0.79 | 9.5 | slide | 84.65 | -21.6 | 0.284 (0.235) |

## Typography examples (reviewed)

- sept26-event-recap f968: "Longest battery life / in iPhone history / iPhone " - fade, entry 0 fr, hold 52 fr, cap 10.67%, #e5e5e5 on #373737
- sept26-event-recap f1075: "Siri" - other, entry 10 fr, hold 3 fr, cap 5.2%, #f5f5f5 on #000000
- sept26-event-recap f1377: "Active Noise / Cancellation" - counter/number roll, entry 17 fr, hold 50 fr, cap 11.93%, #f3f4f5 on #282727
- sept26-event-recap f1646: "Most accurate heart rate / sensing in a wearable" - scale up from small, entry 34 fr, hold 1 fr, cap 9.93%, #cdf3cf on #05400b
- wwdc22-day1-recap f324: "DC" - scale up from small, entry 15 fr, hold 46 fr, cap 45.61%, #40526a on #030912
- wwdc22-day1-recap f1400: "iCloud Shared / Photo Library" - cut on, entry 0 fr, hold 66 fr, cap 3.28%, #141517 on #dae0e0
- wwdc22-day1-recap f2468: "SM2" - scale up from small, entry 8 fr, hold 35 fr, cap 3.24%, #1f201f on #f4f4f4
- wwdc22-day1-recap f2522: "Up to" - blur in, entry 9 fr, hold 16 fr, cap 2.35%, #141414 on #e7e7e7
- wwdc22-day1-recap f2511: "18%" - scale down from large, entry 15 fr, hold 10 fr, cap 7.13%, #8c14a0 on #e7e7e7
- wwdc22-day1-recap f2511: "35%" - cut on, entry 1 fr, hold 17 fr, cap 7.65%, #8b15a3 on #e7e7e7
- wwdc22-day1-recap f2528: "Faster GPU" - slide up with mask, entry 7 fr, hold 12 fr, cap 2.5%, #181818 on #e7e7e7
- wwdc22-day1-recap f2526: "Faster CPU" - scale up from small, entry 7 fr, hold 13 fr, cap 2.59%, #151515 on #e7e7e7
- wwdc22-day1-recap f2898: "Ventura" - fade, entry 8 fr, hold 36 fr, cap 20.08%, #fbf1ee on #f17b20
- wwdc22-day1-recap f2890: "macOS" - blur in, entry 22 fr, hold 30 fr, cap 6.85%, #fae9df on #f3891e
- wwdc22-day1-recap f3047: "Stage Manager" - fade, entry 5 fr, hold 21 fr, cap 6.16%, #131516 on #e5e7eb
- wwdc22-day1-recap f4037: "Shared with You API" - cut on, entry 0 fr, hold 34 fr, cap 5.47%, #0f0f0f on #f4f4f4
- wwdc23-17things f0: "17 things" - other, entry 4 fr, hold 12 fr, cap 14.64%, #080808 on #f5f5f5
- wwdc23-17things f18: "WWDC23 / 17things / 77" - slide down with mask, entry 4 fr, hold 23 fr, cap 10.67%, #0c0c0c on #f5f5f5
- wwdc23-17things f0: "WWDC23" - slide up with mask, entry 26 fr, hold 20 fr, cap 11.12%, #080808 on #f5f5f5
- wwdc23-17things f21: "big & little / WWDC23" - slide up with mask, entry 32 fr, hold 21 fr, cap 11.82%, #0a0a0a on #f5f5f5
- wwdc23-17things f49: "17 things" - slide down with mask, entry 8 fr, hold 20 fr, cap 14.99%, #090909 on #f5f5f5
- wwdc23-17things f82: "17 things / 17 / big & little / WWDC23" - swap in place, entry 3 fr, hold 13 fr, cap 12.27%, #0b0b0b on #f5f5f5
- wwdc23-17things f112: "WWDC23 / things / 17 / big & little" - swap in place, entry 2 fr, hold 18 fr, cap 11.88%, #0b0b0b on #f5f5f5
- wwdc23-17things f971: "Journal" - fade, entry 5 fr, hold 43 fr, cap 4.35%, #080808 on #f5f5f5
- wwdc23-17things f2717: "That's so" - per-letter, entry 4 fr, hold 48 fr, cap 5.02%, #0e0e0e on #f5f5f5
- wwdc23-17things f2738: "cool:" - per-letter, entry 17 fr, hold 12 fr, cap 5.74%, #101d2e on #f5f5f5
- wwdc23-17things f2774: "Atocorrect" - cut on, entry 0 fr, hold 24 fr, cap 10.72%, #080808 on #f5f5f5
- wwdc25-welcome f112: "WDC25" - per-letter, entry 29 fr, hold 1 fr, cap 20.78%, #b89ca2 on #000000
- wwdc25-welcome f120: "WDC2S" - per-letter, entry 30 fr, hold 20 fr, cap 20.92%, #bea3a3 on #000000
- wwdc25-welcome f142: "WDC25" - slide, entry 26 fr, hold 14 fr, cap 23.5%, #767d83 on #2a3225
- wwdc25-welcome f534: "Metal 4" - fade, entry 5 fr, hold 9 fr, cap 3.52%, #292a2c on #f2f2f4
- wwdc25-welcome f1268: "W 25" - counter/number roll, entry 8 fr, hold 4 fr, cap 30.23%, #b0928d on #f4f4f6
- wwdc25-welcome f1311: "Platforms State / of the Union" - scale down from large, entry 7 fr, hold 2 fr, cap 9.42%, #8f979c on #f4f4f6
- wwdc25-welcome f1815: "Liqjuid Glass" - slide, entry 8 fr, hold 22 fr, cap 17.03%, #dcdce6 on #efeff4
- wwdc25-welcome f1817: "Liqjuid Olass" - slide, entry 17 fr, hold 11 fr, cap 18.14%, #d6d6e1 on #efeff4
- wwdc25-welcome f1817: "Liqjuid Glass" - slide, entry 21 fr, hold 12 fr, cap 12.48%, #d0d0dc on #efeff4
- wwdc25-welcome f1817: "Liquid Glass" - blur in, entry 31 fr, hold 10 fr, cap 18.11%, #cbcad7 on #efeff4
- wwdc25-welcome f4436: "IDC25" - slide, entry 6 fr, hold 7 fr, cap 20.89%, #bca5c7 on #000000
- wwdc25-welcome f4436: "WDC2S" - blur in, entry 35 fr, hold 1 fr, cap 20.89%, #bca0a2 on #000000
