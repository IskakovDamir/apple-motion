import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {SPRING, TYPE} from './tokens';

export type UICardProps = {
  title: string;
  subtitle?: string;
  /** small leading glyph / emoji / icon node */
  icon?: React.ReactNode;
  tone?: 'light' | 'dark' | 'glass';
  /** width in % of frame width */
  widthPct?: number;
  x?: number;
  y?: number;
  /** frame (local) at which the card pops in */
  at?: number;
  entryFrames?: number;
  /** title size in % of frame height (UI inside a device needs ~2.5-4.5 to read in a recap) */
  fontPct?: number;
};

/**
 * Notification / widget style card: large continuous radius, system materials, no drop shadow.
 * Pops in with the measured text spring (scale 0.92 -> 1 + fade), like UI inserts in the recaps.
 */
export const UICard: React.FC<UICardProps> = ({
  title,
  subtitle,
  icon,
  tone = 'light',
  widthPct = 34,
  x = 50,
  y = 50,
  at = 0,
  entryFrames = 12,
  fontPct = 2.6,
}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const p = spring({frame: frame - at, fps, config: SPRING.textIn, durationInFrames: entryFrames});
  const w = (widthPct / 100) * width;
  const bg = tone === 'dark' ? 'rgba(28,28,30,0.96)' : tone === 'glass' ? 'rgba(255,255,255,0.55)' : 'rgba(255,255,255,0.97)';
  const fg = tone === 'dark' ? '#ffffff' : '#1d1d1f';
  const sub = tone === 'dark' ? 'rgba(235,235,245,0.6)' : 'rgba(60,60,67,0.6)';
  const base = (fontPct / 100) * height;
  return (
    <div
      style={{
        position: 'absolute',
        left: `${x}%`,
        top: `${y}%`,
        width: w,
        transform: `translate(-50%, -50%) scale(${interpolate(p, [0, 1], [0.92, 1])})`,
        opacity: interpolate(p, [0, 0.4], [0, 1], {extrapolateRight: 'clamp'}),
        background: bg,
        backdropFilter: tone === 'glass' ? 'blur(30px) saturate(1.6)' : undefined,
        borderRadius: base * 1.25,
        padding: `${base * 0.75}px ${base * 0.9}px`,
        display: 'flex',
        gap: base * 0.6,
        alignItems: 'center',
        fontFamily: TYPE.family,
        color: fg,
      }}
    >
      {icon ? (
        <div style={{width: base * 1.9, height: base * 1.9, borderRadius: base * 0.45, display: 'grid', placeItems: 'center', fontSize: base * 1.2, flexShrink: 0}}>
          {icon}
        </div>
      ) : null}
      <div style={{minWidth: 0}}>
        <div style={{fontSize: base, fontWeight: 600, letterSpacing: '-0.01em', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'}}>{title}</div>
        {subtitle ? <div style={{fontSize: base * 0.86, color: sub, marginTop: base * 0.12}}>{subtitle}</div> : null}
      </div>
    </div>
  );
};
