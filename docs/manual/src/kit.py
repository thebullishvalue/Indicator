"""Building blocks for Manual 2.0's new chapters, in the 1.x markup (build.py's CSS and book.py's print CSS)."""
import re

M = '<span class="ev ev-m">Measured</span>'
X = '<span class="ev ev-x">External</span>'
U = '<span class="ev ev-u">Unmeasured</span>'


def sec(sid, title, body):
    """A section, in the form build.structure() numbers."""
    return f'<section class="chap" id="{sid}"><div class="chead"><div class="chapno">Chapter ⟦#⟧</div><h3>{title}</h3></div>\n{body}\n</section>\n'


def tbl(head, rows, title=None, widths=None, cls=""):
    """A numbered, titled table; widths in percent, summing to 100."""
    if widths:
        assert len(widths) == len(head) and abs(sum(widths) - 100) < 1e-6, (title, widths)
        cg = "<colgroup>" + "".join(f'<col style="width:{x}%">' for x in widths) + "</colgroup>"
    else:
        cg = ""
    cap = f'<div class="tcap"><b>⟦tcap⟧</b> {title}</div>' if title else ""
    h = "".join(f"<th>{c}</th>" for c in head)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    wide = " wide" if len(head) >= 5 else ""
    return cap + f'<div class="tbl{wide} {cls}"><table>{cg}<thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>'


def chip(text, tone="neut"):
    return f'<span class="chip c-{tone}">{text}</span>'


def k(text):
    return f'<span class="k">{text}</span>'


def note(html, rule=False):
    return f'<div class="note{" rule" if rule else ""}">{html}</div>'


def steps(items):
    return '<div class="steps">' + "".join(f'<div class="step"><div><b>{a}</b><p>{b}</p></div></div>' for a, b in items) + "</div>"


def flow(items):
    """A left-to-right sequence of boxes."""
    parts = []
    for i, (a, b) in enumerate(items):
        if i:
            parts.append('<div class="arrow">→</div>')
        parts.append(f'<div><b>{a}</b><span class="fx">{b}</span></div>')
    return '<div class="flow">' + "".join(parts) + "</div>"


def cards(items):
    return '<div class="cards">' + "".join(f'<div class="card"><h4>{a}</h4>{b}</div>' for a, b in items) + "</div>"


def math(text):
    return f'<div class="math">{text}</div>'


def objectives(items):
    return '<div class="obj"><b>After this chapter you can</b><ul>' + "".join(f"<li>{x}</li>" for x in items) + "</ul></div>"


def setup_card(code, name, evidence, verdict, fields):
    """fields: [(label, html)]"""
    head = f'<div class="sh"><span class="code">{code}</span><b>{name}</b>{evidence}{(" " + chip(verdict, "neut")) if verdict else ""}</div>'
    body = "".join(f"<dt>{a}</dt><dd>{b}</dd>" for a, b in fields)
    return f'<div class="setup">{head}<dl>{body}</dl></div>'


def checklist(items):
    return '<ul class="check">' + "".join(f"<li>{x}</li>" for x in items) + "</ul>"


def drill(no, question, body=""):
    return f'<div class="drill"><div class="dq"><span class="dn">{no}</span>{question}</div>{body}</div>'


def fig(key, svg, caption):
    return f'<figure><div class="scroll">{svg}</div><figcaption><b>⟦figcap:{key}⟧</b> {caption}</figcaption></figure>'


def plain(h):
    return re.sub(r"<[^>]+>", "", h)


EXTRA_CSS = r"""
.obj{border:1px solid var(--line);border-left:3px solid var(--accent);background:var(--surface);border-radius:0 6px 6px 0;padding:10px 14px 4px;margin:4px 0 18px;font-size:14.5px}
.obj>b{font-family:var(--display);font-stretch:88%;font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:var(--accent)}
.obj ul{margin:6px 0 6px;padding-left:20px}
.setup{border:1px solid var(--line);background:var(--surface);border-radius:6px;margin:16px 0;overflow:hidden}
.setup .sh{display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:9px 14px;border-bottom:1px solid var(--line);background:var(--tint-neut)}
.setup .sh b{font-family:var(--display);font-stretch:88%;font-size:17px}
.setup .code{font-family:var(--mono);font-size:12.5px;color:var(--accent);font-weight:600}
.setup dl{display:grid;grid-template-columns:150px minmax(0,1fr);margin:0}
.setup dt{font-weight:600;font-size:13.5px;padding:7px 14px;border-top:1px solid var(--line);color:var(--muted)}
.setup dd{margin:0;padding:7px 14px 7px 0;border-top:1px solid var(--line);font-size:14.5px}
.setup dt:first-of-type,.setup dd:first-of-type{border-top:none}
@media (max-width:560px){.setup dl{grid-template-columns:1fr}.setup dt{padding-bottom:0}.setup dd{padding:2px 14px 8px;border-top:none}}
ul.check{list-style:none;padding-left:0;margin:10px 0}
ul.check li{position:relative;padding:4px 0 4px 28px;border-bottom:1px solid var(--line)}
ul.check li::before{content:"";position:absolute;left:4px;top:8px;width:13px;height:13px;border:1.5px solid var(--muted);border-radius:2px}
.drill{border:1px solid var(--line);background:var(--surface);border-radius:6px;padding:10px 14px;margin:12px 0}
.drill .dq{font-weight:600}
.drill .dn{display:inline-block;min-width:30px;font-family:var(--mono);color:var(--accent)}
.drill .ro{font-family:var(--mono);font-size:13px;background:var(--bg);border:1px solid var(--line);border-radius:4px;padding:8px 10px;margin:8px 0 2px;white-space:pre-wrap}
.ans{border-left:3px solid var(--accent);padding:2px 0 2px 12px;margin:10px 0}
.ans b.an{font-family:var(--mono);color:var(--accent);margin-right:6px}
.kv{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:8px;margin:12px 0}
.tbl.wide table{min-width:720px}
td{overflow-wrap:normal}
.kv>div{border:1px solid var(--line);background:var(--surface);border-radius:6px;padding:8px 10px}
.kv b{display:block;font-family:var(--mono);font-size:12px;color:var(--muted);font-weight:400}
.kv span{font-family:var(--mono);font-size:15px}
"""

PRINT_CSS = r"""
.obj{font-family:var(--body);font-size:8.8pt;line-height:1.45;padding:6pt 9pt 3pt;margin:0 0 12pt;border-radius:0;border:none;border-left:2pt solid var(--accent);background:var(--tint-neut);break-inside:avoid}
.obj>b{font-size:7.6pt}
.obj ul{margin:3pt 0;padding-left:12pt}
.obj li{text-align:left;margin:0 0 1pt}
.setup{border:none;border-top:1pt solid var(--ink);border-bottom:.6pt solid var(--ink);border-radius:0;background:none;margin:12pt 0;break-inside:avoid}
.setup .sh{background:none;border-bottom:.6pt solid var(--ink);padding:4pt 0}
.setup .sh b{font-size:11pt}
.setup .code{font-size:8pt}
.setup dl{grid-template-columns:28mm minmax(0,1fr)}
.setup dt{font-family:var(--body);font-size:8pt;padding:3.5pt 0;border-top:.3pt solid var(--line)}
.setup dd{font-family:var(--body);font-size:8.6pt;line-height:1.42;padding:3.5pt 0 3.5pt 4pt;border-top:.3pt solid var(--line);text-align:left}
ul.check{font-family:var(--body);font-size:9pt;padding-left:0!important}
ul.check li{padding:2.5pt 0 2.5pt 16pt;text-align:left;border-bottom:.3pt solid var(--line)}
ul.check li::before{top:4.5pt;left:2pt;width:8pt;height:8pt;border-width:.8pt}
.drill{border:none;border-top:.5pt solid var(--line);border-radius:0;background:none;padding:5pt 0;margin:0;break-inside:avoid}
.drill .dq{font-family:var(--body);font-size:9.2pt}
.drill .dn{min-width:20pt;font-size:8.4pt}
.drill .ro{font-size:7.4pt;line-height:1.4;padding:5pt 7pt;border-radius:0;background:var(--tint-neut);border:none}
.drill p{text-align:left}
.ans{border-left:1.5pt solid var(--accent);padding:1pt 0 1pt 8pt;margin:6pt 0;break-inside:avoid}
.ans p{text-align:left;text-indent:0!important}
.kv{grid-template-columns:repeat(3,minmax(0,1fr));gap:4pt;margin:8pt 0}
.kv>div{border:none;border-top:.5pt solid var(--line);border-radius:0;background:none;padding:3pt 0}
.kv b{font-size:7pt}.kv span{font-size:9pt}
"""
