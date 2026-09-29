# Entry training

Targets with fewer than 8 Apple samples are uncertain; their slow-down is capped at 2x.

EntryLab renders every KineticText entry at spring time scales 1 / 1.5 / 2 / 2.75; the extraction
pipeline measures each entry's length (appear -> settled); a line fitted through those points gives the time
scale at which the measured length equals Apple's median for that entry type.

| entry | Apple target (median frames, n) | measured at 1 / 1.5 / 2 / 2.75 | trained time scale |
|---|---|---|---|
| fade | 7 (12) | 6 / 9 / 12 / 13 | 1.07 |
| slideUp | 8 (14) | 6 / 8 / 9 / 11 | 1.63 |
| slideUpMask | 8 (18) | 5 / 8 / 9 | 1.67 |
| scaleDown | 15 (6) | 6 / 7 / 9 / 10 | 2.00 |
| scaleUp | 13 (4) | 6 / 9 / 9 / 9 | 2.00 |
| blurIn | 27 (3) | 5 / 7 / 9 / 12 | 2.00 |
