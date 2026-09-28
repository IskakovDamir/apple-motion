import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {COLOR} from './tokens';

export type BackdropKind = 'black' | 'white' | 'offWhite' | 'gradient';

/**
 * Flat backgrounds dominate Apple's type cards (pure black / pure white / #f5f5f7).
 * 'gradient' is a slow-drifting two-colour field for the few colour moments.
 */
export const Backdrop: React.FC<{kind?: BackdropKind; from?: string; to?: string; children?: React.ReactNode}> = ({
  kind = 'black',
  from = '#0a84ff',
  to = '#5e5ce6',
  children,
}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  if (kind === 'gradient') {
    const a = interpolate(frame, [0, durationInFrames], [20, 60]);
    return <AbsoluteFill style={{background: `linear-gradient(${a}deg, ${from}, ${to})`}}>{children}</AbsoluteFill>;
  }
  const bg = kind === 'white' ? COLOR.white : kind === 'offWhite' ? COLOR.offWhite : COLOR.black;
  return <AbsoluteFill style={{backgroundColor: bg}}>{children}</AbsoluteFill>;
};
