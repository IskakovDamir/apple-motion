import React from 'react';
import {AbsoluteFill, Sequence} from 'remotion';
import {Backdrop, KineticText, type Entry} from '@apple-motion';
import lab from './entry_lab.json';

// Training lab: every entry type at several spring time scales, measured back with the extraction
// pipeline by scripts/train_entries.py to fit ENTRY_TIME against Apple's measured entry lengths.
export const entryLabDuration = lab.cards.length * lab.card;

export const EntryLab: React.FC = () => (
  <AbsoluteFill style={{backgroundColor: 'black'}}>
    {lab.cards.map((c, i) => (
      <Sequence key={i} from={c.start} durationInFrames={c.frames}>
        <Backdrop kind={i % 2 ? 'white' : 'black'}>
          <KineticText lines={c.lines} entry={c.entry as Entry} timeScale={c.timeScale} capHeightPct={7}
            color={i % 2 ? '#1d1d1f' : '#ffffff'} durationInFrames={c.frames} />
        </Backdrop>
      </Sequence>
    ))}
  </AbsoluteFill>
);
