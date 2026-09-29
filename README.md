# apple-motion

A Claude skill that makes Claude write [Remotion](https://www.remotion.dev) videos in the style of
Apple's short, fast recap videos - built from **frame-accurate measurements** of six Apple recaps,
not from vibes.

> Not affiliated with, endorsed by or sponsored by Apple Inc. "Apple", "WWDC", "SF Pro" and product
> names are trademarks of Apple Inc. This repository contains no Apple media: only code, numbers
> measured from publicly available videos, and our own synthesized audio.

<!-- results:start -->
## Results

6 videos, 1107.1 s, 33187 frames. Full report: [`reports/extraction_report.md`](reports/extraction_report.md), distributions: [`skill/apple-motion/references/measurements.md`](skill/apple-motion/references/measurements.md).

| video | fps | dur s | shots | median shot fr | BPM | text ev /10s | typo /10s | median hold fr text / typo | most common typo entry | median entry spring d/k/m (n) | cuts on beat (chance) | text / typo on beat | LUFS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ios26-liquid-glass | 29.97 | 273.77 | 68 | 99.5 | 118.05 | 24.03 | 0.04 | 14.0 / 25.0 | blur in | 128.31/5000.0/1 (1) | 0.277 (0.328) | 0.339 / 0.0 | -19.2 |
| sept26-event-recap | 29.97 | 95.09 | 90 | 22.5 | 127.2 | 30.39 | 0.42 | 12.0 / 28.0 | cut on | None/None/1 (0) | 0.38 (0.354) | 0.355 / 0.5 | -17.0 |
| wwdc22-day1-recap | 29.97 | 179.51 | 72 | 66.0 | 99.18 | 30.97 | 1.06 | 22.0 / 34.0 | cut on | 13.25/75.45/1 (10) | 0.343 (0.276) | 0.29 / 0.368 | -16.5 |
| wwdc23-17things | 29.97 | 135.1 | 35 | 66.0 | 119.57 | 20.36 | 0.81 | 17.0 / 21.0 | cut on | 60.38/406.0/1 (5) | 0.375 (0.332) | 0.234 / 0.75 | -16.7 |
| wwdc25-welcome | 29.97 | 152.09 | 85 | 41.0 | 84.65 | 19.53 | 0.79 | 17.0 / 13.0 | slide | 11.74/88.85/1 (8) | 0.284 (0.235) | 0.327 / 0.167 | -21.6 |
| wwdc26-sotu-recap | 30.0 | 271.5 | 56 | 118.0 | 135.42 | 7.99 | 0.77 | 69.0 / 75.0 | fade | 28.92/201.7/1 (17) | 0.36 (0.376) | 0.358 / 0.333 | -17.7 |

Pooled: median shot 56.5 frames, typography cap height 6.67% of frame height (~SF Pro 600.0), typography hold 33.0 frames, calibrated entry spring damping 15.35 / stiffness 115.0 / mass 1, -17.4 LUFS.
<!-- results:end -->

## What's in here

| path | what |
|---|---|
| `skill/apple-motion/` | **the skill**: `SKILL.md`, measured references, Remotion component library, audio generator, render self-check |
| `scripts/` | the forensic extraction pipeline (shots, OCR text tracking, spring fitting, optical flow, colour, audio/beat/voice, sync) |
| `demo/` | a Remotion project that renders a showcase recap and a calibration video with the skill's components |
| `reports/` | extraction report, per-video summaries, render evaluations and pipeline calibration |
| `reference/` | sources, reviewed typography labels |

## Install the skill

Claude Code:

```bash
mkdir -p ~/.claude/skills && cp -R skill/apple-motion ~/.claude/skills/
```

Claude.ai / Claude apps: zip `skill/apple-motion` and upload it under Settings -> Capabilities -> Skills.

Then ask for something like *"Make a 30-second Apple-style recap in Remotion of our Q3 launch: three
features, one stat, end on the logo"*. Claude will copy `templates/remotion/` into your project,
time everything on a beat grid and use the measured springs, sizes, holds and transitions.

## How the numbers were made

Six Apple recap videos (1107 s, 33,187 frames) went through nine steps, all in `scripts/`:

1. **Shots** - PySceneDetect ContentDetector + a windowed soft-transition pass; every boundary
   classified (cut, whip, dissolve, mask wipe, scale through, match cut) and false cuts inside
   continuous motion rejected by alignment (phase correlation + ECC).
2. **Text** - EasyOCR on every frame of every text-bearing shot; tracks linked by IoU + text
   similarity, split where text is swapped in place; then a template tracker on "ink" maps gives
   per-frame scale, position, opacity (glyph cores vs. a local ring), blur (masked NCC against
   blurred templates) and reveal. Designer typography was separated from UI/product/legal text by
   visual review of every event (`reference/labels/`).
3. **Animation fits** - exact Python port of Remotion's `spring()` / `measureSpring()` (verified
   equal to the stepping implementation), fitted to the leading channel of every entry and exit;
   plus the closest cubic-bezier and the nearest named easing.
4. **Non-text motion** - dense optical flow with a similarity model per frame pair: push, pull,
   pan, tilt, whip, static; accel/decel frames and a fitted spring per camera move.
5. **Colour and layout** - frame class (pure black / white / gradient / UI / product / footage),
   backgrounds, accents, 3x3 text placement.
6. **Frames** - first/middle/last frame of every shot, every frame of every text entry, 4x4
   contact sheets.
7. **Audio** - demucs stems; BPM from a line fit of beat times (librosa's tempo bins are ~2.5%
   apart), downbeats, sections, SFX candidates off the music grid, faster-whisper word timestamps,
   EBU R128 loudness.
8. **Sync** - cuts and text vs. beats, downbeats, word onsets and VO pauses, each with its chance
   rate and a binomial test.
9. **Summary** per video, then `build_fingerprint.py` pools everything into
   `skill/apple-motion/references/fingerprint.json`, and `build_skill_refs.py` regenerates the
   skill's `tokens.ts`, `measurements.md` and the numbers block of `SKILL.md`.

## Calibration: how much to trust the pipeline

The same pipeline is run on videos we rendered ourselves with **known** fonts and springs
(`demo/src/Calibration.tsx`, `scripts/eval_render.py`). Results in `reports/eval/render-cal.md`:

- entry styles (cut, fade, scale down, scale up, blur in, slide, slide under a mask, per-word) are
  recovered correctly;
- the tracked position of a masked slide follows the true spring to within 0.01 progress units;
- fitted springs come out ~19% too fast in time scale (damping ratio preserved), so the skill uses
  **calibrated** springs (fitted / 1.19, stiffness / 1.19^2);
- blur-driven entries are the least accurate (~1.9x); swaps of near-identical text in place
  (e.g. "Weight 500" -> "Weight 600") can shift the appear frame.

The calibration found and fixed four real bugs along the way (merged in-place swaps, per-word
settle, per-word vs per-letter, quantised BPM). That loop - render, measure, compare, fix - is the
"training" of this skill; `scripts/eval_render.py <video> --name X` scores any render against the
Apple ranges.

## Reproduce

Requirements: macOS/Linux, Python 3.12, ffmpeg, yt-dlp, Node 20+. Apple's videos are not
redistributed; `scripts/download.py` fetches them from the public sources in
`reference/sources.txt` for your own analysis.

```bash
source scripts/env.sh            # keeps every cache/tmp inside the project folder
python3 -m venv --copies .venv && source scripts/env.sh
pip install "scenedetect[opencv]" opencv-python easyocr librosa demucs scikit-learn scipy pillow numpy faster-whisper
python scripts/download.py
python scripts/s1_shots.py && for s in $(ls data | grep -v _src); do python scripts/s2a_ocr.py $s; done
python scripts/run_pipeline.py   # steps 2b..9, resumable
python scripts/verify_extract.py
python scripts/build_fingerprint.py && python scripts/build_skill_refs.py
```

Demo:

```bash
cd demo && npm install
python ../skill/apple-motion/scripts/synth_audio.py public --bpm 120 --bars 16
ffmpeg -i public/music_raw.wav -af loudnorm=I=-16:TP=-1.5 public/music.wav
npx remotion render src/index.ts Recap out/recap.mp4
```

## License

MIT for code and documentation. Measurements are facts about public videos; no Apple media is included.
