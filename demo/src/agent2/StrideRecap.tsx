import type {Card, GridIcon, RecapProps} from '@apple-motion';

/*
 * "Stride 2" - 24 s Apple-style recap, music only, ends on the app name.
 *
 * Length (SKILL step 2): 120 BPM at 30 fps -> 1 beat = 15 frames, 1 bar = 60. 24 s = 48 beats = 12 bars.
 * The bed in public/music.wav is 16 bars, so its closing hit (beat 64 = 32 s) is outside the video.
 * We use bars 1-12 only: intro 0-7, build 8-15, main 16-47. The composition ends exactly on beat 48,
 * the bar line where the bed's break (drums out) starts, so the music is cut on a bar line and not mid-bar.
 * tailFrames: 0 keeps the file at exactly 720 frames. Because the bed's own hit is cut off, the logo card
 * carries sfx 'hit' (SKILL step 7: SFX on "the final hit"); the step-2 "don't add sfx: 'hit'" rule
 * only applies when the bed's hit falls inside the video.
 *
 * Cards start on beats 0, 8, 11, 16, 19, 28, 36, 40, 41, 42, 43, 44 -> frames 0, 120, 165, 240, 285,
 * 420, 540, 600, 615, 630, 645, 660; the total is 48 beats = 720 frames.
 * Type cards (feature names, claim, spec, name) sit on bar downbeats (8, 16, 28, 36, 44); picture cards fill between.
 */

const HEART = {from: '#ff6482', to: '#ff2d55'};
const RINGS = {from: '#5ce1d4', to: '#00b3a4'};
const COACH = {from: '#ffb340', to: '#ff7a00'};
const BATTERY = {from: '#5be27a', to: '#00a37a'};

// Rows = the three daily rings, columns = the seven days of the week.
const ringRow = (c: {from: string; to: string}): GridIcon[] => Array.from({length: 7}, () => ({glyph: '◯', ...c}));
const weekOfRings: GridIcon[] = [...ringRow(HEART), ...ringRow({from: '#8be36a', to: '#30b94b'}), ...ringRow(RINGS)];

const cards: Card[] = [
  // 1 | beats 0-7 | intro. Opens on motion (not a title): the phone rises and a live run builds up one UI card
  // every 2 beats. 8 beats = 120 fr, close to the measured opening shot (median 130 fr). Steps 4 and 3 + "No footage?".
  {beats: 8, bg: 'offWhite', device: {everyBeats: 2, cards: [
    {title: 'Morning run', subtitle: '5.2 km · 26:41', icon: '🏃'},
    {title: 'Pace', subtitle: '5:07 /km', icon: '⏱'},
    {title: 'Heart rate', subtitle: '148 bpm', icon: '♥'},
  ]}},

  // 2 | beats 8-10 | build starts. Feature title on white (typography device 1): icon above, 'title' size, fade.
  // First type card lands on the bar-3 downbeat, when bass and kick come in. Steps 3 and 5.
  {beats: 3, bg: 'white', icon: {glyph: '♥', ...HEART}, lines: ['Heart-rate zones'], entry: 'fade', size: 'title'},

  // 3 | beats 11-15 | shows the feature: the zones coaching you live, as UI and not as type. Dark phone on black,
  // one UI card per beat (measured UI entries run ~3.5/s, so 2/s is well inside that). Steps 3 and 4.
  {beats: 5, bg: 'black', device: {tone: 'dark', everyBeats: 1, cards: [
    {title: 'Zone 3', subtitle: '152 bpm · steady', icon: '♥'},
    {title: 'Zone 4', subtitle: 'Push for 2 min', icon: '↑'},
    {title: 'Ease off', subtitle: 'Back to Zone 3', icon: '↓'},
  ]}},

  // 4 | beats 16-18 | main section, drums full: the only whip in the video sits on this musical moment (step 6).
  // Entry 'cut' because the whip already moves the type in, so it doesn't need a second animation.
  // 'cut on' is the most common measured entry (25%). Step 5.
  {beats: 3, bg: 'white', icon: {glyph: '◯', ...RINGS}, lines: ['Weekly rings'], entry: 'cut', size: 'title', transition: 'whip'},

  // 5 | beats 19-27 | a long picture hold: icon wall read as a ring-week (3 rings x 7 days), slowly drifting.
  // A grid is one of the recommended no-footage picture carriers. 9 beats = one of the few long holds (step 4).
  {beats: 9, bg: 'black', grid: {icons: weekOfRings, columns: 7, rows: 3}},

  // 6 | beats 28-35 | a claim beside the phone: device at x 30, two short lines at x 60, left-aligned
  // (the "No footage?" layout). slideUpMask = the slide family (21%, 2nd most common entry). Headline size,
  // 2 lines max. The Coach tab UI builds up every 2 beats. 8-beat UI hold (step 4).
  {beats: 8, bg: 'offWhite', device: {x: 30, everyBeats: 2, cards: [
    {title: 'Coach', subtitle: 'Your plan this week', icon: '⚑'},
    {title: 'Today', subtitle: 'Easy 5 km · Zone 2', icon: '🏃'},
    {title: 'Thursday', subtitle: '6 × 400 m intervals', icon: '⏱'},
  ]}, lines: ['The new', 'Coach tab'], x: 60, align: 'left', size: 'headline', entry: 'slideUpMask'},

  // 7 | beats 36-39 | spec numeral (typography device 4): gradient '40%', only this card uses gradient type.
  // Default spec entry = scale down from large, like Apple's "18% / Faster GPU". Steps 3 and 5.
  {beats: 4, bg: 'white', spec: {value: '40%', label: 'longer watch battery life', gradient: [BATTERY.from, BATTERY.to]}},

  // 8-11 | beats 40-43 | four 1-beat picture cards, one per feature, building to the name (same idea as the example
  // script's final run). 15 fr each: above the <=10 fr "flash" threshold, near the measured shot p10 (13 fr). Step 4.
  // Black and white alternate at 2 changes per second, under the 3/s photosensitivity limit.
  {beats: 1, bg: 'black', icon: {glyph: '♥', ...HEART}},
  {beats: 1, bg: 'white', icon: {glyph: '◯', ...RINGS}},
  {beats: 1, bg: 'black', icon: {glyph: '⚑', ...COACH}},
  {beats: 1, bg: 'white', icon: {glyph: '⚡', ...BATTERY}},

  // 12 | beats 44-47 | the name on the bar-12 downbeat, "single word on black": cut on, display size, with the final
  // hit because the bed's own hit (beat 64) is outside 24 s. 60 fr, inside the measured last-shot range (p25 27 to p50 94 fr).
  // Steps 2 and 7.
  {beats: 4, bg: 'black', lines: ['Stride 2'], entry: 'cut', size: 'display', sfx: 'hit'},
];
// 8+3+5+3+9+8+4+1+1+1+1+4 = 48 beats = 720 frames = 24.0 s

export const strideProps: RecapProps = {bpm: 120, cards, music: 'music.wav', tailFrames: 0};
