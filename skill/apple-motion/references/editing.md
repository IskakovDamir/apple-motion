# Editing: pace, transitions, sync

Numbers: `measurements.md` (shot length distribution, cuts per 10 s, transition mix, sync shares
with chance rates and binomial p-values).

## Pace

- Cut often and unevenly: the median shot is short, but the distribution has a long tail
  (holds on a hero product or a UI demo). Alternate 2-4 quick shots with one longer one.
- Very short shots (4-6 frames) are used as flashes inside a run, never alone.
- Within a longer shot something always moves: UI animation, a slow push, a device turning.

## Transitions

- The hard cut is the default by a wide margin. Accents, in measured order: whip (fast directional
  move with motion blur), dissolve, mask wipe, scale through (push into an element until it fills
  the frame, cut on the fill).
- Motion-graphics sections (e.g. WWDC23's opener) swap states in place instead of cutting: lines slide
  out under a mask while the next line slides in; a stretched/smeared frame or two between states.
- UI demos use the product's own transitions (sheets, zooms) as the edit: zoom into a UI element
  ("Call Again", "Add Sticker") and cut on the zoom - a scale-through built from UI.

## Framing devices seen in the corpus

- **Player chrome** (Sept 2026 recap): the recap is framed as scrubbing through the keynote -
  progress bar, knob, elapsed / remaining timecodes, occasional PiP thumbnail of the source.
  `Scrubber.tsx`.
- **Presenter + label**: presenter on stage with a white pill label naming the feature
  ("Stage Manager", "iCloud Shared Photo Library").
- **Icon grids** for "all the apps" moments (App Store / Design Awards finalists) that pan slowly.
- **Device on flat background**: phone/watch/Mac on #f5f5f7 or white, rising or rotating in.
  `DeviceFrame.tsx`.

## Sync (read with the chance rates)

At ~120 BPM and 30 fps a random frame lands within +-2 frames of a beat about a third of the time,
so "X% of cuts are on the beat" means nothing without the chance rate. Measured:

- Cuts land on the beat only slightly more often than chance in these voice-over-led recaps
  (see p-values). The edit follows the narration and the picture; the music is laid under it.
- Cuts do **not** favour word onsets (often less than chance): picture changes inside words or on
  word ends, not on the first syllable.
- Designer type lands on the spoken word: median offset of text appear vs. the same word in the
  voice-over is a few frames (see `typography appear - same spoken word`).

Practical rule for Remotion: build the beat grid (`beat.ts`) for music-only pieces and put cuts on
beats there; for VO pieces, cut on phrase boundaries and snap only the *big* moments (title card,
final logo) to a downbeat.
