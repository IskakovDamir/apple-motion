import React from 'react';
import {Html5Audio, Sequence, staticFile} from 'remotion';

export type SfxName = 'whoosh' | 'swish' | 'click' | 'hit' | 'riser';

/** Pre-roll so the transient (not the file start) lands on `at`. Whooshes peak ~55% into the file. */
const PREROLL: Record<SfxName, number> = {whoosh: 7, swish: 4, click: 0, hit: 0, riser: 58};

export const Sfx: React.FC<{name: SfxName; at: number; volume?: number; dir?: string}> = ({name, at, volume = 0.5, dir = 'sfx'}) => (
  <Sequence from={Math.max(0, at - PREROLL[name])} durationInFrames={90} layout="none">
    <Html5Audio src={staticFile(`${dir}/${name}.wav`)} volume={volume} />
  </Sequence>
);
