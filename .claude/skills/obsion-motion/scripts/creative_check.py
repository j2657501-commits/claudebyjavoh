#!/usr/bin/env python3
"""creative_check.py plan/creative.md — FORM check of the creative plan (OBSION Motion §1 step 0); the critic judges the content.
Expects sections (any heading text containing): «частых»/«common» (≥ 10 list items, ≥ 5 marked banned/запрещ/❌),
«сюрприз»/«surprise» (≥ 3 items each with a second mark like «5 с»/«0:05»/«5s»), «фирменн»/«signature» (non-empty),
«семя»/«seed» (non-empty), «столкнов»/«collision» (non-empty). Exit 1 with reasons if anything is missing."""
import re, sys
t = open(sys.argv[1], encoding="utf-8").read()
secs = re.split(r"\n(?=#+ )", "\n" + t)
def sec(*keys):
    for s in secs:
        h = s.strip().split("\n", 1)[0].lower()
        if h.startswith("#") and any(k in h for k in keys): return s
    return ""
items = lambda s: [l for l in s.split("\n") if re.match(r"\s*([-*•]|\d+[.)])\s+\S", l)]
errs = []
words = lambda l: len(re.findall(r"\w+", re.sub(r"^\s*([-*•]|\d+[.)])\s*", "", l)))
c = sec("частых", "common"); ci = items(c)
if len(ci) < 10: errs.append(f"common devices: {len(ci)} items, need ≥ 10")
if any(words(l) < 3 for l in ci): errs.append("every common device needs ≥ 3 words (no filler)")
if len(set(l.strip().lower() for l in ci)) != len(ci): errs.append("common devices must be unique")
if len(set((re.findall(r"\w+", l.lower()) or [""])[0] for l in ci)) < 5: errs.append("≥ 5 common devices must start with different words")
if sum(1 for l in ci if re.search(r"запрещ|banned|❌|~~", l, re.I)) < 5: errs.append("mark ≥ 5 common devices as banned (запрещён / banned / ❌)")
s = items(sec("сюрприз", "surprise"))
if len(s) < 3: errs.append(f"surprises: {len(s)}, need ≥ 3")
if any(words(l) < 4 for l in s): errs.append("every surprise needs a real description (≥ 4 words)")
if sum(1 for l in s if re.search(r"\d+([.,]\d+)?\s*(с|s|сек)\b|\d+:\d\d", l)) < 3: errs.append("each surprise needs its second (e.g. «7 с» or «0:07»)")
for keys, name in [(("фирменн", "signature"), "signature moment"), (("семя", "seed"), "seed and payoff"), (("столкнов", "collision"), "collision test")]:
    body = sec(*keys).split("\n", 1)[1].strip() if sec(*keys) else ""
    if len(body) < 15 or len(re.findall(r"\w+", body)) < 4 or len(set(body.replace(" ", ""))) < 6: errs.append(f"{name}: missing, empty or filler")
print("OK: creative plan passes" if not errs else "REJECTED:\n- " + "\n- ".join(errs)); sys.exit(1 if errs else 0)
