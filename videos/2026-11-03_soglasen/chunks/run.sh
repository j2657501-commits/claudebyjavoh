#!/bin/sh
# render in 12 s chunks (resumable), then concat + mastered audio
cd "$(dirname "$0")/.."
R=/home/user/claudebyjavoh/.claude/skills/obsion-motion/scripts
for i in 0 1 2 3; do f=chunks/c$i.mp4; [ -s $f ] && continue
  from=$((i*12)); secs=12; [ $i = 3 ] && secs=11.6
  node $R/render.cjs index.html --fps 60 --w 1080 --h 1920 --from $from --secs $secs --audio voice/mix.wav --no-loudnorm --out $f.tmp.mp4 && mv $f.tmp.mp4 $f
done
python3 $R/loudness.py voice/mix.wav chunks/master.wav
printf "file 'c0.mp4'\nfile 'c1.mp4'\nfile 'c2.mp4'\nfile 'c3.mp4'\n" > chunks/list.txt
ffmpeg -loglevel error -y -f concat -safe 0 -i chunks/list.txt -i chunks/master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -af lowpass=f=16000 -t 47.6 -movflags +faststart soglasen_final.mp4
echo DONE
