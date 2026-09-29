# Blind test of the skill (round 1)

A separate Claude agent got only `skill/apple-motion/` (no access to data, scripts or reports) and the brief
"30-second Apple-style launch recap in Remotion for a fictional app 'Northwind Notes 3.0': offline sync,
smart search, 2x faster to open, new home-screen widgets. Music only. End on the logo."
It wrote `demo/src/agent/AgentRecap.tsx` (14 cards, 66 beats; median card 52.5 frames vs Apple's 56.5;
8% non-cut transitions vs Apple's 8%) and it typechecked on the first try.

What it found wrong in the skill, and what changed:

| finding | fix |
|---|---|
| example-script.md claimed 64 beats but summed to 34; logo not on a bar line | rewritten, sums to 64, logo on beat 64; compiled and rendered as `ExampleScript` in the demo |
| "mostly 1-2 beat cards" contradicted the measured 1.9 s median shot; "half-beat flash runs" contradicted 0 montage runs/min | step 4 rewritten from the measured distribution |
| card starts drifted with rounding (half beats, fractional frames per beat) | `cardStarts()` computes every start from the running beat total |
| whoosh peaked before the whip instead of in its middle | whoosh now peaks at start + tf/2 of the transition |
| synth bed's closing hit and section layout undocumented; logo `sfx: 'hit'` doubled it | documented in SKILL.md and audio.md; demo no longer doubles the hit |
| no guidance without footage; device fixed at centre; gradient colours not settable | "No footage?" section; `device.x`, `device.entry`, `device.everyBeats`, `gradient` on cards; `grid` icon walls |
| UICard / DeviceFrame still stretched the spring; "no visible bounce" vs zeta 0.77 | components use the unstretched calibrated spring; wording: ~2% overshoot |
| no size between headline and hero; hero overflowed on long wordmarks | `display` size (p75); KineticText shrinks lines wider than 88% of the frame |
| no scale-down exit though 12% of measured exits are | `exit: 'scaleDown'` |
| broken reference (timing.md), colour #1d1d1f vs measured #080808 | fixed |

# Blind test round 2

Brief: "24-second Apple-style recap for my fitness app 'Stride 2': heart-rate zones that coach you live,
weekly rings, a new Coach tab, 40% longer battery life on the watch. Music only, end on the app name."
The agent wrote `demo/src/agent2/StrideRecap.tsx` (12 cards, 48 beats, median card 52.5 frames, 4.6 cuts/10 s);
typecheck passed first try. Rendered + mastered: every self-check metric inside Apple's p10-p90 range
(cuts/10 s 4.58, median shot 52.5 fr, -17.4 LUFS, -3.3 dBTP).

| finding | fix |
|---|---|
| total length math unclear (tail added on top, tail rendered black) | last card now holds through `tailFrames`; SKILL.md gives the length formula and a worked 30 s example |
| no way to fit a longer bed | `musicFadeOutFrames`; `synth_audio.py --bars N` sections now scale with N (break was hard-coded at bars 13-14) |
| `cardStarts` documented but not exported | exported |
| three different x positions for text beside a phone; left-aligned lines could overflow | one recipe (`device.x: 30`, `lines` x 58, align left); KineticText fits text between its anchor and the frame edge |
| omitted `entry` gave scaleDown, not the measured default cut-on | default is now `cut` |
| type-density rule ambiguous | every lines/spec/counter card counts; name extra features inside UI cards |
| two loudness targets (audio.md -16 vs tokens -17.4) | one: `scripts/master.sh` with the token targets |
| gradient number roll impossible | `counter.gradient` |
| type always lasted the whole card | `typeBeats` lets type leave while the picture continues |
| UI-tap SFX impossible | `device.tapSfx` |
| empty grey phone screens | default light/dark wallpaper gradients (`device.wallpaper`) |

# Blind test round 3

Brief: "WWDC-style 20-second recap for our developer tool 'Lumen CLI 4': builds 3x faster, new cloud cache,
first-class Swift support, redesigned dashboard. Upbeat, fast, end on the name. Fresh music bed that fits."
The agent generated its own 128 BPM, 9-bar bed, put the logo on the bed's hit (frame 506 of 506.25) and wrote
10 cards (`demo/src/agent3/Round3Recap.tsx`); typecheck passed first try. Rendered + mastered: cuts 4.44/10 s,
median shot 56 frames (Apple median 56.5), -16.7 LUFS; true peak -5.0 dBTP (below Apple's range - the bed had
been pre-normalised before the SFX were mixed).

| finding | fix |
|---|---|
| synth wrote `music_raw.wav` but docs said `music.wav`; raw bed peaks +2.3 dBTP | synth now also writes a mastered `music.wav` (-17.4 LUFS / -2 dBTP) and prints the hit's frame |
| two loudness targets (script docstring -16 / tokens -17.4) | one target everywhere |
| `master.sh` could not master a WAV | accepts audio-only input |
| length examples disagreed (28 s vs 32 s vs 37.5 s); logo length unspecified | one formula; logo ~3 s from the measured last-shot median; example relabelled 37.5 s; 30 s example = 12 bars + 6-beat logo |
| video outlasted the bed after the hit | bed now rings out ~4 s after the hit |
| short beds lose the main section; `--bars >= 8` not enforced | documented (>= 12 bars for a main section); enforced |
| SFX folder fixed to `public/sfx` | `sfxDir` prop; docs say to write the bed into `public/` |
| ">90% hard cuts" impossible with 10 cards | "about one accent per 10-12 cards" |
| type density presented as measured although it is a recommendation for music-only pieces | labelled as a recommendation, measured value given separately |
| calibrated spring listed with `durationInFrames: 20` next to "use without durationInFrames" | labelled as Remotion's natural settle length, reference only |
| emoji vs monochrome glyphs | documented |
