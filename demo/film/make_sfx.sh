#!/bin/sh
# Synthesised sound effects for the film (no third-party samples): whoosh, click, ping, hit.
set -e
D="$(dirname "$0")/studio/public/audio/sfx"
mkdir -p "$D"
ff() { ffmpeg -loglevel error -y "$@"; }
# whoosh: pink noise through a rising band-pass, swelled in and out
ff -f lavfi -i "anoisesrc=color=pink:duration=0.7:amplitude=0.6" -af "bandpass=f=900:width_type=o:w=1.6,highpass=f=200,afade=t=in:d=0.45:curve=exp,afade=t=out:st=0.45:d=0.25,volume=1.6,aresample=48000" -ac 2 "$D/whoosh.wav"
# key click: very short filtered noise tick
ff -f lavfi -i "anoisesrc=color=white:duration=0.03:amplitude=0.8" -af "highpass=f=2500,afade=t=out:d=0.03,volume=0.9,aresample=48000" -ac 2 "$D/click.wav"
# ping: two soft sines, quick decay
ff -f lavfi -i "sine=f=1318:duration=0.6" -f lavfi -i "sine=f=1975:duration=0.6" -filter_complex "[0][1]amix=inputs=2,afade=t=out:st=0.02:d=0.55:curve=exp,volume=0.5,aresample=48000" -ac 2 "$D/ping.wav"
# hit: low sine thump for the title
ff -f lavfi -i "sine=f=52:duration=1.4" -f lavfi -i "anoisesrc=color=brown:duration=0.25:amplitude=0.5" -filter_complex "[0]afade=t=out:st=0.05:d=1.3:curve=exp[a];[1]lowpass=f=400,afade=t=out:d=0.25[b];[a][b]amix=inputs=2,volume=2.2,aresample=48000" -ac 2 "$D/hit.wav"
echo "sfx written to $D"
