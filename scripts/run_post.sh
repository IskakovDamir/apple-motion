#!/bin/bash
# Steps 2b..9 for each slug once its OCR (step 2a) has finished. Usage: run_post.sh [slug ...]
cd "$(dirname "$0")" && source ./env.sh
SLUGS=${@:-sept26-event-recap wwdc23-17things wwdc22-day1-recap wwdc25-welcome wwdc26-sotu-recap ios26-liquid-glass}
for s in $SLUGS; do
  until [ -f "$DATA_DIR/$s/ocr_summary.json" ] && ! pgrep -f "s2a_ocr.py $s" >/dev/null; do sleep 30; done
  log="$PROJECT_ROOT/.cache/logs/post_$s.log"
  echo "== $(date) $s" >> "$log"
  for step in s2b_text_events s3_text_anim s4_motion s5_color_layout s6_frames s8_sync s9_summary; do
    python $step.py "$s" >> "$log" 2>&1 || echo "FAILED $step" >> "$log"
  done
  echo "== done $(date) $s" >> "$log"
done
