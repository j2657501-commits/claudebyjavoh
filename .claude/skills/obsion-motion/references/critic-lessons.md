# Уроки критика: что не пускало первые версии к 10 и что закладывать сразу

**Owner:** «учись на критике, который выдаёт отчёты, чтобы в следующие разы быть ближе к 10 из 10».

**Sources:** 8 reports from the episode tests (`content/youtube/2026-10-19_obsion-claude-animation/research/critic/`):
- loop critics S1-C r0–r2, S2-C r0, S3-C r0, S4-C r0;
- blind judges S1 and S3.

First drafts made with the skill scored 7.0–8.1. The defects below repeated across tests. Each one is now a rule, applied BEFORE the first render.

| # | Recurring defect (where seen) | Rule for the first draft | Self-check |
|---|---|---|---|
| 1 | Frame 0 empty or «being drawn», the first surprise at 3 s (S1, S2, S4) | The subject is ALREADY acting on frame 0; the first surprise lands ≤ 1.5 s | Look at frame 0 and at 1.5 s: does something happen, not just appear? |
| 2 | Camera dead in the finale or mid-film: 3.7 s (S2), 7.5 s (S3), 9.9 s total (S1) | No hold ≥ 0.5 s anywhere, the finale included: a push, an orbit or a drift always runs | `watch.py`: `holds_total_s` = 0, low-motion < 10 % of runtime |
| 3 | The hero object sits at one screen point all film (S1) | The hero moves in screen space and has body language per scene | Plot the hero's screen position: it must travel |
| 4 | The climax lands at 74 % and is followed by an epilogue (S3) | The payoff is the LAST beat and the LOUDEST hit (+10 dB, 150 ms of silence before it), then ≤ 3 s out | Find the peak in the waveform: it is in the last 10 % |
| 5 | One device repeated 6× (S1 film fly-in) | Every beat gets its own gag rooted in its world's physics | List the beats: no two exits are the same |
| 6 | First answers of the genre (snail, cat hero, whale, Mario; S1) | For each world, write the 3 first ideas and use none of them | `creative.md` lists the banned ones per world |
| 7 | No through-line: the bold ideas that lifted every score were ONE object/rule threading everything (red sun «Луч», camera = pointer, kleptomaniac shadow) | Pick one carrier (object, rule, sound) that is planted in 3 s, transforms through every beat and pays off in the final frame | The retelling uses the carrier |
| 8 | Details too small to notice: 20 px «Ø 9», 60 px mirror gag (S1, S3) | Anything meant to be noticed is ≥ 120 px and on screen ≥ 1 s; a gag gets a medium close-up | Check each gag at 1× on a phone-size preview |
| 9 | Gag hidden: a face behind a bus, a key sign blurred by a whip (S2, S3) | The gag's face and prop are unoccluded and sharp for ≥ 0.7 s | Dense sheet at 12 fps over the gag |
| 10 | Sound late by 2 frames, sound «walls» (S2 stomp, S3 whooshes, S4) | Sound and picture come from ONE event list. Snap SFX to the frames the picture actually updates on («on twos» styles!). Low-pass whooshes at 8 kHz; no broadband bed under dialogue-free action | `metrics.py`: sync ≥ 70 % within ±1 frame AND clearly above the shifted control |
| 11 | Ghost copies / comb at transitions (S4) | Motion blur = sub-frame averaging (≥ 16 samples), never stacked offset copies | 12 fps seam strips: no doubles |
| 12 | The crowd reacts only when scripted (S4) | Every event has cause → reaction 1 → reaction 2: crowd, props, camera | For each beat, name who reacts |
| 13 | Banned clichés in explainers: probability bars (S4) | Show the mechanism with characters or objects, not charts | grep the plan for «график/столбик/bar chart» |
| 14 | Factual slips in explainers (S4) | Every claim in on-screen text checked against a source | A fact list with sources in `plan/` |
| 15 | Text below 54 px, labels at the frame edge, a line crossing a number (S1, S2, S4) | Text ≥ 54 px (UI ≥ 30), margins ≥ 72 px, labels never cross figures, canvas text checked by eye | `layout_check` + a 1-per-second sheet |
| 16 | The animatic was skipped (S1 B1, B2) | The animatic is mandatory even when the brief fixes the plot: pitches vary staging and camera, not the plot | `plan/pitch-*.html` exist |

**What moved scores most** (score deltas in the loops):
- S1 6→8 hook and 5→8 camera came from rules 1–3.
- S1 7.75→8.17 came from rule 7, the «Луч» carrier.
- Creativity stays at 8–8.5 without rules 6 and 7. That is the gap to 10.

## Blind-panel lessons (20 Oct 2026)
- A loop critic overrates the work it helped fix: about 0.8 points against a fresh blind judge. Always check the final with a fresh judge who never saw a round.
- Two judges can differ by up to 1.3 points on the same clip. Treat a gap under 0.5 as noise.
- The rules can make a clip tidy but timid. A bare prompt with one bold idea beat the rules-only runs in 3 of 6 tests. Pick the bold idea first, then apply the craft rules to serve it.
