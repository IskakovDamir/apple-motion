import type {Card, RecapProps} from '@apple-motion';
import data from './vo_cards.json';

// Voice-over recap: cards timed to the spoken words by skill/apple-motion/scripts/vo_cards.py.
export const voProps: RecapProps = {
  bpm: data.bpm,
  cards: data.cards as Card[],
  music: 'vo/music.wav',
  voice: 'vo/vo.wav',
  voiceFrom: data.voiceFromFrames,
  voiceSpan: data.voiceSpanFrames as [number, number],
  sfxDir: 'vo/sfx',
  musicFadeOutFrames: 30,
};
