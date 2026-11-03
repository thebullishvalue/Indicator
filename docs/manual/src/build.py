import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plates import plate_pane, plate_chart, plate_am

M = '<span class="ev ev-m">Measured</span>'
X = '<span class="ev ev-x">External</span>'
U = '<span class="ev ev-u">Unmeasured</span>'

CSS = r"""
/* Layout: an operator's field manual. A contents rail beside the reading column on wide screens,
   one column on phones; plates (annotated diagrams) and reference tables break out to full width. */
:root{
  --bg:#F5F6F6; --surface:#FFFFFF; --ink:#172027; --muted:#55606A; --line:#D7DDE1;
  --bull:#0DA07E; --bear:#982116; --gold:#8F7A0E; --neut:#69757E; --slate:#7E8891;
  --va:#2C5C99; --poc:#2B2B2B; --vwap:#A32468; --violet:#6A3F84; --accent:#2C5C99;
  --tint-bull:rgba(13,160,126,.12); --tint-bear:rgba(152,33,22,.10); --tint-gold:rgba(143,122,14,.12); --tint-neut:rgba(105,117,126,.10);
  --display:"Archivo","Arial Narrow",system-ui,sans-serif; --body:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif; --mono:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bg:#0D1215; --surface:#141B20; --ink:#E3E9EC; --muted:#A3AEB5; --line:#27323A;
  --bull:#6EDDC3; --bear:#E8644A; --gold:#E3CE63; --neut:#8A97A0; --slate:#8E9AA6;
  --va:#6A9BE0; --poc:#C2CEFF; --vwap:#F06BA8; --violet:#B48BCB; --accent:#7FA9E6;
  --tint-bull:rgba(110,221,195,.12); --tint-bear:rgba(232,100,74,.13); --tint-gold:rgba(227,206,99,.12); --tint-neut:rgba(138,151,160,.12); color-scheme:dark}}
:root[data-theme="dark"]{
  --bg:#0D1215; --surface:#141B20; --ink:#E3E9EC; --muted:#A3AEB5; --line:#27323A;
  --bull:#6EDDC3; --bear:#E8644A; --gold:#E3CE63; --neut:#8A97A0; --slate:#8E9AA6;
  --va:#6A9BE0; --poc:#C2CEFF; --vwap:#F06BA8; --violet:#B48BCB; --accent:#7FA9E6;
  --tint-bull:rgba(110,221,195,.12); --tint-bear:rgba(232,100,74,.13); --tint-gold:rgba(227,206,99,.12); --tint-neut:rgba(138,151,160,.12); color-scheme:dark}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:var(--body);font-size:16px;line-height:1.6;margin:0}
.wrap{max-width:1180px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:28px 80px;display:grid;grid-template-columns:minmax(0,1fr);gap:40px}
@media (min-width:1040px){.wrap{grid-template-columns:220px minmax(0,1fr)}}
nav.toc{display:none}
@media (min-width:1040px){nav.toc{display:block;position:sticky;top:calc(env(safe-area-inset-top,0px) + 20px);align-self:start;max-height:calc(100vh - 40px);overflow:auto;font-size:13px;line-height:1.45;border-right:1px solid var(--line);padding-right:14px}}
nav.toc a{color:var(--muted);text-decoration:none;display:block;padding:3px 0}
nav.toc a:hover,nav.toc a:focus-visible{color:var(--accent)}
nav.toc .tp{font-family:var(--display);font-stretch:80%;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--ink);margin-top:14px;font-size:12px}
main{min-width:0}
h1,h2,h3,h4{font-family:var(--display);text-wrap:balance;line-height:1.15;margin:0}
h1{font-size:clamp(40px,7vw,72px);font-stretch:78%;font-weight:800;letter-spacing:-.01em}
h2{font-size:clamp(26px,3.6vw,36px);font-stretch:85%;font-weight:750;margin-top:8px}
h3{font-size:21px;font-stretch:90%;font-weight:700;margin-top:30px}
h4{font-size:16px;font-weight:700;margin-top:18px}
p,li{max-width:72ch}
p{margin:10px 0}
a{color:var(--accent)}
code,.mono{font-family:var(--mono);font-size:.92em}
.eyebrow{font-family:var(--display);font-stretch:80%;font-weight:700;letter-spacing:.12em;text-transform:uppercase;font-size:12.5px;color:var(--accent)}
.lede{font-size:19px;color:var(--muted);max-width:62ch}
.cover{display:grid;gap:18px;padding-block:18px 26px;border-bottom:2px solid var(--ink)}
.cover .q{font-family:var(--display);font-stretch:85%;font-size:clamp(20px,2.6vw,26px);font-weight:600}
.meta{display:flex;flex-wrap:wrap;gap:8px 22px;font-size:13px;color:var(--muted);font-family:var(--mono)}
section.part{padding-top:44px;margin-top:20px;border-top:1px solid var(--line)}
section.chap{padding-top:26px}
.chapno{font-family:var(--mono);font-size:13px;color:var(--muted)}
.ev{display:inline-block;font-family:var(--mono);font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;padding:1px 6px;border-radius:3px;vertical-align:2px;white-space:nowrap}
.ev-m{background:var(--va);color:var(--surface)}
.ev-x{border:1px solid var(--slate);color:var(--muted)}
.ev-u{border:1px dashed var(--gold);color:var(--gold)}
.legend{display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));margin:14px 0}
.legend>div{border:1px solid var(--line);background:var(--surface);padding:12px 14px;border-radius:6px;min-width:0}
.legend b{display:block;margin-bottom:4px}
figure{margin:22px 0;background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:14px}
figure .scroll{overflow-x:auto}
figure svg{display:block;width:100%;min-width:680px;height:auto}
figcaption{font-size:14px;color:var(--muted);margin-top:10px}
figcaption b{color:var(--ink)}
ol.callouts{columns:2 280px;column-gap:28px;font-size:14.5px;padding-left:22px;margin:12px 0 0}
ol.callouts li{break-inside:avoid;margin-bottom:6px}
.tbl{overflow-x:auto;margin:16px 0;border:1px solid var(--line);border-radius:6px;background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:14.5px;min-width:560px}
th,td{text-align:left;vertical-align:top;padding:9px 12px;border-bottom:1px solid var(--line)}
th{font-family:var(--display);font-stretch:88%;font-weight:700;font-size:13.5px;letter-spacing:.02em;background:var(--tint-neut)}
tr:last-child td{border-bottom:none}
td .k{font-family:var(--mono);font-size:13px}
.num{font-variant-numeric:tabular-nums;font-family:var(--mono);font-size:13.5px}
.chip{display:inline-block;font-family:var(--mono);font-size:12px;padding:1px 7px;border-radius:3px;white-space:nowrap}
.c-bull{background:var(--tint-bull);color:var(--bull)} .c-bear{background:var(--tint-bear);color:var(--bear)}
.c-gold{background:var(--tint-gold);color:var(--gold)} .c-neut{background:var(--tint-neut);color:var(--muted)}
.c-va{background:var(--tint-neut);color:var(--va)}
.swatches{display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));margin:14px 0}
.sw{display:flex;gap:12px;align-items:flex-start;border:1px solid var(--line);background:var(--surface);padding:12px;border-radius:6px;min-width:0}
.sw i{flex:0 0 26px;height:26px;border-radius:4px;display:block}
.sw b{display:block}
.sw span{font-size:13.5px;color:var(--muted)}
.cards{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));margin:16px 0}
.card{border:1px solid var(--line);background:var(--surface);border-radius:6px;padding:14px 16px;min-width:0}
.card h4{margin-top:0;display:flex;justify-content:space-between;gap:8px;align-items:baseline}
.card p{font-size:14.5px;margin:6px 0}
.card .where{font-size:13px;color:var(--muted)}
.grid3{display:grid;grid-template-columns:72px repeat(3,minmax(0,1fr));gap:6px;margin:18px 0;min-width:520px}
.grid3 .h{font-family:var(--display);font-stretch:85%;font-weight:700;font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:2px}
.grid3 .h span{display:block}
.grid3 .rh{align-items:flex-start;text-align:left}
.cell{border-radius:6px;padding:12px;border:1px solid var(--line);min-height:104px;position:relative}
.cell .fam{font-family:var(--mono);font-size:11.5px;letter-spacing:.06em;color:var(--muted)}
.cell .act{font-family:var(--display);font-stretch:85%;font-size:22px;font-weight:750;line-height:1.1;margin-top:4px}
.cell .u{font-family:var(--mono);font-size:13px;margin-top:4px}
.cell .mk{position:absolute;right:10px;top:8px;font-size:18px}
.b4{background:rgba(13,160,126,.26)} .b3{background:rgba(13,160,126,.19)} .b15{background:var(--tint-bull)}
.n1{background:var(--tint-neut)} .t075{background:var(--tint-bear)} .x025{background:rgba(152,33,22,.22)}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .b4{background:rgba(110,221,195,.26)} :root:not([data-theme="light"]) .b3{background:rgba(110,221,195,.19)} :root:not([data-theme="light"]) .x025{background:rgba(232,100,74,.26)}}
:root[data-theme="dark"] .b4{background:rgba(110,221,195,.26)} :root[data-theme="dark"] .b3{background:rgba(110,221,195,.19)} :root[data-theme="dark"] .x025{background:rgba(232,100,74,.26)}
.act.buy{color:var(--bull)} .act.sell{color:var(--bear)} .act.hold{color:var(--ink)}
.steps{display:grid;gap:10px;margin:16px 0;counter-reset:s}
.step{display:grid;grid-template-columns:38px minmax(0,1fr);gap:12px;align-items:start;border:1px solid var(--line);background:var(--surface);border-radius:6px;padding:12px 14px}
.step::before{counter-increment:s;content:counter(s);font-family:var(--display);font-stretch:80%;font-weight:800;font-size:26px;color:var(--accent);line-height:1}
.step p{margin:2px 0;font-size:14.5px}
.flow{display:flex;flex-wrap:wrap;gap:8px;align-items:stretch;margin:16px 0}
.flow>div{flex:1 1 150px;border:1px solid var(--line);border-radius:6px;padding:10px 12px;background:var(--surface);font-size:14px;min-width:0}
.flow>div b{display:block;font-family:var(--display);font-stretch:88%;font-size:15px}
.flow .arrow{flex:0 0 auto;border:none;background:none;padding:0 2px;display:flex;align-items:center;color:var(--muted);font-size:20px}
.note{border-left:3px solid var(--gold);background:var(--tint-gold);padding:10px 14px;border-radius:0 6px 6px 0;margin:16px 0;font-size:15px}
.note.rule{border-left-color:var(--accent);background:var(--tint-neut)}
.math{font-family:var(--mono);background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:12px 14px;overflow-x:auto;font-size:14px;white-space:pre}
.quick{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(250px,1fr))}
.quick .card ul{padding-left:18px;margin:6px 0;font-size:14px}
.disclaimer{font-size:13.5px;color:var(--muted);border-top:1px solid var(--line);padding-top:14px;margin-top:40px}
svg .f-surface{fill:var(--surface)} svg .s-line{stroke:var(--line)} svg .f-bull{fill:var(--bull)} svg .f-bear{fill:var(--bear)} svg .f-gold{fill:var(--gold)}
svg .f-neut{fill:var(--neut)} svg .f-slate{fill:var(--slate)} svg .f-va{fill:var(--va)} svg .f-poc{fill:var(--poc)} svg .f-node{fill:var(--neut)} svg .f-vwap{fill:var(--vwap)}
svg .f-muted{fill:var(--muted)} svg .f-ink{fill:var(--ink)} svg .f-accent{fill:var(--accent)}
svg .s-muted{stroke:var(--muted)} svg .s-ink{stroke:var(--ink)} svg .s-bull{stroke:var(--bull)} svg .s-bear{stroke:var(--bear)} svg .s-neut{stroke:var(--neut)}
svg .s-slate{stroke:var(--slate)} svg .s-va{stroke:var(--va)} svg .s-poc{stroke:var(--poc)} svg .s-vwap{stroke:var(--vwap)}
svg text{font-family:var(--mono)} svg .t-small{font-size:11.5px} svg .t-tiny{font-size:10.5px} svg .t-mark{font-size:20px;font-family:var(--body)}
svg .t-callout{font-size:11.5px;font-weight:700;fill:var(--surface);font-family:var(--body)}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
@media print{
  :root,:root[data-theme="dark"]{--bg:#FFFFFF;--surface:#FFFFFF;--ink:#172027;--muted:#4F5A63;--line:#CDD4D8;--bull:#0DA07E;--bear:#982116;--gold:#8F7A0E;--neut:#69757E;--slate:#7E8891;--va:#2C5C99;--poc:#2B2B2B;--vwap:#A32468;--accent:#2C5C99;color-scheme:light}
  body{font-size:11pt}
  .wrap{display:block;padding:0}
  nav.toc{display:none}
  section.part{break-before:page;border-top:none;padding-top:0;margin-top:0}
  figure,.tbl,.card,.cell,.step,.legend>div,.sw,.note,.math{break-inside:avoid}
  figure svg{min-width:0}
  .tbl{overflow:visible} table{min-width:0;font-size:9.5pt}
  .grid3{min-width:0}
  h2,h3{break-after:avoid}
  a{color:var(--ink);text-decoration:none}
}
"""

def tbl(head, rows, cls=""):
    h = "".join(f"<th>{c}</th>" for c in head)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="tbl {cls}"><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>'

def cell(fam, act, units, cls, actcls, mark=""):
    mk = f'<span class="mk">{mark}</span>' if mark else ""
    return f'<div class="cell {cls}">{mk}<div class="fam">{fam}</div><div class="act {actcls}">{act}</div><div class="u">{units} units</div></div>'

GRID = f"""
<div class="tbl" style="border:none;background:none"><div class="grid3">
  <div></div><div class="h">Cheap<br><span style="font-weight:400;text-transform:none;letter-spacing:0">value past −θ</span></div><div class="h">Fair<br><span style="font-weight:400;text-transform:none;letter-spacing:0">inside θ</span></div><div class="h">Rich<br><span style="font-weight:400;text-transform:none;letter-spacing:0">value past +θ</span></div>
  <div class="h rh">Up<br>buyers</div>{cell("TURNED","Buy","3","b3","buy")}{cell("BUILDING","Hold","1.5","n1","hold")}{cell("PAID","Trim","0.75","t075","sell")}
  <div class="h rh">Faint</div>{cell("BASING","Accumulate","1.5","b15","buy")}{cell("IDLE","Wait","1","n1","hold")}{cell("STALLING","Trim","0.75","t075","sell")}
  <div class="h rh">Down<br>sellers</div>{cell("DISLOCATED · capitulation","Buy","4","b4","buy",'<span style="color:var(--bull)">▲</span>')}{cell("FADING","Accumulate","1.5","b15","buy")}{cell("DISTRIBUTION","Exit","0.25","x025","sell",'<span style="color:var(--bear)">▼</span>')}
</div></div>
"""

def matrix_a():
    fam = [
      ("UP · cheap", "TURNED", "Buy 3",
       ("Aligned. Trend, buyers and a cheap price agree: the strongest constructive picture.", "Hold the system's size.", "Buy toward 3 units."),
       ("Buyers are early; long momentum has not caught up.", "No position: the system is flat.", "Buy toward 3 units. The grid leads here."),
       ("A turn against a falling trend: buyers take control while price is still cheap.", "The system stays short until its rules flip it. Expect a conflict.", "Build in stages. Buy toward 3 units.")),
      ("UP · fair", "BUILDING", "Hold 1.5",
       ("A healthy trend at a fair price.", "Hold.", "Hold 1.5. Do not chase."),
       ("Buyers in control, no trend yet.", "Flat.", "Hold."),
       ("A bounce inside a downtrend.", "Short, usually small (S is small).", "Hold. No adds.")),
      ("UP · rich", "PAID", "Trim 0.75",
       ("A late trend: the move is already paid for.", "Hold the system's size; it sizes by S. Do not add.", "Trim toward 0.75."),
       ("Stretched, with no trend behind it.", "Flat.", "Trim."),
       ("A squeeze into a downtrend, at a rich price.", "Short.", "Trim or avoid.")),
      ("FAINT · cheap", "BASING", "Accumulate 1.5",
       ("A pullback inside an uptrend, now cheap.", "Hold.", "Accumulate."),
       ("Basing: cheap, nobody in control.", "Flat.", "Accumulate slowly."),
       ("Cheap inside a downtrend, nobody in control.", "Short.", "Accumulate small. Wait for DOWN · cheap or a turn.")),
      ("FAINT · fair", "IDLE", "Wait 1",
       ("The trend is resting.", "Hold.", "Wait. Hold what you have."),
       ("Nothing to read.", "Flat.", "Wait."),
       ("The downtrend is resting.", "Short.", "Wait.")),
      ("FAINT · rich", "STALLING", "Trim 0.75",
       ("An uptrend stalling at a rich price.", "Hold. Watch for the system to go flat.", "Trim."),
       ("Rich and stalling.", "Flat.", "Trim."),
       ("Weak, rich, falling.", "Short.", "Trim or avoid.")),
      ("DOWN · cheap", "DISLOCATED", "Buy 4 · ▲ here",
       ("A capitulation dip inside a long uptrend.", "Long holds; its size falls as S falls.", "Buy toward 4 units. Add on the ▲."),
       ("Capitulation, trend undecided.", "Flat.", "Stage in. Add on the ▲."),
       ("Capitulation inside a downtrend: the classic conflict between horizons.", "Short, by the trend rule.", "Stage in small. The ▲ is the trigger. Not on crypto.")),
      ("DOWN · fair", "FADING", "Accumulate 1.5",
       ("Sellers inside an uptrend, fair price.", "Hold.", "Accumulate."),
       ("Fading.", "Flat.", "Accumulate slowly."),
       ("A downtrend with sellers in control.", "Short.", "Accumulate small.")),
      ("DOWN · rich", "DISTRIBUTION", "Exit 0.25 · ▼ here",
       ("Sellers have taken a rich price while the long trend is still up: early distribution.", "Long until the system flips. Its size will fade.", "Exit toward 0.25."),
       ("Distribution.", "Flat.", "Exit."),
       ("Distribution inside a downtrend: aligned to the downside.", "Short.", "Exit.")),
    ]
    rows = []
    for name, family, act, l, f, s in fam:
        def c(x, tone):
            return f'<div class="mx {tone}"><b>{x[0]}</b><br><span class="mono" style="font-size:12px">TRADE</span> {x[1]}<br><span class="mono" style="font-size:12px">INVEST</span> {x[2]}</div>'
        rows.append([f'<b>{name}</b><br><span class="mono" style="font-size:12px">{family}</span><br><span class="chip c-neut">{act}</span>',
                     c(l, ""), c(f, ""), c(s, "")])
    return tbl(['Grid family', '<span class="chip c-bull">AM LONG</span>', '<span class="chip c-neut">AM FLAT</span>', '<span class="chip c-bear">AM SHORT</span>'], rows, "matrix")

def build():
    toc = [("Part I · Basics", [("setup", "1 Setup in five minutes"), ("colour", "2 The colour grammar"), ("pane", "3 The pane, labelled"), ("chart", "4 The price chart, labelled"), ("engines", "5 The engines in plain words")]),
           ("Part II · Reading every state", [("grid", "6 The Conviction-Value Grid"), ("readout", "7 The readout table"), ("panel", "8 The information panel"), ("signals", "9 Signals and marks")]),
           ("Part III · Investment guide", [("inv-frame", "10 The investor's frame"), ("inv-families", "11 Nine families, nine actions"), ("inv-cap", "12 The capitulation plan"), ("inv-book", "13 Building the book"), ("inv-risk", "14 Investor risk")]),
           ("Part IV · Trade guide", [("am", "15 Accepted momentum, the tested system"), ("am-book", "16 Running it as a portfolio"), ("overlay", "17 Discretionary overlays"), ("stops", "18 Stops, targets, invalidation")]),
           ("Part V · Permutations", [("mx-a", "19 System × grid: 27 cases"), ("mx-b", "20 OI × location"), ("mx-c", "21 Trail × migration"), ("mx-d", "22 Asset class × evidence"), ("conflict", "23 When readings disagree")]),
           ("Part VI · Reference", [("alerts", "24 Alerts"), ("settings", "25 Settings"), ("evidence", "26 What is measured"), ("glossary", "27 Glossary"), ("card", "28 Quick card")])]
    nav = "".join(f'<div class="tp">{p}</div>' + "".join(f'<a href="#{i}">{t}</a>' for i, t in items) for p, items in toc)

    html = f"""<title>Pragati Field Manual</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..900&family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:ital,wght@0,400;0,600;0,700;1,400&display=swap">
<style>{CSS}
.matrix td{{min-width:190px}} .mx{{font-size:13.5px;line-height:1.45}} .mx b{{font-weight:600}}
</style>
<div class="wrap">
<nav class="toc" aria-label="Contents">{nav}</nav>
<main>

<header class="cover">
  <div class="eyebrow">Pragati v9.9 · BullishValue · Field manual</div>
  <h1>Pragati Field Manual</h1>
  <div class="q">"Is this move paid for, and is it paid for on every timeframe?"</div>
  <p class="lede">How to read every part of the indicator, how to invest with its grid, how to trade its tested trend system, and what every combination of readings means. Each claim is tagged with how well it is known.</p>
  <div class="meta"><span>Version 9.9 · branch pragati-v9.9</span><span>Daily charts are the default and the tested timeframe</span><span>Educational, not financial advice</span></div>
</header>

<section class="chap">
  <h3>How to read the evidence tags</h3>
  <p>Pragati was built and audited in public, and many of its parts were tested on markets. Not all of them were. Every claim in this manual carries one of three tags.</p>
  <div class="legend">
    <div><b>{M}</b>Tested in this repository on real market data with a pre-registered plan, and on data the design never saw. The numbers are in <code>docs/trail-lab.md</code> and <code>docs/trail-tradability.md</code>.</div>
    <div><b>{X}</b>Measured in the v9 audit (380 instruments, six asset classes, three eras), whose data lives in a separate repository. The numbers are quoted in the script and were not re-checked here.</div>
    <div><b>{U}</b>A reading aid or a reasoned combination. Useful for context, never proven to make money. Size accordingly.</div>
  </div>
</section>

<section class="part" id="part-1"><div class="eyebrow">Part I</div><h2>Basics</h2>

<section class="chap" id="setup"><div class="chapno">Chapter 1</div><h3>Setup in five minutes</h3>
<div class="steps">
  <div class="step"><div><b>Add Pragati to the chart.</b><p>It opens in its own pane under price, and it draws the trail, the volume profile and the readout table on the price chart itself.</p></div></div>
  <div class="step"><div><b>Use standard candles.</b><p>On Heikin Ashi, Renko, Kagi, Point &amp; Figure or range bars the prices never traded, so every family pauses and says "non-standard chart".</p></div></div>
  <div class="step"><div><b>Start on the daily chart.</b><p>Daily bars are what was tested. Weekly bars were tested for the ▲ and the grid. Intraday works, but nothing on it was measured.</p></div></div>
  <div class="step"><div><b>Leave the defaults alone at first.</b><p>View <span class="k">Full</span>, Trace <span class="k">Conviction × Value</span>, conviction on <span class="k">Ladder down</span>, value on <span class="k">Ladder up</span>, Accepted momentum <span class="k">on</span>. Every number in this manual was measured at these settings.</p></div></div>
  <div class="step"><div><b>Give it history.</b><p>Conviction's histogram needs about 450 bars to calibrate (1.8 years of daily bars). Until then the push gate is warming: the grid's rows have no memory, the trail cannot start, and the readout says so.</p></div></div>
  <div class="step"><div><b>Create one alert.</b><p>Choose the condition "Any alert() function call" on Pragati. It carries every event once, at its bar's close (Chapter 24).</p></div></div>
</div>
</section>

<section class="chap" id="colour"><div class="chapno">Chapter 2</div><h3>The colour grammar: one hue, one job</h3>
<p>Colours mean the same thing everywhere in Pragati. Learn these six and every element reads itself.</p>
<div class="swatches">
  <div class="sw"><i style="background:var(--bull)"></i><div><b>Green · direction up, action buy</b><span>Buyers in control, a rich value reading, a long position, a Buy or Accumulate action.</span></div></div>
  <div class="sw"><i style="background:var(--bear)"></i><div><b>Red · direction down, action sell</b><span>Sellers in control, a cheap value reading, a short position, a Trim or Exit action.</span></div></div>
  <div class="sw"><i style="background:var(--gold)"></i><div><b>Gold · caution, never a direction</b><span>Read with care: a probe, a quiet regime, a held row, a crowded book, short covering, crypto's capitulation.</span></div></div>
  <div class="sw"><i style="background:var(--neut)"></i><div><b>Grey · neutral</b><span>Nothing to read, Hold or Wait, Accepted momentum flat.</span></div></div>
  <div class="sw"><i style="background:var(--va)"></i><div><b>Blue · the session profile's value area</b><span>Identity, not direction. The VAH, VAL and value rows.</span></div></div>
  <div class="sw"><i style="background:var(--slate)"></i><div><b>Slate · the trail's rolling value ribbon</b><span>Identity: a different value area from the session profile's.</span></div></div>
</div>
<div class="note">On the value tape, green means <b>rich</b> and red means <b>cheap</b>. A red value tape is a price below fair value, which is what the capitulation ▲ wants.</div>
</section>

<section class="chap" id="pane"><div class="chapno">Chapter 3</div><h3>The pane, labelled</h3>
<figure><div class="scroll">{plate_pane()}</div>
<figcaption><b>Plate 1 · The oscillator pane.</b> Numbers match the list below.</figcaption>
<ol class="callouts">
  <li><b>Trace.</b> Default Conviction × Value: how stretched the move is, in effort and in price against fair value. Rails at ±θ (±43 at the default) and ±60, a 3σ stretch. {U}</li>
  <li><b>Histogram.</b> The trace minus its 9-bar signal. Hue is the direction of the push. Bright means pressing, mid means decelerating, pale means turning. {U}</li>
  <li><b>Rails.</b> Dotted ±θ, dashed ±60. On the Conviction trace they are the inner (±30) and outer (±60) zones.</li>
  <li><b>Conviction tape (+82)</b> with its momentum band (+89). The ladder's view of who is in control: green buyers, red sellers, bright past the inner zone.</li>
  <li><b>Value tape (−82)</b> with its momentum band (−89). Samanvaya's multi-timeframe value: green rich, red cheap, bright past θ.</li>
  <li><b>▲ Capitulation turn.</b> The grid stands in DOWN · cheap and value momentum has turned back toward fair. {X}</li>
  <li><b>▼ Distribution.</b> Sellers have taken control of a price rich past θ. {X}</li>
  <li><b>Background tint.</b> Green while the grid holds Buy · capitulation, deeper after value momentum turns. Red in Exit · distribution. Gold on crypto.</li>
  <li><b>Gold cast.</b> Columns turn gold when the push was paid for more by exits than new positions, from open interest. {X}</li>
</ol></figure>
<p>A column's colour is not who is in control. Control is the trace's side of zero. A green column under a trace at −45 means sellers still control, with their grip easing. When the market is unusually quiet the columns lose half their colour: a loud pane in a quiet market is drawn quiet.</p>
</section>

<section class="chap" id="chart"><div class="chapno">Chapter 4</div><h3>The price chart, labelled</h3>
<figure><div class="scroll">{plate_chart()}</div>
<figcaption><b>Plate 2 · On the price chart.</b> Numbers match the list below.</figcaption>
<ol class="callouts">
  <li><b>Accepted momentum trail.</b> The tested engine. Hue is its side, intensity its size, grey when flat. {M}</li>
  <li><b>Flat segment.</b> The trail's side and momentum disagree, so the position is zero.</li>
  <li><b>Value ribbon</b> (slate) with its dotted POC. Where 70% of the trail window's participation traded.</li>
  <li><b>Probe ×</b> (gold). The first close beyond the trail that the market did not accept.</li>
  <li><b>Session volume profile.</b> Rows by price: the POC row bright, value-area rows blue, tails grey. Session = day intraday, week on daily, month on weekly. {U}</li>
  <li><b>Level tags.</b> POC, VAH, VAL, VWAP (TWAP when volume is off), IBH and IBL intraday, prior-session levels.</li>
  <li><b>Session VWAP</b> (rose).</li>
  <li><b>Naked POC.</b> A prior session's POC that price has not traded back through since. Up to 5, up to 250 bars old.</li>
  <li><b>The readout.</b> Three rows (OI, CVG, AUCTION) and five columns (STATE, WHY, PUSH, CHART, SPAN). Chapter 7.</li>
</ol></figure>
</section>

<section class="chap" id="engines"><div class="chapno">Chapter 5</div><h3>The engines in plain words</h3>
<div class="cards">
  <div class="card"><h4>Conviction</h4><p>How much of the window's effort turned into net movement, weighted by participation (volume, or true range where there is none).</p><p class="where">Answers: who is in control? · Seen in: the Conviction trace, the conviction tape, the histogram.</p></div>
  <div class="card"><h4>Value (Samanvaya)</h4><p>Where price stands against fair value: a macro-hedged relative-value leg blended with a breadth leg, in σ. Past θ is cheap or rich.</p><p class="where">Answers: is the price stretched? · Seen in: the value tape, the Value trace.</p></div>
  <div class="card"><h4>The ladder</h4><p>Both readings across timeframes. Conviction on Ladder down reads the bars inside each chart bar. Value on Ladder up reads the chart and the frames above.</p><p class="where">Answers: is it true on every timeframe? · Seen in: the two tapes.</p></div>
  <div class="card"><h4>The Conviction-Value Grid</h4><p>The two tapes as a 3 × 3 map. Each cell is a family with an action and units, the weights Pragyam sizes from. {X}</p><p class="where">Answers: what should a portfolio hold? · Seen in: the CVG row, the ▲▼, the tint.</p></div>
  <div class="card"><h4>The auction</h4><p>A rolling volume profile of the chart's own bars: where participation was accepted, and whether value is migrating.</p><p class="where">Answers: where has the market agreed on price? · Seen in: the trail, the ribbon, the AUCTION row.</p></div>
  <div class="card"><h4>Accepted momentum</h4><p>The six-month acceptance trail sets the side; time-series momentum sets the size. Long only when both say up, short only when both say down. {M}</p><p class="where">Answers: should a trend book be long, flat or short? · Seen in: the trail's colour, the AUCTION row's CHART cell.</p></div>
  <div class="card"><h4>Open interest</h4><p>On futures: whether this bar's trading opened risk (builds) or closed it (covering, unwinding). {X}</p><p class="where">Answers: what kind of positioning? · Seen in: the OI row, the gold cast.</p></div>
  <div class="card"><h4>Session volume profile</h4><p>Where volume traded in the current session: POC, value area, VWAP, initial balance, naked POCs. {U}</p><p class="where">Answers: where are the reference levels? · Seen in: the right edge of the price chart.</p></div>
</div>
</section>
</section>

<section class="part" id="part-2"><div class="eyebrow">Part II</div><h2>Reading every state</h2>

<section class="chap" id="grid"><div class="chapno">Chapter 6</div><h3>The Conviction-Value Grid</h3>
<p>Rows come from the conviction tape: UP past the inner zone (+30), DOWN past −30, FAINT between. Columns come from the value tape: CHEAP past −θ, RICH past +θ, FAIR between. Each of the nine cells is a family named for what it says to do. The number is its units, the relative weight a portfolio gives the name.</p>
<figure><div class="scroll">{GRID}</div><figcaption><b>Plate 3 · The 3 × 3 map.</b> Green actions buy, red actions sell, grey change nothing. The word is the weight: Buy 4 is four times Wait 1. {X} The graded units were positive in all three eras outside crypto.</figcaption></figure>
<h4>Rows move only on a push</h4>
<p>A row changes only when conviction's own histogram confirms a push that way: on the move's side, not turning, not in a quiet regime. Without that push the row is <b>held</b> where it was, and WHY shows "held" in gold. This stops the grid flickering on every wobble of the tape.</p>
<h4>The 5 × 5: phases</h4>
<p>Each edge has a momentum that confirms it or not. Conviction confirms a row while buyers (or sellers) are <b>running</b>; it is <b>pausing</b> otherwise. Value confirms a cheap or rich column once it is <b>turning</b> back toward fair; it is <b>still cheapening</b> or <b>still richening</b> otherwise. An unconfirmed edge sits half-way to the middle, so its units fall. Inside a cell the units are also shaded by how strongly each tape is drawn.</p>
{tbl(["You see in WHY", "It means", "Effect on units"], [
 ["buyers running · sellers running", "Conviction momentum stands on the row's side", "The full row"],
 ["buyers pausing · sellers pausing", "A pullback against the row", "Half-way to the middle"],
 ["turning up (from cheap) · turning down (from rich)", "Value momentum reverting toward fair", "The full column. On DOWN · cheap this is the ▲'s condition"],
 ["still cheapening · still richening", "The dislocation is still widening", "Half-way to the middle"],
 ["no edge", "FAINT and FAIR: nothing to confirm", "Wait, 1 unit"],
 ["· held (gold)", "The tape left the row without a push that way", "Between half and all of the held row, by the push's strength"],
 ["· gate warming", "Conviction's histogram is still calibrating (about 450 bars)", "Rows follow the tape with no memory yet"],
])}
</section>

<section class="chap" id="readout"><div class="chapno">Chapter 7</div><h3>The readout table, cell by cell</h3>
<p>Five columns ask the same question on every row. STATE: where the layer stands. WHY: what makes it so. PUSH: what pushes it now. CHART: one more reading that differs by row. SPAN: how long it has stood, counting the current bar as the first. Hover any cell on TradingView for its tooltip.</p>
<h4>OI row (futures with open interest)</h4>
{tbl(["STATE", "Colour", "What happened this bar"], [
 ['<span class="chip c-bull">Long build-up</span>', "Green", "Price up, open interest up: new longs, risk committed"],
 ['<span class="chip c-bear">Short build-up</span>', "Red", "Price down, open interest up: new shorts, risk committed"],
 ['<span class="chip c-gold">Short covering</span>', "Gold", "Price up, open interest down: a rally paid for by exits. Short-covering rallies lagged " + X],
 ['<span class="chip c-gold">Long unwinding</span>', "Gold", "Price down, open interest down: a decline paid for by exits"],
 ['<span class="chip c-neut">Balanced</span>', "Grey", "The change is within 0.5σ of zero"],
 ['<span class="chip c-neut">Price flat</span>', "Grey", "The book moved past 0.5σ but the close did not, so there is no side"],
 ['<span class="chip c-gold">Expiry / roll</span>', "Gold", "Over 50% of the book in one bar, or over 3σ and 20%: structural, ignored"],
 ['<span class="chip c-gold">Warming</span> <span class="chip c-gold">Stale feed</span> <span class="chip c-gold">Daily only</span> <span class="chip c-gold">No symbol</span> <span class="chip c-gold">Paused</span>', "Gold", "Not enough history yet, an end-of-day feed, no OI at this timeframe, a chart modifier, or a non-standard chart"],
 ['<span class="chip c-neut">No OI</span>', "Grey", "The instrument has no open interest. Correct for cash equity and spot"],
])}
<p>WHY adds who is doing it and how full the book is: "book 85 pct" means total open interest sits at the 85th percentile of its last 250 bars. From the 80th it turns gold: a crowded book. PUSH is the change in σ. A faded row means the size of the book's change does not track activity (ρ below 0.20), so do not read it. <b>Expiry caution:</b> a front-month future's book falls into every expiry as positions roll, which can read as covering or unwinding. {U}</p>
<h4>CVG row</h4>
{tbl(["Cell", "Shows", "Example"], [
 ["STATE", "The family's action and its shaded units", '<span class="chip c-bull">Buy 3.42</span> <span class="chip c-bear">Exit 0.31</span>'],
 ["WHY", "Each momentum's phase on its edge (table above)", "sellers running · turning up"],
 ["PUSH", "Conviction's histogram: ↑↑ an impulse past k·σ, ↑ a push, turning (no push), quiet (gold, no push), and the mirrored ↓ ↓↓", "↑"],
 ["CHART", "Where this chart alone would put the name, against the ladder's state. ↑ more units, ↓ fewer, = same units elsewhere, same", "↑ Buy"],
 ["SPAN", "How long the name has stood in this family", "6d"],
])}
<h4>AUCTION row</h4>
{tbl(["Cell", "Shows", "States"], [
 ["STATE", "Value's migration against the window six months earlier", '<span class="chip c-bull">Migrating ↑</span> value areas no longer overlap · <span class="chip c-bull">Shifting ↑</span> only the POC has left · <span class="chip c-neut">Balance</span> · and the mirrored ↓ states'],
 ["WHY", "The trail's side and the close against value", 'trail ↑ · in value · <span class="chip c-gold">probe, not accepted</span> · accepted, flips at the close · push gate warming'],
 ["PUSH", "The histogram push the trail steps by", "↑ · turning"],
 ["CHART", "Accepted momentum's position and size", '<span class="chip c-bull">LONG 0.62</span> <span class="chip c-neut">FLAT · disagree</span> <span class="chip c-bear">SHORT 0.40</span>'],
 ["SPAN", "Bars since the trail started or flipped (the position can be younger)", "41d"],
])}
</section>

<section class="chap" id="panel"><div class="chapno">Chapter 8</div><h3>The information panel</h3>
<p>Off by default (setting 8). Turn it on for a diagnostic view at the right of the pane.</p>
{tbl(["Row", "Read it for"], [
 ["Header", "The trace's zone in words: buyers in control, STRETCHED UP, CHEAP · past θ, WARMING UP"],
 ["declaration", "The last ▲ or ▼ and how many bars ago. As a held position it carried no edge " + X + ". Paused with the reason, or off"],
 ["value · chart", "Samanvaya's value on this chart against θ. Gold while the macro basket settles"],
 ["MTF · conv · value", "The two tape readings. ↺ means the ladder fell back to the other direction"],
 ["MTF momentum", "Both momentum readings with their phase words"],
 ["impulse", "The histogram against k·σ, in native units"],
 ["trace", "The trace's ingredients: C and V in σ, ρ, split or settling"],
 ["raw share · σ", "The untransformed reading. QUIET (gold): small imbalances are being magnified"],
 ["participation", "What weighted the last closed bar, and by how much. At the cap: extreme participation"],
 ["effort → result", "How much effort became movement. ABSORBED (gold) in the bottom fifth"],
 ["macro share, overlap, rungs, driver timing, rebuild error", "Model diagnostics. Gold flags mean read the value side with care"],
 ["Profile Mode, Location", "What the session profile actually did, and where price sits in it"],
])}
</section>

<section class="chap" id="signals"><div class="chapno">Chapter 9</div><h3>Signals and marks</h3>
{tbl(["Mark", "Fires when", "Default", "Evidence"], [
 ['<span style="color:var(--bull)">▲</span> Capitulation turn', "The first closed bar in DOWN · cheap with value momentum reverting. Not on a grid that wakes up already inside the cell", "On", X + " Positive in all three eras, daily and weekly, in 4 to 5 of 5 non-crypto classes. About +0.05σ over 10 to 20 bars: a lean, not a trade. Fails on crypto"],
 ['<span style="color:var(--bear)">▼</span> Distribution', "The first closed bar on which sellers control a price rich past θ", "On", X + " As a state, followed by underperformance in every era"],
 ["◆ Continuation", "A pullback that reset value, then a push past +k·σ", "Off", X + " Negative in both eras. Do not lean on it"],
 ["R · H divergence", "Price and conviction disagree at pivots", "Off", X + " R about zero; H negative or mixed"],
 ['<span style="color:var(--gold)">×</span> Probe', "The first close beyond the trail the market has not accepted", "On", U],
 ["Background tint", "While the grid holds capitulation (green) or distribution (red)", "Grid state", X + " The state carried the edge"],
 ["Gold cast", "The push was paid for by exits (open interest)", "On", X + " Marked pushes did worse"],
])}
<div class="note rule">Every signal fires at the close of its bar and never repaints. Intrabar, the readout is live and can change until the close.</div>
</section>
</section>

<section class="part" id="part-3"><div class="eyebrow">Part III</div><h2>Investment guide · weeks to months</h2>

<section class="chap" id="inv-frame"><div class="chapno">Chapter 10</div><h3>The investor's frame</h3>
<p>For investing, the grid is the tool. Each name in your universe sits in one family, and its units say how much weight it deserves relative to the others. You hold everything you would hold anyway, more of what is cheap with sellers exhausted, and less of what is rich with sellers in control. Units are relative weights for a book of many names, not a buy-or-sell switch for one.</p>
<div class="note">Evidence {X}: the graded units were positive in all three eras outside crypto. In Pragyam's allocator the units beat its seed weights in both eras on the Nifty 50 and the Dow 30.</div>
<div class="flow"><div><b>Daily chart</b>Conviction on Ladder down, value on Ladder up: exactly what Pragyam sizes from.</div><div class="arrow" aria-hidden="true">→</div><div><b>Read at the week's last close</b>One reading per name: the CVG row's STATE.</div><div class="arrow" aria-hidden="true">→</div><div><b>Units to weights</b>Weight = units ÷ sum of units across the book.</div><div class="arrow" aria-hidden="true">→</div><div><b>Rebalance with a band</b>Trade only where a weight moved by more than a tenth of its target.</div></div>
</section>

<section class="chap" id="inv-families"><div class="chapno">Chapter 11</div><h3>Nine families, nine actions</h3>
{tbl(["Family", "Condition", "Action · units", "Typical next family", "What it says"], [
 ['<span class="chip c-bull">DISLOCATED</span>', "Sellers in control, price cheap", "Buy · 4", "BASING, FADING, TURNED", "The capitulation cell. The strongest measured lean. Stage in; add on the ▲"],
 ['<span class="chip c-bull">TURNED</span>', "Buyers in control, price cheap", "Buy · 3", "BUILDING", "A turn while still cheap. Buy"],
 ['<span class="chip c-bull">BASING</span>', "Nobody in control, cheap", "Accumulate · 1.5", "TURNED, DISLOCATED", "Accumulate slowly"],
 ['<span class="chip c-bull">FADING</span>', "Sellers in control, fair price", "Accumulate · 1.5", "DISLOCATED, IDLE", "Sellers at a fair price were followed by gains (v8, outside crypto) " + X],
 ['<span class="chip c-neut">BUILDING</span>', "Buyers in control, fair price", "Hold · 1.5", "PAID, IDLE", "Hold. Buyers at a fair price lagged (v8), so do not add"],
 ['<span class="chip c-neut">IDLE</span>', "Nobody in control, fair", "Wait · 1", "anything", "Do nothing"],
 ['<span class="chip c-bear">PAID</span>', "Buyers in control, rich", "Trim · 0.75", "STALLING, DISTRIBUTION", "The move is paid for. Trim"],
 ['<span class="chip c-bear">STALLING</span>', "Nobody in control, rich", "Trim · 0.75", "DISTRIBUTION, IDLE", "Trim"],
 ['<span class="chip c-bear">DISTRIBUTION</span>', "Sellers in control, rich", "Exit · 0.25", "FADING, STALLING", "Exit toward a token weight. The ▼ marks the entry"],
])}
</section>

<section class="chap" id="inv-cap"><div class="chapno">Chapter 12</div><h3>The capitulation plan</h3>
<p>The one event the v9 audit found positive in every era is the capitulation turn. This is a staged plan around it. The staging itself is a house rule {U}; the state and the turn are {X}.</p>
<div class="flow">
 <div><b>1 · Enter DOWN · cheap</b>The green tint appears; STATE reads Buy 4. Buy the first third.</div><div class="arrow" aria-hidden="true">→</div>
 <div><b>2 · ▲ fires</b>Value momentum turns back toward fair; the tint deepens. Buy the second third.</div><div class="arrow" aria-hidden="true">→</div>
 <div><b>3 · Leaves the cell</b>BASING or FADING (Accumulate 1.5), or TURNED (Buy 3). Buy the last third on the next push ↑.</div><div class="arrow" aria-hidden="true">→</div>
 <div><b>4 · BUILDING</b>Hold 1.5. Let the position run.</div><div class="arrow" aria-hidden="true">→</div>
 <div><b>5 · PAID or STALLING</b>Trim 0.75.</div><div class="arrow" aria-hidden="true">→</div>
 <div><b>6 · ▼ DISTRIBUTION</b>Exit toward 0.25.</div>
</div>
<h4>When the plan is wrong</h4>
<ul>
 <li><b>Crypto.</b> The capitulation reading failed there. The tint and the ▲ are drawn gold. Skip the plan.</li>
 <li><b>Gold readings.</b> A held row, a quiet regime, "basket settling", or a paused grid. Wait for them to clear before adding.</li>
 <li><b>A trend against you.</b> If Accepted momentum is SHORT, the long-horizon trend still points down. Keep each tranche small (Chapter 19).</li>
</ul>
</section>

<section class="chap" id="inv-book"><div class="chapno">Chapter 13</div><h3>Building the book: a worked example</h3>
<p>Six names, read at the week's close. Weights are units divided by their sum.</p>
{tbl(["Name", "CVG STATE", "Units", "Weight"], [
 ["A", '<span class="chip c-bull">Buy 3.6</span> · DISLOCATED', '<span class="num">3.6</span>', '<span class="num">32.4%</span>'],
 ["B", '<span class="chip c-bull">Buy 2.8</span> · TURNED', '<span class="num">2.8</span>', '<span class="num">25.2%</span>'],
 ["C", '<span class="chip c-neut">Hold 1.5</span> · BUILDING', '<span class="num">1.5</span>', '<span class="num">13.5%</span>'],
 ["D", '<span class="chip c-bull">Accumulate 1.4</span> · BASING', '<span class="num">1.4</span>', '<span class="num">12.6%</span>'],
 ["E", '<span class="chip c-neut">Wait 1.0</span> · IDLE', '<span class="num">1.0</span>', '<span class="num">9.0%</span>'],
 ["F", '<span class="chip c-bear">Trim 0.8</span> · PAID', '<span class="num">0.8</span>', '<span class="num">7.2%</span>'],
 ["Total", "", '<span class="num">11.1</span>', '<span class="num">100% (rounded)</span>'],
])}
<p>With a small book, one name can grow large. A practical cap of about a tenth of the book per name keeps the plan diversified {U}. The more names, the closer you get to how the units were measured.</p>
</section>

<section class="chap" id="inv-risk"><div class="chapno">Chapter 14</div><h3>Investor risk</h3>
<ul>
 <li><b>Trend filters trade return for drawdown.</b> On 119 markets, holding only while the trail was up cut the worst drawdown from −73.5% to −35%, but gave up about 11 points of yearly growth (13.5% against 24.4%) {M}. Use Accepted momentum as an investor's filter only if a shallower drawdown matters more to you than return.</li>
 <li><b>The ▲ is a lean.</b> About +0.05σ over 10 to 20 bars. It pays across many names and many events, not on any one {X}.</li>
 <li><b>Gold is caution.</b> Reduce or wait; never read gold as a direction.</li>
</ul>
</section>
</section>

<section class="part" id="part-4"><div class="eyebrow">Part IV</div><h2>Trade guide · systematic and swing</h2>

<section class="chap" id="am"><div class="chapno">Chapter 15</div><h3>Accepted momentum, the tested system</h3>
<p>This is the one trade system in Pragati that passed a held-out test {M}. It was chosen by a fixed rule from eleven trials on data up to 2019, frozen, and then run once on 2020-26 and on 411 markets it had never seen.</p>
<figure><div class="scroll">{plate_am()}</div><figcaption><b>Plate 4 · How the position is decided.</b> The trail's side and momentum's direction must agree.</figcaption></figure>
{tbl(["Rule", "Exactly"], [
 ["Side", "The acceptance trail on a 126-bar (six-month) window: up while value has migrated and ratcheted up, down while it has migrated down"],
 ["Momentum score S", "The 1-, 3-, 6- and 12-month moves of the close (21, 63, 126, 252 bars), each divided by volatility × √horizon, capped at ±2, averaged and halved, so S lies between −1 and +1"],
 ["Position", "Side × max(0, side × S): LONG with size S when both say up, SHORT with size |S| when both say down, FLAT when they disagree"],
 ["Decide and trade", "Read at the close; trade at the next open. Never on the forming bar"],
 ["Size", "Weight = size × 10% ÷ annualised volatility, capped at 2 (two times the market's capital slice)"],
 ["Rebalance", "Weekly. Skip a resize smaller than a tenth of the target. Change sides at once"],
])}
<h4>Worked sizing example</h4>
<div class="math">Book ₹10,00,000 across 20 markets  →  slice per market ₹50,000
Stock X: readout says LONG 0.62; annualised volatility 28%
weight   = 0.62 × 10% ÷ 28%                  = 0.221
notional = 0.221 × ₹50,000                    = ₹11,071
price ₹2,500  →  buy 4 shares (₹10,000), the nearest whole lot
Cap: weight never above 2.0 (notional ₹1,00,000 for this slice)</div>
</section>

<section class="chap" id="am-book"><div class="chapno">Chapter 16</div><h3>Running it as a portfolio</h3>
{tbl(["Holdout", "Sharpe, net of costs", "Timing beyond leaning long", "Worst drawdown", "Markets positive"], [
 ["411 unseen markets", '<span class="num">+0.79 (t 4.0)</span>', '<span class="num">t 4.1</span>', '<span class="num">−3.7%</span>', '<span class="num">79%</span>'],
 ["119 markets, 2020-26", '<span class="num">+1.21 (t 3.7)</span>', '<span class="num">t 2.2</span>', '<span class="num">−2.5%</span>', '<span class="num">80%</span>'],
])}
<ul>
 <li><b>The edge is a portfolio's.</b> On one market the median Sharpe was only +0.23 to +0.38, and about a quarter of markets lost money over the period. Run the same rules on many markets at once.</li>
 <li><b>It did not beat plain momentum</b> by the pre-registered test. It matched it at lower turnover and drawdown.</li>
 <li><b>Costs.</b> At twice the assumed costs the Sharpe was still +0.69 and +1.11.</li>
 <li><b>Risk level.</b> At 10% per market the diversified book ran at about 1.6% volatility. Reaching a useful risk level needs futures-style leverage; shorting Indian cash stocks overnight needs stock or index futures.</li>
 <li><b>Where it was weak.</b> The INR currency pairs lost; crypto was about flat (Chapter 22).</li>
</ul>
<div class="note"><b>Before capital:</b> six months of paper trading at the same costs, then one-tenth of the intended size for six months. Stop if the drawdown exceeds 1.5 times the backtest's worst, or if the rolling 12-month Sharpe stays below zero for two quarters.</div>
</section>

<section class="chap" id="overlay"><div class="chapno">Chapter 17</div><h3>Discretionary overlays</h3>
<p>These add context to a trade. None of them was tested as a rule {U}. Use them to adjust timing or size within the system's rules, not to replace them.</p>
{tbl(["Overlay", "Use it to", "Caution"], [
 ["Grid family", "Avoid adding to a long in PAID, STALLING or DISTRIBUTION; prefer adds in BASING or FADING", "The grid is an investor's horizon"],
 ["▲ during an AM short", "Tighten or reduce the short: capitulation leans up for 10 to 20 bars", "The system stays short by rule"],
 ["OI character", "A breakout on long build-up is committed; one on short covering is fragile", "Builds did not predict continuation " + X],
 ["AUCTION probe", "A probe against your side is a warning, not an exit: the break is not accepted yet", "Accepted breaks flip the trail at the close"],
 ["Migration", "Migrating with your side supports holding; Shifting against it is an early warning", "Unmeasured"],
 ["Quiet regime (gold)", "Expect amplified readings; size down", "A display state, not a direction"],
])}
</section>

<section class="chap" id="stops"><div class="chapno">Chapter 18</div><h3>Stops, targets and invalidation</h3>
<p>The system exits by its own rules. For a discretionary trader, Pragati's structure gives natural levels {U}.</p>
{tbl(["Level", "Long trade", "Short trade"], [
 ["The trail", "The floor of accepted value. A close below it with the POC following and value migrating flips the trail", "The ceiling, mirrored"],
 ["VAL / VAH", "Initial stop below the session VAL", "Initial stop above the session VAH"],
 ["POC", "First target from below value; the balance point", "First target from above value"],
 ["Naked POC", "An unfinished level above: a target", "An unfinished level below: a target"],
 ["Prior session VAH / VAL", "Acceptance above the prior VAH supports the trade", "Acceptance below the prior VAL supports it"],
 ["VWAP", "Holding above the session VWAP intraday", "Holding below it"],
])}
</section>
</section>

<section class="part" id="part-5"><div class="eyebrow">Part V</div><h2>Permutations and combinations</h2>

<section class="chap" id="mx-a"><div class="chapno">Chapter 19</div><h3>Matrix A · The system against the grid: 27 cases</h3>
<p>Rows are the nine grid families; columns are Accepted momentum's three positions. In each case, TRADE follows the tested system {M} and INVEST follows the family's action {X}. The combined reading is reasoning {U}. When they conflict, each book follows its own tool (Chapter 23).</p>
{matrix_a()}
</section>

<section class="chap" id="mx-b"><div class="chapno">Chapter 20</div><h3>Matrix B · Open interest against location in value</h3>
<p>The OI row's character, read against where the close sits in the session profile (the panel's Location row, or the price against VAH and VAL). Practitioner readings {U}, except where tagged.</p>
{tbl(["OI character", "Above value", "In value", "Below value"], [
 ['<span class="chip c-bull">Long build-up</span>', "New longs pushing for acceptance higher. Watch for the trail to accept", "New longs inside balance", "Longs adding below value: bottom-fishing with commitment"],
 ['<span class="chip c-bear">Short build-up</span>', "Shorts leaning against a breakout", "New shorts inside balance", "A breakdown with commitment"],
 ['<span class="chip c-gold">Short covering</span>', "A rally paid for by exits beyond value: fragile. Short-covering rallies lagged " + X, "Covering inside balance", "A relief bounce from below value"],
 ['<span class="chip c-gold">Long unwinding</span>', "Longs leaving up high: a distribution risk", "Liquidation inside balance", "Liquidation below value: fuel for a capitulation"],
 ['<span class="chip c-neut">Balanced · Price flat</span>', "No read", "No read", "No read"],
])}
</section>

<section class="chap" id="mx-c"><div class="chapno">Chapter 21</div><h3>Matrix C · Trail side against migration</h3>
{tbl(["Migration (AUCTION STATE)", "Trail ↑", "Trail ↓"], [
 ['<span class="chip c-bull">Migrating ↑</span>', "Value moving with the trail. Steps are likely", "Value has left upward. A close above with the POC following flips the trail up"],
 ['<span class="chip c-bull">Shifting ↑</span>', "The POC has left the old value upward. Supportive", "An early warning for the down trail"],
 ['<span class="chip c-neut">Balance</span>', "Value has not moved. The trail holds flat", "The trail holds flat"],
 ['<span class="chip c-bear">Shifting ↓</span>', "An early warning for the up trail", "The POC has left downward. Supportive"],
 ['<span class="chip c-bear">Migrating ↓</span>', "Value has left downward. A close below with the POC following flips the trail down", "Value moving with the trail. Steps are likely"],
])}
<p>Add the WHY cell: a <span class="chip c-gold">probe</span> is a break without acceptance and often fails back; "accepted, flips at the close" means all three conditions hold on the live bar. Unmeasured {U}.</p>
</section>

<section class="chap" id="mx-d"><div class="chapno">Chapter 22</div><h3>Matrix D · Asset class against evidence</h3>
{tbl(["Asset class", "▲ and grid units " + X, "Accepted momentum, Sharpe by class " + M, "Open interest"], [
 ["NSE stocks", "Positive, all eras", '<span class="num">+1.02</span> (2020-26) · <span class="num">+0.84</span> (unseen)', "Measured on NSE F&amp;O " + X],
 ["Indices", "Positive, all eras", '<span class="num">+0.98</span> (2020-26)', "On index futures"],
 ["ETFs", "Positive, all eras", '<span class="num">+1.18</span> (2020-26)', "None"],
 ["Commodities", "Positive, all eras", '<span class="num">+0.47</span> (2020-26)', "On futures"],
 ["FX", "Positive, all eras", '<span class="num">−0.17</span> (INR pairs, 2020-26)', "None on spot"],
 ["Crypto", "<b>Fails</b>: drawn gold", '<span class="num">+0.29</span> (2020-26) · <span class="num">−0.04</span> (unseen)', "On perpetuals"],
])}
<p>US stocks and world indices were not in the Accepted momentum test.</p>
</section>

<section class="chap" id="conflict"><div class="chapno">Chapter 23</div><h3>When readings disagree</h3>
<div class="steps">
 <div class="step"><div><b>Data first.</b><p>Non-standard chart, warming, paused, stale or gold: there is no reading. Do nothing new.</p></div></div>
 <div class="step"><div><b>The horizon chooses the tool.</b><p>A trading book follows Accepted momentum. An investment book follows the grid's units. Do not let one book borrow the other's signal.</p></div></div>
 <div class="step"><div><b>Gold reduces size; it never sets direction.</b><p>Held rows, probes, quiet regimes, crowded books and short covering all mean the same thing: smaller, or later.</p></div></div>
 <div class="step"><div><b>Do not trade the untested parts.</b><p>The 20-bar trail, the ◆, R and H measured null or negative as signals. Read them as structure.</p></div></div>
 <div class="step"><div><b>Crypto is the exception.</b><p>Skip the capitulation plan there.</p></div></div>
</div>
</section>
</section>

<section class="part" id="part-6"><div class="eyebrow">Part VI</div><h2>Reference</h2>

<section class="chap" id="alerts"><div class="chapno">Chapter 24</div><h3>Alerts</h3>
{tbl(["Alert", "How", "Carries"], [
 ["Everything, once", 'Create an alert on Pragati with the condition "Any alert() function call"', "▲, ▼, capitulation entered and left (setting 2), Accepted momentum's position changes or trail flips (setting 5, off by default), with ticker, interval, grid action and both tapes"],
 ["One event", "Choose a single alertcondition entry", "▲ capitulation turn · ▼ distribution · ◆ long / short · R and H divergences"],
])}
<p>Alerts fire once, at the bar's close, in realtime only.</p>
</section>

<section class="chap" id="settings"><div class="chapno">Chapter 25</div><h3>Settings reference</h3>
{tbl(["Group", "Setting", "Default", "Change it when"], [
 ["1 · View", "View · Palette · Pane background", "Full · Auto · Grid state", "Core for the pane alone; Declaration to tint the last ▲▼"],
 ["2 · Signals", "▲▼ · cooldown · capitulation alerts · ◆", "On · 10 bars · On · Off", "Rarely. The ◆ is off for a measured reason"],
 ["3 · Trace and tapes", "Trace · conviction ladder · value ladder · momentum drawing", "Conviction × Value · Ladder down · Ladder up · Separate band", "Amalgamated folds momentum into each tape: TALL means a confirmed edge"],
 ["4 · Pane display", "Histogram, gain, shading, quiet desaturation, trace intensity", "On, 2.0, Expansion + slope, On, On", "Display only"],
 ["5 · Acceptance trail", "Trail · Accepted momentum · ribbon · probes · alerts", "On · On · On · On · Off", "Turn Accepted momentum off for the structural 20-bar trail"],
 ["6 · Readout", "Position · OI row · gold cast · CVG row · AUCTION row", "Bottom left · On · On · On · On", "Move it if the profile is off"],
 ["7 · Volume profile", "Master · intrabar · volume · bins · value area · layers", "On · On · On · ATR, 4 per ATR · 70%", "Fixed ticks for tick-based levels"],
 ["8 · Panel", "Information panel · detail", "Off · Detailed", "On to diagnose a reading"],
 ["9 · Conviction engine", "Lookback · smoothing · signal · k · normalization · participation · zones", "20 · 3 · 9 · 0.5 · 200 · Auto · ±30 / ±60", "Avoid. Every number was measured at these values"],
 ["10 · Value model", "Macro hedge · clock · leg mix · θ", "Auto · Daily · 0.5 · 1.5", "Weekly clock on daily-and-above charts"],
 ["11 · Divergence", "R · H and their pivots", "Off", "Only to see them; they measured null"],
])}
</section>

<section class="chap" id="evidence"><div class="chapno">Chapter 26</div><h3>What is measured, and what is not</h3>
{tbl(["Component", "Grade", "Result"], [
 ["Accepted momentum", M, "Holdout Sharpe +0.79 (411 unseen markets) and +1.21 (2020-26), net of costs; timing t 4.1 and 2.2; did not beat plain momentum"],
 ["20-bar acceptance trail as a trade", M, "No timing skill: what it earned was drift. Structure only"],
 ["Trend filter for investing", M, "Drawdown −35% against −73.5%, growth 13.5% against 24.4% a year"],
 ["▲ capitulation turn and state", X, "Positive in all three eras, daily and weekly, outside crypto; about +0.05σ over 10 to 20 bars"],
 ["▼ distribution state", X, "Followed by underperformance in every era"],
 ["Grid units", X, "Positive in all three eras outside crypto"],
 ["Declaration (held ▲▼)", X, "No edge"],
 ["◆, R, H", X, "Negative, about zero, negative or mixed"],
 ["Open interest", X, "Short-covering rallies lagged; builds did not predict continuation"],
 ["Volume profile, migration, probes, HVN / LVN, VWAP, IB", U, "Reference structure"],
 ["Every combination in Part V", U, "Reasoning from the measured parts"],
])}
<p>Known limits: the Accepted momentum test is mostly Indian markets plus crypto, and its NSE stocks are today's listings (survivorship). The v9 audit's figures come from a separate repository.</p>
</section>

<section class="chap" id="glossary"><div class="chapno">Chapter 27</div><h3>Glossary</h3>
{tbl(["Term", "Meaning"], [
 ["Acceptance", "A close beyond the trail with the window's POC beyond it and value migrated that way. Only acceptance flips the trail"],
 ["Capitulation", "Sellers in control across the ladder at a price cheap past θ: the DOWN · cheap cell"],
 ["Conviction", "The share of the window's participation-weighted effort that became net movement"],
 ["Family", "One of the grid's nine cells, named for its action"],
 ["Held", "A grid row kept in place because no push confirmed the tape's move"],
 ["Impulse", "A histogram column past k standard deviations of its history (↑↑)"],
 ["Ladder down / up", "Reading the timeframes below the chart (inside each bar) or above it"],
 ["Migration", "This window's value area against the one six months earlier: Migrating (no overlap), Shifting (only the POC left), Balance"],
 ["Naked POC", "A prior session's POC that price has not traded back through"],
 ["POC · VAH · VAL", "The most-traded price; the top and bottom of the 70% value area"],
 ["Probe", "A close beyond the trail without acceptance"],
 ["Push gate", "Conviction's histogram on the move's side, not turning, not quiet"],
 ["Quiet regime", "Raw volatility in the bottom fifth of its history: readings are magnified"],
 ["S", "Accepted momentum's score, −1 to +1, from the 1-, 3-, 6- and 12-month moves"],
 ["Sharpe", "Return per unit of volatility, yearly. t is how far from zero it is, in standard errors"],
 ["θ (theta)", "Samanvaya's value threshold, ±43 on the pane at the default 1.5"],
 ["Units", "The relative weight a family gives a name in a portfolio"],
])}
</section>

<section class="chap" id="card"><div class="chapno">Chapter 28</div><h3>Quick card</h3>
<div class="quick">
 <div class="card"><h4>Every close</h4><ul><li>Gold anywhere? Smaller, or later.</li><li>Trader: read the AUCTION row's CHART cell; act at the next open.</li><li>Investor: read the CVG row's STATE at the week's last close.</li></ul></div>
 <div class="card"><h4>Investor</h4><ul><li>Weight = units ÷ total units.</li><li>Stage into DOWN · cheap; add on the ▲.</li><li>Trim in PAID and STALLING; exit in DISTRIBUTION.</li><li>Not on crypto.</li></ul></div>
 <div class="card"><h4>Trader</h4><ul><li>LONG or SHORT only when trail and momentum agree.</li><li>Weight = size × 10% ÷ volatility, cap 2.</li><li>Many markets, weekly rebalance.</li><li>Paper first, then a tenth.</li></ul></div>
 <div class="card"><h4>Never</h4><ul><li>Trade the forming bar.</li><li>Read gold as a direction.</li><li>Lean on the ◆, R, H or the 20-bar trail.</li><li>Use non-standard candles.</li></ul></div>
</div>
<p class="disclaimer">This manual is educational. It describes how an indicator works and how it was tested; it is not investment advice. Past results, including held-out tests, do not guarantee future results. Trade only what you can afford to lose, and paper-trade first.</p>
</section>
</section>

</main></div>
"""
    return html

if __name__ == "__main__":
    out = sys.argv[1]
    h = build()
    open(out, "w", encoding="utf-8").write(h)
    print(len(h), "bytes")
