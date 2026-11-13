"""Apply journal formatting to a pandoc docx. Usage: python3 format_docx.py file.docx [--landscape] [--spacing 2.0] [--table-pt 8]"""
import sys, argparse
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ap = argparse.ArgumentParser(); ap.add_argument("file"); ap.add_argument("--landscape", action="store_true")
ap.add_argument("--spacing", type=float, default=2.0); ap.add_argument("--table-pt", type=float, default=8.5)
ap.add_argument("--no-page-numbers", action="store_true")
a = ap.parse_args()
d = Document(a.file)
for s in d.sections:
    s.page_width, s.page_height = Inches(8.5), Inches(11)
    if a.landscape:
        s.orientation = WD_ORIENT.LANDSCAPE; s.page_width, s.page_height = Inches(11), Inches(8.5)
    s.left_margin = s.right_margin = s.top_margin = s.bottom_margin = Inches(1)
    s.header_distance = Inches(0.5)
    if not a.no_page_numbers:
        p = s.header.paragraphs[0] if s.header.paragraphs else s.header.add_paragraph()
        for r in list(p.runs): r._r.getparent().remove(r._r)
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r = p.add_run()
        for tag, text in (("begin", None), (None, "PAGE"), ("end", None)):
            if tag:
                e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), tag)
            else:
                e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = text
            r._r.append(e)
for p in d.paragraphs:
    if p.style.name.lower().startswith("source code") or "Code" in p.style.name:
        p.paragraph_format.line_spacing = 1.0; continue
    p.paragraph_format.line_spacing = a.spacing
for t in d.tables:
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    tblPr = t._tbl.tblPr
    for el in tblPr.findall(qn("w:tblW")): tblPr.remove(el)
    w = OxmlElement("w:tblW"); w.set(qn("w:w"), "5000"); w.set(qn("w:type"), "pct"); tblPr.append(w)
    for el in tblPr.findall(qn("w:tblLayout")): tblPr.remove(el)
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "autofit"); tblPr.append(lay)
    prev = t._tbl.getprevious()
    if prev is not None and prev.tag == qn("w:p"):
        pPr = prev.get_or_add_pPr(); pPr.append(OxmlElement("w:keepNext"))
    nrows = len(t.rows)
    for ri, row in enumerate(t.rows):
        trPr = row._tr.get_or_add_trPr(); trPr.append(OxmlElement("w:cantSplit"))
        for c in row.cells:
            tcPr = c._tc.get_or_add_tcPr()
            for el in tcPr.findall(qn("w:tcW")): tcPr.remove(el)
            if nrows <= 22 and ri < nrows - 1:
                for p in c.paragraphs: p.paragraph_format.keep_with_next = True
            for p in c.paragraphs:
                p.paragraph_format.line_spacing = 1.0
                p.paragraph_format.space_before = Pt(1); p.paragraph_format.space_after = Pt(1)
                for r in p.runs: r.font.size = Pt(a.table_pt - (1 if len(t.columns) >= 8 else 0))
d.save(a.file)
