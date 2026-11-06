#!/usr/bin/env bash
# Downloads the videos and the model weights (they are not stored in git).
# Files that already exist are skipped, so it is safe to run again.
set -euo pipefail
cd "$(dirname "$0")/.."

MEVA=https://mevadata-public-01.s3.amazonaws.com/drops-123-r13
VIDEOS=(
  "2018-03-09/10/2018-03-09.10-40-01.10-45-01.school.G420.r13.avi"  # entrance
  "2018-03-07/17/2018-03-07.17-20-00.17-25-00.school.G421.r13.avi"  # counter
  "2018-03-07/11/2018-03-07.11-10-01.11-15-01.school.G421.r13.avi"  # counter_morning
)
WEIGHTS_URL=https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo11n.pt

download() {  # download <url> <file>
  if [ -f "$2" ]; then
    echo "already here: $2"
    return
  fi
  echo "downloading:  $2"
  curl -fL --retry 3 -o "$2.part" "$1"  # .part first, so a broken download is never mistaken for a full file
  mv "$2.part" "$2"
}

mkdir -p videos weights
for path in "${VIDEOS[@]}"; do
  download "$MEVA/$path" "videos/meva_$(basename "$path")"
done
download "$WEIGHTS_URL" weights/yolo11n.pt
