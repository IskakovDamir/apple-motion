# eval: render-vo-demo

Measured with the extraction pipeline; Apple = pooled over 6 videos.

| metric | render | Apple p10 | p50 | p90 | inside |
|---|---|---|---|---|---|
| median shot length (frames) | 69.5 | 13.0 | 56.5 | 173.5 | yes |
| cuts per 10 s | 3.67 | 2.24 | 3.24 | 7.44 | yes |
| typography per 10 s | 4.2 | 0.23 | 0.78 | 0.94 | no |
| cap height % (median) | 5.05 | 3.25 | 6.67 | 20.23 | yes |
| stroke / cap (weight) | 0.163 | 0.137 | 0.161 | 0.191 | yes |
| typography hold frames (median) | 38.5 | 10.0 | 33.0 | 80.6 | yes |
| entry frames, animated (median) | 5.0 | 5.0 | 8.0 | 24.0 | yes |
| entry spring damping | 38.35 | 4.49 | 18.27 | 97.66 | yes |
| entry spring stiffness | 803.55 | 14.7 | 162.9 | 2329.3 | yes |
| BPM | 126.06 | 91.9 | 118.8 | 131.3 | yes |
| integrated LUFS | -17.3 | -20.4 | -17.4 | -16.6 | yes |
| true peak dBTP | -5.1 | -3.9 | -2.0 | -1.0 | no |
| cuts on beat (share; Apple's VO-led edits sit at chance level - informational) | 0.429 | 0.28 | 0.352 | 0.378 | - |

**10/12 metrics inside Apple's p10-p90 range.**

Entry styles measured: slide down with mask 1, cut on 2, fade 1, slide 3, scale down from large 1

## Pipeline calibration (measured vs. ground truth)

| card | text | true appear | measured appear | true entry fr | measured entry fr | true style | measured style | true effective d/k | fitted d/k | idiomatic fit (damping, durationInFrames) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Northwind Notes 3 | 63 | 63 | 0 | 0 | cut | cut on | - | 118.87/5000.0 | 9.27, 2 |
| 3 | Smart search | 222 | 223 | 0 | 6 | fade | fade | - | 19.09/142.1 | 16.23, 19 |
| 4 | reciept | 249 | 259 | 0 | 5 | cut | slide | - | 31.54/304.9 | 16.23, 14 |
| 5 | 2x / faster to open | 322 | 326 | 0 | 5 | cut | scale down from large | - | 45.16/4610.7 | 4.0, 6 |
| 7 | Northwind Notes 3. | 437 | 437 | 0 | 0 | cut | cut on | - | 119.09/5000.0 | 9.27, 2 |

Appear-frame error: median +1.0 fr, max |err| 10 fr (n=5).
