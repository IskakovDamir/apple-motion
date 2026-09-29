import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {SPRING, TYPE} from './tokens';

export type GridIcon = {glyph: string; from: string; to: string};

/**
 * "All the apps" moment: a large grid of app-icon tiles that pans slowly (measured: these grid
 * shots are long holds with a slow diagonal drift, colour carried entirely by the icons).
 * Tiles pop in with a short diagonal stagger.
 */
export const IconGrid: React.FC<{
  icons: GridIcon[];
  columns?: number;
  rows?: number;
  tilePct?: number;
  bg?: string;
  /** drift in % of frame per second */
  driftPctPerSec?: [number, number];
  staggerFrames?: number;
}> = ({icons, columns = 9, rows = 5, tilePct = 17, bg = '#000', driftPctPerSec = [-1.2, -0.6], staggerFrames = 1}) => {
  const frame = useCurrentFrame();
  const {fps, height, width} = useVideoConfig();
  const tile = (tilePct / 100) * height;
  const gap = tile * 0.28;
  const gridW = columns * tile + (columns - 1) * gap;
  const gridH = rows * tile + (rows - 1) * gap;
  const dx = (driftPctPerSec[0] / 100) * width * (frame / fps);
  const dy = (driftPctPerSec[1] / 100) * height * (frame / fps);
  const cells = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < columns; c++) {
      const i = r * columns + c;
      const ic = icons[i % Math.max(1, icons.length)];
      if (!ic) continue;
      const p = spring({frame: frame - (r + c) * staggerFrames, fps, config: SPRING.textIn});
      cells.push(
        <div
          key={i}
          style={{
            position: 'absolute',
            left: c * (tile + gap),
            top: r * (tile + gap),
            width: tile,
            height: tile,
            borderRadius: tile * 0.225,
            background: `linear-gradient(180deg, ${ic.from}, ${ic.to})`,
            display: 'grid',
            placeItems: 'center',
            color: '#fff',
            fontFamily: TYPE.family,
            fontWeight: 600,
            fontSize: tile * 0.46,
            opacity: interpolate(p, [0, 0.4], [0, 1], {extrapolateRight: 'clamp'}),
            transform: `scale(${interpolate(p, [0, 1], [0.85, 1])})`,
          }}
        >
          {ic.glyph}
        </div>,
      );
    }
  }
  return (
    <AbsoluteFill style={{backgroundColor: bg, overflow: 'hidden'}}>
      <div style={{position: 'absolute', left: (width - gridW) / 2 + dx, top: (height - gridH) / 2 + dy, width: gridW, height: gridH}}>{cells}</div>
    </AbsoluteFill>
  );
};
