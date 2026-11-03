"""The print edition of the Pragati Field Manual: an A4 book built from the same content as the page.

Two passes lay the body out, read back the page on which every chapter landed
(pdftotext) and write those numbers into the contents; a designed cover is
rendered on its own and joined in front (pdfunite).

    python3 print_edition.py OUT.pdf
"""
import base64, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build
from plates import cover_art

EDITION = "Manual 1.2"
FONT_CSS = open(os.path.join(HERE, "fonts", "fonts.css")).read()
FONT_CSS = re.sub(r"url\((https://[^)]+\.ttf)\)(?: format\('truetype'\))?",
                  lambda m: "url(data:font/ttf;base64," + base64.b64encode(open(os.path.join(HERE, "fonts", m.group(1).rsplit("/", 1)[1]), "rb").read()).decode() + ") format('truetype')", FONT_CSS)

PRINT_CSS = r"""
/* PRINT EDITION · an A4 book: one 176 mm text column, every block on its edges */
:root,:root[data-theme="dark"]{--bg:#FFFFFF;--surface:#FFFFFF;--ink:#141C22;--muted:#56616A;--line:#D3D9DD;
  --bull:#0B8F70;--bear:#982116;--gold:#86700A;--neut:#66727B;--slate:#7E8891;--va:#2C5C99;--poc:#2B2B2B;--vwap:#A32468;--accent:#2C5C99;
  --tint-bull:rgba(11,143,112,.10);--tint-bear:rgba(152,33,22,.08);--tint-gold:rgba(134,112,10,.10);--tint-neut:rgba(102,114,123,.08);color-scheme:light}
@page{size:A4}
html,body{background:#FFFFFF}
body{font-size:9.4pt;line-height:1.5;color:var(--ink);-webkit-print-color-adjust:exact;print-color-adjust:exact}
.wrap{display:block;max-width:none;padding:0;margin:0}
nav,header.cover{display:none!important}
p,li{max-width:none;orphans:3;widows:3}
section.chap>ul,section.chap>ol:not(.callouts){break-inside:avoid}
li{break-inside:avoid}
p{margin:4pt 0}
ul,ol{margin:4pt 0;padding-left:14pt}
h2{font-size:30pt;font-stretch:82%;font-weight:800;letter-spacing:-.01em;margin:0}
h3{font-size:14pt;font-stretch:88%;font-weight:750;margin:0}
h4{font-size:10.4pt;margin:10pt 0 3pt;break-after:avoid}
.eyebrow{font-size:7.6pt}
section.part{break-before:page;border-top:none;padding-top:0;margin-top:0}
section.part>.eyebrow{font-size:9pt;letter-spacing:.24em}
section.part>h2{padding-bottom:8pt;border-bottom:1.4pt solid var(--ink);margin-top:2pt}
.opener{list-style:none;padding:0;margin:6pt 0 2pt;columns:2;column-gap:10mm;font-size:8.6pt;color:var(--muted)}
.opener li{padding:1pt 0;break-inside:avoid}
.opener b{font-family:var(--mono);font-weight:400;color:var(--accent);display:inline-block;width:16pt}
section.chap{padding-top:0;margin-top:13pt}
.chead{border-top:.6pt solid var(--line);padding-top:7pt;margin-bottom:4pt;break-inside:avoid;break-after:avoid}
.chead+*{break-before:avoid}
.chapno{font-size:7.2pt;letter-spacing:.14em;text-transform:uppercase;color:var(--accent)}
.lede{font-size:10.5pt}
.ev{font-size:6.4pt;padding:0 4pt;vertical-align:1pt}
.chip{font-size:7.2pt;padding:0 4pt}
.legend,.swatches{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:5pt;margin:6pt 0}
.legend>div,.sw{padding:6pt 7pt;border-radius:3pt;font-size:8.4pt;line-height:1.4}
.sw i{flex:0 0 14pt;height:14pt;border-radius:2pt}
.sw span{font-size:8pt}
.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:5pt;margin:6pt 0}
.card{padding:7pt 9pt;border-radius:3pt}
.card h4{font-size:10pt;margin:0 0 2pt}
.card p{font-size:8.6pt;margin:2pt 0;line-height:1.42}
.card .where{font-size:7.8pt}
.quick{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:5pt}
.quick .card ul{font-size:8.6pt}
figure{margin:7pt 0;padding:8pt;border-radius:3pt;break-inside:avoid}
figure svg{min-width:0;width:100%}
figcaption{font-size:8.2pt;margin-top:5pt}
ol.callouts{columns:2;column-gap:8mm;font-size:8.3pt;line-height:1.42;margin-top:6pt;padding-left:13pt}
ol.callouts li{margin-bottom:2pt}
.tbl{margin:6pt 0;border-radius:3pt;overflow:visible;break-inside:auto}
table{min-width:0!important;font-size:8.3pt;line-height:1.4;table-layout:fixed}
th{font-size:7.8pt;padding:4pt 6pt;letter-spacing:.03em}
td{padding:4pt 6pt}
tr{break-inside:avoid}
thead{display:table-header-group}
.mx{font-size:8pt;line-height:1.38}
.mx .mono{font-size:6.8pt!important}
.grid3{min-width:0;grid-template-columns:44pt repeat(3,minmax(0,1fr));gap:4pt;margin:4pt 0}
.cell{min-height:0;padding:7pt 8pt;border-radius:3pt}
.cell .fam{font-size:6.6pt}
.cell .act{font-size:15pt}
.cell .u{font-size:7.6pt}
.grid3 .h{font-size:7.4pt}
.steps{gap:0;margin:4pt 0}
.step{border:none;border-top:.5pt solid var(--line);border-radius:0;background:none;padding:5pt 0;grid-template-columns:18pt minmax(0,1fr);gap:6pt}
.step:last-child{border-bottom:.5pt solid var(--line)}
.step::before{font-size:13pt}
.step b{font-size:9.2pt}
.step p{font-size:8.7pt;margin:1pt 0}
.flow{display:block;margin:5pt 0;border-bottom:.5pt solid var(--line)}
.flow .arrow{display:none}
.flow>div{display:grid;grid-template-columns:46mm minmax(0,1fr);column-gap:5mm;border:none;border-top:.5pt solid var(--line);border-radius:0;background:none;padding:4.5pt 0;font-size:8.7pt;break-inside:avoid}
.flow>div b{font-size:9.2pt}
.note{font-size:8.7pt;padding:6pt 9pt;margin:7pt 0;break-inside:avoid}
.math{font-size:8pt;padding:7pt 9pt;line-height:1.45}
.disclaimer{font-size:8pt;margin-top:14pt}
a{color:var(--ink);text-decoration:none}
/* contents */
.pcontents h2{font-size:30pt;border-bottom:1.4pt solid var(--ink);padding-bottom:8pt;margin-bottom:6pt}
.pc-part{font-family:var(--display);font-stretch:85%;font-weight:700;font-size:8.4pt;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);margin-top:8pt;display:flex;align-items:baseline;gap:5pt}
.pc-part .t{flex:0 0 auto}
.pc-row{display:flex;align-items:baseline;gap:5pt;font-size:9.4pt;padding:1.2pt 0}
.pc-row .n{flex:0 0 16pt;font-family:var(--mono);font-size:8pt;color:var(--muted)}
.pc-row .t{flex:0 0 auto}
.lead{flex:1 1 auto;border-bottom:.7pt dotted #9AA4AB;transform:translateY(-2.5pt)}
.pg{flex:0 0 18pt;text-align:right;font-family:var(--mono);font-size:8.6pt;font-variant-numeric:tabular-nums}
.pc-intro{margin-top:16pt}
"""

COVER_CSS = r"""
@page{size:A4;margin:0}
html,body{margin:0;padding:0;background:#0D1215}
body{-webkit-print-color-adjust:exact;print-color-adjust:exact;font-family:"IBM Plex Sans",sans-serif;color:#E3E9EC}
.cv{width:210mm;height:297mm;box-sizing:border-box;padding:22mm 18mm 16mm;display:flex;flex-direction:column;background:#0D1215;position:relative;overflow:hidden}
.cv .top{display:flex;justify-content:space-between;font-family:"IBM Plex Mono",monospace;font-size:8.5pt;letter-spacing:.16em;text-transform:uppercase;color:#8A97A0}
.cv h1{font-family:"Archivo",sans-serif;font-weight:800;font-size:92pt;line-height:.9;letter-spacing:-.02em;margin:30mm 0 0;color:#E3E9EC}
.cv .sub{font-family:"Archivo",sans-serif;font-weight:600;font-size:30pt;letter-spacing:.01em;margin-top:4mm;color:#7FA9E6}
.cv .q{font-size:14pt;font-style:italic;margin-top:10mm;max-width:150mm;color:#C9D2D7;line-height:1.4}
.cv .art{margin:16mm -18mm 0;height:72mm}
.cv .art svg{width:100%;height:100%;display:block}
.cv .three{display:grid;grid-template-columns:repeat(3,1fr);gap:7mm;margin-top:12mm;border-top:.8pt solid #2A353D;padding-top:6mm}
.cv .three b{display:block;font-family:"Archivo",sans-serif;font-size:12pt;letter-spacing:.06em;text-transform:uppercase;margin-bottom:2mm}
.cv .three span{font-size:9.6pt;line-height:1.45;color:#B4BEC4}
.cv .foot{margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end;font-family:"IBM Plex Mono",monospace;font-size:8pt;color:#8A97A0;letter-spacing:.04em}
.cv .foot .ed{font-size:9.5pt;color:#E3E9EC}
"""

def _text(h):
    return re.sub(r"<[^>]+>", "", h).strip()

def body_html(pages=None):
    html = build.build()
    title = re.search(r"<title>.*?</title>", html).group(0)
    html = html.replace(title, "")
    html = re.sub(r'<link rel="(?:preconnect|stylesheet)"[^>]*>', "", html)
    html = re.sub(r'<meta name="claude:viewport-fit-sides"[^>]*>', "", html)
    # flows: wrap each step's text so the print grid has exactly two cells
    html = re.sub(r'(<div class="flow">.*?</div>\s*</div>)', lambda m: re.sub(r"<div><b>(.*?)</b>(.*?)</div>", r'<div><b>\1</b><span class="fx">\2</span></div>', m.group(1), flags=re.S), html, flags=re.S)
    # the unnumbered first chapter gets an anchor
    html = html.replace('<section class="chap">\n  <h3>How to read the evidence tags</h3>', '<section class="chap" id="tags"><div class="chead"><div class="chapno">Before you start</div><h3>How to read the evidence tags</h3></div>', 1)
    # structure: parts and their chapters, in order
    parts = []
    for pm in re.finditer(r'<section class="part" id="(part-\d)"><div class="eyebrow">(Part [IVX]+)([^<]*)</div><h2>(.*?)</h2>', html):
        parts.append({"id": pm.group(1), "label": pm.group(2), "sub": pm.group(3), "title": _text(pm.group(4)), "pos": pm.start(), "chs": []})
    for cm in re.finditer(r'<section class="chap" id="([\w-]+)"><div class="chead"><div class="chapno">Chapter (\d+)</div><h3>(.*?)</h3>', html):
        part = [p for p in parts if p["pos"] < cm.start()][-1]
        part["chs"].append((cm.group(1), cm.group(2), _text(cm.group(3))))
    # part openers: the part's chapters under its title
    for p in parts:
        li = "".join(f"<li><b>{n}</b>{t}</li>" for _, n, t in p["chs"])
        html = html.replace(f'<div class="eyebrow">{p["label"]}{p["sub"]}</div><h2>', f'<div class="eyebrow">{p["label"]}{p["sub"]}</div><h2 data-part="{p["id"]}">', 1)
        html = re.sub(rf'(<h2 data-part="{p["id"]}">.*?</h2>)', lambda m: m.group(1) + f'<ul class="opener">{li}</ul>', html, count=1, flags=re.S)
    pg = lambda k: f'<span class="pg">{(pages or {}).get(k, "00")}</span>'
    rows = [f'<div class="pc-row pc-intro"><span class="n"></span><span class="t">How to read the evidence tags</span><span class="lead"></span>{pg("tags")}</div>']
    for p in parts:
        rows.append(f'<div class="pc-part"><span class="t">{p["label"]} · {p["title"]}</span><span class="lead" style="border:none"></span>{pg(p["id"])}</div>')
        rows += [f'<div class="pc-row"><span class="n">{n}</span><span class="t">{t}</span><span class="lead"></span>{pg(i)}</div>' for i, n, t in p["chs"]]
    contents = f'<section class="pcontents"><div class="eyebrow">Pragati Field Manual · {EDITION}</div><h2>Contents</h2>{"".join(rows)}</section>'
    tags = re.search(r'<section class="chap" id="tags">.*?</section>', html, flags=re.S).group(0)
    html = html.replace(tags, "")
    # the evidence tags open Part I, so the contents page is followed by a full page
    html = re.sub(r'(<h2 data-part="part-1">.*?</h2><ul class="opener">.*?</ul>)', lambda m: m.group(1) + tags, html, count=1, flags=re.S)
    html = html.replace("<main>", "<main>" + contents, 1)
    doc = f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Pragati Field Manual</title><style>{FONT_CSS}</style><style>' + \
          re.search(r"<style>(.*?)</style>", html, flags=re.S).group(1) + PRINT_CSS + "</style></head><body>" + \
          re.sub(r"<style>.*?</style>", "", html, count=1, flags=re.S) + "</body></html>"
    keys = {"tags": "How to read the evidence tags"}
    for p in parts:
        keys[p["id"]] = p["title"]
        for i, n, t in p["chs"]:
            keys[i] = (n, t)
    return doc, keys

def cover_html():
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Pragati Field Manual</title><style>{FONT_CSS}</style><style>{COVER_CSS}</style></head><body>
<div class="cv">
  <div class="top"><span>BullishValue</span><span>For Pragati v9.9 on TradingView</span></div>
  <h1>Pragati</h1>
  <div class="sub">Field Manual</div>
  <div class="q">"Is this move paid for, and is it paid for on every timeframe?"</div>
  <div class="art">{cover_art()}</div>
  <div class="three">
    <div><b>Read</b><span>Every element of the pane and the price chart, and every state of the readout.</span></div>
    <div><b>Invest</b><span>The Conviction-Value Grid as an allocation map, with the capitulation plan.</span></div>
    <div><b>Trade</b><span>Accepted momentum, the system that passed a held-out test, with its exact rules.</span></div>
  </div>
  <div class="foot"><span class="ed">{EDITION} · November 2026</span><span>Educational, not financial advice</span></div>
</div></body></html>"""

def page_of(pdf, keys):
    txt = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True, check=True).stdout
    pages = txt.split("\f")
    norm = lambda s: re.sub(r"\s+", " ", s)
    out = {}
    for k, v in keys.items():
        for no, ptxt in enumerate(pages, 1):
            if no == 1:      # the contents page lists every title
                continue
            t = norm(ptxt)
            if isinstance(v, tuple):
                if f"CHAPTER {v[0]} " in t.upper() + " " and norm(v[1])[:22] in t:
                    out[k] = no; break
            elif norm(v)[:22] in t:
                out[k] = no; break
    return out

def main(out_pdf):
    d = HERE
    run = lambda *a: subprocess.run(["node", os.path.join(d, "render_print.js"), *a], check=True)
    doc, keys = body_html()
    open(os.path.join(d, "body.html"), "w", encoding="utf-8").write(doc)
    run(os.path.join(d, "body.html"), os.path.join(d, "body1.pdf"), "body")
    pages = page_of(os.path.join(d, "body1.pdf"), keys)
    missing = [k for k in keys if k not in pages]
    assert not missing, missing
    doc, _ = body_html({k: str(v) for k, v in pages.items()})
    open(os.path.join(d, "body.html"), "w", encoding="utf-8").write(doc)
    run(os.path.join(d, "body.html"), os.path.join(d, "body.pdf"), "body")
    again = page_of(os.path.join(d, "body.pdf"), keys)
    assert again == pages, "pagination moved between passes"
    open(os.path.join(d, "cover.html"), "w", encoding="utf-8").write(cover_html())
    run(os.path.join(d, "cover.html"), os.path.join(d, "cover.pdf"), "cover")
    subprocess.run(["pdfunite", os.path.join(d, "cover.pdf"), os.path.join(d, "body.pdf"), out_pdf], check=True)
    print("pages:", {k: pages[k] for k in list(pages)[:6]}, "…", "last chapter on", max(pages.values()))

if __name__ == "__main__":
    main(sys.argv[1])
