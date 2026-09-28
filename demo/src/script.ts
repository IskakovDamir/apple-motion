import type {Card} from './Recap';
import data from './cards.json';

// The whole video is data: every card is timed in beats (120 BPM -> 1 beat = 15 frames at 30 fps).
// scripts/eval_render.py reads the same JSON to know the ground truth of every animation.
export const bpm: number = data.bpm;
export const offsetFrames: number = data.offsetFrames;
export const cards = data.cards as Card[];
