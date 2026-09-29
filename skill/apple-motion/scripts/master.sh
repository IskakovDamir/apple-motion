#!/bin/bash
# Master a rendered video to the measured Apple loudness (two-pass EBU R128 loudnorm, video copied).
# Usage: master.sh in.mp4 out.mp4 [LUFS] [TRUE_PEAK]   (defaults = AUDIO.lufs / AUDIO.truePeakDb in tokens.ts)
set -euo pipefail
IN=$1; OUT=$2; I=${3:--17.4}; TP=${4:--2.0}
J=$(ffmpeg -hide_banner -nostats -i "$IN" -af "loudnorm=I=$I:TP=$TP:LRA=7:print_format=json" -f null - 2>&1 | sed -n '/^{/,/^}/p')
g() { echo "$J" | sed -n "s/.*\"$1\" : \"\\(.*\\)\".*/\\1/p"; }
ffmpeg -hide_banner -v error -y -i "$IN" -c:v copy -af "loudnorm=I=$I:TP=$TP:LRA=7:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true" -ar 48000 -c:a aac -b:a 256k "$OUT"
ffmpeg -hide_banner -nostats -i "$OUT" -af ebur128=peak=true -f null - 2>&1 | grep -E "I:|Peak:" | tail -2
