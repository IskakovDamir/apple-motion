# Audio: music, voice, SFX, loudness

Numbers: `measurements.md` (BPM per video, integrated LUFS, true peak, LRA, VO words/s, SFX rate).

## Music

- Upbeat electronic/pop beds; BPM per video is in measurements.md (BPM from a line fit of beat
  times, not librosa's quantised tempo bin - see the report). Sections are few and long: an energy
  lift into the main part, a short breakdown, a final hit or a clean stop on the logo.
- Under voice-over the bed sits roughly 10-15 dB below the voice (stem RMS shares in the report).
- License real music or generate a bed: `scripts/synth_audio.py OUT --bpm 120 --bars 16` writes a
  CC0 bed (kick, clap, hats, bass, supersaw chords, pluck arp, riser, final hit) and an SFX kit.

## Voice-over

- Fast, conversational, dense: words per second while speaking in measurements.md. Few pauses; the
  voice is continuous and the picture changes under it.

## SFX

- Sparse and mostly musical: transients that are not on the music grid are a few per 10 s.
  Whooshes on whips, soft clicks on UI taps, a hit on the final logo. Pre-roll whooshes so the peak
  (not the file start) lands on the cut - `Sfx.tsx` does this.

## Loudness

Master to the measured integrated loudness and true-peak ceiling (see measurements.md; the Apple
videos sit around -16 to -22 LUFS with -1 to -4 dBTP true peak):

```bash
ffmpeg -i out.mp4 -af loudnorm=I=-16:TP=-1.5:LRA=7 -c:v copy out_mastered.mp4
```
