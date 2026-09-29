import React from 'react';
import {Easing, interpolate, useCurrentFrame} from 'remotion';
import {EASE, TYPE} from './tokens';
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
  y = 46,
  size = 'hero',
  capHeightPct,
  ...rest
}) => {
  const frame = useCurrentFrame();
  const v = interpolate(frame, [0, rollFrames], [from, to], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(EASE.camera[0], EASE.camera[1], EASE.camera[2], EASE.camera[3]),
  });
  const text = `${prefix}${v.toLocaleString('en-US', {minimumFractionDigits: decimals, maximumFractionDigits: decimals})}${suffix}`;
  const cap = capHeightPct ?? Math.min(TYPE.capHeightPct[size], 14);
  return (
    <>
      <KineticText
        {...rest}
        size={size}
        capHeightPct={cap}
        y={y}
        lines={[text]}
        entry="fade"
        entryFrames={4}
        style={{fontVariantNumeric: 'tabular-nums', ...style}}
      />
      {caption ? (
        <KineticText {...rest} y={y + cap * 0.75 + 5} lines={[caption]} size="caption" weight={500} entry="fade" entryFrames={6} />
      ) : null}
    </>
  );
};
