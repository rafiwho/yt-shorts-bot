#!/usr/bin/env bash
set -e

# Ensure predictable locale
export LC_ALL=C

# Limit FFmpeg threads (CRITICAL for memory)
export FFREPORT=file=ffmpeg.log:level=32

# Prepare text file for drawtext (safe, no shell expansion)
cp output.txt caption.txt

ffmpeg -y \
  -threads 1 \
  -loop 1 -i assets/bg.jpg \
  -vf "scale=720:1280,
       drawtext=textfile=caption.txt:
       fontcolor=white:
       fontsize=42:
       line_spacing=8:
       box=1:
       boxcolor=black@0.6:
       boxborderw=16:
       x=(w-text_w)/2:
       y=(h-text_h)/2" \
  -t 8 \
  -pix_fmt yuv420p \
  -movflags +faststart \
  output.mp4
