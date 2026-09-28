// Beat grid helpers. Everything in frames.
// Apple recaps are timed to the voice-over first and the music second (see references/timing.md):
// use the grid to place cuts and hits, then nudge text onto the spoken word.

export type BeatGrid = {
  bpm: number;
  fps: number;
  /** frame of the first beat (music offset) */
  offset: number;
  /** frames per beat (float) */
  beat: number;
  /** frames per 4/4 bar (float) */
  bar: number;
};

export const beatGrid = (bpm: number, fps: number, offset = 0): BeatGrid => {
  const beat = (60 / bpm) * fps;
  return {bpm, fps, offset, beat, bar: beat * 4};
};

/** Frame of beat n (0-based), rounded to the nearest frame. Fractions allowed: onBeat(g, 2.5). */
export const onBeat = (g: BeatGrid, n: number): number => Math.round(g.offset + n * g.beat);

/** Frame of bar n (0-based) downbeat. */
export const onBar = (g: BeatGrid, n: number): number => Math.round(g.offset + n * g.bar);

/** Snap an arbitrary frame to the nearest beat subdivision (1 = beat, 2 = 8th, 4 = 16th). */
export const snap = (g: BeatGrid, frame: number, subdivision = 1): number => {
  const step = g.beat / subdivision;
  return Math.round(g.offset + Math.round((frame - g.offset) / step) * step);
};

/** Duration of n beats in whole frames (use for Sequence durationInFrames). */
export const beats = (g: BeatGrid, n: number): number => Math.round(n * g.beat);
