"""Pragati Field Manual, the book: typeset for A4 from the same content as the web page.

Publishing rules applied
  structure    cover · front matter (title, imprint, contents, how to use) · six parts ·
               fourteen chapters · numbered sections · back matter (quick reference card,
               glossary, index, colophon) · back cover
  placement    each part on a recto of its own with a blank verso, so its first chapter
               opens on a recto; a blank verso before a part when needed; every chapter
               opens a new page with its title sunk; the index opens on a recto; the page
               count is even, the back cover on the last verso
  folios       roman in the front matter (none on the title and imprint), arabic from 1 at
               Part I; none on part and blank pages; a drop folio, centred, on openings;
               outer corners elsewhere
  running heads  part on the verso, chapter on the recto; none on openings
  margins      mirrored: inner 24 mm, outer 28 mm, top 24 mm, bottom 26 mm
  text         IBM Plex Serif 10.4/15 pt, justified and hyphenated, indented paragraphs,
               a measure of about 75 characters; headings, tables and captions in Plex Sans
  apparatus    numbered figures with captions below; numbered tables titled above and ruled
               top, head and foot only, a short table never split, a long one splitting with
               its head repeated and at least two rows on each side; contents and index
               read back from the laid-out pages, and re-laid until they agree with them

    python3 book.py OUT.pdf      (needs Node with Playwright, and poppler's pdftotext and pdfunite)
"""
import base64, html as _h, json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build
from plates import cover_art

EDITION, DATE = "Manual 1.3", "November 2026"
TOP, BOT, INNER, OUTER = 24, 26, 24, 28            # mm
W = os.path.join(HERE, "work"); os.makedirs(W, exist_ok=True)

def _font(url):
    """The TTF beside fonts.css, fetched once from Google Fonts (SIL Open Font License) if absent."""
    path = os.path.join(HERE, "fonts", url.rsplit("/", 1)[1])
    if not os.path.exists(path):
        import urllib.request
        urllib.request.urlretrieve(url, path)
    return open(path, "rb").read()

def _fonts():
    css = open(os.path.join(HERE, "fonts", "fonts.css")).read() + open(os.path.join(HERE, "fonts", "serif.css")).read()
    return re.sub(r"url\((https://[^)]+\.ttf)\)(?: format\('truetype'\))?",
                  lambda m: "url(data:font/ttf;base64," + base64.b64encode(_font(m.group(1))).decode() + ") format('truetype')", css)
FONTS = _fonts()

BOOK_CSS = r"""
:root,:root[data-theme="dark"]{--bg:#FFFFFF;--surface:#FFFFFF;--ink:#151C21;--muted:#5A646C;--line:#D5DBDF;
  --bull:#0B8F70;--bear:#982116;--gold:#86700A;--neut:#66727B;--slate:#7E8891;--va:#2C5C99;--poc:#2B2B2B;--vwap:#A32468;--accent:#2C5C99;
  --tint-bull:rgba(11,143,112,.10);--tint-bear:rgba(152,33,22,.08);--tint-gold:rgba(134,112,10,.10);--tint-neut:rgba(102,114,123,.07);
  --serif:"IBM Plex Serif",Georgia,serif;color-scheme:light}
html,body{background:#FFFFFF}
body{font-family:var(--serif);font-size:10.4pt;line-height:15pt;color:var(--ink);-webkit-print-color-adjust:exact;print-color-adjust:exact;hyphens:auto;-webkit-hyphens:auto}
.wrap{display:block;max-width:none;padding:0;margin:0}
nav,header.cover,.disclaimer{display:none!important}
main p{margin:0;max-width:none;text-align:justify;orphans:2;widows:2}
main p+p{text-indent:1.3em}
main ul,main ol{margin:5pt 0 6pt;padding-left:15pt;max-width:none}
main li{max-width:none;margin:0 0 2.5pt;text-align:justify;break-inside:avoid}
section.chap>ul,section.chap>ol:not(.callouts){break-inside:avoid}
a{color:inherit;text-decoration:none}
code,.k,.mono{font-family:var(--mono);font-size:.86em}
/* ── part pages: recto, a page of their own ── */
section.part{break-before:auto;border:none;padding:0;margin:0}
section.part>.eyebrow,section.part>h2{display:none}
.part-page{break-before:page;break-after:page;height:236mm;box-sizing:border-box;padding-top:58mm;display:block}
.pp-label{font-family:var(--display);font-weight:700;font-size:10pt;letter-spacing:.42em;text-transform:uppercase;color:var(--accent)}
.pp-title{font-family:var(--display);font-weight:800;font-size:46pt;line-height:1;letter-spacing:-.01em;margin:9pt 0 0}
.pp-sub{font-family:var(--serif);font-style:italic;font-size:13pt;color:var(--muted);margin-top:9pt}
.pp-rule{width:24mm;border-top:1.6pt solid var(--accent);margin:20pt 0 14pt}
.pp-list{list-style:none;padding:0!important;margin:0!important;font-family:var(--body);font-size:9.8pt}
.pp-list li{display:flex;gap:8pt;align-items:baseline;padding:4pt 0;border-bottom:.4pt solid var(--line);text-align:left;margin:0}
.pp-list .n{flex:0 0 22pt;font-family:var(--mono);font-size:8.6pt;color:var(--accent)}
.pp-list .t{flex:1 1 auto}
.pp-list .pg{flex:0 0 auto;font-family:var(--mono);font-size:8.6pt;color:var(--muted)}
.blank-page{break-before:page;break-after:page;height:2mm}
/* ── chapter openings: a new page, the title sunk ── */
.chapter-head{break-before:page;border:none;margin:0 0 22pt;padding:44mm 0 0}
.chapter-head .chapno{font-family:var(--display);font-weight:700;font-size:9.4pt;letter-spacing:.36em;text-transform:uppercase;color:var(--accent)}
.chapter-head .ct{font-family:var(--display);font-weight:800;font-size:30pt;line-height:1.06;margin:7pt 0 0;letter-spacing:-.005em}
.chapter-head::after{content:"";display:block;width:24mm;border-top:1.6pt solid var(--accent);margin-top:14pt}
.chapter-head.back{padding-top:44mm}
/* ── sections: A-heads; B-heads ── */
section.chap{padding:0;margin:0}
.chead{margin:22pt 0 7pt;padding:0;border:none;break-inside:avoid;break-after:avoid}
.chapter-head+section.chap>.chead{margin-top:0}
.chead+*{break-before:avoid}
.chead{display:flex;align-items:baseline}
.secno{flex:0 0 auto;font-family:var(--body);font-weight:600;font-size:13.2pt;line-height:1.2;color:var(--accent);letter-spacing:0;margin-right:.62em;font-variant-numeric:tabular-nums}
.chead h3{font-family:var(--body);font-weight:600;font-size:13.2pt;line-height:1.2;margin:0;font-stretch:100%}
main h4{font-family:var(--body);font-weight:600;font-size:10.4pt;margin:15pt 0 4pt;break-after:avoid}
main h4+p{text-indent:0}
/* ── figures: caption below ── */
figure{margin:13pt 0;padding:0;border:none;background:none;break-inside:avoid}
figure .scroll{overflow:visible}
figure svg{min-width:0;width:100%}
figcaption{font-family:var(--body);font-size:8.4pt;line-height:1.42;color:var(--muted);margin-top:6pt;text-align:left}
figcaption b{color:var(--ink);margin-right:3pt}
ol.callouts{columns:2;column-gap:8mm;font-family:var(--body);font-size:8.3pt;line-height:1.42;margin:7pt 0 0;padding-left:13pt}
ol.callouts li{text-align:left}
/* ── tables: numbered, titled above, three rules ── */
.tcap{font-family:var(--body);font-size:8.6pt;margin:14pt 0 4pt;color:var(--ink);break-after:avoid}
.tcap b{color:var(--accent);margin-right:5pt;font-weight:600}
.tbl{margin:0 0 13pt;border:none;border-radius:0;background:none;overflow:visible;break-inside:auto}
table{min-width:0!important;width:100%;table-layout:fixed;border-collapse:collapse;font-family:var(--body);font-size:8.2pt;line-height:1.4;border-top:1pt solid var(--ink);border-bottom:1pt solid var(--ink)}
th{background:none!important;font-family:var(--body);font-weight:600;font-size:7.8pt;letter-spacing:.02em;padding:4.5pt 6pt 4pt;border-bottom:.6pt solid var(--ink);text-align:left;vertical-align:bottom}
td{padding:4pt 6pt;border-bottom:.3pt solid var(--line);text-align:left}
tr:last-child td{border-bottom:none}
tr{break-inside:avoid}
.tbl.keep{break-inside:avoid}
/* a split table keeps two rows with its head and leaves no fewer than two behind */
tbody tr:nth-child(2),tbody tr:last-child{break-before:avoid}
th,td{overflow-wrap:normal;word-break:normal}
th{hyphens:manual}
thead{display:table-header-group}
.mx{font-size:7.8pt;line-height:1.36}
.mx .mono{font-size:6.6pt!important}
/* ── furniture in sans: notes, steps, flows, cards, swatches ── */
.note{font-family:var(--body);font-size:8.8pt;line-height:1.45;padding:6pt 9pt;margin:11pt 0;border-radius:0;break-inside:avoid;text-align:left}
.steps{gap:0;margin:8pt 0 10pt}
.step{border:none;border-top:.5pt solid var(--line);border-radius:0;background:none;padding:5pt 0;grid-template-columns:18pt minmax(0,1fr);gap:6pt;break-inside:avoid}
.step:last-child{border-bottom:.5pt solid var(--line)}
.step::before{font-size:12pt}
.step b{font-family:var(--body);font-size:9.4pt}
.step p{font-size:9.8pt;line-height:14pt;margin:1pt 0;text-align:left;text-indent:0!important}
.flow{display:block;margin:8pt 0 10pt;border-bottom:.5pt solid var(--line)}
.flow .arrow{display:none}
.flow>div{display:grid;grid-template-columns:46mm minmax(0,1fr);column-gap:5mm;border:none;border-top:.5pt solid var(--line);border-radius:0;background:none;padding:4.5pt 0;font-family:var(--body);font-size:8.8pt;break-inside:avoid}
.flow>div b{font-size:9.2pt}
.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));column-gap:7mm;row-gap:8pt;margin:8pt 0}
.card{border:none;border-top:.8pt solid var(--ink);border-radius:0;background:none;padding:5pt 0 0;break-inside:avoid}
.card h4{font-size:10pt;margin:0 0 2pt}
.card p{font-family:var(--serif);font-size:9.4pt;line-height:13.4pt;margin:2pt 0;text-align:left;text-indent:0!important}
.card .where{font-family:var(--body);font-size:7.8pt;line-height:1.4;color:var(--muted)}
.quick{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));column-gap:7mm;row-gap:8pt}
.quick .card ul{font-family:var(--body);font-size:8.8pt}
.legend,.swatches{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));column-gap:6mm;row-gap:7pt;margin:8pt 0}
.legend>div,.sw{border:none;border-top:.5pt solid var(--line);border-radius:0;background:none;padding:5pt 0 0;font-family:var(--body);font-size:8.4pt;line-height:1.42}
.sw i{flex:0 0 13pt;height:13pt;border-radius:2pt}
.sw span{font-size:8pt}
.grid3{min-width:0;grid-template-columns:44pt repeat(3,minmax(0,1fr));gap:4pt;margin:2pt 0}
.cell{min-height:0;padding:7pt 8pt;border-radius:2pt}
.cell .fam{font-size:6.6pt}.cell .act{font-size:15pt}.cell .u{font-size:7.6pt}.grid3 .h{font-size:7.4pt}
.math{font-size:8pt;line-height:1.5;padding:7pt 10pt;border-radius:0;border:none;border-left:2pt solid var(--accent);background:var(--tint-neut);margin:8pt 0 12pt}
.chip{font-size:7.2pt;padding:0 3.5pt;border-radius:2pt}
.ev{font-size:6.2pt;padding:0 3.5pt;vertical-align:1pt;border-radius:2pt}
.num{font-size:inherit}
/* ── back matter ── */
.index{columns:2;column-gap:9mm;font-family:var(--body);font-size:8.4pt;line-height:1.5}
.index .ix{break-inside:avoid;padding-left:9pt;text-indent:-9pt}
.index .ix .p{color:var(--muted);font-family:var(--mono);font-size:7.6pt}
.index .lt{font-family:var(--display);font-weight:700;font-size:10pt;color:var(--accent);margin:8pt 0 2pt;break-after:avoid}
.gloss{border-top:1pt solid var(--ink);border-bottom:1pt solid var(--ink)}
.gloss .g{display:grid;grid-template-columns:40mm minmax(0,1fr);column-gap:6mm;padding:4.6pt 0;border-top:.3pt solid var(--line);break-inside:avoid}
.gloss .g:first-child{border-top:none}
.gloss b{font-family:var(--body);font-weight:600;font-size:9pt;line-height:13pt}
.gloss span{font-size:9.6pt;line-height:13pt;text-align:left;hyphens:manual}
.colophon p{font-family:var(--body);font-size:8.8pt;line-height:1.5;text-align:left}
"""

FRONT_CSS = r"""
@page{size:A4}
html,body{background:#FFFFFF;margin:0}
body{font-family:"IBM Plex Serif",Georgia,serif;color:#151C21;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.pg{break-after:page;box-sizing:border-box;position:relative;display:flow-root}
.title,.imprint{height:236mm}
.pg:last-child{break-after:auto}
.title{padding-top:60mm}
.title .a{font-family:"Archivo",sans-serif;font-weight:800;font-size:64pt;line-height:.95;letter-spacing:-.02em}
.title .b{font-family:"Archivo",sans-serif;font-weight:600;font-size:24pt;color:#2C5C99;margin-top:6pt}
.title .r{width:24mm;border-top:1.6pt solid #2C5C99;margin:22pt 0}
.title .q{font-style:italic;font-size:13.5pt;line-height:1.45;max-width:118mm;color:#3A444B}
.title .by{position:absolute;bottom:0;left:0;font-family:"IBM Plex Sans",sans-serif;font-size:9.4pt;letter-spacing:.24em;text-transform:uppercase;color:#5A646C}
.imprint{display:flex;flex-direction:column;justify-content:flex-end}
.imprint p{font-family:"IBM Plex Sans",sans-serif;font-size:8.2pt;line-height:1.55;margin:0 0 7pt;color:#3A444B;max-width:120mm}
.imprint b{color:#151C21}
h1.fm{font-family:"Archivo",sans-serif;font-weight:800;font-size:30pt;margin:44mm 0 18pt}
h1.fm::after{content:"";display:block;width:24mm;border-top:1.6pt solid #2C5C99;margin-top:14pt}
.toc{font-family:"IBM Plex Sans",sans-serif}
.toc .p{display:flex;align-items:baseline;gap:6pt;font-family:"Archivo",sans-serif;font-weight:700;font-size:8.6pt;letter-spacing:.2em;text-transform:uppercase;color:#2C5C99;margin:11pt 0 3pt;break-after:avoid}
.toc .cg{break-inside:avoid}
.toc .c,.toc .s{display:flex;align-items:baseline;gap:6pt;break-inside:avoid}
.toc .c{font-size:10pt;font-weight:600;padding:2pt 0 1pt}
.toc .s{font-size:9pt;color:#3A444B;padding:.5pt 0 .5pt 22pt}
.toc .n{flex:0 0 20pt;font-family:"IBM Plex Mono",monospace;font-weight:400;font-size:8.4pt;color:#2C5C99}
.toc .s .n{flex-basis:26pt;color:#5A646C}
.toc .t{flex:0 1 auto}
.toc .ld{flex:1 1 auto;border-bottom:.7pt dotted #9AA4AB;transform:translateY(-3pt);min-width:8pt}
.toc .pn{flex:0 0 auto;font-family:"IBM Plex Mono",monospace;font-size:8.6pt;font-weight:400}
.howto p{font-size:10.4pt;line-height:15pt;text-align:justify;hyphens:auto;margin:0}
.howto p+p{text-indent:1.3em}
.howto h4{font-family:"IBM Plex Sans",sans-serif;font-weight:600;font-size:10.4pt;margin:15pt 0 4pt}
.howto .legend{display:grid;grid-template-columns:repeat(3,1fr);column-gap:6mm;margin:8pt 0}
.howto .legend>div{border-top:.5pt solid #D5DBDF;padding-top:5pt;font-family:"IBM Plex Sans",sans-serif;font-size:8.4pt;line-height:1.42}
.howto .legend b{display:block;margin-bottom:3pt}
.howto ul{font-size:10pt;line-height:14.4pt;padding-left:15pt;margin:4pt 0}
.howto li{margin-bottom:3pt}
.ev{display:inline-block;font-family:"IBM Plex Mono",monospace;font-size:6.6pt;letter-spacing:.05em;text-transform:uppercase;padding:0 4pt;border-radius:2pt;vertical-align:1pt}
.ev-m{background:#2C5C99;color:#FFFFFF}.ev-x{border:1px solid #7E8891;color:#5A646C}.ev-u{border:1px dashed #86700A;color:#86700A}
code{font-family:"IBM Plex Mono",monospace;font-size:.86em}
"""

COVER_CSS = r"""
@page{size:A4;margin:0}
html,body{margin:0;padding:0;background:#0D1215}
body{-webkit-print-color-adjust:exact;print-color-adjust:exact;font-family:"IBM Plex Sans",sans-serif;color:#E3E9EC}
.cv{width:210mm;height:297mm;box-sizing:border-box;padding:24mm 22mm 18mm;display:flex;flex-direction:column;background:#0D1215;overflow:hidden}
.cv .top{display:flex;justify-content:space-between;font-family:"IBM Plex Mono",monospace;font-size:8.5pt;letter-spacing:.18em;text-transform:uppercase;color:#8A97A0}
.cv h1{font-family:"Archivo",sans-serif;font-weight:800;font-size:96pt;line-height:.9;letter-spacing:-.02em;margin:34mm 0 0;color:#E3E9EC}
.cv .sub{font-family:"Archivo",sans-serif;font-weight:600;font-size:30pt;margin-top:4mm;color:#7FA9E6}
.cv .q{font-family:"IBM Plex Serif",serif;font-size:14pt;font-style:italic;margin-top:11mm;max-width:150mm;color:#C9D2D7;line-height:1.42}
.cv .art{margin:15mm -22mm 0;height:70mm}
.cv .art svg{width:100%;height:100%;display:block}
.cv .three{display:grid;grid-template-columns:repeat(3,1fr);gap:8mm;margin-top:12mm;border-top:.8pt solid #2A353D;padding-top:6mm}
.cv .three b{display:block;font-family:"Archivo",sans-serif;font-size:11.5pt;letter-spacing:.12em;text-transform:uppercase;margin-bottom:2mm}
.cv .three span{font-size:9.4pt;line-height:1.45;color:#B4BEC4}
.cv .foot{margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end;font-family:"IBM Plex Mono",monospace;font-size:8pt;color:#8A97A0;letter-spacing:.04em}
.cv .foot .ed{font-size:9.5pt;color:#E3E9EC}
"""

BACK_CSS = r"""
.bk .bt{font-family:"Archivo",sans-serif;font-weight:800;font-size:40pt;line-height:1;letter-spacing:-.01em;margin:46mm 0 0;color:#E3E9EC}
.bk .bt span{font-weight:600;font-size:20pt;color:#7FA9E6;letter-spacing:0}
.bk .lead{font-family:"IBM Plex Serif",serif;font-size:13pt;line-height:1.5;color:#D3DBE0;max-width:140mm;margin:12mm 0 0}
.bk .two{display:grid;grid-template-columns:1fr 1fr;gap:9mm;margin-top:11mm;border-top:.8pt solid #2A353D;padding-top:6mm;max-width:150mm}
.bk .two b{display:block;font-family:"Archivo",sans-serif;font-size:11pt;letter-spacing:.12em;text-transform:uppercase;margin-bottom:2.5mm;color:#E3E9EC}
.bk .two span{font-size:9.6pt;line-height:1.5;color:#B4BEC4}
.bk .sm{font-size:9.6pt;line-height:1.5;color:#B4BEC4;max-width:150mm;margin-top:9mm}
"""

INDEX_TERMS = [
 ("Accepted momentum", ["accepted momentum"]), ("acceptance", ["acceptance"]), ("alerts", ["alert"]), ("AUCTION row", ["auction row"]),
 ("BASING", ["BASING"]), ("BUILDING", ["BUILDING"]), ("capitulation", ["capitulation"]), ("capitulation plan", ["capitulation plan"]),
 ("CHART cell", ["chart cell"]), ("colour grammar", ["colour grammar"]), ("conviction tape", ["conviction tape"]), ("costs", ["costs", " bps"]),
 ("crowded book", ["crowded"]), ("crypto", ["crypto"]), ("CVG row", ["cvg row"]), ("declaration", ["declaration"]), ("DISLOCATED", ["DISLOCATED"]),
 ("DISTRIBUTION", ["DISTRIBUTION"]), ("divergence, R and H", ["divergence"]), ("drawdown", ["drawdown"]), ("effort → result", ["effort → result", "absorbed"]),
 ("evidence tags", ["evidence tag", "how well each claim", "what is measured"]), ("expiry", ["expiry"]), ("FADING", ["FADING"]), ("FAINT", ["FAINT"]), ("gate warming", ["gate warming"]),
 ("held row", ["held row", "row is held", "held (gold)"]), ("histogram", ["histogram"]), ("HVN and LVN", ["hvn", "lvn"]), ("IDLE", ["IDLE"]),
 ("impulse", ["impulse"]), ("information panel", ["information panel"]), ("Initial Balance", ["initial balance", "IBH"]),
 ("Ladder down, Ladder up", ["ladder down", "ladder up"]), ("long build-up", ["long build-up"]), ("long unwinding", ["long unwinding"]),
 ("migration", ["migrat"]), ("momentum score S", ["momentum score", "momentum's score"]), ("naked POC", ["naked poc"]), ("non-standard charts", ["non-standard"]),
 ("OI row", ["oi row"]), ("open interest", ["open interest"]), ("PAID", ["PAID"]), ("paper trading", ["paper-trade", "paper trading"]), ("POC", ["POC"]),
 ("probe", ["probe"]), ("push gate", ["push gate"]), ("quiet regime", ["quiet regime"]), ("readout", ["readout"]), ("rebalance", ["rebalanc"]),
 ("Sharpe ratio", ["sharpe"]), ("short build-up", ["short build-up"]), ("short covering", ["short covering", "short-covering"]), ("sizing", ["sizing", "weight = size"]),
 ("STALLING", ["STALLING"]), ("θ, value threshold", ["θ"]), ("timeframes", ["timeframe"]), ("TURNED", ["TURNED"]), ("TWAP", ["TWAP"]), ("units", ["units"]),
 ("value area, VAH and VAL", ["value area", "VAH"]), ("value tape", ["value tape"]), ("volatility", ["volatility"]), ("volume profile", ["volume profile", "session profile"]),
 ("VWAP", ["VWAP"]), ("▲ capitulation turn", ["▲"]), ("▼ distribution", ["▼"]), ("◆ continuation", ["◆"]),
]

BACKM = (("card", "Quick reference card"), ("glossary", "Glossary"), ("index", "Index"), ("colophon", "Colophon"))

def _plain(h):
    return _h.unescape(re.sub(r"<[^>]+>", "", h)).strip()

def source():
    """The page's content, its structure and the pieces the front matter takes."""
    html = build.build()
    style = re.search(r"<style>(.*?)</style>", html, flags=re.S).group(1)
    html = re.sub(r"<style>.*?</style>", "", html, count=1, flags=re.S)
    html = re.sub(r"<title>.*?</title>|<link [^>]*>|<meta [^>]*>", "", html)
    tags = re.search(r'<section class="chap">\s*<h3>How to read the evidence tags</h3>(.*?)</section>', html, flags=re.S)
    html = html.replace(tags.group(0), "")
    struct = []
    for pid, ptitle, chs in build.STRUCTURE:
        m = re.search(rf'<section class="part" id="{pid}"><div class="eyebrow">(Part [IVX]+)([^<]*)</div><h2>(.*?)</h2>', html)
        chapters = []
        for cid, ctitle, secs in chs:
            n = int(re.search(rf'<div class="chapter-head" id="{cid}"><div class="chapno">Chapter (\d+)</div>', html).group(1))
            sl = []
            for sid in secs:
                sm = re.search(rf'<section class="chap" id="{sid}"><div class="chead"><div class="secno">([\d.]+)</div><h3>(.*?)</h3>', html)
                if sm:
                    sl.append((sid, sm.group(1), _plain(sm.group(2))))
            chapters.append((cid, n, ctitle, sl))
        struct.append((pid, m.group(1), m.group(2).strip(" ·"), ptitle, chapters))
    return style, html, tags.group(1), struct

def main_doc(style, html, struct, blanks=(), pages=None, index_html="", index_blank=False):
    pages = pages or {}
    pg = lambda k: str(pages.get(k, "00"))
    for pid, label, sub, ptitle, chapters in struct:
        li = "".join(f'<li><span class="n">{n}</span><span class="t">{ct}</span><span class="pg">{pg(cid)}</span></li>' for cid, n, ct, _ in chapters)
        page = (f'<div class="part-page"><div class="pp-label">{label}</div><h1 class="pp-title">{ptitle}</h1>'
                + (f'<div class="pp-sub">{sub[0].upper() + sub[1:]}</div>' if sub else "") + f'<div class="pp-rule"></div><ul class="pp-list">{li}</ul></div>')
        blank = '<div class="blank-page"></div>' if pid in blanks else ""
        html = html.replace(f'<section class="part" id="{pid}">', blank + f'<section class="part" id="{pid}">' + page + '<div class="blank-page"></div>', 1)
    colophon = ('<section class="chap back colophon" id="colophon"><div class="chapter-head back"><h2 class="ct">Colophon</h2></div>'
                f'<p>Pragati Field Manual, {EDITION}, {DATE}. Set in IBM Plex Serif for the text and IBM Plex Sans for headings, tables and captions, '
                'with IBM Plex Mono for what the indicator prints and Archivo for display. Typeset from the same source as the web edition by '
                '<code>docs/manual/src/book.py</code>: the body is laid out, each part, chapter and section is located on its page, parts are moved '
                'to recto pages, and the contents and index are written from the pages they point to. The figures are drawn from synthetic series '
                'in the indicator\'s own palette.</p></section>')
    def gloss(m):
        rows = re.findall(r"<tr><td>(.*?)</td><td>(.*?)</td></tr>", m.group(0))
        return '<div class="gloss">' + "".join(f'<div class="g"><b>{a}</b><span>{b}.</span></div>' for a, b in rows) + "</div>"
    gi = html.index('<section class="chap back" id="glossary">')
    ge = html.index("</section>", gi)
    html = html[:gi] + re.sub(r'<div class="tbl\s*">.*?</table></div>', gloss, html[gi:ge], count=1, flags=re.S) + html[ge:]
    # a short table is not split: a one-row remnant at the top of a page reads as a stray
    def keep(m):
        return m.group(0).replace('class="tbl', 'class="tbl keep', 1) if m.group(0).count("<tr>") <= 5 else m.group(0)
    html = re.sub(r'<div class="tbl[^"]*">.*?</table></div>', keep, html, flags=re.S)
    if index_blank:
        index_html = '<div class="blank-page"></div>' + index_html
    html = html.replace("</main>", index_html + colophon + "</main>", 1)
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Pragati Field Manual</title><style>{FONTS}</style><style>{style}{BOOK_CSS}</style></head><body>{html}</body></html>'

def render_layout(doc, name):
    src = os.path.join(W, name + ".html"); out = os.path.join(W, name + ".pdf")
    open(src, "w", encoding="utf-8").write(doc)
    m = json.dumps({"top": f"{TOP}mm", "bottom": f"{BOT}mm", "left": f"{(INNER + OUTER) / 2}mm", "right": f"{(INNER + OUTER) / 2}mm"})
    subprocess.run(["node", os.path.join(HERE, "render_book.js"), "layout", src, m, out], check=True)
    return src, out

def page_texts(pdf):
    t = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True, check=True).stdout.split("\f")
    if t and not t[-1].strip():
        t = t[:-1]
    return t

def locate(texts, struct):
    sq = lambda s: re.sub(r"[\s\u00ad-]+", "", s)
    T = [sq(t) for t in texts]
    where, roles = {}, {}
    def first(pred, start, what):
        for i in range(start, len(T)):
            if pred(T[i]):
                return i + 1
        raise SystemExit(f"locate: {what} not found from page {start + 1}")
    cursor = 0
    for pid, label, sub, ptitle, chapters in struct:
        key = sq(label.upper()) + sq(ptitle)
        p = first(lambda t: t.startswith(key) or (sq(label.upper()) in t[:20] and sq(ptitle) in t[:80]), cursor, pid)
        where[pid] = p; roles[p] = "part"; cursor = p
        for cid, n, ct, secs in chapters:
            ck = f"CHAPTER{n}" + sq(ct)[:16]
            c = first(lambda t: t.startswith(ck), cursor, cid)
            where[cid] = c; roles[c] = ("chap", cid); cursor = c - 1
            for sid, num, st in secs:
                sk = sq(num) + sq(st)[:14]
                s = first(lambda t: sk in t, cursor, sid)
                where[sid] = s; cursor = s - 1
    for bid, bt in BACKM:
        try:
            b = first(lambda t: t.startswith(sq(bt)), cursor, bid)
        except SystemExit:
            continue
        where[bid] = b; roles[b] = ("back", bid); cursor = b - 1
    for i, t in enumerate(T, 1):
        if not t:
            roles[i] = "blank"
    return where, roles

def build_index(texts, where):
    lo, hi = where["part-1"], where["card"] - 1
    joined = []
    for i in range(lo - 1, hi):
        t = re.sub(r"(\w)-\n\s*(\w)", r"\1\2", texts[i])
        joined.append((i + 1, re.sub(r"\s+", " ", t)))
    entries = []
    for term, pats in INDEX_TERMS:
        hits = []
        for no, t in joined:
            for pt in pats:
                if (pt.isupper() and pt in t) or (not pt.isupper() and pt.lower() in t.lower()):
                    hits.append(no); break
        hits = sorted(set(hits))
        if not hits:
            continue
        rng, a = [], hits[0]
        for prev, cur in zip(hits, hits[1:] + [None]):
            if cur != prev + 1:
                rng.append(f"{a}" if a == prev else f"{a}–{prev}"); a = cur
        entries.append((term, rng))
    entries.sort(key=lambda e: re.sub(r"[^a-z]", "", e[0].lower()) or "~" + e[0])
    out, letter = [], None
    for term, rng in entries:
        L = re.sub(r"[^A-Za-z]", "", term)[:1].upper() or "Symbols"
        if L != letter:
            out.append(f'<div class="lt">{L}</div>'); letter = L
        out.append(f'<div class="ix">{term}, <span class="p">{", ".join(rng)}</span></div>')
    return ('<section class="chap back" id="index"><div class="chapter-head back"><h2 class="ct">Index</h2></div>'
            f'<div class="index">{"".join(out)}</div></section>')

def head(text, align, inner_left):
    l, r = (INNER, OUTER) if inner_left else (OUTER, INNER)
    return (f'<div style="width:100%;margin:0 {r}mm 0 {l}mm;font-family:Helvetica,Arial,sans-serif;font-size:6.8px;letter-spacing:.12em;'
            f'text-transform:uppercase;color:#6B757D;display:flex;justify-content:{align};padding-bottom:3px;border-bottom:0.5px solid #CCD3D8">'
            f'<span>{text}</span></div>')

def foot(text, align, inner_left):
    l, r = (INNER, OUTER) if inner_left else (OUTER, INNER)
    return (f'<div style="width:100%;margin:0 {r}mm 0 {l}mm;font-family:Helvetica,Arial,sans-serif;font-size:7.6px;color:#5A646C;'
            f'display:flex;justify-content:{align}"><span>{text}</span></div>')

def render_pages(src, specs, tag):
    job = {"pages": []}
    for k, sp in specs:
        odd = k % 2 == 1
        l, r = (INNER, OUTER) if odd else (OUTER, INNER)
        job["pages"].append({"n": k, "out": os.path.join(W, f"{tag}{k:03d}.pdf"), "margin": {"top": f"{TOP}mm", "bottom": f"{BOT}mm", "left": f"{l}mm", "right": f"{r}mm"},
                             "header": sp.get("header"), "footer": sp.get("footer")})
    jf = os.path.join(W, tag + "job.json"); json.dump(job, open(jf, "w"))
    subprocess.run(["node", os.path.join(HERE, "render_book.js"), "pages", src, jf, ""], check=True)
    return [p["out"] for p in job["pages"]]

def roman(n):
    vals = [(10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]
    out = ""
    for v, s in vals:
        while n >= v:
            out += s; n -= v
    return out

def front_doc(struct, where, tags_html):
    toc = []
    for pid, label, sub, ptitle, chapters in struct:
        toc.append(f'<div class="p"><span class="t">{label} · {ptitle}</span><span class="ld" style="border:none"></span><span class="pn">{where[pid]}</span></div>')
        for cid, n, ct, secs in chapters:
            toc.append(f'<div class="cg"><div class="c"><span class="n">{n}</span><span class="t">{ct}</span><span class="ld"></span><span class="pn">{where[cid]}</span></div>'
                       + "".join(f'<div class="s"><span class="n">{num}</span><span class="t">{st}</span><span class="ld"></span><span class="pn">{where[sid]}</span></div>' for sid, num, st in secs) + "</div>")
    toc.append('<div class="p"><span class="t">Back matter</span><span class="ld" style="border:none"></span><span class="pn"></span></div>')
    for bid, bt in BACKM:
        toc.append(f'<div class="c"><span class="n"></span><span class="t">{bt}</span><span class="ld"></span><span class="pn">{where[bid]}</span></div>')
    legend = re.search(r'<div class="legend">.*?</div>\s*</section>|<div class="legend">(.*?)</div>\s*$', tags_html, flags=re.S)
    leg = re.search(r'(<div class="legend">.*)', tags_html, flags=re.S).group(1)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Pragati Field Manual</title><style>{FONTS}</style><style>{FRONT_CSS}</style></head><body>
<div class="pg title"><div class="a">Pragati</div><div class="b">Field Manual</div><div class="r"></div>
<div class="q">"Is this move paid for, and is it paid for on every timeframe?"<br>How to read the indicator, invest with its grid and trade its tested trend system.</div>
<div class="by">BullishValue</div></div>
<div class="pg imprint">
<p><b>Pragati Field Manual</b><br>{EDITION} · {DATE}<br>For Pragati v9.9 on TradingView (branch <code>pragati-v9.9</code>)</p>
<p>Published by BullishValue. © 2026 BullishValue. The Pragati script is released under the Mozilla Public License 2.0.</p>
<p><b>Not financial advice.</b> This manual is educational. It describes how an indicator works and how it was tested. Past results, including results on held-out data, do not guarantee future results. Trade only what you can afford to lose, and paper-trade first.</p>
<p><b>Sources.</b> Measured results are from <code>docs/trail-lab.md</code> and <code>docs/trail-tradability.md</code> in the Pragati repository. Results marked External are quoted from the v9 audit, which lives in a separate repository and was not re-checked for this edition.</p>
<p>Set in IBM Plex Serif, IBM Plex Sans, IBM Plex Mono and Archivo.</p></div>
<div class="pg"><h1 class="fm">Contents</h1><div class="toc">{"".join(toc)}</div></div>
<div class="pg howto"><h1 class="fm">How to use this manual</h1>
<p>Pragati answers one question about a market: whether a move is paid for, and on every timeframe. This manual explains each thing it draws and prints, then shows how to use it two ways. Part III treats it as an investor's allocation map, and Part IV as a trader's tested trend system. Part V works through how the readings combine.</p>
<p>Read Part I first. Parts II to V can be read in any order, and Part VI is for reference.</p>
<h4>How well each claim is known</h4>
<p>Pragati was built and audited in public, and many of its parts were tested on markets, but not all of them. Every claim carries one of three tags.</p>
{leg}
<h4>Conventions</h4>
<ul>
<li>Text in a monospace face, and coloured chips such as <code>LONG 0.62</code>, show what the indicator itself prints.</li>
<li>"Section 9.1" refers to a numbered section, and "chapter 5" to a chapter that has no sections. Figures and tables are numbered by chapter.</li>
<li>▲ ▼ ◆ × are the marks the indicator draws. Gold always means caution and never a direction.</li>
<li>Every figure in this manual is drawn from the indicator's defaults on daily charts, which is how it was tested.</li>
</ul></div>
</body></html>"""

def main(out_pdf):
    style, html, tags_html, struct = source()
    blanks = set()
    for _ in range(8):
        src, pdf = render_layout(main_doc(style, html, struct, blanks), "main")
        texts = page_texts(pdf)
        where, roles = locate(texts, struct)
        wrong = [pid for pid, *_ in struct if where[pid] % 2 == 0 and pid not in blanks]
        if not wrong:
            break
        blanks.add(wrong[0])
    index_html = build_index(texts, where)
    # final layout: part lists carry page numbers, the index and colophon are in place.
    # It has settled only when the index printed is the index of the pages printed.
    index_blank = False
    for _ in range(6):
        src, pdf = render_layout(main_doc(style, html, struct, blanks, where, index_html, index_blank), "main")
        texts = page_texts(pdf)
        w2, roles = locate(texts, struct)
        new_ix = build_index(texts, w2)
        if w2["index"] % 2 == 0 and not index_blank:
            index_blank = True                                   # the index opens on a recto
        elif new_ix == index_html and all(w2.get(k) == where.get(k) for k in w2):
            where = w2; break
        where, index_html = w2, new_ix
    else:
        raise SystemExit("layout did not settle")
    assert all(where[pid] % 2 == 1 for pid, *_ in struct), "a part is not on a recto"
    assert where["index"] % 2 == 1, "the index is not on a recto"
    # per-page running heads and folios
    cur_part = cur_chap = None
    chap_title = {cid: f"{n} · {ct}" for _, _, _, _, chs in struct for cid, n, ct, _ in chs}
    part_title = {pid: f"{label} · {pt}" for pid, label, _, pt, _ in struct}
    back_title = dict(BACKM)
    starts = sorted([(v, k) for k, v in where.items() if v])
    specs = []
    for k in range(1, len(texts) + 1):
        for v, key in starts:
            if v <= k:
                if key.startswith("part-"):
                    cur_part, cur_chap = key, None
                elif key in chap_title:
                    cur_chap = key
                elif key in back_title:
                    cur_part, cur_chap = None, key
        role = roles.get(k)
        odd = k % 2 == 1
        if role in ("part", "blank"):
            specs.append((k, {}))
        elif isinstance(role, tuple):
            specs.append((k, {"footer": foot(str(k), "center", odd)}))
        else:
            if odd:
                h = chap_title.get(cur_chap) or back_title.get(cur_chap, "")
            else:
                h = part_title.get(cur_part, "Pragati Field Manual") if cur_part else "Pragati Field Manual"
            specs.append((k, {"header": head(h, "flex-end" if odd else "flex-start", odd), "footer": foot(str(k), "flex-end" if odd else "flex-start", odd)}))
    mains = render_pages(src, specs, "m")
    # front matter, roman folios, padded to an even count so Part I falls on a recto
    fsrc = os.path.join(W, "front.html")
    open(fsrc, "w", encoding="utf-8").write(front_doc(struct, where, tags_html))
    fl = os.path.join(W, "front_layout.pdf")
    subprocess.run(["node", os.path.join(HERE, "render_book.js"), "layout", fsrc, json.dumps({"top": f"{TOP}mm", "bottom": f"{BOT}mm", "left": f"{(INNER + OUTER) / 2}mm", "right": f"{(INNER + OUTER) / 2}mm"}), fl], check=True)
    ft = page_texts(fl); nf = len(ft)
    fspecs = [(k, {} if k <= 2 or not ft[k - 1].strip() else {"footer": foot(roman(k), "flex-end" if k % 2 else "flex-start", k % 2 == 1)}) for k in range(1, nf + 1)]
    fronts = render_pages(fsrc, fspecs, "f")
    pad = []
    if nf % 2:
        bsrc = os.path.join(W, "blank.html"); open(bsrc, "w").write("<!doctype html><html><body></body></html>")
        bp = os.path.join(W, "blank.pdf")
        subprocess.run(["node", os.path.join(HERE, "render_book.js"), "layout", bsrc, json.dumps({"top": "0", "bottom": "0", "left": "0", "right": "0"}), bp], check=True)
        pad = [bp]
    # cover, inside cover, front matter, body
    csrc = os.path.join(W, "cover.html")
    open(csrc, "w", encoding="utf-8").write(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><style>{FONTS}</style><style>{COVER_CSS}</style></head><body><div class="cv">
<div class="top"><span>BullishValue</span><span>For Pragati v9.9 on TradingView</span></div><h1>Pragati</h1><div class="sub">Field Manual</div>
<div class="q">"Is this move paid for, and is it paid for on every timeframe?"</div><div class="art">{cover_art()}</div>
<div class="three"><div><b>Read</b><span>Every element of the pane and the price chart, and every state of the readout.</span></div>
<div><b>Invest</b><span>The Conviction-Value Grid as an allocation map, with the capitulation plan.</span></div>
<div><b>Trade</b><span>Accepted momentum, the system that passed a held-out test, with its exact rules.</span></div></div>
<div class="foot"><span class="ed">{EDITION} · {DATE}</span><span>Educational, not financial advice</span></div></div></body></html>""")
    cp = os.path.join(W, "cover.pdf")
    subprocess.run(["node", os.path.join(HERE, "render_book.js"), "layout", csrc, json.dumps({"top": "0", "bottom": "0", "left": "0", "right": "0"}), cp], check=True)
    inside = os.path.join(W, "inside.pdf")
    bsrc = os.path.join(W, "blank.html"); open(bsrc, "w").write("<!doctype html><html><body></body></html>")
    subprocess.run(["node", os.path.join(HERE, "render_book.js"), "layout", bsrc, json.dumps({"top": "0", "bottom": "0", "left": "0", "right": "0"}), inside], check=True)
    # back cover on the last verso: the book's page count is even
    bksrc = os.path.join(W, "back.html")
    open(bksrc, "w", encoding="utf-8").write(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><style>{FONTS}</style><style>{COVER_CSS}{BACK_CSS}</style></head><body><div class="cv bk">
<div class="top"><span>BullishValue</span><span>{EDITION} · {DATE}</span></div>
<div class="bt">Pragati<br><span>Field Manual</span></div>
<p class="lead">Pragati asks one question of a market: is this move paid for, and is it paid for on every timeframe? This manual reads every element it draws and prints, and then uses it two ways.</p>
<div class="two"><div><b>Investment guide</b><span>The Conviction-Value Grid as an allocation map: nine families, their units, the capitulation plan and how to build a book.</span></div>
<div><b>Trade guide</b><span>Accepted momentum, the trend system that passed a held-out test on 411 unseen markets, with its exact sizing, rebalance and kill rules.</span></div></div>
<p class="sm">Every claim carries its evidence: measured, external or unmeasured. Four matrices and worked scenarios cover how the readings combine and what to do when they disagree.</p>
<div class="foot"><span>For Pragati v9.9 on TradingView</span><span>Educational, not financial advice</span></div></div></body></html>""")
    bk = os.path.join(W, "back.pdf")
    subprocess.run(["node", os.path.join(HERE, "render_book.js"), "layout", bksrc, json.dumps({"top": "0", "bottom": "0", "left": "0", "right": "0"}), bk], check=True)
    tail = [bk] if len(texts) % 2 else [inside, bk]
    subprocess.run(["pdfunite", cp, inside, *fronts, *pad, *mains, *tail, out_pdf], check=True)
    print(f"front {nf}{' + 1 blank' if pad else ''} · body {len(texts)} · blanks before {sorted(blanks)} · parts on {[where[p] for p, *_ in struct]}")

if __name__ == "__main__":
    main(sys.argv[1])
