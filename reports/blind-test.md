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
