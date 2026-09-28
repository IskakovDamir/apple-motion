import React from 'react';
import {Composition} from 'remotion';
import {Recap, recapDuration, type RecapProps} from './Recap';
import {Calibration, calibrationDuration} from './Calibration';
import {bpm, cards, offsetFrames} from './script';

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
  <Composition id="Calibration" component={Calibration} durationInFrames={calibrationDuration} fps={30} width={1920} height={1080} />
  </>
);
