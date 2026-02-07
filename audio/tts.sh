#!/usr/bin/env bash
set -e

# Clean text (espeak hates special chars)
sed 's/[^a-zA-Z0-9 .,?!]/ /g' output.txt > clean.txt

# Generate voice
espeak-ng \
  -s 145 \
  -p 55 \
  -v en \
  -w voice.wav \
  "$(cat clean.txt)"
