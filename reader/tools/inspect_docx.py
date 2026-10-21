"""Inspect a docx: paragraph styles, run formatting samples, numbering, tables."""
import collections
import sys
import xml.etree.ElementTree as ET
import zipfile

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
path = sys.argv[1] if len(sys.argv) > 1 else r"D:\Projects\X9Project\reader\sample\doc.docx"

z = zipfile.ZipFile(path)
root = ET.fromstring(z.read("word/document.xml"))
body = root.find(f"{W}body")

styles = collections.Counter()
vert = collections.Counter()
have_num = 0
tables = 0
for el in body:
    tag = el.tag.replace(W, "")
    if tag == "tbl":
        tables += 1
        continue
    if tag != "p":
        continue
    ppr = el.find(f"{W}pPr")
    style = "Normal"
    if ppr is not None:
        ps = ppr.find(f"{W}pStyle")
        if ps is not None:
            style = ps.get(f"{W}val")
        if ppr.find(f"{W}numPr") is not None:
            have_num += 1
    styles[style] += 1
    for r in el.iter(f"{W}r"):
        rpr = r.find(f"{W}rPr")
        if rpr is not None:
            va = rpr.find(f"{W}vertAlign")
            if va is not None:
                vert[va.get(f"{W}val")] += 1

print("paragraph styles:", dict(styles))
print("vertAlign runs:", dict(vert))
print("numbered paragraphs:", have_num)
print("tables:", tables)
