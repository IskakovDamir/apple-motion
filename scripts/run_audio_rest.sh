#!/bin/bash
cd "$(dirname "$0")" && source ./env.sh
for s in wwdc26-sotu-recap ios26-liquid-glass sept26-event-recap; do
  rm -rf "$DATA_DIR/$s/audio/_demucs"
  python s7_audio.py "$s" >> "$PROJECT_ROOT/.cache/logs/audio.log" 2>&1
done
echo ALLDONE2 >> "$PROJECT_ROOT/.cache/logs/audio.log"
