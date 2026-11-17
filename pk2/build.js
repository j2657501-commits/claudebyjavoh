// Builds the PK-2 paper (.docx) from the text/*.txt sources.
// Usage: node build.js out.docx [pages.json]
const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, FootnoteReferenceRun, AlignmentType,
  HeadingLevel, Footer, PageNumber, TabStopType, LeaderType, PageBreak,
} = require('docx');

const out = process.argv[2] || 'out.docx';
const pages = process.argv[3] && fs.existsSync(process.argv[3]) ? JSON.parse(fs.readFileSync(process.argv[3], 'utf8')) : {};

const FONT = 'Times New Roman';
const SZ = 28;          // 14 pt
const FN_SZ = 24;       // 12 pt in footnotes
const LINE = 360;       // 1.5 spacing
const INDENT = 709;     // 1.25 cm
const CM = 567;

const dir = path.join(__dirname, 'text');
const files = fs.readdirSync(dir).filter(f => f.endsWith('.txt')).sort();

const footnotes = {};
let fnId = 0;
const toc = [];
const body = [];
let bibNo = 0;
let inBib = false;

function runs(text) {
  const parts = text.split(/(\[\[[\s\S]*?\]\])/);
  const res = [];
  for (const p of parts) {
    if (!p) continue;
    if (p.startsWith('[[')) {
      fnId += 1;
      const t = p.slice(2, -2).trim();
      footnotes[fnId] = {
        children: [new Paragraph({
          alignment: AlignmentType.JUSTIFIED,
          spacing: { line: 240, before: 0, after: 0 },
          children: [new TextRun({ text: ' ' + t, font: FONT, size: FN_SZ })],
        })],
      };
      res.push(new FootnoteReferenceRun(fnId));
    } else {
      res.push(new TextRun({ text: p, font: FONT, size: SZ }));
    }
  }
  return res;
}

for (const f of files) {
  const lines = fs.readFileSync(path.join(dir, f), 'utf8').split('\n');
  for (const raw of lines) {
    const line = raw.trimEnd();
    if (!line.trim()) continue;
    if (line.startsWith('# ')) {
      const t = line.slice(2);
      inBib = t.startsWith('СПИСОК');
      toc.push({ level: 1, text: t });
      body.push(new Paragraph({
        heading: HeadingLevel.HEADING_1,
        alignment: AlignmentType.CENTER,
        spacing: { line: LINE, before: 0, after: 240 },
        children: [new PageBreak(), new TextRun({ text: t, font: FONT, size: SZ, bold: true })],
      }));
    } else if (line.startsWith('## ')) {
      const t = line.slice(3);
      if (!inBib) toc.push({ level: 2, text: t });
      body.push(new Paragraph({
        heading: HeadingLevel.HEADING_2,
        alignment: AlignmentType.JUSTIFIED, keepNext: true,
        indent: { firstLine: INDENT },
        spacing: { line: LINE, before: 240, after: 120 },
        children: [new TextRun({ text: t, font: FONT, size: SZ, bold: true })],
      }));
    } else if (line.startsWith('~ ')) {
      bibNo += 1;
      body.push(new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        indent: { firstLine: INDENT },
        spacing: { line: LINE, before: 0, after: 0 },
        children: [new TextRun({ text: `${bibNo}. ` + line.slice(2), font: FONT, size: SZ })],
      }));
    } else if (line.startsWith('- ')) {
      body.push(new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        indent: { firstLine: INDENT },
        spacing: { line: LINE, before: 0, after: 0 },
        children: runs('– ' + line.slice(2)),
      }));
    } else {
      body.push(new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        indent: { firstLine: INDENT },
        spacing: { line: LINE, before: 0, after: 0 },
        children: runs(line),
      }));
    }
  }
}

// Title page
const c = (text, opts = {}) => new Paragraph({
  alignment: opts.align || AlignmentType.CENTER,
  spacing: { line: LINE, before: opts.before || 0, after: opts.after || 0 },
  children: [new TextRun({ text, font: FONT, size: opts.size || SZ, bold: !!opts.bold })],
});
const title = [
  c('ТАШКЕНТСКИЙ ГОСУДАРСТВЕННЫЙ ЮРИДИЧЕСКИЙ УНИВЕРСИТЕТ', { bold: true }),
  c('ВТОРАЯ ПРОМЕЖУТОЧНАЯ КОНТРОЛЬНАЯ РАБОТА ПК-2', { bold: true, before: 2400 }),
  c('по модулю «Право международных договоров»', { after: 360 }),
  c('на тему:'),
  c('КРИЗИС МЕЖДУНАРОДНОГО ПРАВОПОРЯДКА, ОСНОВАННОГО НА ПРАВИЛАХ: УТРАЧИВАЕТ ЛИ МЕЖДУНАРОДНОЕ ПРАВО СВОЮ ЮРИДИЧЕСКУЮ СИЛУ И АВТОРИТЕТ В УСЛОВИЯХ ГЕОПОЛИТИЧЕСКОГО СОПЕРНИЧЕСТВА ВЕЛИКИХ ДЕРЖАВ?', { bold: true, after: 1400 }),
  c('Выполнил: студент 3 курса Б потока', { align: AlignmentType.RIGHT }),
  c('Абдурахмонов Темур Фахриддин угли', { align: AlignmentType.RIGHT }),
  c('Проверил: учитель по модулю', { align: AlignmentType.RIGHT, before: 240 }),
  c('«Право международных договоров»', { align: AlignmentType.RIGHT }),
  c('Толибов Азизбек Толибович', { align: AlignmentType.RIGHT }),
  c('Ташкент – 2026', { before: 1800 }),
];

// Table of contents (page numbers filled in on the second pass)
const tocParas = [new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { line: LINE, after: 240 },
  children: [new PageBreak(), new TextRun({ text: 'ОГЛАВЛЕНИЕ', font: FONT, size: SZ, bold: true })],
})];
const tabPos = 11906 - 3 * CM - 1.5 * CM - 10; // text width in twips (A4 width minus margins)
for (const e of toc) {
  const p = pages[e.text] || '00';
  tocParas.push(new Paragraph({
    alignment: AlignmentType.LEFT,
    indent: e.level === 2 ? { left: INDENT, right: 500 } : { right: 500 },
    spacing: { line: 300, before: 0, after: 60 },
    tabStops: [{ type: TabStopType.RIGHT, position: tabPos - (e.level === 2 ? 0 : 0), leader: LeaderType.DOT }],
    children: [
      new TextRun({ text: e.text, font: FONT, size: SZ, bold: e.level === 1 }),
      new TextRun({ text: '\t' + p, font: FONT, size: SZ }),
    ],
  }));
}

const doc = new Document({
  creator: 'Абдурахмонов Т.Ф.',
  title: 'ПК-2. Кризис международного правопорядка, основанного на правилах',
  styles: {
    default: { document: { run: { font: FONT, size: SZ } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: FONT, size: SZ, bold: true, color: '000000' },
        paragraph: { spacing: { before: 0, after: 240, line: LINE }, keepNext: true, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: FONT, size: SZ, bold: true, color: '000000' },
        paragraph: { spacing: { before: 240, after: 120, line: LINE }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  footnotes,
  sections: [{
    properties: {
      titlePage: true,
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 2 * CM, bottom: 2 * CM, left: 3 * CM, right: Math.round(1.5 * CM) },
        pageNumbers: { start: 1 },
      },
    },
    footers: {
      default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
        children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 24 })] })] }),
      first: new Footer({ children: [new Paragraph({ children: [] })] }),
    },
    children: [...title, ...tocParas, ...body],
  }],
});

Packer.toBuffer(doc).then(b => {
  fs.writeFileSync(out, b);
  fs.writeFileSync(out + '.toc.json', JSON.stringify(toc.map(t => t.text)));
  console.log('written', out, 'footnotes:', fnId, 'bib:', bibNo);
});
