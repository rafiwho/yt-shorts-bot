#!/usr/bin/env bash
set -e

# Copy caption text safely
cp output.txt caption.txt

# Generate base video (no audio)
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
  silent.mp4

# Merge voice with video
ffmpeg -y \
  -i silent.mp4 \
  -i voice.wav \
  -c:v copy \
  -c:a aac \
  -shortest \
  output.mp4
