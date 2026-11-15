#!/usr/bin/env python3
"""Renders every listening section to audio/listening-NN.mp3 with the Kokoro offline TTS model.

Usage: python3 gen_audio.py <dir with kokoro-v1.0.onnx and voices-v1.0.bin> [only_number ...]
"""
import os, subprocess, sys, tempfile
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
from build import ROOT, listening_units

FEMALE = ["bf_emma", "af_heart", "bf_isabella", "af_bella", "af_sarah", "af_kore"]
MALE = ["bm_fable", "am_michael", "bm_daniel", "am_fenrir", "am_puck", "bm_lewis"]
NARRATOR = "bm_george"
SR = 24000


def main():
    mdir = sys.argv[1]
    only = {int(x) for x in sys.argv[2:]}
    k = Kokoro(os.path.join(mdir, "kokoro-v1.0.onnx"), os.path.join(mdir, "voices-v1.0.bin"))
    out_dir = os.path.join(ROOT, "audio")
    os.makedirs(out_dir, exist_ok=True)

    def say(text, voice, speed):
        s, sr = k.create(text, voice=voice, speed=speed, lang="en-gb" if voice[0] == "b" else "en-us")
        assert sr == SR
        return s.astype(np.float32)

    gap = lambda sec: np.zeros(int(SR * sec), dtype=np.float32)
    for n, u in enumerate(listening_units(), 1):
        out = os.path.join(out_dir, f"listening-{n:02d}.mp3")
        if (only and n not in only) or (not only and os.path.exists(out)):
            continue
        fi = mi = n  # rotate voices from unit to unit
        vmap = {}
        for sp, g in u["voices"].items():
            if g == "f":
                vmap[sp] = FEMALE[fi % len(FEMALE)]; fi += 1
            else:
                vmap[sp] = MALE[mi % len(MALE)]; mi += 1
        speed = 0.95 if u["cat"] in ("Section 3", "Section 4") else 1.0
        # exam-style frame: introduction, time to read the questions, the recording, closing line
        parts = [say(f"{u['cat']}. {u['ctx']} First, you have some time to look at questions one to ten.",
                     NARRATOR, 0.95), gap(20),
                 say("Now listen carefully and answer questions one to ten.", NARRATOR, 0.95), gap(1.6)]
        prev = None
        for sp, tx in u["lines"]:
            parts += [gap(0.55 if sp != prev else 0.7), say(tx, vmap[sp], speed)]
            prev = sp
        parts += [gap(2.0), say(f"That is the end of {u['cat'].lower()}. You now have half a minute to check your answers.",
                                NARRATOR, 0.95), gap(0.5)]
        audio = np.concatenate(parts)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as t:
            sf.write(t.name, audio, SR)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", t.name, "-ac", "1", "-ar", "24000",
                        "-codec:a", "libmp3lame", "-b:a", "48k",
                        "-metadata", f"title=Listening {n:02d}. {u['name']}",
                        "-metadata", "album=IELTS 4 Skills Pack", "-metadata", f"track={n}", out], check=True)
        os.unlink(t.name)
        print(f"{n:02d} {u['name']} [{u['cat']}] {len(audio)/SR:.0f}s {vmap}", flush=True)


if __name__ == "__main__":
    main()
