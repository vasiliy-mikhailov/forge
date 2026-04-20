#!/usr/bin/env bash
# Move all source-media files (video + audio) from a local "incoming"
# folder on your laptop into the kurpatov-wiki sources tree on the
# server over LAN. Files are *moved* (deleted locally after each one
# is fully transferred + verified), not copied — so you can drop new
# lectures into ~/Downloads/Курпатов/ and run this once to ship them.
#
# The kurpatov-transcriber daemon has an inotify watcher on the sources
# tree, so transcription starts automatically the moment files land.
# The daemon picks up any suffix in its MEDIA_EXTENSIONS allow-list
# (video: mp4/mkv/webm/mov/m4v/avi; audio: mp3/m4a/wav/ogg/flac/opus/aac).
# This script uses the same list when selecting what to push.
#
# Usage:
#   scripts/push-sources.sh                # default src + default module
#   MODULE='006 ...' scripts/push-sources.sh
#   COURSE='...' MODULE='...' SRC=~/elsewhere scripts/push-sources.sh
#   scripts/push-sources.sh --dry-run      # show what would move, change nothing
#
# Defaults (override with env vars):
#   SRC      = ~/Downloads/Курпатов
#   HOST     = 192.168.0.2          (server on LAN; set to mikhailov.tech for VPN)
#   PORT     = 22                   (set to 2222 for VPN)
#   REMOTE   = vmihaylov
#   COURSE   = Психолог-консультант
#   MODULE   = 005 Природа внутренних конфликтов. Базовые психологические потребности
#   SOURCES  = /mnt/steam/forge/kurpatov-wiki/sources
#
# Requires: GNU rsync 3.x (macOS default `openrsync` / 2.6.9 won't work —
# `brew install rsync` and make sure /opt/homebrew/bin is ahead in PATH).

set -euo pipefail

SRC="${SRC:-$HOME/Downloads/Курпатов}"
HOST="${HOST:-192.168.0.2}"
PORT="${PORT:-22}"
REMOTE="${REMOTE:-vmihaylov}"
COURSE="${COURSE:-Психолог-консультант}"
MODULE="${MODULE:-005 Природа внутренних конфликтов. Базовые психологические потребности}"
SOURCES="${SOURCES:-/mnt/steam/forge/kurpatov-wiki/sources}"

# MEDIA_EXTENSIONS — must stay in sync with notebooks/{02,03}*.py.
MEDIA_EXTS=(mp4 mkv webm mov m4v avi mp3 m4a wav ogg flac opus aac)

DRY_RUN=""
if [[ "${1:-}" == "--dry-run" || "${1:-}" == "-n" ]]; then
  DRY_RUN="n"
fi

# Sanity: rsync must be GNU 3.x. openrsync has no -s and no --append-verify.
# Capture the version line into a variable (avoids head/pipefail SIGPIPE races).
rsync_ver="$(rsync --version 2>/dev/null || true)"
rsync_ver="${rsync_ver%%$'\n'*}"
case "$rsync_ver" in
  rsync\ *) ;;    # GNU rsync — good
  *)
    echo "error: your \`rsync\` is '${rsync_ver:-unknown}' — not GNU rsync." >&2
    echo "fix:   brew install rsync, then ensure /opt/homebrew/bin is in PATH." >&2
    exit 2
    ;;
esac

if [[ ! -d "$SRC" ]]; then
  echo "error: source folder does not exist: $SRC" >&2
  echo "hint:  drop your media files there, or override with SRC=~/other/path" >&2
  exit 2
fi

shopt -s nullglob nocaseglob
files=()
for ext in "${MEDIA_EXTS[@]}"; do
  for f in "$SRC"/*."$ext"; do
    files+=("$f")
  done
done
shopt -u nocaseglob

if [[ ${#files[@]} -eq 0 ]]; then
  echo "nothing to do: no media files in $SRC"
  echo "  (looking for: ${MEDIA_EXTS[*]})"
  exit 0
fi

DEST="$REMOTE@$HOST:$SOURCES/$COURSE/$MODULE/"

echo "moving ${#files[@]} file(s):"
for f in "${files[@]}"; do echo "  - $(basename "$f")"; done
echo "  -> $DEST"
echo

rsync -avh${DRY_RUN} -s \
  --partial --progress --append-verify --remove-source-files \
  -e "ssh -p $PORT -o StrictHostKeyChecking=accept-new" \
  "${files[@]}" "$DEST"

if [[ -z "$DRY_RUN" ]]; then
  echo
  echo "done. the transcriber's inotify watcher will queue each file within ~10s."
  echo "tail it with:  ssh -p $PORT $REMOTE@$HOST 'docker logs -f --tail=20 kurpatov-transcriber'"
fi
