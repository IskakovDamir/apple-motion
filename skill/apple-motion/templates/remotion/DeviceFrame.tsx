import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {SPRING} from './tokens';

export type DeviceFrameProps = {
  children: React.ReactNode;
  /** device height in % of frame height (Apple product shots: phone fills 60-90% of the height) */
  heightPct?: number;
  x?: number;
  y?: number;
  /** entry: rise from below and settle, or none */
  entry?: 'rise' | 'none';
  /** slow push during the hold, % scale per second (measured holds drift slightly) */
  pushPctPerSec?: number;
  tiltDeg?: number;
  screenColor?: string;
  /** soft wallpaper gradient behind the UI (Apple's UI shots are never an empty grey screen) */
  wallpaper?: readonly [string, string] | null;
};

/**
 * Minimal iPhone-style frame (no Apple artwork): continuous-corner body, thin bezel, Dynamic-Island pill.
 * Put UI (UICard, KineticText, images) inside as the screen.
 */
export const DeviceFrame: React.FC<DeviceFrameProps> = ({
  children,
  heightPct = 78,
  x = 50,
  y = 50,
  entry = 'rise',
  pushPctPerSec = 1.5,
  tiltDeg = 0,
  screenColor = '#000000',
  wallpaper = null,
}) => {
  const frame = useCurrentFrame();
  const {fps, height} = useVideoConfig();
  const h = (heightPct / 100) * height;
  const w = h * 0.4615; // 19.5:9 screen + bezel
  const p = entry === 'rise' ? spring({frame, fps, config: SPRING.camera}) : 1;
  const ty = interpolate(p, [0, 1], [0.35 * height, 0]);
  const push = 1 + (pushPctPerSec / 100) * (frame / fps);
  const r = w * 0.17;
  const bezel = w * 0.035;
  return (
    <AbsoluteFill>
      <div
        style={{
          position: 'absolute',
          left: `${x}%`,
          top: `${y}%`,
          width: w,
          height: h,
          transform: `translate(-50%, -50%) translateY(${ty}px) scale(${push}) rotate(${tiltDeg}deg)`,
          borderRadius: r,
          background: 'linear-gradient(145deg, #3a3a3c, #1c1c1e 40%, #2c2c2e)',
          padding: bezel,
          boxSizing: 'border-box',
          opacity: interpolate(p, [0, 0.3], [0, 1], {extrapolateRight: 'clamp'}),
        }}
      >
        <div style={{position: 'relative', width: '100%', height: '100%', borderRadius: r - bezel, overflow: 'hidden',
          background: wallpaper ? `linear-gradient(160deg, ${wallpaper[0]}, ${wallpaper[1]})` : screenColor}}>
          {children}
          <div
            style={{
              position: 'absolute',
              top: w * 0.03,
              left: '50%',
              transform: 'translateX(-50%)',
              width: w * 0.3,
              height: w * 0.085,
              borderRadius: w,
              background: '#000',
            }}
          />
        </div>
      </div>
    </AbsoluteFill>
  );
};
