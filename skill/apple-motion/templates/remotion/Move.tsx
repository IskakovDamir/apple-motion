import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {MOTION} from './tokens';

export type CameraMove = 'static' | 'push' | 'pull' | 'pan' | 'panRight' | 'tilt' | 'tiltDown';

/**
 * Measured global motion on a shot: Apple holds are rarely dead still. Rates are the medians of the
 * corpus (MOTION.zoomPctPerSec, MOTION.panPctPerSec). Constant speed, like the measured holds
 * (the accel/decel phases of real moves are only a few frames).
 * `pull` starts slightly in and ends at 1.0; pans/tilts start over-scanned so no edge ever shows.
 */
export const Move: React.FC<{move?: CameraMove; durationInFrames: number; intensity?: number; children: React.ReactNode}> = ({
  move = 'static',
  durationInFrames,
  intensity = 1,
  children,
}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  if (move === 'static') return <AbsoluteFill>{children}</AbsoluteFill>;
  const t = Math.min(frame, durationInFrames) / fps;
  const T = durationInFrames / fps;
  const z = (MOTION.zoomPctPerSec / 100) * intensity;
  const p = (MOTION.panPctPerSec / 100) * intensity;
  let transform = '';
  if (move === 'push') transform = `scale(${1 + z * t})`;
  if (move === 'pull') transform = `scale(${1 + z * (T - t)})`;
  if (move === 'pan' || move === 'panRight' || move === 'tilt' || move === 'tiltDown') {
    const travel = p * T; // fraction of the frame travelled over the shot
    const over = 1 + travel + 0.01;
    const d = p * t - travel / 2; // centred travel
    const sign = move === 'panRight' || move === 'tiltDown' ? 1 : -1;
    transform =
      move === 'pan' || move === 'panRight'
        ? `scale(${over}) translateX(${(sign * d * width) / over}px)`
        : `scale(${over}) translateY(${(sign * d * height) / over}px)`;
  }
  return <AbsoluteFill style={{transform, transformOrigin: '50% 50%'}}>{children}</AbsoluteFill>;
};

/** Deterministic move for card i following the measured mix (static ~38%, pull ~20%, push ~16%, pan/tilt ~19%). */
export const autoMove = (i: number): CameraMove => {
  const cycle: CameraMove[] = ['push', 'static', 'pull', 'static', 'pan', 'push', 'static', 'pull', 'tilt', 'static'];
  return cycle[i % cycle.length] ?? 'static';
};
