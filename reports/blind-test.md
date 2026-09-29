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
