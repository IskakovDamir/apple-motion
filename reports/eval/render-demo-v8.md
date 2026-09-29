# eval: render-demo-v8

Measured with the extraction pipeline; Apple = pooled over 6 videos.

| metric | render | Apple p10 | p50 | p90 | inside |
|---|---|---|---|---|---|
| median shot length (frames) | 33.0 | 13.0 | 56.5 | 173.5 | yes |
| cuts per 10 s | 5.87 | 2.24 | 3.24 | 7.44 | yes |
| typography per 10 s | 1.87 | 0.23 | 0.78 | 0.94 | no |
| cap height % (median) | 6.54 | 3.25 | 6.67 | 20.23 | yes |
| stroke / cap (weight) | 0.168 | 0.137 | 0.161 | 0.191 | yes |
| typography hold frames (median) | 51.0 | 10.0 | 33.0 | 80.6 | yes |
| entry frames, animated (median) | 5.5 | 5.0 | 8.0 | 24.0 | yes |
| entry spring damping | 65.67 | 4.49 | 18.27 | 97.66 | yes |
| entry spring stiffness | 1587.65 | 14.7 | 162.9 | 2329.3 | yes |
| BPM | 119.44 | 91.9 | 118.8 | 131.3 | yes |
| integrated LUFS | -17.4 | -20.4 | -17.4 | -16.6 | yes |
| true peak dBTP | -2.2 | -3.9 | -2.0 | -1.0 | yes |
| static shot share | 0.739 | 0.095 | 0.366 | 0.608 | no |
| push/pull shot share | 0.13 | 0.242 | 0.349 | 0.507 | no |
| cuts on beat (share; Apple's VO-led edits sit at chance level - informational) | 0.864 | 0.28 | 0.352 | 0.378 | - |

**11/14 metrics inside Apple's p10-p90 range.**

Entry styles measured: cut on 1, scale up from small 1, counter/number roll 1, slide 1, per-letter 1, per-word pop 1, blur in 1

## Pipeline calibration (measured vs. ground truth)

| card | text | true appear | measured appear | true entry fr | measured entry fr | true style | measured style | true effective d/k | fitted d/k | idiomatic fit (damping, durationInFrames) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Six Apple recaps. | 90 | 90 | 0 | 0 | cut | cut on | - | 118.87/5000.0 | 9.27, 2 |
| 3 | 33187 / frames, one by one | 210 | 213 | 4 | 6 | counter | counter/number roll | 76/2875 | 87.49/1335.6 | 19.57, 7 |
| 9 | Every cut. / Every word. | 540 | 549 | 8 | 10 | slideUpMask | per-letter | 38/719 | 11.4/95.2 | 12.27, 30 |
| 12 | Type is the accent. | 720 | 730 | 8 | 7 | perWord | per-word pop | 38/719 | 135.36/4580.6 | 12.27, 7 |
| 21 | apple-motion | 960 | 962 | 8 | 3 | scaleDown | slide | 38/719 | 2.89/32.2 | 11.17, 25 |

Appear-frame error: median +3.0 fr, max |err| 10 fr (n=5).
