// Compiles and renders the card script from skill/apple-motion/references/example-script.md
import type {Card, RecapProps} from '@apple-motion';

export const exampleCards: Card[] = [
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
  // break (44-55): drums drop out - one calm hold
  {beats: 12, bg: 'gradient', gradient: ['#0a84ff', '#5e5ce6'], lines: ['Your notes. Everywhere.'], entry: 'perWord', size: 'headline'},
  // final (56-63): four 2-beat picture cards building to the hit
  {beats: 2, bg: 'white', icon: {glyph: '↻', from: '#64d2ff', to: '#0a84ff'}},
  {beats: 2, bg: 'black', icon: {glyph: '⌕', from: '#ff9f0a', to: '#ff375f'}},
  {beats: 2, bg: 'white', icon: {glyph: '▦', from: '#30d158', to: '#00a86b'}},
  {beats: 2, bg: 'black', icon: {glyph: '⚡', from: '#ffd60a', to: '#ff9f0a'}},
  // beat 64 = the bed's closing hit: logo, no extra sfx
  {beats: 8, bg: 'black', lines: ['Northwind Notes'], entry: 'scaleDown', size: 'display'},
];

export const exampleProps: RecapProps = {bpm: 120, cards: exampleCards, music: 'music.wav'};
