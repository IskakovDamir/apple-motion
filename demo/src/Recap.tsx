import React from 'react';
import {AbsoluteFill, Html5Audio, staticFile} from 'remotion';
import {TransitionSeries} from '@remotion/transitions';
import {
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
              y={c.y}
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
