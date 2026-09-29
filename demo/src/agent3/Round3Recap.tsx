import type {Card, RecapProps} from '@apple-motion';

/**
 * Lumen CLI 4 - WWDC-style 20 s recap, music only, no footage.
 *
 * Length first (SKILL step 2): 128 BPM (brief says "upbeat, fast": between the measured p75 125.3 and
 * p90 131.3), 9 bars = 36 beats of cards + a 4-beat logo. At 30 fps 1 beat = 14.0625 frames, so
 * 40 beats = 563 frames + tailFrames 45 = 608 frames = 20.3 s.
 * Bed: `synth_audio.py demo/public/agent3 --bpm 128 --bars 9`, loudnormed to AUDIO.lufs / AUDIO.truePeakDb
 * -> public/agent3/music.wav. Sections (0-based beats): intro 0-7, build 8-15 (kick + bass),
 * main 16-19 (full drums + arp), break 20-27 (drums out, riser), final 28-35, closing hit on beat 36.
 *
 * Type moments (SKILL step 5, one per 5-7 s without VO): "3x" 3.75 s, "First-class Swift" 7.5 s,
 * "Redesigned dashboard." 13.1 s, "Lumen CLI 4" 16.9 s. Cloud cache is named inside the UI only.
 * UI strings inside the phones are placeholder product UI, not claims - swap in real ones.
 */

const SPEED = {glyph: '⚡', from: '#bf5af2', to: '#ff375f'};
const CACHE = {glyph: '☁', from: '#64d2ff', to: '#0a84ff'};
const SWIFT = {glyph: '{ }', from: '#ff9f0a', to: '#ff453a'};

const cards: Card[] = [
  // beats 0-7 (intro, pads + hats). Step 4: long opening shot (8 beats = 112 fr, measured first shot
  // p25-p50 83-130 fr) that starts on motion, not a title. "No footage?": device on #f5f5f7, build
  // notifications pop every 2 beats; tapSfx = soft UI clicks (step 7) in the quiet intro.
  {beats: 8, bg: 'offWhite', device: {cards: [
    {title: 'lumen build', subtitle: 'app-ios · release', icon: '▸'},
    {title: 'Compiling', subtitle: 'Swift + TypeScript', icon: '⚙'},
    {title: 'Build succeeded', subtitle: 'ready to ship', icon: '✓'}], everyBeats: 2, tapSfx: true}},

  // beat 8 = build section, kick enters. Step 3/5 + typography device 4 (spec numerals): the headline
  // claim as gradient numerals, default scaleDown entry (Apple's "18% / Faster CPU" is scale-down).
  {beats: 4, bg: 'white', spec: {value: '3x', label: 'faster builds', gradient: [SPEED.from, SPEED.to]}},

  // beats 12-15: the cache feature named INSIDE the UI (step 5: more features than type moments allow).
  // Dark phone on black, one UI card per beat so the 4-beat shot keeps moving (editing.md: something
  // always moves).
  {beats: 4, bg: 'black', device: {tone: 'dark', cards: [
    {title: 'Cloud cache', subtitle: 'connected', icon: '☁'},
    {title: 'Cache hit', subtitle: 'restored remotely', icon: '⚡'},
    {title: 'Shared with team', subtitle: 'every branch', icon: '⇄'}], everyBeats: 1}},

  // beat 16 = main section downbeat (full drums + arp). Typography device 1 (feature title on white):
  // icon above, one line, size title, entry fade. Hard cut (step 6: >90% cuts).
  {beats: 4, bg: 'white', icon: SWIFT, lines: ['First-class Swift'], entry: 'fade', size: 'title'},

  // beats 20-27 = break (drums out, riser). Step 4: one long picture hold (8 beats) where the music
  // breathes; "No footage?": icon wall, slow drift, colour carried by the tiles. No type.
  {beats: 8, bg: 'black', grid: {icons: [
    SWIFT, {glyph: '◆', from: '#30d158', to: '#00a86b'}, CACHE, {glyph: '▲', from: '#ffd60a', to: '#ff9f0a'},
    SPEED, {glyph: '●', from: '#5ac8fa', to: '#30b0c7'}, {glyph: '■', from: '#ff6482', to: '#ff375f'}], columns: 9, rows: 5}},

  // beat 28 = the drop after the riser, the biggest musical moment before the hit: the ONE accent
  // (step 6: whip, on a musical moment; whoosh placed automatically). "No footage?" layout: device at
  // x 30, two-line headline at x 58 left-aligned, slideUpMask (same recipe as example-script's
  // "Finds what / you meant." card; 2 lines is the stated maximum, step 5).
  {beats: 4, bg: 'offWhite', transition: 'whip', device: {x: 30, cards: [
    {title: 'Builds', subtitle: 'all green', icon: '▦'},
    {title: 'Cache', subtitle: 'synced', icon: '☁'},
    {title: 'Swift targets', subtitle: 'up to date', icon: '{}'}], everyBeats: 1},
    lines: ['Redesigned', 'dashboard.'], x: 58, align: 'left', size: 'headline', entry: 'slideUpMask'},

  // beats 32-35 = final section: short picture-only icon cards accelerating 2-1-1 beats into the hit
  // (example-script's closing run, shortened; 14 fr min stays above the <=10 fr montage threshold, step 4).
  {beats: 2, bg: 'white', icon: SPEED},
  {beats: 1, bg: 'black', icon: CACHE},
  {beats: 1, bg: 'white', icon: SWIFT},

  // beat 36 = the bed's closing hit (step 2: logo starts there, no sfx:'hit'). Typography device 3
  // (single word/name on black), display size, scaleDown. Holds 4 beats + 45-frame tail = 101 fr
  // (measured last shot median 94 fr).
  {beats: 4, bg: 'black', lines: ['Lumen CLI 4'], entry: 'scaleDown', size: 'display'},
];
// 8+4+4+4+8+4+2+1+1 = 36 -> the logo starts on beat 36 = frame round(36 * 14.0625) = 506 (hit at 506.25).

export const round3Props: RecapProps = {bpm: 128, cards, music: 'agent3/music.wav'};
