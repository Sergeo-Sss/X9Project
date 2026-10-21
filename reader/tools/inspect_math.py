"""Audit how maths is stored in a docx: OMML equations vs typed text, slashes, and
whether any text is dropped by reading only w:t (what the converter does)."""
import re
import sys
import zipfile

path = sys.argv[1] if len(sys.argv) > 1 else r"D:\Projects\X9Project\reader\sample\doc.docx"
z = zipfile.ZipFile(path)
xml = z.read("word/document.xml").decode("utf-8", "ignore")

M = "http://schemas.openxmlformats.org/officeDocument/2006/math"
print("=== OMML (real Word equations) ===")
for tag in ["oMath", "oMathPara", "f", "num", "den", "nary", "rad", "sSub",
            "sSup", "sSubSup", "d", "func", "limLow", "limUpp"]:
    n = len(re.findall(rf"<m:{tag}[ >]", xml))
    if n:
        print(f"  m:{tag}: {n}")
if "<m:oMath" not in xml:
    print("  none — formulas are typed as plain text, not Word equations")

print("\n=== slash characters in body text ===")
# crude: count '/' inside <w:t> runs
wt = re.findall(r"<w:t[^>]*>(.*?)</w:t>", xml, re.S)
body_text = "".join(wt)
print("  '/' occurrences:", body_text.count("/"))
frac_like = re.findall(r"\S*/\S*", body_text)
print("  slash fragments (first 40):")
for f in frac_like[:40]:
    print("   ", f)

print("\n=== files that may hold extra content ===")
for n in z.namelist():
    if n.endswith(".xml") and ("footnote" in n or "endnote" in n or "header" in n
                               or "footer" in n or "textbox" in n):
        data = z.read(n).decode("utf-8", "ignore")
        txt = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", data, re.S)).strip()
        if txt:
            print(f"  {n}: {len(txt)} chars -> {txt[:150]!r}")
