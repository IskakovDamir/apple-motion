import React from 'react';
import {Composition} from 'remotion';
import {Recap, recapDuration, type RecapProps} from './Recap';
import {Calibration, calibrationDuration} from './Calibration';
import {exampleProps} from './Example';
import {bpm, cards, offsetFrames} from './script';
import {Recap as AppleRecap, recapDuration as appleRecapDuration} from '@apple-motion';
import {agentProps} from './agent/AgentRecap';
import {strideProps} from './agent2/StrideRecap';
import {round3Props} from './agent3/Round3Recap';

const props: RecapProps = {bpm, offsetFrames, cards, music: 'music.wav'};

export const RemotionRoot: React.FC = () => (
  <>
  <Composition
    id="Recap"
    component={Recap}
    durationInFrames={recapDuration(props, 30)}
    fps={30}
    width={1920}
    height={1080}
    defaultProps={props}
  />
  <Composition id="ExampleScript" component={Recap} durationInFrames={recapDuration(exampleProps, 30)} fps={30} width={1920} height={1080} defaultProps={exampleProps} />
  <Composition id="Calibration" component={Calibration} durationInFrames={calibrationDuration} fps={30} width={1920} height={1080} />
  <Composition
    id="AgentRecap"
    component={AppleRecap}
    durationInFrames={appleRecapDuration(agentProps, 30)}
    fps={30}
    width={1920}
    height={1080}
    defaultProps={agentProps}
  />
  <Composition
    id="StrideRecap"
    component={AppleRecap}
    durationInFrames={appleRecapDuration(strideProps, 30)}
    fps={30}
    width={1920}
    height={1080}
    defaultProps={strideProps}
  />
  <Composition
    id="Round3Recap"
    component={AppleRecap}
    durationInFrames={appleRecapDuration(round3Props, 30)}
    fps={30}
    width={1920}
    height={1080}
    defaultProps={round3Props}
  />
  </>
);
