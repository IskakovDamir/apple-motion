#!/bin/bash
# run_steps.sh "slug:step1,step2 slug2:step..." - sequential, logged, continues on failure
cd "$(dirname "$0")" && source ./env.sh
for spec in "$@"; do
  s=${spec%%:*}; steps=${spec#*:}
  log="$PROJECT_ROOT/.cache/logs/post_$s.log"
  for step in ${steps//,/ }; do
    echo "== $(date +%T) $step" >> "$log"
    python $step.py "$s" >> "$log" 2>&1 || echo "FAILED $step" >> "$log"
  done
done
echo "ALLDONE $*" >> "$PROJECT_ROOT/.cache/logs/steps.log"
