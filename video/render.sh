#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ffmpeg -y \
  -threads 1 \
  -loop 1 -i assets/bg.jpg \
  -vf "scale=720:1280" \
  -t 8 \
  -pix_fmt yuv420p \
  silent.mp4

# 2. Mix voice + background music with ducking
ffmpeg -y \
  -i silent.mp4 \
  -i voice.wav \
  -stream_loop -1 -i audio/bg.mp3 \
  -filter_complex "\
    [2:a]volume=0.15[a_bg]; \
    [1:a][a_bg]sidechaincompress=threshold=0.02:ratio=10:attack=5:release=200[a_mix]" \
  -map 0:v \
  -map "[a_mix]" \
  -c:v copy \
  -c:a aac \
  -shortest \
  -metadata:s:v:0 rotate=0 \
  output.mp4
