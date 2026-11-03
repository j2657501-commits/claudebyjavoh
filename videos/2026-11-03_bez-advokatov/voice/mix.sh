#!/bin/sh
# voice/mix.sh — голос (ElevenLabs) + SFX/музыка со страницы → voice/mix.wav (мастеринг делает render.cjs)
set -e
cd "$(dirname "$0")/.."
node -e "
const {chromium}=require('playwright');const fs=require('fs'),path=require('path');
(async()=>{const b=await chromium.launch({args:['--mute-audio']});const p=await b.newPage();await p.goto('file://'+path.resolve('index.html')+'?render=1');await p.evaluate(async()=>{await window.__ready});
const s=await p.evaluate(async()=>await window.__audioWav());fs.writeFileSync('voice/sfx.wav',Buffer.from(s,'base64'));await b.close()})()"
ffmpeg -loglevel error -y -i voice/vo_raw.mp3 -i voice/sfx.wav -filter_complex "\
[0:a]aresample=48000,highpass=f=70,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=2,loudnorm=I=-16:TP=-2:LRA=9,apad=whole_dur=88.7,asplit=2[vo][key];\
[1:a]aresample=48000[bg];\
[bg][key]sidechaincompress=threshold=0.04:ratio=3:attack=25:release=350[duck];\
[vo]pan=stereo|c0=c0|c1=c0[vos];\
[vos][duck]amix=inputs=2:duration=longest:normalize=0[m]" -map "[m]" -ar 48000 voice/mix.wav
echo "voice/mix.wav ready"
