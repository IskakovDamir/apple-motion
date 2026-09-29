# apple-motion extraction report

6 videos, 1107.1 s, 33187 frames. All numbers measured by `scripts/` (see README). 'text' = every tracked text block (UI, products, chrome, legal included); 'typo' = reviewed designer typography only. 'On beat' = within +-2 frames of a tracked beat; chance = 5 / beat period.

| video | fps | dur s | shots | median shot fr | BPM | text ev /10s | typo /10s | median hold fr text / typo | most common typo entry | median entry spring d/k/m (n) | cuts on beat (chance) | text / typo on beat | LUFS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ios26-liquid-glass | 29.97 | 273.77 | 68 | 99.5 | 118.05 | 24.03 | 0.04 | 8.0 / 28.0 | blur in | 37.36/732.8/1 (1) | 0.277 (0.328) | 0.351 / 1.0 | -19.2 |
| sept26-event-recap | 29.97 | 95.09 | 90 | 22.5 | 127.2 | 30.39 | 0.42 | 10.0 / 26.5 | cut on | None/None/1 (0) | 0.38 (0.354) | 0.328 / 0.25 | -17.0 |
| wwdc22-day1-recap | 29.97 | 179.51 | 72 | 66.0 | 99.18 | 30.97 | 1.06 | 22.0 / 34.0 | scale up from small | 8.5/33.6/1 (11) | 0.343 (0.276) | 0.268 / 0.421 | -16.5 |
| wwdc23-17things | 29.97 | 135.1 | 35 | 66.0 | 119.57 | 20.36 | 0.81 | 15.0 / 20.0 | cut on | 41.49/409.5/1 (7) | 0.375 (0.332) | 0.207 / 0.75 | -16.7 |
| wwdc25-welcome | 29.97 | 152.09 | 85 | 41.0 | 84.65 | 19.53 | 0.79 | 14.0 / 9.5 | slide | 5.21/14.8/1 (7) | 0.284 (0.235) | 0.333 / 0.167 | -21.6 |
| wwdc26-sotu-recap | 30.0 | 271.5 | 56 | 118.0 | 135.42 | 7.99 | 0.77 | 69.0 / 75.0 | fade | 28.92/201.7/1 (17) | 0.36 (0.376) | 0.363 / 0.333 | -17.7 |

Pooled cuts on beat: 134/400 vs 124.8 expected by chance (z=1.0, p=0.1586).
Spring-fit calibration (known springs rendered and measured back): fitted springs are 1.19x too fast (n=5, damping ratio preserved x1.032); calibrated pooled entry spring: {'damping': 14.0, 'stiffness': 82.1, 'mass': 1, 'durationInFrames': 24}.
Font weight calibration (stroke/cap of SF Pro Display rendered at known weights): [(0.109, 400), (0.138, 500), (0.159, 600), (0.177, 700), (0.197, 800)].

## Storage

- Project size (du -sh /Volumes/Transcend/dev/apple-motion): 19G
```
Filesystem        Size    Used   Avail Capacity iused ifree %iused  Mounted on
/dev/disk3s1s1   228Gi    11Gi    24Gi    33%    453k  251M    0%   /
/dev/disk3s5     228Gi   175Gi    24Gi    88%    2.5M  251M    1%   /System/Volumes/Data
/dev/disk4s1     931Gi   131Gi   800Gi    15%       1     0  100%   /Volumes/Transcend
```
- Internal Data volume used: 178.57 GB at baseline (Mon Sep 28 23:30:52 +05 2026) -> 183.67 GB now: +4979 MB. This counts everything on the Mac (other apps, browsers, other Claude sessions, caches), not just this project.
  - this project's files on the internal disk: /Users/damir/.claude/projects/-Volumes-Transcend-dev-apple-motion 57.7 MB
  - this project's files on the internal disk: /Users/damir/.claude/projects/-Users-damir-dev-apple-motion 2.1 MB
  - this project's files on the internal disk: /private/tmp/claude-501/-Volumes-Transcend-dev-apple-motion 4.9 MB
- This project's own internal-disk footprint (session transcript + scratchpad + the ~/dev symlink): 65 MB (<= 200 MB: OK)
- Left on the internal disk from the earlier aborted attempt (moved aside, not deleted): /Users/damir/dev/apple-motion.internal-old-20260928 (1.5 GB; safe to delete by hand)
