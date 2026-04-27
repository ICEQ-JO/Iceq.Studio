#!/bin/bash

# FFmpeg Shim to handle missing libx264 by using libopenh264
# and removing incompatible options like x264-params, crf, and preset.

ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    libx264)
      ARGS+=("libopenh264")
      ;;
    -x264-params|-crf|-preset)
      # Skip the flag and its value
      shift
      ;;
    *)
      ARGS+=("$1")
      ;;
  esac
  shift
done

# Optionally add default quality for libopenh264
# ARGS+=("-rc_mode" "0")

exec /usr/bin/ffmpeg "${ARGS[@]}"
