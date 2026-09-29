#!/bin/bash
# retime + downstream for all six Apple videos (no pixel re-measurement)
cd "$(dirname "$0")" && source ./env.sh
for s in sept26-event-recap wwdc23-17things wwdc22-day1-recap wwdc25-welcome wwdc26-sotu-recap ios26-liquid-glass; do
  for st in s2c_retime s3_text_anim s5_color_layout s6_frames s8_sync s9_summary; do
    python $st.py $s >> "$PROJECT_ROOT/.cache/logs/retime_$s.log" 2>&1 || echo "FAILED $st $s" >> "$PROJECT_ROOT/.cache/logs/retime_all.log"
  done
  echo "done $s $(date +%T)" >> "$PROJECT_ROOT/.cache/logs/retime_all.log"
done
echo ALLDONE >> "$PROJECT_ROOT/.cache/logs/retime_all.log"
