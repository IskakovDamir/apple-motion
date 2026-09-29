# Source at the top of every script / shell session in this project.
# Everything heavy stays on the external Transcend drive.
export PROJECT_ROOT=/Volumes/Transcend/dev/apple-motion
if [ ! -d /Volumes/Transcend ] || [ ! -w "$PROJECT_ROOT" ]; then
  echo "env.sh: /Volumes/Transcend not mounted or project not writable" >&2
  return 1 2>/dev/null || exit 1
fi
export CACHE_ROOT="$PROJECT_ROOT/.cache"
export PIP_CACHE_DIR="$CACHE_ROOT/pip"
export TORCH_HOME="$CACHE_ROOT/torch"
export HF_HOME="$CACHE_ROOT/hf"
export XDG_CACHE_HOME="$CACHE_ROOT/xdg"
export TMPDIR="$CACHE_ROOT/tmp"
export EASYOCR_DIR="$CACHE_ROOT/easyocr"
export MPLCONFIGDIR="$CACHE_ROOT/mpl"
export NUMBA_CACHE_DIR="$CACHE_ROOT/numba"
export YTDLP_CACHE_DIR="$CACHE_ROOT/yt-dlp"
export PYTHONPYCACHEPREFIX="$CACHE_ROOT/pycache"
export COPYFILE_DISABLE=1
# keep background jobs from oversubscribing the 10-core M4 (and swapping)
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-3}
export MKL_NUM_THREADS=$OMP_NUM_THREADS VECLIB_MAXIMUM_THREADS=$OMP_NUM_THREADS OPENBLAS_NUM_THREADS=$OMP_NUM_THREADS
export CV_THREADS=${CV_THREADS:-3}
export DATA_DIR="$PROJECT_ROOT/data"
export npm_config_cache="$CACHE_ROOT/npm"
# optional read-only RAM-disk copy of data/_src (see common.video_path)
[ -d /Volumes/amvideo ] && export VIDEO_CACHE_DIR=/Volumes/amvideo
export REMOTION_CACHE_DIR="$CACHE_ROOT/remotion"
mkdir -p "$PIP_CACHE_DIR" "$TORCH_HOME" "$HF_HOME" "$XDG_CACHE_HOME" "$TMPDIR" "$EASYOCR_DIR" \
         "$MPLCONFIGDIR" "$NUMBA_CACHE_DIR" "$YTDLP_CACHE_DIR" "$DATA_DIR"
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
  . "$PROJECT_ROOT/.venv/bin/activate"
fi
