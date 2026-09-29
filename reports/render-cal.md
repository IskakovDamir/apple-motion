# eval: render-cal

Measured with the extraction pipeline; Apple = pooled over 1 videos.

| metric | render | Apple p10 | p50 | p90 | inside |
|---|---|---|---|---|---|
| median shot length (frames) | 60.0 | 5.0 | 22.5 | 75.0 | yes |
| cuts per 10 s | 2.69 | 9.36 | 9.36 | 9.36 | no |
| typography per 10 s | 5.0 | 0.63 | 0.63 | 0.63 | no |
| cap height % (median) | 7.14 | 5.38 | 9.59 | 13.25 | yes |
| stroke / cap (weight) | 0.157 | 0.102 | 0.162 | 0.276 | yes |
| typography hold frames (median) | 57.0 | 0.0 | 28.5 | 46.5 | no |
| entry frames, animated (median) | 3.5 | 6.2 | 19.0 | 35.0 | no |
| entry spring damping | 36.85 | 2.22 | 23.86 | 46.04 | yes |
| entry spring stiffness | 816.0 | 9.38 | 215.1 | 936.72 | yes |
| BPM | 119.03 | 123.0 | 123.0 | 123.0 | no |
| integrated LUFS | -16.3 | -17.0 | -17.0 | -17.0 | no |
| true peak dBTP | -2.0 | -1.8 | -1.8 | -1.8 | no |
| cuts on beat (share) | 1.0 | 0.38 | 0.38 | 0.38 | no |

**5/13 metrics inside Apple's p10-p90 range.**

Entry styles measured: cut on 3, other 1, scale up from small 2, slide down with mask 1, fade 1, scale down from large 1, blur in 1, slide 1, slide up with mask 1, per-word pop 1

## Pipeline calibration (measured vs. ground truth)

| card | text | true appear | measured appear | true entry fr | measured entry fr | true style | measured style | true effective d/k | fitted d/k | idiomatic fit (damping, durationInFrames) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | Weight 400 | 0 | 0 | 0 | 0 | cut | cut on | - | 118.87/5000.0 | 9.27, 2 |
| 1 | Weight 500 | 60 | 75 | 0 | 0 | cut | cut on | - | 120.81/5000.0 | 6.38, 2 |
| 2 | Weight 600 | 120 | 135 | 0 | 0 | cut | cut on | - | 120.81/5000.0 | 6.38, 2 |
| 3 | Weight 700 | 180 | 195 | 0 | 45 | cut | scale up from small | - | 8.42/1.9 | 13.47, 207 |
| 4 | Weight 800 | 240 | 255 | 0 | 45 | cut | slide down with mask | - | 8.42/2.0 | 13.47, 182 |
| 5 | Entry cut | 300 | missed | | | cut | | |
| 6 | Entry fade | 360 | 361 | 8 | 2 | fade | fade | 38/703 | 50.29/964.5 | 14.79, 8 |
| 7 | Entry scaleDown | 420 | 421 | 12 | 3 | scaleDown | scale down from large | 25/312 | 29.42/606.7 | 13.47, 7 |
| 8 | Entry blurIn | 480 | 482 | 12 | 2 | blurIn | blur in | 25/312 | 55.31/1118.8 | 19.57, 5 |
| 9 | Entry slideUp | 540 | 541 | 10 | 3 | slideUp | slide | 30/450 | 36.85/637.7 | 14.79, 9 |
| 10 | Entry slideUpMask | 600 | 602 | 10 | 6 | slideUpMask | slide up with mask | 30/450 | 35.53/816.0 | 11.17, 11 |
| 11 | Every word counts | 660 | 666 | 10 | 3 | perWord | per-word pop | 30/450 | 16.86/107.8 | 19.57, 15 |
| 12 | Entry scaleUp | 720 | 721 | 16 | 4 | scaleUp | scale up from small | 19/176 | 21.77/220.8 | 14.79, 14 |

Appear-frame error: median +2.0 fr, max |err| 15 fr (n=12).
