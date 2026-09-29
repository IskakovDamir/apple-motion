---
name: apple-motion
description: Write Remotion (React) videos in the style of Apple's short, fast, upbeat recap videos (WWDC recaps, event recaps, feature intros) - pacing, kinetic typography, springs and easing, transitions, device/UI shots, beat and voice-over sync, music, SFX and loudness - using numbers measured frame by frame from six Apple recaps. Use when asked for an "Apple-style", keynote-style or WWDC-recap-style video, a product/launch/feature recap, kinetic typography, or any Remotion composition that should feel like Apple motion design.
---

# apple-motion

Every default here is measured, not guessed: six Apple recap videos (1107 s, 33,187 frames) went
through a forensic pipeline (OCR text tracking, spring fitting, optical flow, beat tracking,
loudness), and the pipeline itself was calibrated on renders with known springs and fonts.
Not affiliated with Apple.

## The style in numbers

<!-- numbers:start -->
- **Pace.** Median shot 56.5 frames (1.9 s); p10 13.0, p90 173.5 frames; 3.24 cuts per 10 s (median video). Transitions: cut 92%, whip 5%, scale through 1%, dissolve 1%.
- **Typography is an accent, not the bed.** Designer-set type appears 0.78 times per 10 s (median video); most on-screen text is UI inside product shots. Hold 33.0 frames median (p10 10.0, p90 80.6).
- **Size.** Cap height median 6.67% of frame height (p10 3.25%, p90 20.23%). Lines: 1 84%, 2 10%, 4 4%. Alignment: center 60%, right 19%, left 15%.
- **Entries.** cut on 25%, slide 21%, fade 18%, scale down from large 9%, per-letter 7%. Animated entries are visibly done in 8.0 frames (median). Spring (calibrated): damping 15.35, stiffness 115.0, mass 1 - use it without durationInFrames.
- **Exits.** cut off 59%, slide out 13%, fade out 10%, blur out 7%; median 0.0 frames.
- **Sound.** 118.8 BPM median (p10 91.9, p90 131.3); -17.4 LUFS integrated, -2.0 dBTP true peak; voice-over at 3.04 words/s. Cuts are not locked to the beat: 134/400 within +-2 frames vs 124.8 expected by chance (p=0.1586) - the edit follows the voice and picture.
<!-- numbers:end -->

## How to build one

1. **Copy the library.** `templates/remotion/` -> `src/apple-motion/` in the user's Remotion project
   (needs `remotion` and `@remotion/transitions`). `tokens.ts` is the measured style - don't edit it.
2. **Fix the length on the music first.** Pick BPM (numbers block), then the number of bars. At 30 fps
   and 120 BPM: 1 beat = 15 frames, 1 bar = 60, 16 bars = 32 s. A "30-second recap" = 16 bars.
   With `scripts/synth_audio.py` the bed is laid out as: intro bars 1-2, build 3-4, main 5-12,
   break 13-14 (drums out), final 15-16, and a closing **hit exactly on the last bar line**
   (beat 64 for 16 bars). Land the logo card on that beat and don't add another `sfx: 'hit'`.
3. **Write the video as cards** (`Card[]`, see `Recap.tsx`). Each card lasts a number of beats
   (half beats allow) and is one of: footage/still (`media`), claim or word (`lines`), feature title
   (`icon` + `lines` on white), spec (`spec`: gradient numerals + label), number roll (`counter`),
   device with UI (`device`), icon wall (`grid`), player-chrome moment (`scrubber`).
4. **Pace to the measurements.** Median card ~1.9 s (about 4 beats at 120 BPM); most cards 1-7
   beats; a few long holds (8-12 beats) on product or UI. The opening shot is long (median ~4 s:
   start on something that moves, not on a title). Runs of very short (<= 10 frame) shots are rare in
   the corpus - don't build a flash montage unless the brief asks for one.
5. **Type is punctuation.** 1-4 words per line, 1 line (84% of measured type), at most 2. Name a
   feature, state a claim, show a number. With a voice-over, type is rare (numbers block); without
   one, type has to name the features - still keep it to about one type card per 5-7 s.
6. **Transitions:** leave `transition` empty (hard cut) on >90% of cards; `whip` is the common
   accent, `dissolve` / `maskWipe` / `scaleThrough` are rare. Put accents on musical moments.
7. **Mix and master:** SFX only on whips (automatic), UI taps, the final hit. Render, then
   `scripts/master.sh out.mp4 final.mp4` (two-pass loudnorm to `AUDIO.lufs` / `AUDIO.truePeakDb`).
8. **Check:** `python scripts/check_render.py final.mp4` prints your pace and loudness next to
   Apple's p10-p90 ranges. Fix anything marked OUTSIDE.

```tsx
// src/Root.tsx
import {Composition} from 'remotion';
import {Recap, recapDuration, type Card, type RecapProps} from './apple-motion';

const cards: Card[] = [                                    // 120 BPM, 16 bars = 64 beats
  {beats: 8, bg: 'offWhite', device: {cards: [{title: 'Northwind 3.0', subtitle: "What's new", icon: '📝'}]}},
  {beats: 4, bg: 'white', icon: {glyph: '↻', from: '#64d2ff', to: '#0a84ff'}, lines: ['Offline sync'], entry: 'fade', size: 'title'},
  {beats: 8, bg: 'black', device: {tone: 'dark', cards: [{title: 'Offline', subtitle: '3 edits saved'}, {title: 'Synced', subtitle: 'just now'}]}},
  {beats: 4, bg: 'white', icon: {glyph: '⌕', from: '#ff9f0a', to: '#ff375f'}, lines: ['Smart search'], entry: 'fade', size: 'title', transition: 'whip'},
  {beats: 8, bg: 'black', media: {src: 'search.mp4', type: 'video'}},
  {beats: 4, bg: 'white', spec: {value: '2x', label: 'faster to open', gradient: ['#b150e2', '#e0417b']}},
  {beats: 12, bg: 'black', grid: {icons: [{glyph: '✦', from: '#5e5ce6', to: '#bf5af2'}]}},
  {beats: 16, bg: 'gradient', gradient: ['#0a84ff', '#5e5ce6'], lines: ['Your notes.', 'Everywhere.'], entry: 'slideUpMask', size: 'headline'},
  {beats: 8, bg: 'black', lines: ['Northwind'], entry: 'scaleDown', size: 'display'}, // starts on beat 64 = the bed's final hit
];
const props: RecapProps = {bpm: 120, cards, music: 'music.wav'};
export const Root = () => (
  <Composition id="Recap" component={Recap} defaultProps={props} fps={30} width={1920} height={1080}
    durationInFrames={recapDuration(props, 30)} />
);
```

The engine computes every card's start from the running total of beats (no drift), overlaps a
transition into the outgoing card so the incoming card still starts on its beat, and peaks the whoosh
in the middle of each whip.

## No footage?

About half of Apple's frames are footage. Without it, carry the picture with: `device` cards (UI
inside a phone; set `device.x` to ~30 and put `lines` at `x` ~62, `align: 'left'` to have a claim
beside the phone), `grid` icon walls, `spec` numerals, gradient fields (`bg: 'gradient'` +
`gradient: [from, to]`), and single `icon` cards. Avoid long stretches of plain black or white: the
corpus is ~8% pure black and ~21% pure white frames.

## Rules the measurements back up

- **Type:** SF Pro Display (system font on macOS; Inter off Apple platforms), weight from the
  calibrated stroke measurement (`TYPE.weight`), tight tracking, leading from `TYPE.lineHeight`.
  White on black/footage; near-black (#080808-#1d1d1f) on white or #f5f5f7. Flat colour - except spec
  numerals (vertical gradient). No outlines, shadows, boxes behind text, rotation.
- **Sizes:** `size` maps to measured cap-height percentiles: caption (p10), title (p25), headline
  (median), display (p75), hero (p90, event wordmarks). `KineticText` shrinks a line that would exceed
  88% of the frame width.
- **Motion:** the calibrated type spring is slightly under-damped (a ~2% overshoot, no visible
  bounce). Remotion detail: `spring({durationInFrames})` stretches the spring and the visible move
  ends ~3x earlier than `durationInFrames`; the components therefore use `SPRING.textIn` unstretched,
  which reproduces Apple's visible entry length. Most type cuts on with its shot; most exits are cuts.
- **Sync:** in Apple's voice-over recaps cuts are *not* locked to the beat (numbers block); the edit
  follows the voice and picture, and type lands on the spoken word. For music-only pieces the card
  engine keeps cuts on beats - a deliberate choice, not a measured Apple trait.
- **Loudness:** `AUDIO.lufs` integrated, `AUDIO.truePeakDb` true peak (median of the six videos).

## Library (templates/remotion)

| file | what |
|---|---|
| `tokens.ts` | measured defaults, generated from `references/fingerprint.json` |
| `Recap.tsx` | card engine (`Card`, `Recap`, `recapDuration`, `cardStarts`) |
| `KineticText.tsx` | `lines`, `entry` (cut, fade, blurIn, scaleDown, scaleUp, slideUp, slideUpMask, perWord, perLetter), `exit` (cut, fade, blurOut, scaleUp, scaleDown, slideOut), `size`, `gradient`, `maxWidthPct` |
| `Counter.tsx` | number roll with tabular figures and a caption line |
| `DeviceFrame.tsx`, `UICard.tsx` | phone mock-up and notification/widget card (max 3 per phone; titles up to ~17 characters at the default size) |
| `AppIcon.tsx`, `IconGrid.tsx`, `Scrubber.tsx`, `Backdrop.tsx` | feature-title icon, icon wall, player chrome, flat/gradient backgrounds |
| `transitions.tsx` | `appleTransition('whip' / 'dissolve' / 'maskWipe' / 'scaleThrough', key)` |
| `beat.ts`, `Sfx.tsx` | beat grid helpers, pre-rolled SFX |

## References

- `references/measurements.md` - every measured distribution, pooled and per video (generated)
- `references/typography.md` - the recurring type devices and how to set them
- `references/editing.md` - pace, transitions, framing devices, sync
- `references/audio.md` - music, voice-over, SFX, loudness, the synth bed's layout
- `references/example-script.md` - a complete 16-bar card script with the reasoning
- `references/fingerprint.json` - machine-readable fingerprint
- `scripts/synth_audio.py` (CC0 bed + SFX), `scripts/master.sh` (loudness), `scripts/check_render.py` (self-check)
