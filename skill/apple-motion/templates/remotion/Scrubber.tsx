import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {TYPE} from './tokens';

/**
 * Player-chrome overlay (the device of Apple's Sept 2026 event recap: the recap is framed as
 * scrubbing through the keynote). A thin progress bar with a knob + elapsed / remaining timecodes.
 * `from`/`to` are the fake keynote timestamps (seconds) the bar travels between.
 */
export const Scrubber: React.FC<{from: number; to: number; total?: number; tone?: 'light' | 'dark'}> = ({
  from,
  to,
  total = 3600 + 20 * 60,
  tone = 'dark',
}) => {
  const frame = useCurrentFrame();
  const {durationInFrames, height, width} = useVideoConfig();
  const t = interpolate(frame, [0, durationInFrames], [from, to]);
  const fmt = (s: number) => {
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const ss = Math.floor(s % 60);
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(ss).padStart(2, '0')}`;
  };
  const fg = tone === 'dark' ? 'rgba(255,255,255,0.92)' : 'rgba(29,29,31,0.9)';
  const track = tone === 'dark' ? 'rgba(255,255,255,0.28)' : 'rgba(29,29,31,0.18)';
  const barY = height * 0.8;
  const left = width * 0.052;
  const right = width * 0.948;
  const px = left + ((right - left) * t) / total;
  const fs = height * 0.0165;
  return (
    <div style={{position: 'absolute', inset: 0, pointerEvents: 'none', fontFamily: TYPE.family, color: fg}}>
      <div style={{position: 'absolute', left, top: barY, width: right - left, height: height * 0.0055, borderRadius: 99, background: track}} />
      <div style={{position: 'absolute', left, top: barY, width: px - left, height: height * 0.0055, borderRadius: 99, background: fg}} />
      <div style={{position: 'absolute', left: px, top: barY + height * 0.00275, width: height * 0.022, height: height * 0.022, borderRadius: 99, background: '#fff', transform: 'translate(-50%, -50%)'}} />
      <div style={{position: 'absolute', left, top: barY + height * 0.022, fontSize: fs, fontVariantNumeric: 'tabular-nums'}}>{fmt(t)}</div>
      <div style={{position: 'absolute', right: width - right, top: barY + height * 0.022, fontSize: fs, fontVariantNumeric: 'tabular-nums'}}>{fmt(total - t)}</div>
    </div>
  );
};
