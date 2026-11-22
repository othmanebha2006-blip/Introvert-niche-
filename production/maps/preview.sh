#!/bin/bash
# usage: preview.sh <episode_dir> <times comma-separated> <out.jpg> [cols]
M=$(cd "$(dirname "$0")" && pwd); EP=$(cd "$1" && pwd)
python3 "$M/render.py" "$EP" --preview "$2" 2>&1 | grep -v Fontconfig | grep -v '\.png'
files=(); for t in ${2//,/ }; do files+=("$EP/build/preview/t$(printf '%06.2f' $t).png"); done
args=(); for f in "${files[@]}"; do args+=(-i "$f"); done
n=${#files[@]}; cols=${4:-8}; rows=$(( (n + cols - 1) / cols ))
ffmpeg -v error -y "${args[@]}" -filter_complex "$(for i in $(seq 0 $((n-1))); do printf '[%d]scale=300:-1[v%d];' $i $i; done)$(for i in $(seq 0 $((n-1))); do printf '[v%d]' $i; done)xstack=inputs=$n:layout=$(python3 -c "
n=$n;c=$cols;print('|'.join(f'{(i%c)*300}_{(i//c)*533}' for i in range(n)))"):fill=black" -frames:v 1 "$3"
