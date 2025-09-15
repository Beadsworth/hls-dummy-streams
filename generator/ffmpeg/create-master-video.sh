#!/bin/sh
set -eu

INPUT="video.mp4"
ZIP="${INPUT}.zip"
MASTER="video_4k.mp4"

# Unzip
unzip "$ZIP" && mv *.mp4 "$INPUT"

# Create 4K master copy
ffmpeg -y -i "$INPUT" \
  -c:v libx264 -preset fast -profile:v high -level 5.1 \
  -vf "scale=3840:2160,fps=24" -b:v 12000k \
  -c:a aac -b:a 256k -ar 48000 -ac 2 \
  -movflags +faststart -brand mp42 \
  "$MASTER"
