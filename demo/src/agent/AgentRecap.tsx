import type {Card, RecapProps} from '@apple-motion';

/*
 * Northwind Notes 3.0 - 30 s launch recap, music only, ends on the logo.
 * Built only from the skill's library (DeviceFrame + UICard, AppIcon feature titles, spec numerals,
 * Backdrop). No footage, no voice-over.
 *
 * "SKILL n" = step n of "How to build one" in SKILL.md; numbers are from references/measurements.md.
 *
 * MUSIC MAP (public/music.wav, 120 BPM, 1 beat = 15 fr, SKILL 2). Checked against the file's RMS:
 *   bars 0-1  (beats 0-7)   intro: pad + hats, no kick
 *   bars 2-3  (beats 8-15)  build: kick, clap, bass come in
 *   bars 4-11 (beats 16-47) main: full band + arp
 *   bars 12-13 (beats 48-55) break: drums out, riser
 *   bars 14-15 (beats 56-63) final: drop; the bed's own closing hit sounds at beat 64 (frame 960)
 *
 * PACING (SKILL 3, editing.md "Pace")
 * - 66 beats = 33 s of cards + 15 fr tail. The bed's structure sets the length, not the brief: the drop is
 *   at 28 s and its closing hit at 32 s, so the logo lands on the drop and holds through that hit.
 * - 14 cards, 13 cuts -> 3.9 cuts / 10 s (measured median 3.24, p75 5.13).
 * - Card lengths 15-150 fr, median 52.5 fr (measured median shot 56.5 fr, p90 173.5).
 * - First card 120 fr (measured first shot p50 130 fr). Last card 150 fr (last shot p50 94, p75 195).
 * - Feature title -> UI demo pairs: titles 3 beats (45 fr) because the measured "feature title on white"
 *   examples (Core AI, App Intents, Xcode Cloud, Journal) sit on screen about 40-90 fr; demos 5-9 beats are
 *   the "few longer holds on product or UI", and inside each one a UI card pops on every beat so
 *   something always moves (editing.md: "Within a longer shot something always moves").
 * - Music-only piece, so every cut sits on a beat, and the big moments land on bar downbeats
 *   (SKILL "Sync", editing.md "Practical rule"): the titles on beats 8, 16, 28, the spec on 40, the icon run on 52,
 *   the logo on 56. The UI demos start on off-bar beats so it doesn't feel like a slideshow.
 * - 1-beat run of the four feature icons over the riser's last bar, then the logo (SKILL 3: "quick run of
 *   1-beat cards before the finale"). 15 fr each, so no "montage run" of <= 10 fr shots (measured median 0/min).
 *
 * TYPE (SKILL 4, typography.md)
 * - Designer type only for feature names (3 titles), one number (2x) and the logo = 5 events in 33 s
 *   (1.5 / 10 s). That's above the measured 0.78 (p90 0.94), which comes from recaps where a voice-over names
 *   the features. Here nothing else can name them. The product name at the top lives in the UI
 *   ("What's new in 3.0"), not as a type card, to keep designer type down.
 * - Feature titles: device #1 "feature title on white": icon above, graphite Semibold, size 'title' (cap 5.43%;
 *   the measured feature titles are 5.3-5.7%), entry 'fade' (the recurring WWDC26 feature-title entry).
 * - Spec: device #4, gradient numerals (the only non-flat type), entry 'scaleDown' (measured "18%").
 * - Logo: app icon + wordmark, size 'headline' not 'hero'. At hero (cap 20.23%) "Northwind Notes" would be about
 *   2300 px wide and not fit 1920. Entry 'scaleUp' so the wordmark grows in the same direction as the AppIcon's
 *   0.9 -> 1 spring (scaleDown would fight it).
 * - All exits are the default cut (measured cut off 47%, the most common exit).
 *
 * TRANSITIONS (SKILL 5)
 * - 12 hard cuts + 1 whip = 8% non-cut (measured: cut 92%, whip 5%). The whip is into "Smart search" on
 *   beat 16, where the main section and the arp come in. The engine adds the whoosh.
 * - No dissolve into the logo: the drop plus the hit carry it, and a cut is the measured default.
 *
 * SOUND (SKILL 6, audio.md)
 * - Bed only. SFX: the automatic whoosh on the whip, plus 'hit' on the logo's first frame (the drop).
 *   The bed's own closing hit at beat 64 falls while the logo is still up, so the video ends on the logo.
 * - Colour: icons use system-like gradients (green, yellow, orange-red, teal). The brand is amber-orange
 *   (logo tile and 2x). No coloured boxes behind type, no shadows (typography.md "Never").
 */

const cards: Card[] = [
  // 0-8 intro (quiet). Open on motion, not on a title: the phone rises and notes pop one per beat. 8 beats =
  // 120 fr, close to the measured first-shot median (130 fr). The UI carries the product name.
  {
    beats: 8,
    bg: 'offWhite',
    device: {
      tone: 'light',
      cards: [
        {title: 'Northwind Notes', subtitle: "What's new in 3.0", icon: '✦'},
        {title: 'Launch plan', subtitle: 'Edited just now', icon: '✎'},
        {title: 'Reading list', subtitle: '12 notes', icon: '☰'},
        {title: 'Weekly review', subtitle: 'Friday, 9:00', icon: '◷'},
      ],
    },
  },

  // 8 kick in. Feature 1 title on white; cuts on with the downbeat.
  {beats: 3, bg: 'white', icon: {glyph: '↻', from: '#5ce07a', to: '#28a745'}, lines: ['Offline sync'], entry: 'fade', size: 'title'},
  // 11-16 offline -> back online -> synced, one UI state per beat (dark device on black for contrast).
  {
    beats: 5,
    bg: 'black',
    device: {
      tone: 'dark',
      cards: [
        {title: 'Offline', subtitle: 'Edits saved on device', icon: '⊘'},
        {title: 'Back online', subtitle: 'Syncing 3 notes', icon: '↻'},
        {title: 'All notes synced', subtitle: 'Just now', icon: '✓'},
      ],
    },
  },

  // 16 main section + arp: the one whip, as an accent on the musical change.
  {beats: 3, bg: 'white', icon: {glyph: '⌕', from: '#ffd60a', to: '#ff9f0a'}, lines: ['Smart search'], entry: 'fade', size: 'title', transition: 'whip'},
  // 19-28 query, then results pop in on the beat. Longer UI hold (135 fr, under measured p90 173.5).
  {
    beats: 9,
    bg: 'offWhite',
    device: {
      tone: 'light',
      cards: [
        {title: '“receipt”', subtitle: 'Searching all notes', icon: '⌕'},
        {title: 'March trip', subtitle: '2 matches', icon: '▣'},
        {title: 'Budget 2026', subtitle: '1 match', icon: '≡'},
        {title: 'Tax documents', subtitle: '3 matches', icon: '▤'},
      ],
    },
  },

  // 28 (bar 7 downbeat). Feature 3 title.
  {beats: 3, bg: 'white', icon: {glyph: '▦', from: '#64e3e0', to: '#1ea6ba'}, lines: ['Home Screen widgets'], entry: 'fade', size: 'title'},
  // 31-40 widgets stacking on a dark home screen, one per beat.
  {
    beats: 9,
    bg: 'black',
    device: {
      tone: 'dark',
      cards: [
        {title: 'Today', subtitle: '3 notes due', icon: '▦'},
        {title: 'Quick note', subtitle: 'Tap to write', icon: '✎'},
        {title: 'Pinned', subtitle: 'Launch plan', icon: '✦'},
        {title: 'Recent', subtitle: 'Reading list', icon: '☰'},
      ],
    },
  },

  // 40 (bar 10 downbeat). The number: gradient numerals + small label.
  {beats: 4, bg: 'white', spec: {value: '2x', label: 'faster to open', gradient: ['#ff9f0a', '#ff453a']}, entry: 'scaleDown'},

  // 44-52 recap in the product's own UI: the What's New sheet. The 4th row pops on beat 48, when the
  // drums drop out. The rest is a calm hold across the break.
  {
    beats: 8,
    bg: 'offWhite',
    device: {
      tone: 'light',
      cards: [
        {title: 'Offline sync', subtitle: 'Edit without a signal', icon: '↻'},
        {title: 'Smart search', subtitle: 'Find any note', icon: '⌕'},
        {title: 'Faster launch', subtitle: 'Opens 2x faster', icon: '≫'},
        {title: 'Widgets', subtitle: 'On your Home Screen', icon: '▦'},
      ],
    },
  },

  // 52-56 riser's last bar: 1-beat run of the four feature icons, swapped in place on white (no type).
  {beats: 1, bg: 'white', icon: {glyph: '↻', from: '#5ce07a', to: '#28a745'}},
  {beats: 1, bg: 'white', icon: {glyph: '⌕', from: '#ffd60a', to: '#ff9f0a'}},
  {beats: 1, bg: 'white', icon: {glyph: '2x', from: '#ff9f0a', to: '#ff453a'}},
  {beats: 1, bg: 'white', icon: {glyph: '▦', from: '#64e3e0', to: '#1ea6ba'}},

  // 56 drop: logo on a hard cut + hit, held 10 beats (150 fr) so the bed's own closing hit (beat 64) lands
  // on it and the video ends on the logo.
  {beats: 10, bg: 'black', icon: {glyph: 'N', from: '#ffb340', to: '#ff7a00'}, lines: ['Northwind Notes'], entry: 'scaleUp', size: 'headline', sfx: 'hit'},
];

// tailFrames 15: the closing hit (frame 960) has decayed to about -45 dBFS by frame 1005, so 15 fr of black
// after the logo (ends at 990) lets it ring out without dead air.
export const agentProps: RecapProps = {bpm: 120, offsetFrames: 0, cards, music: 'music.wav', tailFrames: 15};
