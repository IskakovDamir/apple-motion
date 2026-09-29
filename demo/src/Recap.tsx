import React from 'react';
import {AbsoluteFill, Html5Audio, staticFile} from 'remotion';
import {TransitionSeries} from '@remotion/transitions';
import {
  AppIcon,
  DeviceFrame,
  Scrubber,
  UICard,
  appleTransition,
  transitionFrames,
  Backdrop,
  beatGrid,
  beats,
  COLOR,
  Counter,
  KineticText,
  Sfx,
  type AppleTransition,
  type BackdropKind,
  type Entry,
  type Exit,
  type Size,
} from '@apple-motion';

export type Card = {
  /** length in beats */
  beats: number;
  bg: BackdropKind;
  /** feature title card: app icon above the title */
  icon?: {glyph: string; from: string; to: string};
  /** spec numeral with a gradient fill and a small label under it */
  spec?: {value: string; label: string; gradient: [string, string]};
  /** device mock-up with UI cards popping in, one per beat */
  device?: {cards: {title: string; subtitle?: string; icon?: string}[]};
  /** player-chrome framing with a caption pill */
  scrubber?: {from: number; to: number; pill?: string};
  lines?: string[];
  counter?: {to: number; suffix?: string; caption?: string; decimals?: number};
  entry?: Entry;
  exit?: Exit;
  size?: Size;
  align?: 'left' | 'center' | 'right';
  x?: number;
  y?: number;
  /** transition INTO this card */
  transition?: AppleTransition;
  sfx?: 'hit' | 'click' | 'swish';
};

export type RecapProps = {bpm: number; offsetFrames: number; cards: Card[]; music: string};

const textColor = (bg: BackdropKind) => (bg === 'white' || bg === 'offWhite' ? COLOR.graphite : COLOR.white);

/**
 * Each card starts exactly on its beat. A transition INTO card i overlaps the tail of card i-1,
 * so card i-1 is extended by the transition length (its own beat count stays the visible time).
 */
const cardFrames = (cards: Card[], bpm: number, fps: number, offset: number) => {
  const g = beatGrid(bpm, fps, offset);
  return cards.map((c, i) => {
    const next = cards[i + 1];
    return beats(g, c.beats) + (next?.transition ? transitionFrames(next.transition) : 0);
  });
};

export const recapDuration = (p: RecapProps, fps: number) => {
  const g = beatGrid(p.bpm, fps, p.offsetFrames);
  return p.offsetFrames + p.cards.reduce((a, c) => a + beats(g, c.beats), 0) + 45;
};

export const Recap: React.FC<RecapProps> = ({bpm, offsetFrames, cards, music}) => {
  const fps = 30;
  const g = beatGrid(bpm, fps, offsetFrames);
  const items: React.ReactNode[] = [];
  const sfx: React.ReactNode[] = [];
  const durs = cardFrames(cards, bpm, fps, offsetFrames);
  let cursor = offsetFrames; // beat-aligned start of the current card
  cards.forEach((c, i) => {
    const dur = durs[i] ?? 0;
    const tf = i > 0 && c.transition ? transitionFrames(c.transition) : 0;
    if (tf > 0 && c.transition) {
      items.push(appleTransition(c.transition, `t${i}`));
      if (c.transition === 'whip') sfx.push(<Sfx key={`w${i}`} name="whoosh" at={cursor - Math.round(tf / 2)} volume={0.35} />);
    }
    if (c.sfx) sfx.push(<Sfx key={`s${i}`} name={c.sfx} at={cursor} volume={c.sfx === 'hit' ? 0.6 : 0.4} />);
    const color = textColor(c.bg);
    items.push(
      <TransitionSeries.Sequence key={`c${i}`} durationInFrames={dur}>
        <Backdrop kind={c.bg}>
          {c.icon ? <AppIcon glyph={c.icon.glyph} from={c.icon.from} to={c.icon.to} y={40} sizePct={15} /> : null}
          {c.device ? (
            <DeviceFrame heightPct={150} y={78} entryFrames={g.beat} pushPctPerSec={1.2} screenColor="#f2f2f7">
              {c.device.cards.map((u, k) => (
                <UICard key={k} title={u.title} subtitle={u.subtitle} icon={u.icon} widthPct={33} fontPct={4.2} x={50} y={17 + k * 14}
                  at={Math.round(g.beat * (k + 1))} />
              ))}
            </DeviceFrame>
          ) : null}
          {c.scrubber ? <Scrubber from={c.scrubber.from} to={c.scrubber.to} /> : null}
          {c.scrubber?.pill ? (
            <div style={{position: 'absolute', left: '50%', top: '69%', transform: 'translateX(-50%)', padding: '10px 22px',
              borderRadius: 99, background: 'rgba(40,40,42,0.72)', color: '#fff', fontFamily: 'SF Pro Display, -apple-system, Inter, sans-serif',
              fontSize: 26, letterSpacing: '0.04em', fontWeight: 500}}>{c.scrubber.pill}</div>
          ) : null}
          {c.spec ? (
            <>
              <KineticText lines={[c.spec.value]} durationInFrames={dur} entry={c.entry ?? 'scaleDown'} size="hero" capHeightPct={16}
                gradient={c.spec.gradient} y={44} weight={700} />
              <KineticText lines={[c.spec.label]} durationInFrames={dur} entry="fade" size="caption" capHeightPct={3.2}
                color={color} y={64} weight={500} />
            </>
          ) : null}
          {c.counter ? (
            <Counter
              to={c.counter.to}
              suffix={c.counter.suffix}
              caption={c.counter.caption}
              decimals={c.counter.decimals}
              durationInFrames={dur}
              rollFrames={Math.round(g.beat * 2)}
              size={c.size ?? 'hero'}
              color={color}
              align={c.align}
              x={c.x}
              y={c.y}
              exit={c.exit}
            />
          ) : c.lines ? (
            <KineticText
              lines={c.lines}
              durationInFrames={dur}
              entry={c.entry}
              exit={c.exit}
              size={c.size}
              color={color}
              align={c.align}
              x={c.x}
              y={c.y ?? (c.icon ? 64 : undefined)}
            />
          ) : null}
        </Backdrop>
      </TransitionSeries.Sequence>,
    );
    cursor += beats(g, c.beats);
  });
  return (
    <AbsoluteFill style={{backgroundColor: COLOR.black}}>
      <Html5Audio src={staticFile(music)} />
      <TransitionSeries from={offsetFrames}>{items}</TransitionSeries>
      {sfx}
    </AbsoluteFill>
  );
};
