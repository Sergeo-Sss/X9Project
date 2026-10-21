"""Convert a .docx into a self-contained, watch-friendly HTML reader page.

Preserves headings, paragraphs, lists, tables, bold/italic and the sub/superscript
runs that carry the math. Output is one standalone .html (CSS+JS embedded) that both
previews in a browser and is loaded by the WebView reader app.

Usage: python docx2html.py <in.docx> <out.html> [Title]
"""
import html
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

from mathfmt import fractionize_html

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def w(tag):
    return f"{W}{tag}"


def run_html(r):
    """One <w:r> run -> inline HTML, honouring bold/italic/sub/superscript."""
    # Skip field instruction text (e.g. the TOC field), keep real text only.
    parts = []
    for t in r.iter(w("t")):
        parts.append(t.text or "")
    text = "".join(parts)
    if not text:
        if r.find(w("br")) is not None or r.find(w("tab")) is not None:
            return " "
        return ""
    out = html.escape(text)
    rpr = r.find(w("rPr"))
    if rpr is not None:
        va = rpr.find(w("vertAlign"))
        if va is not None:
            val = va.get(w("val"))
            if val == "subscript":
                out = f"<sub>{out}</sub>"
            elif val == "superscript":
                out = f"<sup>{out}</sup>"
        if rpr.find(w("b")) is not None:
            out = f"<strong>{out}</strong>"
        if rpr.find(w("i")) is not None:
            out = f"<em>{out}</em>"
    return out


def para_inner(p):
    """Inline HTML of a paragraph, skipping TOC/field instruction runs."""
    chunks = []
    for r in p.findall(w("r")):
        if r.find(w("instrText")) is not None:
            continue
        chunks.append(run_html(r))
    return "".join(chunks).strip()


def para_style(p):
    ppr = p.find(w("pPr"))
    if ppr is None:
        return "Normal", False
    style = "Normal"
    ps = ppr.find(w("pStyle"))
    if ps is not None:
        style = ps.get(w("val"))
    is_list = ppr.find(w("numPr")) is not None
    return style, is_list


HEADING = {"Title": "h1", "Heading1": "h1", "Heading2": "h2", "Heading3": "h3",
           "Heading4": "h4"}


def convert_body(body):
    out = []
    headings = []  # (level, id, text)
    list_open = False

    def close_list():
        nonlocal list_open
        if list_open:
            out.append("</ul>")
            list_open = False

    last_content = False  # True after a paragraph/list/table, for the question divider

    for el in body:
        tag = el.tag.replace(W, "")
        if tag == "tbl":
            close_list()
            out.append(table_html(el))
            last_content = True
            continue
        if tag != "p":
            continue
        style, is_list = para_style(el)
        inner = para_inner(el)
        if not inner:
            continue
        if style in HEADING:
            close_list()
            level = HEADING[style]
            # A yellow rule closes the previous question before a new part (h1) or
            # question (h2) begins — but not between a part and its first question.
            if level in ("h1", "h2") and last_content:
                out.append('<hr class="qend">')
            hid = f"h{len(headings)}"
            headings.append((int(level[1]), hid, re.sub("<[^>]+>", "", inner)))
            out.append(f'<{level} id="{hid}">{inner}</{level}>')
            last_content = False
        elif is_list or style == "ListParagraph":
            if not list_open:
                out.append("<ul>")
                list_open = True
            out.append(f"<li>{fractionize_html(inner)}</li>")
            last_content = True
        else:
            close_list()
            out.append(f"<p>{fractionize_html(inner)}</p>")
            last_content = True
    close_list()
    if last_content:
        out.append('<hr class="qend">')   # close the final question
    return "\n".join(out), headings


def table_html(tbl):
    rows = []
    for tr in tbl.findall(w("tr")):
        cells = []
        for tc in tr.findall(w("tc")):
            inner = " ".join(para_inner(p) for p in tc.findall(w("p"))).strip()
            cells.append(f"<td>{fractionize_html(inner)}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return '<div class="tw"><table>' + "".join(rows) + "</table></div>"


PAGE = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>{title}</title>
<style>
:root {{ --fs: 20px; }}
* {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
html, body {{ margin: 0; background: #000; }}
body {{
  color: #ececec;
  font-family: -apple-system, Roboto, "Segoe UI", sans-serif;
  font-size: var(--fs);
  line-height: 1.5;
  /* Padding keeps text clear of the rounded corners of the watch screen. */
  padding: 40px 18px 72px;
  -webkit-text-size-adjust: none;
}}
h1 {{ font-size: 1.5em; line-height: 1.25; margin: .2em 0 .5em; color: #fff; }}
h2 {{ font-size: 1.28em; line-height: 1.25; margin: 1em 0 .4em; color: #fff; }}
h3 {{ font-size: 1.12em; line-height: 1.3; margin: .9em 0 .3em; color: #cfe3ff; }}
h4 {{ font-size: 1em; margin: .8em 0 .3em; color: #cfe3ff; }}
p {{ margin: .55em 0; }}
ul {{ margin: .5em 0; padding-left: 1.1em; }}
li {{ margin: .35em 0; }}
sub, sup {{ font-size: .72em; line-height: 0; }}
strong {{ color: #fff; }}
em {{ color: #ffe0a8; font-style: italic; }}
.tw {{ overflow-x: auto; margin: .6em 0; -webkit-overflow-scrolling: touch; }}
table {{ border-collapse: collapse; font-size: .88em; }}
td {{ border: 1px solid #444; padding: 4px 8px; white-space: nowrap; text-align: center; }}

/* stacked fractions */
.frac {{ display: inline-flex; flex-direction: column; vertical-align: -0.45em;
  text-align: center; margin: 0 .12em; font-size: .95em; }}
.frac > .fn {{ padding: 0 .3em; border-bottom: 1.5px solid currentColor; line-height: 1.25; }}
.frac > .fd {{ padding: 0 .3em; line-height: 1.25; }}

/* yellow rule marking the end of a question */
hr.qend {{ border: none; border-top: 2px solid #e8b000; border-radius: 2px;
  margin: 1.5em 0 .3em; }}

/* inline contents at the top of the page */
#contents {{ border: 1px solid #333; border-radius: 10px; background: #0d0d0d;
  margin: 0 0 1.1em; padding: 4px 12px; }}
#contents > summary {{ cursor: pointer; font-weight: 700; color: #cfe3ff;
  padding: 8px 0; font-size: 1.02em; list-style: none; }}
#contents > summary::-webkit-details-marker {{ display: none; }}
#contents > summary::before {{ content: "\\25B6  "; font-size: .8em; color: #789; }}
#contents[open] > summary::before {{ content: "\\25BC  "; }}
#contents a {{ display: block; color: #cfe3ff; text-decoration: none;
  padding: 7px 2px; border-top: 1px solid #1c1c1c; font-size: .92em; }}
#contents a.lvl2 {{ padding-left: 14px; color: #bcd; }}
#contents a.lvl3 {{ padding-left: 30px; color: #9ab; font-size: .86em; }}

/* fixed bottom control bar */
#ctl {{ position: fixed; left: 0; right: 0; bottom: 0; height: 52px;
  display: flex; align-items: center; justify-content: center; gap: 10px;
  background: rgba(14,14,16,.96); border-top: 1px solid #333; z-index: 10;
  padding-bottom: 4px; }}
#ctl button {{ background: #242424; color: #fff; border: none; border-radius: 18px;
  font-size: 15px; padding: 8px 13px; }}
#ctl .tocbtn {{ background: #1f3350; color: #cfe3ff; font-weight: 700; padding: 8px 16px; }}
</style>
</head>
<body>
<div id="ctl">
  <button onclick="fs(-1)">A&minus;</button>
  <button class="tocbtn" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">&#9650; Оглавление</button>
  <button onclick="fs(1)">A+</button>
</div>
<main>
<details id="contents" open>
<summary>&#128209; Оглавление</summary>
{inlinetoc}
</details>
{body}
</main>
<script>
var root = document.documentElement;
function clamp(v){{ return Math.max(14, Math.min(34, v)); }}
function applyFs(v){{ root.style.setProperty('--fs', v+'px'); try{{ localStorage.setItem('fs', v); }}catch(e){{}} }}
function fs(d){{
  var cur = parseInt(getComputedStyle(root).getPropertyValue('--fs')) || 20;
  applyFs(clamp(cur + d*2));
}}
(function(){{ try{{ var s = localStorage.getItem('fs'); if(s) applyFs(clamp(parseInt(s))); }}catch(e){{}} }})();
// inline contents: jump, then collapse so the text is right below
document.getElementById('contents').addEventListener('click', function(e){{
  var a = e.target.closest('a[href^="#"]'); if(!a) return;
  var d = document.getElementById('contents');
  setTimeout(function(){{ d.removeAttribute('open'); }}, 0);
}});
// rotary crown often arrives as a wheel event in WebView
window.addEventListener('wheel', function(e){{ window.scrollBy(0, e.deltaY); }}, {{passive:true}});
</script>
</body>
</html>
"""


def _visible(headings):
    """Drop a redundant 'Содержание' heading from the generated contents lists."""
    return [h for h in headings if h[2].strip().lower() != "содержание"]


def build_toc(headings):
    items = []
    for level, hid, text in _visible(headings):
        cls = f"lvl{level}"
        items.append(f'<a class="{cls}" href="#{hid}">{html.escape(text)}</a>')
    return "\n".join(items)


def main():
    src = sys.argv[1]
    dst = sys.argv[2]
    title = sys.argv[3] if len(sys.argv) > 3 else "Документ"
    z = zipfile.ZipFile(src)
    root = ET.fromstring(z.read("word/document.xml"))
    body = root.find(w("body"))
    body_html, headings = convert_body(body)
    toc_html = build_toc(headings)
    page = PAGE.format(title=html.escape(title), body=body_html,
                       toc=toc_html, inlinetoc=toc_html)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"wrote {dst}: {len(headings)} headings, {len(body_html)} bytes of body")


if __name__ == "__main__":
    main()
