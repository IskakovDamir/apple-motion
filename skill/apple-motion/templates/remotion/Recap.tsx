import React from 'react';
import {AbsoluteFill, Html5Audio, Img, interpolate, OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {TransitionSeries} from '@remotion/transitions';
import {AppIcon} from './AppIcon';
import {Backdrop, type BackdropKind} from './Backdrop';
import {beatGrid, beats} from './beat';
import {Counter} from './Counter';
import {DeviceFrame} from './DeviceFrame';
import {KineticText, type Entry, type Exit, type Size} from './KineticText';
import {Scrubber} from './Scrubber';
import {Sfx, type SfxName} from './Sfx';
import {appleTransition, transitionFrames, type AppleTransition} from './transitions';
import {UICard} from './UICard';
import {COLOR} from './tokens';

/**
 * A recap is DATA: a list of cards, each lasting a whole number of beats. The engine keeps every
 * card starting exactly on its beat, overlaps transitions into the previous card's tail, and places
 * SFX (whoosh under whips, hits/clicks where asked). Write the cards; don't hand-place frames.
 */
export type Card = {
  /** length in beats (1 beat = 60/bpm s) */
  beats: number;
  bg?: BackdropKind;
  /** user footage or still (in /public): the picture layer; type can sit on top */
  media?: {src: string; type: 'video' | 'image'; pushPctPerSec?: number; startFromSec?: number; fit?: 'cover' | 'contain'};
  /** designer type (1-4 words per line, max 2 lines for headlines) */
  lines?: string[];
  entry?: Entry;
  exit?: Exit;
  size?: Size;
  align?: 'left' | 'center' | 'right';
  x?: number;
  y?: number;
  color?: string;
  /** number roll */
  counter?: {to: number; from?: number; suffix?: string; prefix?: string; caption?: string; decimals?: number};
  /** feature title card: icon above the title (use with bg 'white') */
  icon?: {glyph: string; from: string; to: string};
  /** spec numeral with gradient fill + small label */
  spec?: {value: string; label: string; gradient: [string, string]};
  /** device mock-up; UI cards pop in one per beat */
  device?: {cards: {title: string; subtitle?: string; icon?: string}[]; tone?: 'light' | 'dark'};
  /** player-chrome framing + optional caption pill */
  scrubber?: {from: number; to: number; pill?: string};
  /** transition INTO this card (default: cut) */
  transition?: AppleTransition;
  sfx?: SfxName;
};

export type RecapProps = {bpm: number; offsetFrames?: number; cards: Card[]; music?: string; tailFrames?: number};

const isLight = (bg?: BackdropKind) => bg === 'white' || bg === 'offWhite';

/** Frames of each card including the overlap of the next card's transition. */
export const cardFrames = (cards: Card[], bpm: number, fps: number, offset = 0) => {
  const g = beatGrid(bpm, fps, offset);
  return cards.map((c, i) => {
    const next = cards[i + 1];
    return beats(g, c.beats) + (next?.transition ? transitionFrames(next.transition) : 0);
  });
};

/** Total composition length: all cards (on the grid) + tail for the last hit to ring out. */
export const recapDuration = (p: RecapProps, fps: number) => {
  const g = beatGrid(p.bpm, fps, p.offsetFrames ?? 0);
  return (p.offsetFrames ?? 0) + p.cards.reduce((a, c) => a + beats(g, c.beats), 0) + (p.tailFrames ?? 45);
};

const Media: React.FC<NonNullable<Card['media']>> = ({src, type, pushPctPerSec = 1.5, startFromSec = 0, fit = 'cover'}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const scale = 1 + (pushPctPerSec / 100) * (frame / fps);
  const style: React.CSSProperties = {width: '100%', height: '100%', objectFit: fit, transform: `scale(${scale})`};
  return (
    <AbsoluteFill>
      {type === 'video' ? (
        <OffthreadVideo src={staticFile(src)} trimBefore={Math.round(startFromSec * fps)} muted style={style} />
      ) : (
        <Img src={staticFile(src)} style={style} />
      )}
    </AbsoluteFill>
  );
};

const CardView: React.FC<{c: Card; dur: number; beat: number}> = ({c, dur, beat}) => {
  const color = c.color ?? (isLight(c.bg) ? COLOR.graphite : COLOR.white);
  return (
    <Backdrop kind={c.bg ?? 'black'}>
      {c.media ? <Media {...c.media} /> : null}
      {c.icon ? <AppIcon glyph={c.icon.glyph} from={c.icon.from} to={c.icon.to} y={40} sizePct={15} /> : null}
      {c.device ? (
        <DeviceFrame heightPct={150} y={78} entryFrames={Math.round(beat)} pushPctPerSec={1.2} screenColor={c.device.tone === 'dark' ? '#000' : '#f2f2f7'}>
          {c.device.cards.map((u, k) => (
            <UICard key={k} title={u.title} subtitle={u.subtitle} icon={u.icon} tone={c.device?.tone === 'dark' ? 'dark' : 'light'}
              widthPct={33} fontPct={4.2} x={50} y={17 + k * 14} at={Math.round(beat * (k + 1))} />
          ))}
        </DeviceFrame>
      ) : null}
      {c.scrubber ? <Scrubber from={c.scrubber.from} to={c.scrubber.to} tone={isLight(c.bg) ? 'light' : 'dark'} /> : null}
      {c.scrubber?.pill ? <Pill text={c.scrubber.pill} /> : null}
      {c.spec ? (
        <>
          <KineticText lines={[c.spec.value]} durationInFrames={dur} entry={c.entry ?? 'scaleDown'} size="hero" capHeightPct={16}
            gradient={c.spec.gradient} y={44} weight={700} />
          <KineticText lines={[c.spec.label]} durationInFrames={dur} entry="fade" size="caption" capHeightPct={3.2} color={color} y={64} weight={500} />
        </>
      ) : null}
      {c.counter ? (
        <Counter to={c.counter.to} from={c.counter.from} suffix={c.counter.suffix} prefix={c.counter.prefix} caption={c.counter.caption}
          decimals={c.counter.decimals} durationInFrames={dur} rollFrames={Math.round(beat * 2)} size={c.size ?? 'hero'} color={color}
          align={c.align} x={c.x} y={c.y} exit={c.exit} />
      ) : c.lines && !c.spec ? (
        <KineticText lines={c.lines} durationInFrames={dur} entry={c.entry} exit={c.exit} size={c.size} color={color} align={c.align}
          x={c.x} y={c.y ?? (c.icon ? 64 : undefined)} />
      ) : null}
    </Backdrop>
  );
};

const Pill: React.FC<{text: string}> = ({text}) => {
  const {height} = useVideoConfig();
  const frame = useCurrentFrame();
  return (
    <div style={{position: 'absolute', left: '50%', top: '69%', transform: 'translateX(-50%)', padding: `${height * 0.009}px ${height * 0.02}px`,
      borderRadius: 999, background: 'rgba(40,40,42,0.72)', color: '#fff', fontFamily: '"SF Pro Text", -apple-system, Inter, sans-serif',
      fontSize: height * 0.024, letterSpacing: '0.04em', fontWeight: 500, opacity: interpolate(frame, [0, 4], [0, 1], {extrapolateRight: 'clamp'})}}>
      {text}
    </div>
  );
};

export const Recap: React.FC<RecapProps> = ({bpm, offsetFrames = 0, cards, music}) => {
  const {fps} = useVideoConfig();
  const g = beatGrid(bpm, fps, offsetFrames);
  const durs = cardFrames(cards, bpm, fps, offsetFrames);
  const items: React.ReactNode[] = [];
  const sfx: React.ReactNode[] = [];
  let cursor = offsetFrames; // beat-aligned start of the current card
  cards.forEach((c, i) => {
    const tf = i > 0 && c.transition ? transitionFrames(c.transition) : 0;
    if (tf > 0 && c.transition) {
      items.push(appleTransition(c.transition, `t${i}`));
      if (c.transition === 'whip') sfx.push(<Sfx key={`w${i}`} name="whoosh" at={cursor - Math.round(tf / 2)} volume={0.35} />);
    }
    if (c.sfx) sfx.push(<Sfx key={`s${i}`} name={c.sfx} at={cursor} volume={c.sfx === 'hit' ? 0.6 : 0.4} />);
    items.push(
      <TransitionSeries.Sequence key={`c${i}`} durationInFrames={durs[i] ?? 1}>
        <CardView c={c} dur={durs[i] ?? 1} beat={g.beat} />
      </TransitionSeries.Sequence>,
    );
    cursor += beats(g, c.beats);
  });
  return (
    <AbsoluteFill style={{backgroundColor: COLOR.black}}>
      {music ? <Html5Audio src={staticFile(music)} /> : null}
      <TransitionSeries from={offsetFrames}>{items}</TransitionSeries>
      {sfx}
    </AbsoluteFill>
  );
};
