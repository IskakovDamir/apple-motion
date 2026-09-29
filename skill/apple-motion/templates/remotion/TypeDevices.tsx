import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {COLOR, SPRING, TYPE} from './tokens';

/**
 * Apple's recurring small type devices, each seen in the measured corpus:
 *   LowerThird  presenter name + title ("Alan Dye / VP, Human Interface"), caption size
 *   Pill        uppercase caption in a translucent pill ("TIME-LAPSE IN 4K", "24 FPS 1/48 SHUTTER SPEED")
 *   WordSwap    one word swapped in place under a mask while the rest of the line holds
 *   Typing      text typed into a field with a blinking cursor, optionally auto-corrected
 */

const capPx = (pct: number, height: number) => (pct / 100) * height;
const CAP_TO_EM = 0.705; // SF Pro Display cap height / em

export const LowerThird: React.FC<{name: string; title?: string; side?: 'left' | 'right'; color?: string; at?: number}> = ({
  name,
  title,
  side = 'left',
  color = COLOR.white,
  at = 0,
}) => {
  const frame = useCurrentFrame();
  const {fps, height} = useVideoConfig();
  const p = spring({frame: frame - at, fps, config: SPRING.textIn});
  const fs = capPx(TYPE.capHeightPct.caption, height) / CAP_TO_EM;
  return (
    <div
      style={{
        position: 'absolute',
        bottom: '10%',
        [side]: '6%',
        textAlign: side,
        fontFamily: TYPE.family,
        color,
        opacity: interpolate(p, [0, 0.5], [0, 1], {extrapolateRight: 'clamp'}),
        transform: `translateY(${interpolate(p, [0, 1], [0.4 * fs, 0])}px)`,
        textShadow: 'none',
      }}
    >
      <div style={{fontSize: fs, fontWeight: 600, letterSpacing: '-0.01em', lineHeight: 1.15}}>{name}</div>
      {title ? <div style={{fontSize: fs * 0.82, fontWeight: 400, opacity: 0.85, lineHeight: 1.2}}>{title}</div> : null}
    </div>
  );
};

export const Pill: React.FC<{text: string; y?: number; at?: number; tone?: 'dark' | 'light'}> = ({text, y = 69, at = 0, tone = 'dark'}) => {
  const frame = useCurrentFrame();
  const {height} = useVideoConfig();
  return (
    <div
      style={{
        position: 'absolute',
        left: '50%',
        top: `${y}%`,
        transform: 'translateX(-50%)',
        padding: `${height * 0.009}px ${height * 0.02}px`,
        borderRadius: 999,
        background: tone === 'dark' ? 'rgba(40,40,42,0.72)' : 'rgba(255,255,255,0.8)',
        color: tone === 'dark' ? '#fff' : COLOR.graphite,
        fontFamily: TYPE.family,
        fontSize: height * 0.024,
        letterSpacing: '0.04em',
        fontWeight: 500,
        textTransform: 'uppercase',
        whiteSpace: 'nowrap',
        opacity: interpolate(frame - at, [0, 4], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
      }}
    >
      {text}
    </div>
  );
};

/** "Built for [speed.] -> [focus.] -> [you.]": the last word is swapped in place every `everyFrames`. */
export const WordSwap: React.FC<{
  prefix?: string;
  words: string[];
  everyFrames: number;
  capHeightPct?: number;
  color?: string;
  accent?: string;
  y?: number;
}> = ({prefix = '', words, everyFrames, capHeightPct = TYPE.capHeightPct.headline, color = COLOR.white, accent, y = 50}) => {
  const frame = useCurrentFrame();
  const {fps, height} = useVideoConfig();
  const fs = capPx(capHeightPct, height) / CAP_TO_EM;
  const i = Math.min(words.length - 1, Math.floor(frame / everyFrames));
  const local = frame - i * everyFrames;
  const pIn = i === 0 ? 1 : spring({frame: local, fps, config: SPRING.textIn});
  const lineStyle: React.CSSProperties = {fontFamily: TYPE.family, fontWeight: TYPE.weight.headline, fontSize: fs,
    letterSpacing: `${TYPE.letterSpacingEm}em`, lineHeight: TYPE.lineHeight, color};
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
      <div style={{position: 'absolute', top: `${y}%`, transform: 'translateY(-50%)', display: 'flex', gap: '0.25em', ...lineStyle}}>
        {prefix ? <span>{prefix}</span> : null}
        <span style={{position: 'relative', display: 'inline-block', overflow: 'hidden', paddingBottom: '0.12em', marginBottom: '-0.12em'}}>
          {i > 0 ? (
            <span style={{position: 'absolute', left: 0, top: 0, color: accent ?? color, transform: `translateY(${interpolate(pIn, [0, 1], [0, -105])}%)`}}>
              {words[i - 1]}
            </span>
          ) : null}
          <span style={{display: 'inline-block', color: accent ?? color, transform: `translateY(${interpolate(pIn, [0, 1], [105, 0])}%)`}}>{words[i]}</span>
        </span>
      </div>
    </AbsoluteFill>
  );
};

/** Text typed into a field, blinking cursor; `correctTo` = the auto-corrected full text shown shortly
 *  after typing ends (autocorrect gag: text "reciept", correctTo "receipt"). */
export const Typing: React.FC<{
  text: string;
  cps?: number;
  correctTo?: string;
  capHeightPct?: number;
  color?: string;
  field?: boolean;
  y?: number;
}> = ({text, cps = 14, correctTo, capHeightPct = TYPE.capHeightPct.title, color = COLOR.graphite, field = true, y = 50}) => {
  const frame = useCurrentFrame();
  const {fps, height} = useVideoConfig();
  const fs = capPx(capHeightPct, height) / CAP_TO_EM;
  const n = Math.min(text.length, Math.floor((frame / fps) * cps));
  const typedDone = n >= text.length;
  const doneAt = Math.ceil((text.length / cps) * fps);
  let shown = text.slice(0, n);
  let corrected = false;
  if (correctTo && typedDone && frame > doneAt + Math.round(0.35 * fps)) {
    shown = correctTo;
    corrected = true;
  }
  const cursorOn = Math.floor(frame / Math.round(fps * 0.5)) % 2 === 0 || !typedDone;
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
      <div
        style={{
          position: 'absolute',
          top: `${y}%`,
          transform: 'translateY(-50%)',
          padding: field ? `${fs * 0.45}px ${fs * 0.8}px` : 0,
          borderRadius: fs * 0.9,
          background: field ? 'rgba(118,118,128,0.12)' : 'transparent',
          fontFamily: TYPE.family,
          fontSize: fs,
          fontWeight: 400,
          color,
          display: 'flex',
          alignItems: 'center',
          whiteSpace: 'pre',
        }}
      >
        <span style={{background: corrected ? 'rgba(10,132,255,0.18)' : 'transparent', borderRadius: 6}}>{shown}</span>
        <span style={{width: Math.max(2, fs * 0.07), height: fs * 1.15, marginLeft: 2, background: '#0a84ff', opacity: cursorOn ? 1 : 0, borderRadius: 2}} />
      </div>
    </AbsoluteFill>
  );
};
