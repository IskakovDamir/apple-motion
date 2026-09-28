#!/bin/bash
# Run OCR for a list of slugs sequentially (resumable). Usage: run_ocr_chain.sh slug1 slug2 ...
cd "$(dirname "$0")" && source ./env.sh
for s in "$@"; do
  python s2a_ocr.py "$s" >> "$PROJECT_ROOT/.cache/logs/ocr_$s.log" 2>&1
done
