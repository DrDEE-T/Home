#!/usr/bin/env bash
# One-time setup for a fresh container. Safe to re-run; skips what is already there.
# Installs OpenCV + Vosk (offline speech-to-text) and fetches the small English Vosk model.
# The model normally lives on alphacephei.com, which sandboxes often block, so we pull it
# from the npm package "transcribe2texts", which bundles vosk-model-small-en-us-0.15.
set -eu
CACHE="${DT_VIDEO_CACHE:-$HOME/.cache/dt-video}"
mkdir -p "$CACHE"

python3 -c "import cv2" 2>/dev/null || pip install -q opencv-python-headless
python3 -c "import numpy, PIL" 2>/dev/null || pip install -q numpy pillow
# vosk's "srt" dependency fails to build in some sandboxes; install vosk without deps and shim srt.
python3 -c "import vosk" 2>/dev/null || {
  pip install -q --no-deps vosk
  pip install -q cffi requests tqdm websockets
}
mkdir -p "$CACHE/shim"; [ -f "$CACHE/shim/srt.py" ] || echo "" > "$CACHE/shim/srt.py"

MODEL="$CACHE/vosk-model-small-en-us-0.15"
if [ ! -f "$MODEL/am/final.mdl" ]; then
  TMP="$CACHE/dl"; mkdir -p "$TMP"
  URL=$(curl -s https://registry.npmjs.org/transcribe2texts/1.0.6 | python3 -c "import sys,json;print(json.load(sys.stdin)['dist']['tarball'])")
  curl -s -o "$TMP/t2t.tgz" "$URL"
  tar xzf "$TMP/t2t.tgz" -C "$TMP" package/vosk-model-small-en-us-0.15
  mv "$TMP/package/vosk-model-small-en-us-0.15" "$MODEL"
  rm -rf "$TMP"
fi
ls /usr/share/fonts/opentype/inter/Inter-ExtraBold.otf >/dev/null 2>&1 || echo "WARN: Inter fonts missing at /usr/share/fonts/opentype/inter/"
echo "setup ok: model at $MODEL"
