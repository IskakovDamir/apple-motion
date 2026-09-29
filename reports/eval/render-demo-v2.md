# eval: render-demo-v2

Measured with the extraction pipeline; Apple = pooled over 6 videos.

| metric | render | Apple p10 | p50 | p90 | inside |
|---|---|---|---|---|---|
| median shot length (frames) | 59.0 | 13.0 | 56.5 | 173.5 | yes |
| cuts per 10 s | 4.53 | 2.24 | 3.24 | 7.44 | yes |
| typography per 10 s | 8.0 | 0.23 | 0.78 | 0.94 | no |
| cap height % (median) | 6.01 | 3.25 | 6.67 | 20.23 | yes |
| stroke / cap (weight) | 0.17 | 0.137 | 0.161 | 0.191 | yes |
| typography hold frames (median) | 27.5 | 5.4 | 28.5 | 80.6 | yes |
| entry frames, animated (median) | 2.0 | 5.0 | 8.0 | 31.6 | no |
| entry spring damping | 62.24 | 4.39 | 16.66 | 76.63 | yes |
| entry spring stiffness | 851.45 | 14.72 | 116.3 | 1267.36 | yes |
| BPM | 119.43 | 91.9 | 118.8 | 131.3 | yes |
| integrated LUFS | -16.1 | -20.4 | -17.4 | -16.6 | no |
| true peak dBTP | -0.1 | -3.9 | -2.0 | -1.0 | no |
| cuts on beat (share; Apple's VO-led edits sit at chance level - informational) | 0.941 | 0.28 | 0.352 | 0.378 | - |

**8/12 metrics inside Apple's p10-p90 range.**

Entry styles measured: scale up from small 9, cut on 12, fade 3, blur in 3, per-letter 1, scale down from large 1, per-word pop 1

## Pipeline calibration (measured vs. ground truth)

| card | text | true appear | measured appear | true entry fr | measured entry fr | true style | measured style | true effective d/k | fitted d/k | idiomatic fit (damping, durationInFrames) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Measured. | 120 | 120 | 0 | 0 | cut | cut on | - | 118.87/5000.0 | 9.27, 2 |
| 2 | Kinetic type | 150 | 151 | 8 | 2 | fade | fade | 42/739 | 48.07/847.9 | 16.23, 8 |
| 3 | Beat grid | 180 | 180 | 8 | 3 | fade | blur in | 42/739 | 119.17/5000.0 | 5.81, 3 |
| 4 | Springs | 210 | 210 | 8 | 3 | fade | blur in | 42/739 | 119.17/5000.0 | 5.81, 3 |
| 5 | 33187 / frames, one by one | 240 | missed | | | counter | | |
| 7 | Every cut. / Every word. | 360 | 366 | 8 | 1 | slideUpMask | cut on | 42/739 | 69.75/3891.7 | 4.0, 5 |
| 9 | Type does the talking. | 480 | 484 | 8 | 5 | perWord | blur in | 42/739 | 86.29/1861.7 | 21.48, 5 |
| 15 | Transitions | 660 | 661 | 8 | 2 | fade | fade | 42/739 | 47.93/844.3 | 16.23, 8 |
| 16 | Loudness | 690 | 690 | 8 | 3 | fade | scale down from large | 42/739 | 123.49/5000.0 | 10.18, 3 |
| 17 | Type is the accent. | 720 | 728 | 8 | 5 | perWord | per-word pop | 42/739 | 31.69/311.0 | 14.79, 19 |
| 18 | Pace. | 840 | 840 | 0 | 0 | cut | cut on | - | 82.38/5000.0 | 9.27, 2 |
| 19 | Type. | 855 | 855 | 0 | 0 | cut | cut on | - | 118.87/5000.0 | 9.27, 2 |
| 20 | Springs. | 870 | 870 | 0 | 0 | cut | cut on | - | 118.87/5000.0 | 9.27, 2 |
| 21 | Cuts. | 885 | 885 | 0 | 0 | cut | cut on | - | 118.87/5000.0 | 9.27, 2 |
| 22 | Beats. | 900 | 900 | 0 | 0 | cut | cut on | - | 118.87/5000.0 | 9.27, 2 |
| 23 | Words. | 915 | 915 | 0 | 0 | cut | cut on | - | 118.87/5000.0 | 9.27, 2 |
| 24 | Loudness. | 930 | 930 | 0 | 0 | cut | cut on | - | 118.87/5000.0 | 9.27, 2 |
| 25 | Measured. | 945 | 945 | 0 | 0 | cut | cut on | - | 118.87/5000.0 | 9.27, 2 |
| 26 | apple-motion | 960 | 961 | 8 | 2 | scaleDown | scale up from small | 42/739 | 82.38/5000.0 | 9.27, 2 |

Appear-frame error: median +0.0 fr, max |err| 8 fr (n=18).
