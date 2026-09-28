# apple-motion extraction report

1 videos, 95.1 s, 2850 frames. All numbers measured by scripts/ (see README).

| video | fps | dur s | shots | median shot fr | BPM | text ev /10s | typo /10s | median typo hold fr | most common typo entry | median entry spring d/k/m | cuts on beat (chance) | typo on beat | LUFS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sept26-event-recap | 29.97 | 95.09 | 90 | 22.5 | 123.05 | 21.03 | 0.63 | 28.5 | other | 23.86/215.1/1 (n=4) | 0.38 (0.342) | 0.0 | -17.0 |

Notes: 'text ev' counts every tracked text block (UI, products, chrome, legal); 'typo' counts reviewed designer typography only. 'On beat' = within +-2 frames; chance = 5 / beat period.

## Storage

- Project size (du -sh /Volumes/Transcend/dev/apple-motion): 15G
```
Filesystem        Size    Used   Avail Capacity iused ifree %iused  Mounted on
/dev/disk3s1s1   228Gi    11Gi    29Gi    29%    453k  307M    0%   /
/dev/disk3s5     228Gi   172Gi    29Gi    86%    2.3M  307M    1%   /System/Volumes/Data
/dev/disk4s1     931Gi   128Gi   804Gi    14%       1     0  100%   /Volumes/Transcend
```
- Internal Data volume used: 178.57 GB at baseline (Mon Sep 28 23:30:52 +05 2026) -> 180.15 GB now: +1549 MB
