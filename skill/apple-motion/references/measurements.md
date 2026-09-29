# Measurements

Pooled over 6 videos, 1107.1 s, 33187 frames. Generated from fingerprint.json - numbers only. Frames at ~30 fps.

## Distributions (pooled)

| metric | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|
| shot length (frames) | 13.0 | 32.2 | 56.5 | 106.0 | 173.5 (n=406) |
| cuts per 10 s (per video) | 2.24 | 2.47 | 3.24 | 5.13 | 7.44 (n=6) |
| typography events per 10 s (per video) | 0.23 | 0.51 | 0.78 | 0.81 | 0.94 (n=6) |
| cap height (% of frame height) | 3.25 | 5.43 | 6.67 | 11.89 | 20.23 (n=68) |
| stroke / cap height (weight proxy) | 0.137 | 0.149 | 0.161 | 0.171 | 0.191 (n=68) |
| estimated SF Pro weight (calibrated) | 500.0 | 550.0 | 600.0 | 650.0 | 765.0 (n=68) |
| x-height / cap height | 0.738 | 0.754 | 0.784 | 0.96 | 0.989 (n=68) |
| line pitch / cap height | 1.24 | 1.46 | 1.53 | 2.34 | 2.41 (n=11) |
| typography hold (frames) | 10.0 | 16.0 | 33.0 | 57.5 | 80.6 (n=68) |
| typography on screen (frames) | 24.0 | 33.8 | 45.5 | 67.2 | 90.3 (n=68) |
| entry duration, all (frames) | 0.0 | 2.5 | 7.0 | 12.0 | 20.3 (n=68) |
| entry duration, animated only (frames) | 5.0 | 6.0 | 8.0 | 15.5 | 24.0 (n=51) |
| exit duration (frames) | 0.0 | 0.0 | 0.0 | 7.0 | 17.0 (n=68) |
| entry start scale | 0.78 | 0.82 | 0.93 | 1.1 | 1.21 (n=13) |
| entry start y offset (% of height) | -3.93 | 0.51 | 1.95 | 2.96 | 5.47 (n=25) |
| entry start blur (px @1080p) | 4.49 | 6.0 | 10.28 | 41.36 | 49.71 (n=20) |
| hold drift, scale (%/s) | -6.53 | -0.18 | 0.0 | 0.14 | 0.86 (n=66) |
| entry spring damping (good fits) | 4.49 | 10.09 | 18.27 | 37.77 | 97.66 (n=41) |
| entry spring stiffness (good fits) | 14.7 | 77.0 | 162.9 | 406.0 | 2329.3 (n=41) |
| entry spring durationInFrames | 5.0 | 12.0 | 17.0 | 35.0 | 72.0 (n=41) |
| music BPM (per video) | 91.9 | 103.9 | 118.8 | 125.3 | 131.3 (n=6) |
| integrated loudness LUFS (per video) | -20.4 | -18.8 | -17.4 | -16.8 | -16.6 (n=6) |
| true peak dBTP (per video) | -3.9 | -3.4 | -2.0 | -1.5 | -1.0 (n=6) |
| loudness range LU (per video) | 2.8 | 3.2 | 3.4 | 3.9 | 4.2 (n=6) |
| VO words/s while speaking (per video) | 2.67 | 2.81 | 3.04 | 3.28 | 3.43 (n=6) |
| SFX candidates per 10 s (per video) | 1.78 | 2.77 | 4.41 | 6.77 | 8.25 (n=6) |
| cuts on beat +-2 fr (per video) | 0.28 | 0.299 | 0.352 | 0.371 | 0.378 (n=6) |
| chance of on-beat (per video) | 0.256 | 0.289 | 0.33 | 0.348 | 0.365 (n=6) |
| cuts near a word onset +-2 fr | 0.236 | 0.257 | 0.319 | 0.38 | 0.441 (n=6) |
| chance near a word onset | 0.348 | 0.367 | 0.393 | 0.433 | 0.455 (n=6) |
| typography appear - same spoken word (frames) | -16.2 | -10.0 | -2.0 | 13.0 | 27.2 (n=45) |
| UI/graphic element entries per s | 2.3 | 3.36 | 3.54 | 3.84 | 4.75 (n=6) |
| camera zoom rate, push/pull shots (%/s) | 1.1 | 1.82 | 4.54 | 10.24 | 18.29 (n=140) |
| camera pan/tilt rate (% of frame/s) | 0.62 | 1.18 | 2.61 | 6.73 | 12.41 (n=76) |
| first shot (frames) | 53.0 | 83.0 | 130.0 | 202.0 | 232.0 (n=6) |
| last shot (frames) | 12.0 | 27.0 | 94.0 | 195.0 | 280.0 (n=6) |
| montage runs (>=4 shots of <=10 fr) per minute | 0.0 | 0.0 | 0.0 | 0.0 | 0.63 (n=6) |

## Shares (pooled)

- Transitions: cut 92%, whip 5%, scale through 1%, dissolve 1%, mask wipe 1%, match cut 0%
- Typography entry styles: cut on 25%, slide 21%, fade 18%, scale down from large 9%, per-letter 7%, scale up from small 6%, blur in 4%, slide down with mask 3%
- Typography exit styles: cut off 59%, slide out 13%, fade out 10%, blur out 7%, scale out (down) 4%, other 4%
- Appear kind: animated 79%, instant 15%, cut 6%; exit kind: cut 37%, animated 31%, instant 22%
- Animated channels in entries: opacity 34%, dy 19%, blur_px 15%, dx 14%, scale 10%, reveal 7%
- Entry spring (median of good fits): damping 18.27, stiffness 162.9, mass 1, durationInFrames 17.0, zeta 0.78, overshoot 2.06%, n=41
- Calibrated entry spring (pipeline speed bias removed, see calibration): {'damping': 15.35, 'stiffness': 115.0, 'mass': 1, 'durationInFrames': 20} - use damping/stiffness/mass WITHOUT durationInFrames; durationInFrames here is only Remotion's natural settle length (measureSpring), for reference; calibration {"time_scale": 1.19, "zeta_ratio": 1.032, "n": 5, "ratios": [1.171, 1.393, 1.19, 1.347, 1.121], "note": "fitted springs are this much faster than the truth; calibrated = fitted / c (damping), / c^2 (stiffness)"}
- Median shot length by quarter of the video: [71.0, 59.5, 68.8, 73.0] frames; share of typography per quarter: [0.294, 0.25, 0.132, 0.324]
- Cuts on the beat, pooled: {"hits": 134, "cuts": 400, "expected_by_chance": 124.8, "z": 1.0, "p_one_sided": 0.1586}
- Idiomatic form: spring({config: {damping: 14.79}, durationInFrames: 19.0}) (stiffness 100, mass 1)
- Entry cubic-bezier (median control points): [0.205, 0.137, 0.732, 0.802]; nearest named: linear 13, ease-in 8, easeOutExpo 7, easeOutBack 6
- Exit cubic-bezier (median): [0.026, 0.422, 0.943, 0.649]
- Line count: 1 84%, 2 10%, 4 4%, 3 2%; alignment: center 60%, right 19%, left 15%, ragged 6%
- Position (3x3 grid): middle-center 46%, bottom-center 32%, middle-right 10%, middle-left 6%, top-center 3%, bottom-left 2%
- Typography colour (most frequent hex): #080808, #0b0b0b, #0e0e0e, #1a1a1a, #0f0f0f, #0c0c0d
- Background behind typography: solid 63%, image 25%, gradient 12%
- Frame classes (mean share of frames): footage 44%, pure white 21%, ui screenshot 20%, pure black 8%, product 6%, gradient 1%
- Global motion per shot: static 38%, pull 20%, push 16%, tilt 10%, pan 9%, local 5%, whip 3%

## Per video

| video | dur s | shots | median shot fr | cuts/10s | typo/10s | median hold fr | top entry | BPM | LUFS | cuts on beat (chance) |
|---|---|---|---|---|---|---|---|---|---|---|
| ios26-liquid-glass | 273.77 | 68 | 99.5 | 2.45 | 0.04 | 25.0 | blur in | 118.05 | -19.2 | 0.277 (0.328) |
| sept26-event-recap | 95.09 | 90 | 22.5 | 9.36 | 0.42 | 28.0 | cut on | 127.2 | -17.0 | 0.38 (0.354) |
| wwdc22-day1-recap | 179.51 | 72 | 66.0 | 3.96 | 1.06 | 34.0 | cut on | 99.18 | -16.5 | 0.343 (0.276) |
| wwdc23-17things | 135.1 | 35 | 66.0 | 2.52 | 0.81 | 21.0 | cut on | 119.57 | -16.7 | 0.375 (0.332) |
| wwdc25-welcome | 152.09 | 85 | 41.0 | 5.52 | 0.79 | 13.0 | slide | 84.65 | -21.6 | 0.284 (0.235) |
| wwdc26-sotu-recap | 271.5 | 56 | 118.0 | 2.03 | 0.77 | 75.0 | fade | 135.42 | -17.7 | 0.36 (0.376) |

## Typography examples (reviewed)

- ios26-liquid-glass f3321: "Liqjuid Glass" - blur in, entry 27 fr, hold 25 fr, cap 17.19%, #dcdcde on #f5f5f5
- sept26-event-recap f968: "Longest battery life / in iPhone history / iPhone " - cut on, entry 0 fr, hold 52 fr, cap 10.67%, #e5e5e5 on #373737
- sept26-event-recap f1075: "Siri" - cut on, entry 13 fr, hold 3 fr, cap 5.2%, #f5f5f5 on #000000
- sept26-event-recap f1377: "Active Noise / Cancellation" - cut on, entry 17 fr, hold 50 fr, cap 11.93%, #f3f4f5 on #282727
- sept26-event-recap f1676: "Most accurate heart rate / sensing in a wearable" - per-word pop, entry 4 fr, hold 6 fr, cap 9.93%, #cdf3cf on #05400b
- wwdc22-day1-recap f329: "DC" - slide down with mask, entry 10 fr, hold 46 fr, cap 45.61%, #40526a on #030912
- wwdc22-day1-recap f1400: "iCloud Shared / Photo Library" - cut on, entry 0 fr, hold 66 fr, cap 3.29%, #151617 on #dae0e0
- wwdc22-day1-recap f2467: "SM2" - scale up from small, entry 9 fr, hold 35 fr, cap 3.15%, #191918 on #f4f4f4
- wwdc22-day1-recap f2525: "Up to" - scale down from large, entry 7 fr, hold 16 fr, cap 2.26%, #1a1a1a on #e7e7e7
- wwdc22-day1-recap f2511: "18%" - scale down from large, entry 20 fr, hold 16 fr, cap 6.2%, #8b149e on #e7e7e7
- wwdc22-day1-recap f2511: "Faster GPU" - scale down from large, entry 31 fr, hold 3 fr, cap 2.41%, #1a1a1a on #e7e7e7
- wwdc22-day1-recap f2532: "Faster CPU" - scale down from large, entry 5 fr, hold 11 fr, cap 2.41%, #171717 on #e7e7e7
- wwdc22-day1-recap f2898: "Ventura" - fade, entry 5 fr, hold 39 fr, cap 19.99%, #fbf0ec on #f17c20
- wwdc22-day1-recap f2890: "macOS" - blur in, entry 11 fr, hold 41 fr, cap 6.85%, #f9dbcb on #f3861e
- wwdc22-day1-recap f3047: "Stage Manager" - slide, entry 5 fr, hold 21 fr, cap 6.18%, #131516 on #e5e7eb
- wwdc22-day1-recap f4037: "Shared with You API" - cut on, entry 0 fr, hold 34 fr, cap 5.47%, #0f0f0f on #f4f4f4
- wwdc22-day1-recap f4071: "App Intents API" - cut on, entry 0 fr, hold 29 fr, cap 5.58%, #0e0e0e on #f4f4f4
- wwdc23-17things f0: "17 things" - cut on, entry 6 fr, hold 10 fr, cap 14.64%, #080808 on #f5f5f5
- wwdc23-17things f22: "WWDC23 / 17things / 77" - cut on, entry 0 fr, hold 23 fr, cap 10.67%, #0c0c0c on #f5f5f5
- wwdc23-17things f21: "WWDC23" - slide down with mask, entry 5 fr, hold 20 fr, cap 11.12%, #080808 on #f5f5f5
- wwdc23-17things f50: "big & little / WWDC23" - slide up with mask, entry 3 fr, hold 21 fr, cap 11.82%, #0a0a0a on #f5f5f5
- wwdc23-17things f53: "17 things" - swap in place, entry 4 fr, hold 19 fr, cap 14.99%, #090909 on #f5f5f5
- wwdc23-17things f84: "17 things / 17 / big & little / WWDC23" - cut on, entry 1 fr, hold 21 fr, cap 12.27%, #0b0b0b on #f5f5f5
- wwdc23-17things f114: "WWDC23 / things / 17 / big & little" - cut on, entry 0 fr, hold 14 fr, cap 11.88%, #0b0b0b on #f5f5f5
- wwdc23-17things f971: "Journal" - fade, entry 5 fr, hold 43 fr, cap 4.35%, #080808 on #f5f5f5
- wwdc23-17things f2717: "That's so" - per-letter, entry 4 fr, hold 48 fr, cap 5.02%, #0e0e0e on #f5f5f5
- wwdc23-17things f2738: "cool:" - per-letter, entry 17 fr, hold 12 fr, cap 5.74%, #101d2e on #f5f5f5
- wwdc23-17things f2774: "Atocorrect" - cut on, entry 0 fr, hold 24 fr, cap 10.72%, #080808 on #f5f5f5
- wwdc25-welcome f120: "WDC25" - per-letter, entry 18 fr, hold 46 fr, cap 20.78%, #b89ca2 on #000000
- wwdc25-welcome f126: "WDC2S" - per-letter, entry 24 fr, hold 20 fr, cap 20.92%, #bea3a3 on #000000
- wwdc25-welcome f142: "WDC25" - slide, entry 8 fr, hold 32 fr, cap 23.5%, #767d83 on #2a3225
- wwdc25-welcome f534: "Metal 4" - fade, entry 4 fr, hold 10 fr, cap 3.52%, #292a2c on #f2f2f4
- wwdc25-welcome f1268: "W 25" - counter/number roll, entry 12 fr, hold 22 fr, cap 30.23%, #b0928d on #f4f4f6
- wwdc25-welcome f1311: "Platforms State / of the Union" - scale down from large, entry 10 fr, hold 14 fr, cap 9.42%, #8f979c on #f4f4f6
- wwdc25-welcome f1815: "Liqjuid Glass" - slide, entry 8 fr, hold 25 fr, cap 17.03%, #dcdce6 on #efeff4
- wwdc25-welcome f1817: "Liqjuid Olass" - slide, entry 17 fr, hold 11 fr, cap 18.14%, #d6d6e1 on #efeff4
- wwdc25-welcome f1817: "Liqjuid Glass" - slide, entry 21 fr, hold 12 fr, cap 12.48%, #d0d0dc on #efeff4
- wwdc25-welcome f1817: "Liquid Glass" - slide, entry 30 fr, hold 11 fr, cap 18.11%, #cbcad7 on #efeff4
- wwdc25-welcome f4436: "IDC25" - slide, entry 6 fr, hold 7 fr, cap 20.89%, #bca5c7 on #000000
- wwdc25-welcome f4436: "WDC2S" - blur in, entry 36 fr, hold 8 fr, cap 20.89%, #bca0a2 on #000000
- wwdc26-sotu-recap f255: "Apple Intelligence" - slide up with mask, entry 15 fr, hold 75 fr, cap 9.17%, #09090a on #f3f3f5
- wwdc26-sotu-recap f995: "Claude" - slide, entry 8 fr, hold 97 fr, cap 6.48%, #1a1a1b on #f3f3f5
- wwdc26-sotu-recap f998: "Gemini" - slide, entry 8 fr, hold 94 fr, cap 5.6%, #222224 on #f3f3f5
- wwdc26-sotu-recap f1113: "Dynamic Profiles" - scale down from large, entry 33 fr, hold 63 fr, cap 10.5%, #545d60 on #fdfdfd
- wwdc26-sotu-recap f1388: "Core AI" - fade, entry 7 fr, hold 59 fr, cap 5.69%, #080809 on #f3f3f5
- wwdc26-sotu-recap f1723: "App Intents" - fade, entry 7 fr, hold 82 fr, cap 5.61%, #0d0d0d on #f3f3f5
- wwdc26-sotu-recap f1962: "Siri" - fade, entry 7 fr, hold 35 fr, cap 5.3%, #141416 on #f3f3f5
- wwdc26-sotu-recap f3433: "SwiftUl" - fade, entry 7 fr, hold 21 fr, cap 5.74%, #060607 on #f3f3f5
- wwdc26-sotu-recap f4854: "Xcode Cloud" - fade, entry 6 fr, hold 34 fr, cap 5.66%, #0c0c0d on #f3f3f5
- wwdc26-sotu-recap f5124: "Device Hub" - fade, entry 7 fr, hold 80 fr, cap 5.65%, #080808 on #f3f3f5
- wwdc26-sotu-recap f7031: "Xcode" - per-letter, entry 6 fr, hold 6 fr, cap 9.26%, #3e80e7 on #f3f3f5
- wwdc26-sotu-recap f7051: "Xcodeis the best place / tocode with agents" - fade, entry 8 fr, hold 77 fr, cap 9.09%, #0c0c0d on #f3f3f5
