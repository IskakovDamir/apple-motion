import React from 'react';
import {AbsoluteFill, Html5Audio, Img, interpolate, OffthreadVideo, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {TransitionSeries} from '@remotion/transitions';
import {AppIcon} from './AppIcon';
import {Backdrop, type BackdropKind} from './Backdrop';
import {beatGrid} from './beat';
import {Counter} from './Counter';
import {DeviceFrame} from './DeviceFrame';
import {IconGrid, type GridIcon} from './IconGrid';
import {KineticText, type Entry, type Exit, type Size} from './KineticText';
import {Scrubber} from './Scrubber';
import {Sfx, type SfxName} from './Sfx';
import {appleTransition, transitionFrames, type AppleTransition} from './transitions';
import {UICard} from './UICard';
import {autoMove, Move, type CameraMove} from './Move';
import {LowerThird, Pill, Typing, WordSwap} from './TypeDevices';
import {AUDIO, COLOR} from './tokens';

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
  /** number roll (optionally with the spec-numeral gradient fill) */
  counter?: {to: number; from?: number; suffix?: string; prefix?: string; caption?: string; decimals?: number;
    gradient?: [string, string]};
  /** type leaves after this many beats while the card's picture continues (measured type on-screen time is
   *  much shorter than many shots: p50 ~1 s, p90 ~3 s). Default: type stays for the whole card. */
  typeBeats?: number;
  /** feature title card: icon above the title (use with bg 'white') */
  icon?: {glyph: string; from: string; to: string};
  /** spec numeral with gradient fill + small label */
  spec?: {value: string; label: string; gradient: [string, string]};
  /** device mock-up; UI cards pop in every `everyBeats` (default 1). x: 30 leaves room for `lines`
   *  on the right (card x: 58, align: 'left'). Max 3 UI cards; titles <= ~17 chars. */
  device?: {cards: {title: string; subtitle?: string; icon?: string}[]; tone?: 'light' | 'dark'; x?: number;
    entry?: 'rise' | 'none'; everyBeats?: number; tapSfx?: boolean;
    /** screen wallpaper gradient; default a soft light/dark pair, null for a flat screen */
    wallpaper?: [string, string] | null};
  /** colours of the gradient backdrop (bg: 'gradient') */
  gradient?: [string, string];
  /** "all the apps" grid of icon tiles, slowly drifting */
  grid?: {icons: GridIcon[]; columns?: number; rows?: number};
  /** player-chrome framing + optional caption pill */
  scrubber?: {from: number; to: number; pill?: string};
  /** global camera move on the picture (type stays put). Default: the measured mix is assigned to
   *  picture cards automatically (RecapProps.autoMove); type-only cards stay static. */
  move?: CameraMove;
  /** presenter name + title, caption size, bottom-left (or right) */
  lowerThird?: {name: string; title?: string; side?: 'left' | 'right'};
  /** uppercase caption pill ("TIME-LAPSE IN 4K") */
  pill?: string;
  /** one word swapped in place every `everyBeats` (default 1) under a mask; prefix holds */
  swap?: {prefix?: string; words: string[]; everyBeats?: number; accent?: string};
  /** text typed into a field with a cursor; `correctTo` = auto-corrected full text shown after typing */
  typing?: {text: string; cps?: number; correctTo?: string};
  /** transition INTO this card (default: cut) */
  transition?: AppleTransition;
  sfx?: SfxName;
};

export type RecapProps = {
  bpm: number;
  offsetFrames?: number;
  cards: Card[];
  music?: string;
  /** extra frames the LAST card holds after its beats (the logo rings out). Default 45. */
  tailFrames?: number;
  /** fade the music out over the last N frames of the composition (use when the bed is longer than the
   *  video; better: generate the bed with the right number of bars). Default 0. */
  musicFadeOutFrames?: number;
  /** SFX gain (0-1). Apple mixes SFX low; master the final file to AUDIO.lufs / AUDIO.truePeakDb. */
  sfxVolume?: number;
  /** folder under public/ holding whoosh/swish/click/hit/riser .wav (default 'sfx') */
  sfxDir?: string;
  /** assign measured camera moves to picture cards that don't set `move` (default true) */
  autoMove?: boolean;
  /** voice-over file in public/. When set, the music is ducked by AUDIO.musicUnderVoiceDb. Time the
   *  cards to the words with scripts/vo_cards.py. */
  voice?: string;
  /** frame at which the voice-over starts (vo_cards.py prints it as voiceFromFrames). Default 0. */
  voiceFrom?: number;
};

const isLight = (bg?: BackdropKind) => bg === 'white' || bg === 'offWhite';

/**
 * Start frame of every card, from the running total of beats (no rounding drift, works for
 * fractional BPM-to-fps ratios and half-beat cards), plus the end frame of the last card.
 */
export const cardStarts = (cards: Card[], bpm: number, fps: number, offset = 0): number[] => {
  const g = beatGrid(bpm, fps, offset);
  const out: number[] = [];
  let acc = 0;
  for (const c of cards) {
    out.push(Math.round(offset + acc * g.beat));
    acc += c.beats;
  }
  out.push(Math.round(offset + acc * g.beat));
  return out;
};

/** Frames of each card, including the overlap into the NEXT card's transition (which plays from the
 *  next card's beat onward, so the outgoing card stays up for the transition). */
export const cardFrames = (cards: Card[], bpm: number, fps: number, offset = 0, tailFrames = 45) => {
  const st = cardStarts(cards, bpm, fps, offset);
  return cards.map((c, i) => {
    const next = cards[i + 1];
    const tail = i === cards.length - 1 ? tailFrames : 0; // the last card holds through the tail
    return (st[i + 1] ?? 0) - (st[i] ?? 0) + (next?.transition ? transitionFrames(next.transition) : 0) + tail;
  });
};

/** Total composition length = beats of all cards + tailFrames (the last card holds through the tail).
 *  e.g. 64 beats at 120 BPM = 960 frames + 45 = 1005 frames (33.5 s). */
export const recapDuration = (p: RecapProps, fps: number) => {
  const st = cardStarts(p.cards, p.bpm, fps, p.offsetFrames ?? 0);
  return (st[st.length - 1] ?? 0) + (p.tailFrames ?? 45);
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

const hasPicture = (c: Card) => Boolean(c.media || c.grid || c.device || (c.icon && !c.lines) || c.scrubber);

const CardView: React.FC<{c: Card; dur: number; beat: number; move: CameraMove}> = ({c, dur: cardDur, beat, move}) => {
  const dur = c.typeBeats ? Math.min(cardDur, Math.round(c.typeBeats * beat)) : cardDur;
  const color = c.color ?? (isLight(c.bg) ? COLOR.graphite : COLOR.white);
  return (
    <Backdrop kind={c.bg ?? 'black'} from={c.gradient?.[0]} to={c.gradient?.[1]}>
      <Move move={move} durationInFrames={cardDur}>
      {c.media ? <Media {...c.media} pushPctPerSec={c.media.pushPctPerSec ?? 0} /> : null}
      {c.grid ? <IconGrid icons={c.grid.icons} columns={c.grid.columns} rows={c.grid.rows} bg={isLight(c.bg) ? '#f5f5f7' : '#000'} /> : null}
      {c.icon ? <AppIcon glyph={c.icon.glyph} from={c.icon.from} to={c.icon.to} y={c.lines ? 40 : 50} sizePct={20} /> : null}
      {c.device ? (
        <DeviceFrame heightPct={150} y={78} x={c.device.x ?? 50} entry={c.device.entry ?? 'rise'} pushPctPerSec={0}
          screenColor={c.device.tone === 'dark' ? '#000' : '#f2f2f7'}
          wallpaper={c.device.wallpaper === undefined ? (c.device.tone === 'dark' ? ['#1c1c3a', '#3a1c32'] : ['#dbe8ff', '#fde2ef']) : c.device.wallpaper}>
          {c.device.cards.slice(0, 3).map((u, k) => (
            <UICard key={k} title={u.title} subtitle={u.subtitle} icon={u.icon} tone={c.device?.tone === 'dark' ? 'dark' : 'light'}
              widthPct={33} fontPct={4.2} x={50} y={17 + k * 15} at={Math.round(beat * (c.device?.everyBeats ?? 1) * (k + 1))} />
          ))}
        </DeviceFrame>
      ) : null}
      </Move>
      {c.scrubber ? <Scrubber from={c.scrubber.from} to={c.scrubber.to} tone={isLight(c.bg) ? 'light' : 'dark'} /> : null}
      {c.scrubber?.pill ? <Pill text={c.scrubber.pill} /> : null}
      {c.spec ? (
        <>
          <KineticText lines={[c.spec.value]} durationInFrames={dur} entry={c.entry ?? 'scaleDown'} exit={c.exit} size="hero" capHeightPct={16}
            gradient={c.spec.gradient} y={44} weight={700} />
          <KineticText lines={[c.spec.label]} durationInFrames={dur} entry="fade" size="caption" capHeightPct={3.2} color={color} y={64} weight={500} />
        </>
      ) : null}
      {c.counter ? (
        <Counter to={c.counter.to} from={c.counter.from} gradient={c.counter.gradient} suffix={c.counter.suffix} prefix={c.counter.prefix} caption={c.counter.caption}
          decimals={c.counter.decimals} durationInFrames={dur} rollFrames={Math.round(beat * 2)} size={c.size ?? 'hero'} color={color}
          align={c.align} x={c.x} y={c.y} exit={c.exit} />
      ) : c.lines && !c.spec ? (
        <KineticText lines={c.lines} durationInFrames={dur} entry={c.entry ?? 'cut'} exit={c.exit ?? (c.typeBeats ? 'fade' : 'cut')} size={c.size} color={color} align={c.align}
          x={c.x} y={c.y ?? (c.icon ? 67 : undefined)} />
      ) : null}
      {c.swap ? (
        <WordSwap prefix={c.swap.prefix} words={c.swap.words} everyFrames={Math.round(beat * (c.swap.everyBeats ?? 1))} color={color}
          accent={c.swap.accent} y={c.y ?? 50} />
      ) : null}
      {c.typing ? <Typing text={c.typing.text} cps={c.typing.cps} correctTo={c.typing.correctTo} color={color} y={c.y ?? 50} /> : null}
      {c.pill ? <Pill text={c.pill} tone={isLight(c.bg) ? 'light' : 'dark'} /> : null}
      {c.lowerThird ? <LowerThird name={c.lowerThird.name} title={c.lowerThird.title} side={c.lowerThird.side} color={color} at={Math.round(beat / 2)} /> : null}
    </Backdrop>
  );
};

export const Recap: React.FC<RecapProps> = ({bpm, offsetFrames = 0, cards, music, sfxVolume = 0.3, tailFrames = 45,
  musicFadeOutFrames = 0, sfxDir = 'sfx', autoMove: auto = true, voice, voiceFrom = 0}) => {
  const {fps, durationInFrames} = useVideoConfig();
  const g = beatGrid(bpm, fps, offsetFrames);
  const durs = cardFrames(cards, bpm, fps, offsetFrames, tailFrames);
  const starts = cardStarts(cards, bpm, fps, offsetFrames);
  const items: React.ReactNode[] = [];
  const sfx: React.ReactNode[] = [];
  cards.forEach((c, i) => {
    const cursor = starts[i] ?? 0; // beat-aligned start of this card
    const tf = i > 0 && c.transition ? transitionFrames(c.transition) : 0;
    if (tf > 0 && c.transition) {
      items.push(appleTransition(c.transition, `t${i}`));
      // the transition plays from this card's beat for tf frames: peak the whoosh in its middle
      if (c.transition === 'whip') sfx.push(<Sfx dir={sfxDir} key={`w${i}`} name="whoosh" at={cursor + Math.round(tf / 2)} volume={sfxVolume} />);
    }
    if (c.device?.tapSfx) {
      c.device.cards.slice(0, 3).forEach((_, k) => {
        sfx.push(<Sfx dir={sfxDir} key={`tap${i}-${k}`} name="click" at={cursor + Math.round(g.beat * (c.device?.everyBeats ?? 1) * (k + 1))} volume={sfxVolume * 0.8} />);
      });
    }
    if (c.sfx) sfx.push(<Sfx dir={sfxDir} key={`s${i}`} name={c.sfx} at={cursor} volume={sfxVolume * (c.sfx === 'hit' ? 1.4 : 1)} />);
    items.push(
      <TransitionSeries.Sequence key={`c${i}`} durationInFrames={durs[i] ?? 1}>
        <CardView c={c} dur={durs[i] ?? 1} beat={g.beat} move={c.move ?? (auto && hasPicture(c) ? autoMove(i) : 'static')} />
      </TransitionSeries.Sequence>,
    );
  });
  return (
    <AbsoluteFill style={{backgroundColor: COLOR.black}}>
      {music ? (
        <Html5Audio
          src={staticFile(music)}
          volume={(f) =>
            (voice ? Math.pow(10, AUDIO.musicUnderVoiceDb / 20) : 1) *
            (musicFadeOutFrames > 0
              ? interpolate(f, [durationInFrames - musicFadeOutFrames, durationInFrames], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})
              : 1)
          }
        />
      ) : null}
      {voice ? (
        <Sequence from={voiceFrom} layout="none">
          <Html5Audio src={staticFile(voice)} />
        </Sequence>
      ) : null}
      <TransitionSeries from={offsetFrames}>{items}</TransitionSeries>
      {sfx}
    </AbsoluteFill>
  );
};
