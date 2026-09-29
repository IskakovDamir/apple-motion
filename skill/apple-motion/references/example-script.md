# Example: a 32-second launch recap as cards

Brief: "30-second Apple-style recap for Northwind Notes 3.0: offline sync, smart search, 2x faster,
new widgets. Music only, end on the logo." 120 BPM -> 1 beat = 15 frames, 16 bars = 64 beats.

```ts
const cards: Card[] = [
  // Open on motion, not on a title: product in hand / UI already moving (2 beats = 1 s).
  {beats: 2, bg: 'black', media: {src: 'open-device.mp4', type: 'video'}},
  // One word, cut on (most measured type cuts on with its shot), short hold.
  {beats: 2, bg: 'black', lines: ['Northwind Notes 3'], entry: 'cut', size: 'headline'},
  // Feature 1: picture first, then its name as a feature-title card on white.
  {beats: 3, bg: 'offWhite', device: {cards: [
    {title: 'Offline', subtitle: 'Edits saved on device', icon: '✈️'},
    {title: 'Back online', subtitle: '12 notes synced', icon: '↻'}]}},
  {beats: 2, bg: 'white', icon: {glyph: '↻', from: '#64d2ff', to: '#0a84ff'}, lines: ['Offline sync'], entry: 'fade', size: 'title'},
  // Feature 2 with a whip on a musical accent (accents only - most edits stay cuts).
  {beats: 3, bg: 'black', media: {src: 'search.mp4', type: 'video'}, transition: 'whip'},
  {beats: 2, bg: 'white', icon: {glyph: '⌕', from: '#ff9f0a', to: '#ff375f'}, lines: ['Smart search'], entry: 'fade', size: 'title'},
  // Spec: gradient numerals are the one place Apple fills type with a gradient.
  {beats: 4, bg: 'white', spec: {value: '2x', label: 'faster launch', gradient: ['#b150e2', '#e0417b']}, entry: 'scaleDown'},
  // Claim over footage: white, left third, two short lines.
  {beats: 4, bg: 'black', media: {src: 'widgets.mp4', type: 'video'}, lines: ['New widgets.', 'Everywhere.'],
   entry: 'slideUpMask', size: 'headline', align: 'left', x: 9},
  // Montage run before the finale: 1-beat cuts (measured "montage runs" of short shots).
  {beats: 1, bg: 'black', media: {src: 'm1.mp4', type: 'video'}},
  {beats: 1, bg: 'black', media: {src: 'm2.mp4', type: 'video'}},
  {beats: 1, bg: 'black', media: {src: 'm3.mp4', type: 'video'}},
  {beats: 1, bg: 'black', media: {src: 'm4.mp4', type: 'video'}},
  // Wordmark: scale down into place, dissolve in, hit on the downbeat, hold 2-4 bars.
  {beats: 8, bg: 'black', lines: ['Northwind Notes'], entry: 'scaleDown', size: 'hero', transition: 'dissolve', sfx: 'hit'},
];
```

Why it reads as Apple (all backed by `measurements.md`):

- Picture carries most cards; type appears ~every 3-4 s, never as a paragraph.
- Card lengths are mostly 1-3 beats (0.5-1.5 s) with a few longer holds; the median shot in the
  corpus is under a second.
- Only two transitions that are not cuts, each on a musical accent.
- The final card lands on a bar line (every card starts on its beat, the engine guarantees it).
- No bouncy type, no rotating type, no coloured boxes behind text.
