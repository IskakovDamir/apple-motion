import React from 'react';
import {Easing, interpolate, useCurrentFrame} from 'remotion';
import {EASE} from './tokens';
import {KineticText, type KineticTextProps} from './KineticText';

export type CounterProps = Omit<KineticTextProps, 'lines' | 'entry'> & {
  from?: number;
  to: number;
  /** frames the number takes to roll; Apple rolls land on a beat */
  rollFrames?: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
  /** second line under the number, e.g. a unit or claim */
  caption?: string;
};

/** Number roll: digits count up with a front-loaded ease, tabular figures so the width never jitters. */
export const Counter: React.FC<CounterProps> = ({
  from = 0,
  to,
  rollFrames = 24,
  decimals = 0,
  prefix = '',
  suffix = '',
  caption,
  style,
  ...rest
}) => {
  const frame = useCurrentFrame();
  const v = interpolate(frame, [0, rollFrames], [from, to], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(EASE.camera[0], EASE.camera[1], EASE.camera[2], EASE.camera[3]),
  });
  const text = `${prefix}${v.toLocaleString('en-US', {minimumFractionDigits: decimals, maximumFractionDigits: decimals})}${suffix}`;
  return (
    <KineticText
      {...rest}
      lines={caption ? [text, caption] : [text]}
      entry="fade"
      entryFrames={4}
      style={{fontVariantNumeric: 'tabular-nums', ...style}}
    />
  );
};
