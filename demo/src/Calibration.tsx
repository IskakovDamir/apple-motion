import React from 'react';
import {AbsoluteFill, Html5Audio, Sequence, staticFile} from 'remotion';
import {Backdrop, KineticText, type Entry} from '@apple-motion';

// Pipeline calibration: known font weights and known entry animations, measured back with the
// same extraction scripts (scripts/eval_render.py --truth demo/out/calibration.truth.json).
export const CAL_CARD = 60;
export const CAL_WEIGHTS = [400, 500, 600, 700, 800];
export const CAL_ENTRIES: {entry: Entry; frames: number}[] = [
  {entry: 'cut', frames: 0},
  {entry: 'fade', frames: 8},
  {entry: 'scaleDown', frames: 12},
  {entry: 'blurIn', frames: 12},
  {entry: 'slideUp', frames: 10},
  {entry: 'slideUpMask', frames: 10},
  {entry: 'perWord', frames: 10},
  {entry: 'scaleUp', frames: 16},
];
export const calibrationDuration = CAL_CARD * (CAL_WEIGHTS.length + CAL_ENTRIES.length);

export const Calibration: React.FC = () => (
  <AbsoluteFill style={{backgroundColor: 'black'}}>
    <Html5Audio src={staticFile('music.wav')} />
    {CAL_WEIGHTS.map((w, i) => (
      <Sequence key={`w${w}`} from={i * CAL_CARD} durationInFrames={CAL_CARD}>
        <Backdrop kind="black">
          <KineticText lines={[`Weight ${w}`]} weight={w} entry="cut" capHeightPct={7} durationInFrames={CAL_CARD} />
        </Backdrop>
      </Sequence>
    ))}
    {CAL_ENTRIES.map((c, i) => (
      <Sequence key={c.entry} from={(CAL_WEIGHTS.length + i) * CAL_CARD} durationInFrames={CAL_CARD}>
        <Backdrop kind={i % 2 ? 'white' : 'black'}>
          <KineticText
            lines={c.entry === 'perWord' ? ['Every word counts'] : [`Entry ${c.entry}`]}
            entry={c.entry}
            entryFrames={c.frames || 1}
            capHeightPct={7}
            color={i % 2 ? '#1d1d1f' : '#ffffff'}
            durationInFrames={CAL_CARD}
          />
        </Backdrop>
      </Sequence>
    ))}
  </AbsoluteFill>
);
