# eval: render-cal-ocr

Measured with the extraction pipeline; Apple = pooled over 4 videos.

| metric | render | Apple p10 | p50 | p90 | inside |
|---|---|---|---|---|---|
| median shot length (frames) | 60.0 | 7.0 | 41.0 | 120.7 | yes |
| cuts per 10 s | 2.69 | 2.95 | 4.74 | 8.21 | no |
| typography per 10 s | 5.0 | 0.53 | 0.8 | 1.02 | no |
| cap height % (median) | 7.13 | 3.42 | 9.42 | 20.89 | yes |
| stroke / cap (weight) | 0.159 | 0.137 | 0.159 | 0.205 | yes |
| typography hold frames (median) | 57.0 | 3.0 | 20.0 | 48.8 | no |
| entry frames, animated (median) | 3.0 | 4.0 | 8.0 | 30.0 | no |
| entry spring damping | 42.09 | 2.84 | 17.83 | 118.91 | yes |
| entry spring stiffness | 912.9 | 11.5 | 141.5 | 2299.1 | yes |
| BPM | 119.03 | 89.0 | 109.4 | 124.9 | yes |
| integrated LUFS | -16.3 | -20.2 | -16.9 | -16.6 | no |
| true peak dBTP | -2.0 | -3.5 | -2.0 | -1.5 | yes |
| cuts on beat (share) | 1.0 | 0.302 | 0.359 | 0.379 | no |

**7/13 metrics inside Apple's p10-p90 range.**

Entry styles measured: cut on 4, scale up from small 2, blur in 2, fade 1, scale down from large 1, slide 1, slide up with mask 1, per-word pop 1

## Pipeline calibration (measured vs. ground truth)

| card | text | true appear | measured appear | true entry fr | measured entry fr | true style | measured style | true effective d/k | fitted d/k | idiomatic fit (damping, durationInFrames) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | Weight 400 | 0 | 0 | 0 | 0 | cut | cut on | - | 118.87/5000.0 | 9.27, 2 |
| 1 | Weight 500 | 60 | 75 | 0 | 0 | cut | cut on | - | 120.81/5000.0 | 6.38, 2 |
| 2 | Weight 600 | 120 | 135 | 0 | 0 | cut | cut on | - | 119.09/5000.0 | 9.27, 2 |
| 3 | Weight 700 | 180 | 195 | 0 | 45 | cut | scale up from small | - | 8.42/1.9 | 13.47, 207 |
| 4 | Weight 800 | 240 | 255 | 0 | 45 | cut | blur in | - | 8.42/2.1 | 13.47, 182 |
| 5 | Entry cut | 300 | missed | | | cut | | |
| 6 | Entry fade | 360 | 361 | 8 | 2 | fade | fade | 38/703 | 50.53/971.4 | 14.79, 8 |
| 7 | Entry scaleDown | 420 | 421 | 12 | 3 | scaleDown | scale down from large | 25/312 | 47.24/981.2 | 14.79, 8 |
| 8 | Entry blurIn | 480 | 482 | 12 | 2 | blurIn | blur in | 25/312 | 64.17/1343.9 | 21.48, 5 |
| 9 | Entry slideUp | 540 | 541 | 10 | 3 | slideUp | slide | 30/450 | 35.87/652.1 | 13.47, 9 |
| 10 | Entry slideUpMask | 600 | 602 | 10 | 3 | slideUpMask | slide up with mask | 30/450 | 36.95/854.4 | 12.27, 11 |
| 11 | Every word counts | 660 | 666 | 10 | 3 | perWord | per-word pop | 30/450 | 10.7/122.8 | 10.18, 25 |
| 12 | Entry scaleUp | 720 | 721 | 16 | 3 | scaleUp | scale up from small | 19/176 | 27.98/296.6 | 17.82, 8 |

Appear-frame error: median +2.0 fr, max |err| 15 fr (n=12).
