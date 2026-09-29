# Example: a 37-second launch recap as cards

Brief: "30-second Apple-style recap for Northwind Notes 3.0: offline sync, smart search, 2x faster
to open, new widgets. Music only, end on the logo."

Length first: 120 BPM (1 beat = 15 frames at 30 fps). 64 beats of cards (32 s) + an 8-beat logo
(4 s) + the 45-frame tail = 1125 frames = 37.5 s. (For exactly 30 s use 12 bars and a 6-beat logo,
see SKILL.md step 2.) The bed from `scripts/synth_audio.py public --bpm 120 --bars 16` has: intro
bars 1-2 (beats 0-7), build 3-4 (8-15), main 5-12 (16-47), break 13-14 (48-55, drums out), final
15-16 (56-63), its closing hit on beat 64 and ~4 s of ring-out. The logo card starts on beat 64.

```ts
const cards: Card[] = [
  // intro (beats 0-7): open on motion, no title - median Apple opening shot is ~4 s
  {beats: 8, bg: 'offWhite', device: {cards: [
    {title: 'Northwind 3.0', subtitle: "What's new", icon: '📝'},
    {title: 'Launch plan', subtitle: 'edited offline', icon: '✈️'}], everyBeats: 3}},
  // build (8-15): name the first feature, then show it
  {beats: 3, bg: 'white', icon: {glyph: '↻', from: '#64d2ff', to: '#0a84ff'}, lines: ['Offline sync'], entry: 'fade', size: 'title'},
  {beats: 5, bg: 'black', device: {tone: 'dark', cards: [
    {title: 'Offline', subtitle: '3 edits saved', icon: '✈️'},
    {title: 'Back online', subtitle: 'all synced', icon: '✓'}], everyBeats: 2}},
  // main (16-47): one whip on the downbeat where the drums are full
  {beats: 3, bg: 'white', icon: {glyph: '⌕', from: '#ff9f0a', to: '#ff375f'}, lines: ['Smart search'], entry: 'fade', size: 'title', transition: 'whip'},
  {beats: 9, bg: 'offWhite', device: {x: 30, cards: [
    {title: 'receipt', subtitle: '3 results', icon: '⌕'}]},
    lines: ['Finds what', 'you meant.'], x: 58, align: 'left', size: 'headline', entry: 'slideUpMask'},
  {beats: 3, bg: 'white', icon: {glyph: '▦', from: '#30d158', to: '#00a86b'}, lines: ['Widgets'], entry: 'fade', size: 'title'},
  {beats: 9, bg: 'black', grid: {icons: [{glyph: '▦', from: '#30d158', to: '#00a86b'}, {glyph: '☼', from: '#ffd60a', to: '#ff9f0a'}, {glyph: '✎', from: '#64d2ff', to: '#0a84ff'}], columns: 6, rows: 3}},
  {beats: 4, bg: 'white', spec: {value: '2x', label: 'faster to open', gradient: ['#b150e2', '#e0417b']}},
  // calm hold from beat 44 into the break (drums drop out at beat 48)
  {beats: 12, bg: 'gradient', gradient: ['#0a84ff', '#5e5ce6'], lines: ['Your notes. Everywhere.'], entry: 'perWord', size: 'headline'},
  // final (56-63): four 2-beat picture cards building to the hit
  {beats: 2, bg: 'white', icon: {glyph: '↻', from: '#64d2ff', to: '#0a84ff'}},
  {beats: 2, bg: 'black', icon: {glyph: '⌕', from: '#ff9f0a', to: '#ff375f'}},
  {beats: 2, bg: 'white', icon: {glyph: '▦', from: '#30d158', to: '#00a86b'}},
  {beats: 2, bg: 'black', icon: {glyph: '⚡\uFE0E', from: '#ffd60a', to: '#ff9f0a'}},
  // beat 64 = the bed's closing hit: logo, no extra sfx
  {beats: 8, bg: 'black', lines: ['Northwind Notes'], entry: 'scaleDown', size: 'display'},
];
// 8+3+5+3+9+3+9+4+12+2+2+2+2 = 64 -> the logo starts on beat 64
```

Check the arithmetic before rendering: `cardStarts(cards, 120, 30)` gives every start frame; the
logo must start at frame 960 (beat 64). Re-add the beats after every edit.

Why it reads as Apple (all backed by `measurements.md`):

- Picture carries most cards (device, grid, icons, spec); type appears about every 5-6 s.
- Median card 3-4 beats (1.5-2 s), a few 8-12 beat holds, a long opening shot.
- One whip, the rest hard cuts.
- The final card lands on the bar line where the music hits (every card starts on its beat).
- No bouncy or rotating type, no coloured boxes behind text.
