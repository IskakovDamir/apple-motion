import path from 'node:path';
import {Config} from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(92);
Config.setConcurrency(3);
// The skill's component library lives outside this project: alias it and resolve its imports here.
Config.overrideWebpackConfig((c) => ({
  ...c,
  resolve: {
    ...c.resolve,
    alias: {
      ...(c.resolve?.alias ?? {}),
      '@apple-motion': path.resolve(process.cwd(), '../skill/apple-motion/templates/remotion'),
    },
    modules: [path.resolve(process.cwd(), 'node_modules'), 'node_modules'],
  },
}));
