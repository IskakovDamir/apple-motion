import React from 'react';
import {AbsoluteFill, interpolate} from 'remotion';
import {linearTiming, springTiming, TransitionSeries, type TransitionPresentation, type TransitionPresentationComponentProps} from '@remotion/transitions';
import {fade} from '@remotion/transitions/fade';
import {wipe} from '@remotion/transitions/wipe';
import {DURATION, SPRING} from './tokens';

type WhipProps = {direction: 'left' | 'right' | 'up' | 'down'; blurPx: number};

/** Whip: both shots travel one frame-width with a directional smear; the speed peaks mid-transition. */
const WhipComponent: React.FC<TransitionPresentationComponentProps<WhipProps>> = ({
  children,
  presentationDirection,
  presentationProgress,
  passedProps,
}) => {
  const p = presentationProgress;
  const sign = passedProps.direction === 'left' || passedProps.direction === 'up' ? -1 : 1;
  const axis = passedProps.direction === 'left' || passedProps.direction === 'right' ? 'X' : 'Y';
  const offset = presentationDirection === 'exiting' ? interpolate(p, [0, 1], [0, 100]) : interpolate(p, [0, 1], [-100, 0]);
  const speed = Math.sin(Math.PI * p); // 0 -> 1 -> 0
  const blur = passedProps.blurPx * speed;
  return (
    <AbsoluteFill
      style={{
        transform: `translate${axis}(${sign * offset}%)`,
        filter: blur > 0.3 ? `blur(${blur}px)` : undefined,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

export const whip = (props: Partial<WhipProps> = {}): TransitionPresentation<WhipProps> => ({
  component: WhipComponent,
  props: {direction: 'left', blurPx: 24, ...props},
});

type ScaleThroughProps = {scaleTo: number};

/** Scale through: push hard into the outgoing shot while it fades, the new shot settles from slightly large. */
const ScaleThroughComponent: React.FC<TransitionPresentationComponentProps<ScaleThroughProps>> = ({
  children,
  presentationDirection,
  presentationProgress,
  passedProps,
}) => {
  const p = presentationProgress;
  const exiting = presentationDirection === 'exiting';
  const scale = exiting ? interpolate(p, [0, 1], [1, passedProps.scaleTo]) : interpolate(p, [0, 1], [1.12, 1]);
  const opacity = exiting ? interpolate(p, [0.4, 1], [1, 0], {extrapolateLeft: 'clamp'}) : interpolate(p, [0, 0.5], [0, 1], {extrapolateRight: 'clamp'});
  const blur = exiting ? p * 10 : (1 - p) * 6;
  return <AbsoluteFill style={{transform: `scale(${scale})`, opacity, filter: `blur(${blur}px)`}}>{children}</AbsoluteFill>;
};

export const scaleThrough = (props: Partial<ScaleThroughProps> = {}): TransitionPresentation<ScaleThroughProps> => ({
  component: ScaleThroughComponent,
  props: {scaleTo: 2.2, ...props},
});

export type AppleTransition = 'cut' | 'whip' | 'dissolve' | 'maskWipe' | 'scaleThrough';

/** Frames a transition overlaps the two shots (0 for a cut). */
export const transitionFrames = (type: AppleTransition, frames: number = DURATION.transitionFrames): number =>
  type === 'cut' ? 0 : frames;

/**
 * <TransitionSeries.Transition> for an Apple transition, or null for a cut
 * (a cut is just the next TransitionSeries.Sequence - Apple's default, >90% of edits).
 */
export const appleTransition = (type: AppleTransition, key: string, frames: number = DURATION.transitionFrames) => {
  const timing = springTiming({config: SPRING.camera, durationInFrames: frames});
  switch (type) {
    case 'whip':
      return <TransitionSeries.Transition key={key} presentation={whip()} timing={timing} />;
    case 'dissolve':
      return <TransitionSeries.Transition key={key} presentation={fade()} timing={linearTiming({durationInFrames: frames})} />;
    case 'maskWipe':
      return <TransitionSeries.Transition key={key} presentation={wipe({direction: 'from-left'})} timing={timing} />;
    case 'scaleThrough':
      return <TransitionSeries.Transition key={key} presentation={scaleThrough()} timing={timing} />;
    default:
      return null;
  }
};
