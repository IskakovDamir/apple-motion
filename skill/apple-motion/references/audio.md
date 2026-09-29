# Audio: music, voice, SFX, loudness

Numbers: `measurements.md` (BPM per video, integrated LUFS, true peak, LRA, VO words/s, SFX rate).

## Music

- Upbeat electronic/pop beds; BPM per video is in measurements.md (BPM from a line fit of beat
  times, not librosa's quantised tempo bin - see the report). Sections are few and long: an energy
  lift into the main part, a short breakdown, a final hit or a clean stop on the logo.
- Under voice-over the bed sits roughly 10-15 dB below the voice (stem RMS shares in the report).
- License real music or generate a bed: `scripts/synth_audio.py OUT --bpm 120 --bars 16` writes a
  CC0 bed (kick, clap, hats, bass, supersaw chords, pluck arp, riser, final hit) and an SFX kit.

## Bed layout of `synth_audio.py`

`--bars N` (default 16): bars 1-2 intro (pads, hats), 3-4 build (bass, kick), then main (full drums,
arp) up to the break, a 2-bar break with the drums out and a riser (bars N-3..N-2), the last 2 bars
final, and a closing hit exactly on beat 4N (the bar line after the last bar). Beat 0 is t = 0. Plan cards so the logo starts on beat 4N; the bed already has the
hit, so don't add `sfx: 'hit'` there.

## Voice-over

- Fast, conversational, dense: words per second while speaking in measurements.md. Few pauses; the
  voice is continuous and the picture changes under it.

## SFX

- Sparse and mostly musical: transients that are not on the music grid are a few per 10 s.
  Whooshes on whips, soft clicks on UI taps, a hit on the final logo. Pre-roll whooshes so the peak
  (not the file start) lands on the cut - `Sfx.tsx` does this.

## Loudness

Master to the measured integrated loudness and true-peak ceiling (`AUDIO.lufs` / `AUDIO.truePeakDb`
in tokens.ts, the medians of the six videos; the corpus spans about -16.5 to -21.6 LUFS):

```bash
scripts/master.sh out.mp4 final.mp4          # two-pass loudnorm to the token targets, video copied
```
