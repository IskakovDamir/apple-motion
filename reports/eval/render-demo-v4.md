# eval: render-demo-v4

Measured with the extraction pipeline; Apple = pooled over 6 videos.

| metric | render | Apple p10 | p50 | p90 | inside |
|---|---|---|---|---|---|
| median shot length (frames) | 33.0 | 13.0 | 56.5 | 173.5 | yes |
| cuts per 10 s | 5.87 | 2.24 | 3.24 | 7.44 | yes |
| typography per 10 s | 1.87 | 0.23 | 0.78 | 0.94 | no |
| cap height % (median) | 6.54 | 3.25 | 6.67 | 20.23 | yes |
| stroke / cap (weight) | 0.168 | 0.137 | 0.161 | 0.191 | yes |
| typography hold frames (median) | 51.0 | 5.4 | 28.5 | 80.6 | yes |
| entry frames, animated (median) | 5.0 | 5.0 | 8.0 | 31.6 | yes |
| entry spring damping | 65.69 | 4.39 | 16.66 | 76.63 | yes |
| entry spring stiffness | 1350.0 | 14.72 | 116.3 | 1267.36 | no |
| BPM | 119.43 | 91.9 | 118.8 | 131.3 | yes |
| integrated LUFS | -17.4 | -20.4 | -17.4 | -16.6 | yes |
| true peak dBTP | -3.0 | -3.9 | -2.0 | -1.0 | yes |
| cuts on beat (share; Apple's VO-led edits sit at chance level - informational) | 0.818 | 0.28 | 0.352 | 0.378 | - |

**10/12 metrics inside Apple's p10-p90 range.**

Entry styles measured: cut on 2, scale up from small 1, slide 1, per-letter 1, per-word pop 1, blur in 1

## Pipeline calibration (measured vs. ground truth)

| card | text | true appear | measured appear | true entry fr | measured entry fr | true style | measured style | true effective d/k | fitted d/k | idiomatic fit (damping, durationInFrames) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Six Apple recaps. | 90 | 90 | 0 | 0 | cut | cut on | - | 118.87/5000.0 | 9.27, 2 |
| 3 | 33187 / frames, one by one | 210 | 214 | 4 | 5 | counter | slide | 84/2956 | 86.27/1860.6 | 21.48, 5 |
| 9 | Every cut. / Every word. | 540 | 547 | 8 | 8 | slideUpMask | per-letter | 42/739 | 11.63/80.0 | 13.47, 25 |
| 12 | Type is the accent. | 720 | 730 | 8 | 7 | perWord | per-word pop | 42/739 | 3.84/19.4 | 13.47, 45 |
| 21 | apple-motion | 960 | 961 | 8 | 2 | scaleDown | slide | 42/739 | 8.33/109.1 | 13.47, 20 |

Appear-frame error: median +4.0 fr, max |err| 10 fr (n=5).
