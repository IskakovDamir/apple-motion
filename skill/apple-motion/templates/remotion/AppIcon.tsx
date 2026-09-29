import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {SPRING, TYPE} from './tokens';

/**
 * Generic app-icon tile (continuous 22.5% corner, vertical gradient, white glyph) for
 * "feature title on white" cards. Not Apple artwork - bring your own glyph (text, emoji or SVG).
 */
export const AppIcon: React.FC<{
  glyph: React.ReactNode;
  from?: string;
  to?: string;
  sizePct?: number;
  x?: number;
  y?: number;
  at?: number;
}> = ({glyph, from = '#5ac8fa', to = '#007aff', sizePct = 14, x = 50, y = 40, at = 0}) => {
  const frame = useCurrentFrame();
  const {fps, height} = useVideoConfig();
  const p = spring({frame: frame - at, fps, config: SPRING.textIn});
  const s = (sizePct / 100) * height;
  return (
    <div
      style={{
        position: 'absolute',
        left: `${x}%`,
        top: `${y}%`,
        width: s,
        height: s,
        transform: `translate(-50%, -50%) scale(${interpolate(p, [0, 1], [0.9, 1])})`,
        opacity: interpolate(p, [0, 0.4], [0, 1], {extrapolateRight: 'clamp'}),
        borderRadius: s * 0.225,
        background: `linear-gradient(180deg, ${from}, ${to})`,
        display: 'grid',
        placeItems: 'center',
        color: '#fff',
        fontFamily: TYPE.family,
        fontWeight: 600,
        fontSize: s * 0.5,
      }}
    >
      {glyph}
    </div>
  );
};
