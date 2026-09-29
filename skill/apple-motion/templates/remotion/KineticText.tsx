import React, {useMemo} from 'react';
import {AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {COLOR, DURATION, EASE, SPRING, START, TYPE} from './tokens';

export type Entry =
  | 'cut'
  | 'fade'
  | 'blurIn'
  | 'scaleDown'
  | 'scaleUp'
  | 'slideUp'
  | 'slideUpMask'
  | 'perWord'
  | 'perLetter';
export type Exit = 'cut' | 'fade' | 'blurOut' | 'scaleUp' | 'scaleDown' | 'slideOut';
export type Size = keyof typeof TYPE.capHeightPct;

export type KineticTextProps = {
  /** One string per line. Keep lines to 1-4 words; Apple rarely sets more than 2 lines. */
  lines: string[];
  /** Total frames this text is on screen (entry + hold + exit). */
  durationInFrames: number;
  entry?: Entry;
  exit?: Exit;
  size?: Size;
  /** Override cap height as % of frame height (measured median is TYPE.capHeightPct.headline). */
  capHeightPct?: number;
  weight?: number;
  color?: string;
  align?: 'left' | 'center' | 'right';
  /** Block anchor in % of frame (centre of the text block). */
  x?: number;
  y?: number;
  entryFrames?: number;
  exitFrames?: number;
  staggerFrames?: number;
  /** vertical gradient fill (Apple uses it only for spec numerals, e.g. ['#b150e2', '#e0417b']) */
  gradient?: readonly [string, string];
  /** shrink the font so the widest line fits this % of frame width (default 88) */
  maxWidthPct?: number;
  style?: React.CSSProperties;
};

const capToEmCache = new Map<string, number>();

/** Cap height / font-size of the actual font in use (measured with canvas, cached). */
const useCapToEm = (family: string, weight: number): number =>
  useMemo(() => {
    const key = `${family}|${weight}`;
    const hit = capToEmCache.get(key);
    if (hit) return hit;
    let v = 0.705; // SF Pro Display
    if (typeof document !== 'undefined') {
      const ctx = document.createElement('canvas').getContext('2d');
      if (ctx) {
        ctx.font = `${weight} 200px ${family}`;
        const m = ctx.measureText('H');
        if (m.actualBoundingBoxAscent > 0) v = m.actualBoundingBoxAscent / 200;
      }
    }
    capToEmCache.set(key, v);
    return v;
  }, [family, weight]);

const ease = (b: readonly [number, number, number, number]) => Easing.bezier(b[0], b[1], b[2], b[3]);

/**
 * 0 -> 1 entry progress. Default: the measured spring UNSTRETCHED - its visible move lasts about
 * DURATION.textInFrames, like Apple's. Passing `frames` stretches it to exactly that many frames
 * (Remotion durationInFrames), which makes the visible move ~3x shorter than `frames`.
 */
const entryProgress = (frame: number, fps: number, frames?: number) =>
  frames === undefined
    ? spring({frame, fps, config: SPRING.textIn})
    : frames <= 0
      ? 1
      : spring({frame, fps, config: SPRING.textIn, durationInFrames: frames});

/** 0 -> 1 exit progress (bezier; Apple exits are short and front-loaded). */
const exitProgress = (frame: number, total: number, frames: number) =>
  frames <= 0
    ? frame >= total
      ? 1
      : 0
    : interpolate(frame, [total - frames, total], [0, 1], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
        easing: ease(EASE.textOut),
      });

export const KineticText: React.FC<KineticTextProps> = ({
  lines,
  durationInFrames,
  entry = 'scaleDown',
  exit = 'cut',
  size = 'headline',
  capHeightPct,
  weight,
  color = COLOR.white,
  align = 'center',
  x = 50,
  y = 50,
  entryFrames,
  exitFrames,
  staggerFrames,
  gradient,
  maxWidthPct = 88,
  style,
}) => {
  const frame = useCurrentFrame();
  const {fps, height} = useVideoConfig();
  const w = weight ?? TYPE.weight[size];
  const capToEm = useCapToEm(TYPE.family, w);
  const {width} = useVideoConfig();
  const wanted = (((capHeightPct ?? TYPE.capHeightPct[size]) / 100) * height) / capToEm;
  const widest = useMemo(() => {
    if (typeof document === 'undefined') return 0;
    const ctx = document.createElement('canvas').getContext('2d');
    if (!ctx) return 0;
    ctx.font = `${w} 100px ${TYPE.family}`;
    return Math.max(...lines.map((l) => ctx.measureText(l).width / 100 + TYPE.letterSpacingEm * l.length));
  }, [lines, w]);
  const fontSize = widest > 0 ? Math.min(wanted, ((maxWidthPct / 100) * width) / widest) : wanted;
  const outFrames = exit === 'cut' ? 0 : exitFrames ?? DURATION.textOutFrames;
  if (frame >= durationInFrames) return null;

  const p = entry === 'cut' ? 1 : entryProgress(frame, fps, entryFrames);
  const q = exitProgress(frame, durationInFrames, outFrames);

  // block-level transform for entry + exit
  let opacity = 1;
  let scale = 1;
  let ty = 0; // px
  let blur = 0; // px
  switch (entry) {
    case 'fade':
      opacity = interpolate(p, [0, 1], [0, 1]);
      break;
    case 'blurIn':
      opacity = interpolate(p, [0, 0.6], [0, 1], {extrapolateRight: 'clamp'});
      blur = interpolate(p, [0, 1], [START.blurPx, 0]);
      break;
    case 'scaleDown':
      scale = interpolate(p, [0, 1], [START.scaleDown, 1]);
      opacity = interpolate(p, [0, 0.5], [0, 1], {extrapolateRight: 'clamp'});
      blur = interpolate(p, [0, 1], [START.blurPx * 0.5, 0]);
      break;
    case 'scaleUp':
      scale = interpolate(p, [0, 1], [START.scaleUp, 1]);
      opacity = interpolate(p, [0, 0.5], [0, 1], {extrapolateRight: 'clamp'});
      break;
    case 'slideUp':
      ty = interpolate(p, [0, 1], [(START.slideYPctH / 100) * height, 0]);
      opacity = interpolate(p, [0, 0.6], [0, 1], {extrapolateRight: 'clamp'});
      break;
    default:
      break;
  }
  switch (exit) {
    case 'fade':
      opacity *= 1 - q;
      break;
    case 'blurOut':
      opacity *= 1 - q;
      blur += q * START.blurPx;
      break;
    case 'scaleUp':
      scale *= 1 + q * (START.scaleDown - 1);
      opacity *= 1 - q;
      break;
    case 'scaleDown':
      scale *= 1 - q * (1 - START.scaleUp);
      opacity *= 1 - q;
      break;
    case 'slideOut':
      ty -= q * (START.slideYPctH / 100) * height;
      opacity *= 1 - q;
      break;
    default:
      break;
  }

  const stagger = staggerFrames ?? (entry === 'perLetter' ? DURATION.letterStaggerFrames : DURATION.wordStaggerFrames);
  const lineStyle: React.CSSProperties = {
    display: 'block',
    whiteSpace: 'pre',
    textAlign: align,
  };

  let unitIndex = 0;
  const renderLine = (line: string, li: number) => {
    if (entry === 'slideUpMask') {
      const lp = entryProgress(frame - li * stagger, fps, entryFrames);
      return (
        <span key={li} style={{...lineStyle, overflow: 'hidden', paddingBottom: '0.12em', marginBottom: '-0.12em'}}>
          <span style={{display: 'inline-block', transform: `translateY(${interpolate(lp, [0, 1], [105, 0])}%)`}}>
            {line}
          </span>
        </span>
      );
    }
    if (entry === 'perWord' || entry === 'perLetter') {
      const parts = entry === 'perWord' ? line.split(/(\s+)/) : Array.from(line);
      return (
        <span key={li} style={lineStyle}>
          {parts.map((part, pi) => {
            if (/^\s+$/.test(part)) return <span key={pi}>{part}</span>;
            const i = unitIndex++;
            const up = entryProgress(frame - i * stagger, fps, entry === 'perLetter' ? 2 : entryFrames);
            const st: React.CSSProperties =
              entry === 'perWord'
                ? {
                    display: 'inline-block',
                    opacity: interpolate(up, [0, 0.5], [0, 1], {extrapolateRight: 'clamp'}),
                    transform: `translateY(${interpolate(up, [0, 1], [0.35, 0])}em) scale(${interpolate(up, [0, 1], [0.92, 1])})`,
                  }
                : {opacity: up > 0.01 ? 1 : 0};
            return (
              <span key={pi} style={st}>
                {part}
              </span>
            );
          })}
        </span>
      );
    }
    return (
      <span key={li} style={lineStyle}>
        {line}
      </span>
    );
  };

  const anchorX = align === 'left' ? '0%' : align === 'right' ? '-100%' : '-50%';
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div
        style={{
          position: 'absolute',
          left: `${x}%`,
          top: `${y}%`,
          transform: `translate(${anchorX}, -50%) translateY(${ty}px) scale(${scale})`,
          transformOrigin: align === 'left' ? '0% 50%' : align === 'right' ? '100% 50%' : '50% 50%',
          fontFamily: TYPE.family,
          fontWeight: w,
          fontSize,
          lineHeight: TYPE.lineHeight,
          letterSpacing: `${TYPE.letterSpacingEm}em`,
          color,
          opacity,
          filter: blur > 0.05 ? `blur(${blur}px)` : undefined,
          fontFeatureSettings: '"kern" 1',
          WebkitFontSmoothing: 'antialiased',
          ...(gradient
            ? {backgroundImage: `linear-gradient(180deg, ${gradient[0]}, ${gradient[1]})`, WebkitBackgroundClip: 'text', backgroundClip: 'text', color: 'transparent'}
            : {}),
          ...style,
        }}
      >
        {lines.map(renderLine)}
      </div>
    </AbsoluteFill>
  );
};
