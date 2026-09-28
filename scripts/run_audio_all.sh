#!/bin/bash
cd "$(dirname "$0")" && source ./env.sh
for s in wwdc23-17things wwdc22-day1-recap wwdc25-welcome wwdc26-sotu-recap ios26-liquid-glass sept26-event-recap; do
  python s7_audio.py "$s" >> "$PROJECT_ROOT/.cache/logs/audio.log" 2>&1
done
echo ALLDONE >> "$PROJECT_ROOT/.cache/logs/audio.log"
