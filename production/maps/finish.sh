#!/bin/bash
# usage: finish.sh <episode_dir> <out.mp4> : mux video + mix, loudness-normalise to -14 LUFS (TikTok/Shorts)
B="$1/build"
ffmpeg -v error -y -i "$B/video_noaudio.mp4" -i "$B/mix.wav" -map 0:v -map 1:a -c:v copy \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11" -ar 48000 -c:a aac -b:a 256k -movflags +faststart -shortest "$2"
ffprobe -v error -show_entries format=duration,bit_rate:stream=width,height -of compact "$2"
