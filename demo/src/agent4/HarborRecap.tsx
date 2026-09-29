import {type Card, type RecapProps} from '@apple-motion';

/**
 * Harbor - 25 s launch recap, cut to the voice-over (public/agent4/vo.wav).
 *
 * Timing (SKILL.md "With a voice-over"):
 *   vo_cards.py src/agent4/cards.json --words src/agent4/words.json --lead-in 7.2 --tail-beats 11.766
 *     -o src/agent4/cards_timed.json          -> the `beats` below, voiceFromFrames 216
 *   words.json = faster-whisper words checked against the waveform's silences: "Pasquis" -> "Passkeys"
 *   (6.58 -> 6.41 s), and the closing "Harbor" moved from 10.12 to 10.58 s (whisper glued it to
 *   "always"; uncorrected, the logo would have cut in 14 frames early, on "always").
 *   Edit cards.json and re-run instead of hand-editing beats.
 * Music: synth_audio.py public/agent4 --bpm 122 --bars 11 (vo_cards suggests 12 - see the logo card).
 *
 * Why 122 BPM and a 7.2 s lead-in: the two spoken "Harbor"s are 9.82 s apart = 5 bars at 122 BPM
 * (between the measured p50 118.8 and p75 125.3). Voice at 7.2 s puts the first "Harbor" on bar 4 (the
 * bed's drop into its main section, frame 236) and the closing "Harbor" on bar 9 (the drop after the
 * break, frame 531). editing.md: "for VO pieces, cut on phrase boundaries and snap only the big moments
 * (title card, final logo) to a downbeat". All other cuts follow the voice, not the grid.
 *
 * Shape vs. measurements: 9 cards / 8 cuts in 25 s = 3.2 cuts per 10 s (median 3.24); median shot
 * 51 frames (median 56.5); hard cuts only (92% of measured edits, and a whoosh would sit on a word -
 * the VO has no gap longer than 0.25 s); 3 type moments (Harbor, Passkeys, Harbor).
 * Glyphs: plain text symbols only (SKILL.md "pick one style per video"); checked that each resolves
 * to a text font on macOS, not Apple Color Emoji (the anchor U+2693 does, so Harbor uses the helm ⎈).
 */

// Start frames at 30 fps (cardStarts): 0, 118, 237, 288, 324, 361, 406, 447, 531; end 705 + 45 tail = 750.
const cards: Card[] = [
  // 0-118, music only (bed intro). Open on motion, not a title (SKILL step 4; measured first shot median
  // 130 fr): an icon wall ("all the apps" device, editing.md) = every account you have a password for.
  // No footage -> grid (SKILL "No footage?"); autoMove gives it a push on top of the grid's drift.
  {beats: 8.0249, bg: 'black', grid: {columns: 9, rows: 5, icons: [
    {glyph: '✉', from: '#64d2ff', to: '#0a84ff'},
    {glyph: '♫', from: '#ff6b81', to: '#ff2d55'},
    {glyph: '$', from: '#4cd964', to: '#28a745'},
    {glyph: '✈', from: '#5ac8fa', to: '#007aff'},
    {glyph: '☼', from: '#ffd60a', to: '#ff9f0a'},
    {glyph: '⚙', from: '#8e8e93', to: '#48484a'},
    {glyph: '♥', from: '#ff375f', to: '#d70015'},
    {glyph: '☁', from: '#8ec5ff', to: '#3a7bd5'},
    {glyph: '✎', from: '#ff9f0a', to: '#ff453a'},
    {glyph: '⌂', from: '#30d158', to: '#00a86b'},
    {glyph: '▶', from: '#ff453a', to: '#c9302c'},
    {glyph: '★', from: '#ffe066', to: '#ffb300'},
  ]}},

  // 118-237, music only (bed build), cut on bar 2 - the lead-in has no voice to follow, so the beat grid
  // rules here. The problem: login errors pop on every 2nd beat with UI tap clicks (SKILL step 7: SFX on
  // UI taps). "Say hello to" starts at frame 216 over this shot, so the cut to the name lands on the name.
  {beats: 8.0249, bg: 'offWhite', device: {everyBeats: 2, tapSfx: true, cards: [
    {title: 'Forgot password?', subtitle: 'Reset link sent', icon: '?'},
    {title: 'Wrong password', subtitle: 'Try again', icon: '!'},
    {title: 'Password expired', subtitle: 'Choose a new one', icon: '×'},
  ]}},

  // 237 = bar 4, onWord "Harbor": the product name on the drop. Feature title on white (typography.md
  // device 1: icon above, one-line title, `fade`, size title). Type appears 2 frames before the word
  // (VO.typeLeadFrames). Holds through "every password," - one breath in the read, and the next pause
  // (after "Harbor,") would leave the name up for only 18 frames.
  {beats: 3.477, bg: 'white', icon: {glyph: '⎈', from: '#3a8dff', to: '#0b3d91'}, lines: ['Harbor'], entry: 'fade', size: 'title'},

  // 288, onWord "on": cut in the breath before "on every device" (afterPhrase can only take the NEXT
  // pause, which is the wrong one here). The devices are named inside the UI, not on their own type
  // card (SKILL step 5); the three syncs pop every half beat under "every device".
  {beats: 2.4332, bg: 'black', device: {tone: 'dark', everyBeats: 0.5, cards: [
    {title: 'Mac', subtitle: 'Synced · just now', icon: '⇄'},
    {title: 'iPad', subtitle: 'Synced · just now', icon: '⇄'},
    {title: 'Apple Watch', subtitle: 'Synced · just now', icon: '⇄'},
  ]}},

  // 324, afterPhrase (mid-pause after "device."): "It fills in for you," - a password field that fills
  // itself, in 0.33 s. Typing device (typography.md device 6) as a UI close-up; not a type moment.
  {beats: 2.4908, bg: 'white', typing: {text: '••••••••••••', cps: 36}},

  // 361, afterPhrase (pause after "you,"): "before you even ask." - the result, in UI. entry 'none'
  // (a cut to the phone, no second rise in a row); "Signed in" pops on "even ask".
  {beats: 3.0873, bg: 'offWhite', device: {entry: 'none', everyBeats: 1, cards: [
    {title: 'Harbor', subtitle: 'Password filled', icon: '⎈'},
    {title: 'Signed in', subtitle: 'Online banking', icon: '✓'},
  ]}},

  // 406, onWord "Passkeys": second feature title, same recipe as the measured "Core AI" / "App Intents"
  // / "Device Hub" cards (fade, ~7 frames, near-black on #f3f3f5 - measurements.md examples).
  // This is the one type moment beyond the measured VO rate (0.8 per 10 s = 2 in 25 s): with no
  // footage the icon + title card is the strongest Apple device available, so it stays.
  {beats: 2.7891, bg: 'white', icon: {glyph: '⚿', from: '#ffd60a', to: '#ff9f0a'}, lines: ['Passkeys'], entry: 'fade', size: 'title'},

  // 447, afterPhrase (pause after "built in,"): "your vault is end-to-end encrypted, always." The longest
  // hold of the middle (editing.md: alternate quick shots with a longer one), under the bed's break
  // (drums out, riser). The claim stays in the UI in the user's own words; the 2nd card pops 4 frames
  // before "always". autoMove gives it a pull.
  {beats: 5.6899, bg: 'black', device: {tone: 'dark', everyBeats: 2, cards: [
    {title: 'Vault locked', subtitle: 'End-to-end encrypted', icon: '⚿'},
    {title: 'Encryption', subtitle: 'Always on', icon: '✓'},
  ]}},

  // 531 = bar 9, onWord "Harbor": the wordmark (SKILL example logo: lines only, scaleDown, display) on
  // the drop after the break. Not on the bed's closing hit: that would need a 10.5 s voiceless lead-in
  // for a 25 s film; the 11-bar bed plays its final 2 bars under the logo and hits at frame 649 (no
  // `sfx: 'hit'` - the drop is the accent). Navy gradient instead of black: a 7.3 s black end card alone
  // would make ~30% of the frames pure black (corpus: 8%). Holds 174 + 45 tail frames = 7.3 s (measured
  // last shot p75 195 / p90 280 frames) - long, because the voice is 12.4 s of a 25 s brief.
  {beats: 11.766, bg: 'gradient', gradient: ['#06142e', '#0b3d91'], lines: ['Harbor'], entry: 'scaleDown', size: 'display'},
];

export const harborProps: RecapProps = {
  bpm: 122,
  cards,
  music: 'agent4/music.wav',
  voice: 'agent4/vo.wav',
  voiceFrom: 216, // vo_cards.py voiceFromFrames (7.2 s lead-in)
  sfxDir: 'agent4/sfx',
};
