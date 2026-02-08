#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

cleantext=$(sed 's/[^a-zA-Z0-9 .,?!]/ /g' output.txt)

espeak-ng \
  -s 145 \
  -p 55 \
  -v en \
  -w voice.wav \
  "$cleantext"
