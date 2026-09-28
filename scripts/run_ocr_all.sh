#!/bin/bash
# Single OCR worker over all videos (MPS memory: one process at a time). Resumable.
cd "$(dirname "$0")" && source ./env.sh
mkdir -p "$PROJECT_ROOT/.cache/run" && echo $$ > "$PROJECT_ROOT/.cache/run/ocr.pid"
for s in sept26-event-recap wwdc23-17things wwdc22-day1-recap wwdc25-welcome wwdc26-sotu-recap ios26-liquid-glass; do
  python s2a_ocr.py "$s" >> "$PROJECT_ROOT/.cache/logs/ocr_$s.log" 2>&1
done
echo ALLDONE >> "$PROJECT_ROOT/.cache/logs/ocr_all.log"
