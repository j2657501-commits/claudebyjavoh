# -*- coding: utf-8 -*-
"""Сборка учебного макета гражданского дела (DOCX -> PDF).

Запуск:  python3 build.py
Результат: delo.docx и delo.pdf в этой папке.
Номера листов в описи считаются автоматически (два прохода).
"""
import json
import os
import re
import subprocess
import sys

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from content import DOCS, TITLE_PAGE

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "Times New Roman"
SIZE = 14


# ---------------------------------------------------------------- helpers
def set_cell_bg(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def set_table_borders(table, on=True, color="808080"):
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single" if on else "nil")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        borders.append(el)
    tblPr.append(borders)


def add_runs(par, text, size=None, bold_all=False, italic=False):
    """Текст с разметкой **жирный** и ^верхний индекс^."""
    text = re.sub(r"(?<=\d) (?=\d{3}\b)", "\u00a0", text)  # 16 800 000 не рвётся
    text = text.replace("№ ", "№\u00a0")
    parts = re.split(r"(\*\*.+?\*\*|\^.+?\^)", text)
    for part in parts:
        if not part:
            continue
        bold = bold_all
        sup = False
        if part.startswith("**") and part.endswith("**"):
            part = part[2:-2]
            bold = True
        elif part.startswith("^") and part.endswith("^") and len(part) > 2:
            part = part[1:-1]
            sup = True
        r = par.add_run(part)
        r.bold = bold
        r.italic = italic
        r.font.name = FONT
        r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        r.font.size = Pt(size or SIZE)
        if sup:
            r.font.superscript = True
    return par


def fmt(par, align=WD_ALIGN_PARAGRAPH.JUSTIFY, indent=True, before=0, after=0,
        left=None, keep=False):
    pf = par.paragraph_format
    pf.alignment = align
    pf.first_line_indent = Cm(1.25) if indent else Cm(0)
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = 1.0
    if left is not None:
        pf.left_indent = Cm(left)
    if keep:
        pf.keep_with_next = True
    return par


def para(doc_or_cell, text, **kw):
    size = kw.pop("size", None)
    bold = kw.pop("bold", False)
    italic = kw.pop("italic", False)
    p = doc_or_cell.add_paragraph()
    add_runs(p, text, size=size, bold_all=bold, italic=italic)
    fmt(p, **kw)
    return p


def court_header(doc, court_uz, court_ru):
    t = doc.add_table(rows=1, cols=3)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t, on=False)
    widths = [Cm(7.2), Cm(2.2), Cm(7.2)]
    for i, w in enumerate(widths):
        t.columns[i].width = w
        t.rows[0].cells[i].width = w
    left, mid, right = t.rows[0].cells
    for cell, lines in ((left, court_uz), (right, court_ru)):
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        cell.paragraphs[0].text = ""
        for j, line in enumerate(lines):
            p = cell.paragraphs[0] if j == 0 else cell.add_paragraph()
            add_runs(p, line, size=8.5, bold_all=True)
            fmt(p, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False)
    mid.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    p = mid.paragraphs[0]
    fmt(p, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False)
    p.add_run().add_picture(os.path.join(HERE, "uz_emblem.png"), width=Cm(1.35))
    # тонкая линия под шапкой
    p = doc.add_paragraph()
    fmt(p, indent=False, after=6)
    pPr = p._p.get_or_add_pPr()
    bdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "000000")
    bdr.append(bottom)
    pPr.append(bdr)
    r = p.add_run()
    r.font.size = Pt(2)


def two_sided(doc, left, right, before=0, after=0, size=None):
    """Строка: текст слева, текст справа (через табуляцию к правому полю)."""
    p = doc.add_paragraph()
    fmt(p, align=WD_ALIGN_PARAGRAPH.LEFT, indent=False, before=before, after=after)
    p.paragraph_format.tab_stops.add_tab_stop(Cm(16.5), WD_TAB_ALIGNMENT.RIGHT)
    add_runs(p, left, size=size)
    add_runs(p, "\t" + right, size=size)
    return p


def table(doc, rows, widths, header=True, size=11, section_rows=(), bold_cols=(),
          align_right_cols=(), center_cols=()):
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t, on=True)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = t.rows[i].cells[j]
            cell.width = Cm(widths[j])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p = cell.paragraphs[0]
            is_head = header and i == 0
            is_sec = i in section_rows
            if is_sec and j > 0:
                continue
            align = WD_ALIGN_PARAGRAPH.LEFT
            if is_head or is_sec or j in center_cols:
                align = WD_ALIGN_PARAGRAPH.CENTER
            if j in align_right_cols and not is_head:
                align = WD_ALIGN_PARAGRAPH.RIGHT
            add_runs(p, val, size=size, bold_all=is_head or is_sec or (j in bold_cols))
            fmt(p, align=align, indent=False, before=1.5, after=1.5)
            if is_head or is_sec:
                set_cell_bg(cell, "E6E6E6")
        if i in section_rows:
            merged = t.rows[i].cells[0].merge(t.rows[i].cells[len(row) - 1])
            # убрать пустые абзацы, оставшиеся после merge
            for extra in merged.paragraphs[1:]:
                extra._element.getparent().remove(extra._element)
    for j, w in enumerate(widths):
        t.columns[j].width = Cm(w)
    return t


def page_break(doc):
    """Крошечный абзац с «разрывом страницы перед» — не создаёт пустых страниц."""
    p = doc.add_paragraph()
    fmt(p, indent=False)
    p.paragraph_format.page_break_before = True
    p.paragraph_format.line_spacing = Pt(1)
    r = p.add_run()
    r.font.size = Pt(1)


# ---------------------------------------------------------------- renderer
def render_block(doc, b):
    kind = b[0]
    if kind == "court":
        court_header(doc, b[1], b[2])
    elif kind == "addr":  # блок адресата справа
        for line in b[1]:
            para(doc, line, align=WD_ALIGN_PARAGRAPH.LEFT, indent=False, left=8.6,
                 after=b[2] if len(b) > 2 else 0)
    elif kind == "addrgap":
        p = para(doc, "", indent=False, after=4)
    elif kind == "title":
        para(doc, b[1], bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False,
             before=b[2] if len(b) > 2 else 6, keep=True)
    elif kind == "subtitle":
        para(doc, b[1], bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False,
             after=b[2] if len(b) > 2 else 6, keep=True)
    elif kind == "center":
        para(doc, b[1], align=WD_ALIGN_PARAGRAPH.CENTER, indent=False,
             after=b[2] if len(b) > 2 else 0)
    elif kind == "dateplace":
        two_sided(doc, b[1], b[2], before=4, after=6)
    elif kind == "p":
        para(doc, b[1], after=b[2] if len(b) > 2 else 0)
    elif kind == "pl":  # без красной строки
        para(doc, b[1], indent=False, after=b[2] if len(b) > 2 else 0)
    elif kind == "plleft":
        para(doc, b[1], indent=False, align=WD_ALIGN_PARAGRAPH.LEFT,
             after=b[2] if len(b) > 2 else 0)
    elif kind == "h":  # жирный заголовок по центру (УСТАНОВИЛ и т.п.)
        para(doc, b[1], bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False,
             before=3, after=3, keep=True)
    elif kind == "hl":  # жирный подзаголовок слева
        para(doc, b[1], bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, indent=False,
             before=4, after=2, keep=True)
    elif kind == "sig":
        two_sided(doc, b[1], b[2], before=b[3] if len(b) > 3 else 14)
    elif kind == "space":
        p = para(doc, "", indent=False)
        p.paragraph_format.space_after = Pt(b[1])
    elif kind == "table":
        opts = b[3] if len(b) > 3 else {}
        table(doc, b[1], b[2], **opts)
    elif kind == "small":
        para(doc, b[1], size=11, italic=True, indent=False,
             align=WD_ALIGN_PARAGRAPH.LEFT, before=b[2] if len(b) > 2 else 6)
    elif kind == "rule":
        p = doc.add_paragraph()
        fmt(p, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, before=10, after=10)
        add_runs(p, "*  *  *", size=12)
    else:
        raise ValueError(kind)


def build(pages=None):
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = FONT
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    st.font.size = Pt(SIZE)
    sec = doc.sections[0]
    sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
    sec.left_margin, sec.right_margin = Cm(2.5), Cm(1.5)
    sec.top_margin, sec.bottom_margin = Cm(2.0), Cm(2.0)

    # --- титульный лист
    p = para(doc, "", align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, before=20)
    p.add_run().add_picture(os.path.join(HERE, "tsul_logo.jpg"), width=Cm(6.0))
    para(doc, "", indent=False, after=40)
    for i, (txt, bold) in enumerate(TITLE_PAGE["lines"]):
        para(doc, txt, bold=bold, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False,
             after=8 if i in TITLE_PAGE["gap_after"] else 4)
    para(doc, "", indent=False, after=250)
    para(doc, TITLE_PAGE["city"], bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False)
    page_break(doc)

    # --- опись
    para(doc, "ОПИСЬ ДОКУМЕНТОВ ДЕЛА", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER,
         indent=False, after=8)
    rows = [["№\nп/п", "Наименование документа", "Листы\nдела"]]
    for i, d in enumerate(DOCS, 1):
        rng = "…"
        if pages:
            a, z = pages[d["id"]]
            rng = str(a) if a == z else f"{a}–{z}"
        rows.append([str(i), d["toc"], rng])
    table(doc, rows, [1.4, 13.0, 2.4], size=12, center_cols=(0, 2))
    page_break(doc)

    for k, d in enumerate(DOCS):
        for b in d["blocks"]:
            if b[0] == "pagebreak":
                page_break(doc)
            else:
                render_block(doc, b)
        if k < len(DOCS) - 1:
            page_break(doc)

    # нумерация страниц внизу по центру (кроме титула)
    sec.different_first_page_header_footer = True
    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = fp.add_run()
    for tag, txt in (("begin", None), (None, "PAGE"), ("end", None)):
        if tag:
            fc = OxmlElement("w:fldChar")
            fc.set(qn("w:fldCharType"), tag)
            run._r.append(fc)
        else:
            it = OxmlElement("w:instrText")
            it.set(qn("xml:space"), "preserve")
            it.text = txt
            run._r.append(it)
    run.font.size = Pt(11)
    run.font.name = FONT

    out = os.path.join(HERE, "delo.docx")
    doc.save(out)
    return out


def to_pdf(docx_path):
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", HERE,
                    docx_path], check=True, capture_output=True)
    return os.path.join(HERE, "delo.pdf")


def find_pages(pdf_path):
    import pdfplumber
    texts = []
    with pdfplumber.open(pdf_path) as pdf:
        for pg in pdf.pages:
            texts.append(re.sub(r"\s+", " ", pg.extract_text() or ""))
    starts = []
    cursor = 2  # 0 — титул, 1 — опись
    for d in DOCS:
        key = re.sub(r"\s+", " ", d["find"])
        for i in range(cursor, len(texts)):
            if key in texts[i]:
                starts.append(i)
                cursor = i + 1
                break
        else:
            sys.exit(f"не найдено начало документа: {d['id']} ({key})")
    pages = {}
    for n, d in enumerate(DOCS):
        a = starts[n]
        z = (starts[n + 1] - 1) if n + 1 < len(DOCS) else len(texts) - 1
        pages[d["id"]] = (a + 1, z + 1)  # номера листов = номера страниц PDF
    return pages, len(texts)


if __name__ == "__main__":
    p1 = to_pdf(build())
    pages, total = find_pages(p1)
    p2 = to_pdf(build(pages))
    pages2, total2 = find_pages(p2)
    if pages2 != pages:
        p3 = to_pdf(build(pages2))
        pages2, total2 = find_pages(p3)
    print(json.dumps(pages2, ensure_ascii=False), "страниц:", total2)
