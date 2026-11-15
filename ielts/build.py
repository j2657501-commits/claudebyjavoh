#!/usr/bin/env python3
"""Builds ielts/IELTS_4_Skills.html from the source files in ielts/src."""
import glob, html, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
OUT = os.path.join(ROOT, "IELTS_4_Skills.html")
E = html.escape

INSTR = {
    "TFNG": "Do the following statements agree with the information in the passage? Choose <b>TRUE</b>, <b>FALSE</b> or <b>NOT GIVEN</b>.",
    "YNNG": "Do the following statements agree with the views of the writer? Choose <b>YES</b>, <b>NO</b> or <b>NOT GIVEN</b>.",
    "MCQ": "Choose the correct letter, <b>A</b>, <b>B</b>, <b>C</b> or <b>D</b>.",
    "GAP": "Complete the sentences. Write <b>NO MORE THAN TWO WORDS AND/OR A NUMBER</b> from the passage for each answer.",
    "SUM": "Complete the summary. Write <b>NO MORE THAN TWO WORDS AND/OR A NUMBER</b> from the passage for each answer.",
    "SHORT": "Answer the questions. Write <b>NO MORE THAN THREE WORDS AND/OR A NUMBER</b> from the passage for each answer.",
    "MATCH": "Which paragraph contains the following information? Choose the correct letter.",
    "HEAD": "Choose the correct heading for each paragraph from the list of headings below.",
    "LGAP": "Complete the notes. Write <b>NO MORE THAN TWO WORDS AND/OR A NUMBER</b> for each answer.",
    "LMCQ": "Choose the correct letter, <b>A</b>, <b>B</b> or <b>C</b>.",
    "LSHORT": "Answer the questions. Write <b>NO MORE THAN THREE WORDS AND/OR A NUMBER</b>.",
}
FULL = {"T": "TRUE", "F": "FALSE", "NG": "NOT GIVEN", "Y": "YES", "N": "NO"}


def select(opts):
    return "<select><option value=''>—</option>" + "".join(
        f"<option>{E(o)}</option>" for o in opts) + "</select>"


def render_questions(groups, nparas, errors, where):
    out, n = [], 0
    for kind, head, items in groups:
        if kind not in INSTR:
            errors.append(f"{where}: unknown question type {kind}")
            continue
        out.append(f"<div class='qgroup'><p class='instr'>{INSTR[kind]}</p>")
        heads = []
        if kind == "HEAD":
            heads = [h.strip() for h in head.split(";") if h.strip()]
            out.append("<ul class='heads'>" + "".join(f"<li>{E(h)}</li>" for h in heads) + "</ul>")
        for it in items:
            n += 1
            parts = [p.strip() for p in it.split("|")]
            ans = parts[-1]
            body = parts[0]
            if len(parts) < 2 or not ans:
                errors.append(f"{where}: question {n} has no answer: {it}")
                continue
            ctrl, shown = "", ans
            if kind in ("TFNG", "YNNG"):
                opts = ["TRUE", "FALSE", "NOT GIVEN"] if kind == "TFNG" else ["YES", "NO", "NOT GIVEN"]
                if FULL.get(ans) not in opts:
                    errors.append(f"{where}: q{n} bad answer {ans}")
                shown = FULL.get(ans, ans)
                ctrl = select(opts)
                q = f"{E(body)} {ctrl}"
            elif kind in ("MCQ", "LMCQ"):
                opts = parts[1:-1]
                letters = [o[0] for o in opts]
                if ans not in letters:
                    errors.append(f"{where}: q{n} MCQ answer {ans} not in options")
                q = (f"{E(body)} {select(letters)}<ul class='opts'>" +
                     "".join(f"<li>{E(o)}</li>" for o in opts) + "</ul>")
            elif kind == "MATCH":
                letters = [chr(65 + i) for i in range(nparas)]
                if ans not in letters:
                    errors.append(f"{where}: q{n} MATCH answer {ans} out of range")
                q = f"{E(body)} {select(letters)}"
            elif kind == "HEAD":
                nums = [h.split(".")[0].strip() for h in heads]
                if ans not in nums:
                    errors.append(f"{where}: q{n} HEAD answer {ans} not in list")
                q = f"{E(body)} {select(nums)}"
            else:  # gap / short
                inp = "<input type='text' autocomplete='off'>"
                if "____" in body:
                    q = E(body).replace("____", inp, 1)
                else:
                    q = f"{E(body)} {inp}"
            out.append(f"<div class='q' data-a=\"{E(shown)}\"><span class='n'>{n}</span> "
                       f"<span class='qt'>{q}</span> <span class='ans'>✔ {E(shown)}</span></div>")
        out.append("</div>")
    out.append("<div class='btns'><button class='chk'>Проверить</button>"
               "<button class='shw'>Показать ответы</button>"
               "<button class='rst'>Сбросить</button><span class='score'></span></div>")
    return "\n".join(out), n


def parse_blocks(text):
    blocks = re.split(r"(?m)^## ", text)
    return [b for b in blocks[1:] if b.strip()]


def parse_block(block):
    lines = block.split("\n")
    title = lines[0].strip()
    sec = {"body": []}
    groups, cur = [], "body"
    for ln in lines[1:]:
        if ln.startswith("@"):
            tag = ln[1:].strip()
            if tag.startswith("Q "):
                rest = tag[2:].strip().split(" ", 1)
                groups.append((rest[0], rest[1] if len(rest) > 1 else "", []))
                cur = "Q"
            else:
                key = tag.split(" ", 1)
                cur = key[0]
                sec.setdefault(cur, [])
                if len(key) > 1:
                    sec[cur].append(key[1])
        elif ln.strip():
            if cur == "Q":
                groups[-1][2].append(ln.strip())
            else:
                sec[cur].append(ln.strip())
    return title, sec, groups


def bold_vocab(par, words):
    for w in words:
        base = re.escape(w)
        par, k = re.subn(rf"(?<![\w>])({base}\w*)", r"<b class='vw'>\1</b>", par, count=1, flags=re.I)
        if k:
            words.remove(w)
            return bold_vocab(par, words)
    return par


def build_reading(errors):
    secs, toc, cats, total_q = [], [], {}, 0
    num = 0
    for f in sorted(glob.glob(os.path.join(SRC, "r*.txt"))):
        for block in parse_blocks(open(f, encoding="utf-8").read()):
            num += 1
            title, sec, groups = parse_block(block)
            name, _, cat = [x.strip() for x in title.partition("|")]
            where = f"Reading {num} ({name})"
            paras = sec["body"]
            vocab = [v.split("=", 1) for v in sec.get("V", [])]
            if len(vocab) < 6:
                errors.append(f"{where}: only {len(vocab)} vocab items")
            pending = [v[0].strip().split(" (")[0] for v in vocab]
            full = " ".join(paras).lower()
            for w in pending:
                if w.lower()[: max(3, len(w) - 2)] not in full:
                    errors.append(f"{where}: vocab '{w}' not found in text")
            ptxt = []
            for i, p in enumerate(paras):
                ptxt.append(f"<p><span class='pl'>{chr(65+i)}</span> {bold_vocab(E(p), pending)}</p>")
            qhtml, nq = render_questions(groups, len(paras), errors, where)
            total_q += nq
            for kind, _, items in groups:
                if kind in ("GAP", "SUM", "SHORT"):
                    for it in items:
                        a = it.split("|")[-1].strip()
                        if not any(x.strip().lower() in full for x in a.split("/")):
                            errors.append(f"{where}: answer '{a}' not in text")
            if nq < 8:
                errors.append(f"{where}: only {nq} questions")
            words = sum(len(p.split()) for p in paras)
            vhtml = "".join(f"<li><b>{E(a.strip())}</b> — {E(b.strip())}</li>" for a, b in vocab)
            cats.setdefault(cat, []).append(num)
            toc.append(f"<a href='#r{num}' title='{E(name)}'>{num}</a>")
            secs.append(
                f"<section class='unit' id='r{num}'><h3>Passage {num}. {E(name)} "
                f"<span class='tag'>{E(cat)}</span> <span class='wc'>{words} words</span></h3>"
                f"<details class='vocab' open><summary>Новые слова</summary><ul>{vhtml}</ul></details>"
                f"<div class='text'>{''.join(ptxt)}</div><div class='qs'>{qhtml}</div></section>")
    return num, total_q, "".join(toc), "\n".join(secs)


def build_listening(errors):
    secs, toc, num = [], [], 0
    for f in sorted(glob.glob(os.path.join(SRC, "l*.txt"))):
        for block in parse_blocks(open(f, encoding="utf-8").read()):
            num += 1
            title, sec, groups = parse_block(block)
            name, _, cat = [x.strip() for x in title.partition("|")]
            where = f"Listening {num} ({name})"
            lines = sec.get("S", [])
            script = []
            for ln in lines:
                m = re.match(r"^([A-Z][A-Za-z .]{0,18}):\s*(.*)$", ln)
                sp, tx = (m.group(1), m.group(2)) if m else ("", ln)
                script.append(f"<p data-sp=\"{E(sp)}\"><b>{E(sp)}{':' if sp else ''}</b> <span>{E(tx)}</span></p>")
            qhtml, nq = render_questions(groups, 0, errors, where)
            if nq != 10:
                errors.append(f"{where}: {nq} questions (expected 10)")
            ctx = " ".join(sec.get("CTX", []))
            toc.append(f"<a href='#l{num}' title='{E(name)}'>{num}</a>")
            secs.append(
                f"<section class='unit listen' id='l{num}'><h3>Listening {num}. {E(name)} "
                f"<span class='tag'>{E(cat)}</span></h3><p class='ctx'>{E(ctx)}</p>"
                f"<div class='player'><button class='play'>▶ Слушать</button>"
                f"<button class='stop'>■ Стоп</button>"
                f"<label>Скорость <select class='rate'><option value='0.8'>0.8×</option>"
                f"<option value='0.95' selected>1×</option><option value='1.1'>1.15×</option></select></label>"
                f"<span class='pstat'></span></div>"
                f"<div class='qs'>{qhtml}</div>"
                f"<details class='script'><summary>Транскрипт (открывай только после проверки)</summary>"
                f"{''.join(script)}</details></section>")
    return num, "".join(toc), "\n".join(secs)


def build_cards():
    out, n = [], 0
    for ln in open(os.path.join(SRC, "cards.txt"), encoding="utf-8"):
        ln = ln.strip()
        if not ln:
            continue
        if "|" not in ln:
            out.append(f"<h4>{E(ln)}</h4>")
            continue
        n += 1
        topic, new, bullets, qs = [x.strip() for x in ln.split("|")]
        out.append(
            f"<div class='cue'><b>{n}. {E(topic)}</b>{'<b class=new>NEW</b>' if new else ''}"
            "<div>You should say:</div><ul>" + "".join(f"<li>{E(b.strip())}</li>" for b in bullets.split(";")) +
            "</ul><div><i>Part 3:</i></div><ul>" + "".join(f"<li>{E(q.strip())}</li>" for q in qs.split(";")) + "</ul></div>")
    return "\n".join(out), n


def main():
    errors = []
    nr, nq, rtoc, reading = build_reading(errors)
    nl, ltoc, listening = build_listening(errors)
    rd = lambda n: open(os.path.join(SRC, n), encoding="utf-8").read()
    page = rd("template.html")
    for k, v in {
        "{{READING}}": reading, "{{RTOC}}": rtoc, "{{NR}}": str(nr), "{{NQ}}": str(nq),
        "{{LISTENING}}": listening, "{{LTOC}}": ltoc, "{{NL}}": str(nl),
        "{{WRITING}}": rd("writing.html"), "{{SPEAKING}}": rd("speaking.html").replace("{{CARDS}}", build_cards()[0]),
    }.items():
        page = page.replace(k, v)
    open(OUT, "w", encoding="utf-8").write(page)
    print(f"reading passages: {nr}, reading questions: {nq}, listening: {nl}")
    print(f"output: {OUT} ({os.path.getsize(OUT)//1024} KB)")
    for e in errors:
        print("ERROR:", e)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
