# Typography

Numbers: `measurements.md` (cap height, weight proxy, leading, hold, entry/exit, springs). This file
is the catalogue of *how* type is used, from reviewing every tracked text event of the six videos.

## What counts as "typography" here

Out of ~1,600 tracked text blocks only a small share is designer-set type laid over the picture.
The rest is text *inside* the picture: app UI on devices, product engravings, player timecodes,
legal lines. When you write an Apple-style recap, most of your frames should be product / UI / people,
and type is the punctuation: a feature name, a claim, a number.

## The recurring type devices

1. **Feature title on white.** App icon (or glyph) centred above, one-line title below it, near-black
   (#1d1d1f) Semibold on #ffffff / #f5f5f7. Holds long enough to read, then cuts.
   Examples: "WeatherKit", "Metal 3", "Swift Charts", "Xcode Cloud", "App Intents API".
   `<Backdrop kind="white"/>` + icon + `<KineticText size="title" entry="fade"|"scaleUp"/>`.
2. **Claim over footage.** White Semibold, one or two lines, left-aligned in the left or middle third,
   or centred. "Active Noise / Cancellation", "Longest battery life / in iPhone history",
   "Most accurate heart rate / sensing in a wearable". Usually cuts on with the shot.
3. **Single word on black.** Big, centred, alone: "Siri". Cut on, short hold, cut off.
4. **Spec numerals.** Huge numerals with a small label: "Up to / 10-core", "18% / Faster CPU",
   "35% / Faster GPU". Here Apple *does* fill the numerals with a vertical gradient (M2: purple to
   magenta) - the only place type is not flat. Use `<Counter/>` for the roll-up.
5. **Wordmark stack.** Event wordmark lines stacked and swapped ("17 things / big & little / WWDC23"),
   lines slide in and out under a mask, with stretched / smeared frames between states.
6. **Typing gag.** A text field line typed letter by letter with a cursor, corrected by autocorrect
   ("That's so ducking cool"). `entry="perLetter"` with 1-frame stagger.
7. **Captions / pills.** Small uppercase pills in the player chrome ("TIME-LAPSE IN 4K",
   "24 FPS 1/48 SHUTTER SPEED") and session cards ("What's new in / SwiftUI"). Label size.
8. **Award / section cards.** "2022 Apple Design Awards", "Finalists" over a grid of app icons.

## Setting

- Family: SF Pro Display (system on macOS); fallback Inter. Weight: see `stroke / cap` in
  measurements (calibrated against SF Pro weights 400-800 rendered through the same pipeline).
- Tracking: tight for display sizes (-0.01 to -0.02 em); numerals tabular in counters.
- Leading: from `line pitch / cap height` (converted to line-height in `tokens.ts`).
- Colour: white on dark / footage; #1d1d1f-ish on white. Colour lives in the picture.
- Never: outlines, drop shadows, boxes behind type, rotation, bouncy overshoot on type.

## Motion

- Most type **cuts on** with its shot (the cut is the entry). Animated entries are fast: the visible
  part of the move is a few frames (see `entry duration, animated only`).
- Animated entries, in measured order of frequency: see `Typography entry styles` in
  measurements.md. The Remotion recipes in `KineticText.tsx` are tuned to the measured start values
  (`entry start scale`, `entry start y offset`, `entry start blur`).
- Holds drift very slightly (slow push of the whole frame); keep type static inside a moving shot.
- Exits are mostly the cut. Animated exits are shorter than entries.

## Spring vs. visible duration (important when you write Remotion code)

A Remotion `spring({durationInFrames: 12})` *looks* finished after ~4 frames: the remaining frames
are sub-pixel settling. Our pipeline measures the visible duration; `tokens.ts` gives you the fitted
spring config that reproduces the measured curve directly (use it without `durationInFrames`), and
`spring_idiomatic` in measurements.md gives the `{damping, durationInFrames}` form.
Calibration of the measurement itself (known springs rendered and measured back) is in
`reports/eval/render-cal.md` of the repository.
