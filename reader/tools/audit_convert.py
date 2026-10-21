"""Verify the HTML reader captured the whole document, and list every fraction.

Compares the source .docx text (paragraph by paragraph, tables included) against the
text of the generated HTML, reporting any source line missing from the output. Also
prints every line containing '/', and any footnote/endnote text.
"""
import html as html_mod
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
docx = sys.argv[1] if len(sys.argv) > 1 else r"D:\Projects\X9Project\reader\sample\doc.docx"
htmlf = sys.argv[2] if len(sys.argv) > 2 else r"D:\Projects\X9Project\reader\sample\doc.html"


def para_text(p):
    """Text of a <w:p>, skipping field instructions (TOC)."""
    out = []
    for r in p.findall(f"{W}r"):
        if r.find(f"{W}instrText") is not None:
            continue
        for t in r.iter(f"{W}t"):
            out.append(t.text or "")
    return "".join(out).strip()


def source_lines(docx):
    z = zipfile.ZipFile(docx)
    root = ET.fromstring(z.read("word/document.xml"))
    body = root.find(f"{W}body")
    lines = []
    for el in body:
        tag = el.tag.replace(W, "")
        if tag == "p":
            t = para_text(el)
            if t:
                lines.append(t)
        elif tag == "tbl":
            for tc in el.iter(f"{W}tc"):
                cell = " ".join(para_text(p) for p in tc.findall(f"{W}p")).strip()
                if cell:
                    lines.append(cell)
    return lines


def html_text(htmlf):
    with open(htmlf, encoding="utf-8") as f:
        doc = f.read()
    doc = doc.split("<main>", 1)[1].split("</main>", 1)[0]
    doc = re.sub(r"(?s)<details.*?</summary>", "", doc)   # drop the TOC block
    doc = re.sub(r"(?s)<[^>]+>", "\n", doc)
    return html_mod.unescape(doc)


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


src = source_lines(docx)
htxt = norm(html_text(htmlf))

print(f"source paragraphs/cells: {len(src)}")
missing = [ln for ln in src if norm(ln) and norm(ln) not in htxt]
print(f"source lines NOT found in HTML: {len(missing)}")
for ln in missing:
    print("   MISSING:", repr(ln[:160]))

print("\n=== every source line with '/' (fraction candidates) ===")
for ln in src:
    if "/" in ln:
        print("  ", ln)

print("\n=== footnotes / endnotes ===")
z = zipfile.ZipFile(docx)
for name in ("word/footnotes.xml", "word/endnotes.xml"):
    if name in z.namelist():
        root = ET.fromstring(z.read(name))
        for note in root:
            txt = "".join(t.text or "" for t in note.iter(f"{W}t")).strip()
            if txt:
                print(f"  {name}: {txt[:200]!r}")
