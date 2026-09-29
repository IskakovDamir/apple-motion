# apple-motion extraction report

4 videos, 561.8 s, 16837 frames. All numbers measured by `scripts/` (see README). 'text' = every tracked text block (UI, products, chrome, legal included); 'typo' = reviewed designer typography only. 'On beat' = within +-2 frames of a tracked beat; chance = 5 / beat period.

| video | fps | dur s | shots | median shot fr | BPM | text ev /10s | typo /10s | median hold fr text / typo | most common typo entry | median entry spring d/k/m (n) | cuts on beat (chance) | text / typo on beat | LUFS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sept26-event-recap | 29.97 | 95.09 | 90 | 22.5 | 127.2 | 30.39 | 0.42 | 10.0 / 26.5 | fade | 99.46/1696.0/1 (2) | 0.38 (0.354) | 0.325 / 0.25 | -17.0 |
| wwdc22-day1-recap | 29.97 | 179.51 | 72 | 66.0 | 99.18 | 30.97 | 1.11 | 19.5 / 29.5 | cut on | 10.47/72.15/1 (14) | 0.343 (0.276) | 0.272 / 0.35 | -16.5 |
| wwdc23-17things | 29.97 | 135.1 | 35 | 66.0 | 119.57 | 20.36 | 0.81 | 15.0 / 20.0 | slide down with mask | 45.77/512.5/1 (8) | 0.375 (0.332) | 0.207 / 0.75 | -16.7 |
| wwdc25-welcome | 29.97 | 152.09 | 85 | 41.0 | 84.65 | 19.53 | 0.79 | 14.0 / 9.5 | slide | 5.21/14.8/1 (7) | 0.284 (0.235) | 0.333 / 0.316 | -21.6 |

Pooled cuts on beat: 95/278 vs 82.1 expected by chance (z=1.7, p=0.0444).
Spring-fit calibration (known springs rendered and measured back): fitted springs are 1.19x too fast (n=5, damping ratio preserved x1.032); calibrated pooled entry spring: {'damping': 14.98, 'stiffness': 99.9, 'mass': 1, 'durationInFrames': 22}.
Font weight calibration (stroke/cap of SF Pro Display rendered at known weights): [(0.109, 400), (0.138, 500), (0.159, 600), (0.177, 700), (0.197, 800)].

## Storage

- Project size (du -sh /Volumes/Transcend/dev/apple-motion): 17G
```
Filesystem        Size    Used   Avail Capacity iused ifree %iused  Mounted on
/dev/disk3s1s1   228Gi    11Gi    25Gi    32%    453k  266M    0%   /
/dev/disk3s5     228Gi   174Gi    25Gi    88%    2.4M  266M    1%   /System/Volumes/Data
/dev/disk4s1     931Gi   129Gi   802Gi    14%       1     0  100%   /Volumes/Transcend
```
- Internal Data volume used: 178.57 GB at baseline (Mon Sep 28 23:30:52 +05 2026) -> 182.17 GB now: +3521 MB. This counts everything on the Mac (other apps, browsers, other Claude sessions, caches), not just this project.
  - this project's files on the internal disk: /Users/damir/.claude/projects/-Volumes-Transcend-dev-apple-motion 46.5 MB
  - this project's files on the internal disk: /Users/damir/.claude/projects/-Users-damir-dev-apple-motion 2.1 MB
  - this project's files on the internal disk: /private/tmp/claude-501/-Volumes-Transcend-dev-apple-motion 4.8 MB
- This project's own internal-disk footprint (session transcript + scratchpad + the ~/dev symlink): 53 MB (<= 200 MB: OK)
- Left on the internal disk from the earlier aborted attempt (moved aside, not deleted): /Users/damir/dev/apple-motion.internal-old-20260928 (1.5 GB; safe to delete by hand)
