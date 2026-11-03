"""Part I additions (the thesis, the mastery path), Part IX's decision tree, Part X · Mastery, and Part XI's
generated settings reference and setup-lab evidence."""
import os
import re
from kit import M, X, U, sec, tbl, chip, k, note, steps, flow, objectives, checklist, drill, cards

S = {}

S["thesis"] = sec("thesis", "The one question", objectives([
    "say in one sentence what Pragati measures, and in one more what it does not claim",
]) + f"""
<p><b>"Is this move paid for, and is it paid for on every timeframe?"</b> Everything in Pragati is a way of asking that question, and each engine asks a different part of it:</p>
{cards([
    ("Paid for in effort", "<p>Conviction: how much of the bars' travel became displacement, and how consistently, weighted by participation. A move that went far on little agreement is not paid for.</p>"),
    ("Paid for in price", "<p>Value: where price stands against a model of fair. A move that has already carried price rich is paid for in the other sense: it is late.</p>"),
    ("Paid for in acceptance", "<p>The auction: whether the market's value has followed price. A break that value has not followed is a probe.</p>"),
    ("On every timeframe", "<p>The ladder reads conviction from inside the bar and value from above it, so one chart answers on three horizons.</p>"),
])}
<p><b>What it does not claim.</b> Most of what Pragati draws <i>describes</i>. Measured without look-ahead, the pane's readings carry almost no timing information of their own {X}. Three things here carry measured leans:
<ul>
<li>the grid's capitulation state and the ▲ that marks its turn {X};</li>
<li>the grid's graded units across a book {X};</li>
<li>Accepted momentum, across many markets {M}.</li>
</ul>
The setup lab adds measured facts about breaks: what a probe does to a trend, and what gets accepted {M}. Everything else is structure for reading, tagged {U}.</p>
<p><b>Design rules you will meet everywhere:</b>
<ul>
<li>Gold means caution, never direction.</li>
<li>Nothing pauses silently.</li>
<li>Nothing that fires repaints.</li>
<li>Every claim carries its evidence.</li>
</ul></p>
""")

S["path"] = sec("path", "The mastery path", objectives([
    "plan how to work through this book",
]) + tbl(["Level", "You can", "Read", "Practise"], [
    ["1 · Reader", "Name every mark and cell on the chart", "Parts I and III", "Drills 1–8"],
    ["2 · Mechanic", "Say which engine made a reading, from what, and when it is final", "Part II", "Rebuild a readout by hand from its rules"],
    ["3 · Contextual reader", "Read a chart top-down and name its regime", "Part IV", "Drills 9–12; the five-minute routine on ten charts a day for two weeks"],
    ["4 · Skeptic", "Spot a trap, and score a break", "Part V", "Drills 13–18"],
    ["5 · Practitioner", "Run a setup card, size it and journal it", "Parts VI and VII, with the cases in Part VIII", "Drills 19–24; paper trading for at least six months"],
    ["6 · Master", "Know where the evidence stops, and act accordingly", "Parts IX and XI", "Teach the context stack to someone else"],
], "Six levels", [18, 34, 24, 24]) + note("Work the drills before reading the answers. ⟦Chap:c30⟧'s answers explain the reasoning and point back to the section that teaches it.", rule=True))

S["tree"] = sec("tree", "The decision tree", objectives(["go from a chart to an action through a fixed sequence of questions"]) + steps([
    ("Is the bar closed, and is every layer I need readable?", "No → do nothing yet. Yes → continue."),
    ("Am I acting as a trader or as an investor?", "Trader → 3. Investor → 7."),
    ("Trader: what does the CHART cell say?", "LONG or SHORT → 4. FLAT · disagree → hold no position in this market; done."),
    ("Is today the rebalance day?", "Yes → move to the target if it changed by more than 10% (⟦ref:pos-time⟧); done. No → 5."),
    ("Discretionary only: was there a break of value with the trend at this close?", "Yes → optionally take the next part, within the target (T2). No → 6."),
    ("A probe against my position?", "Yes → hold; optionally a step off (T4). Never exit on it alone, never add on it."),
    ("Investor: which family, and is anything gold?", "Gold (held, quiet, settling, crypto capitulation) → wait. Otherwise → 8."),
    ("Is it a Buy or Accumulate family?", "Yes → stage in by thirds (I3); add the second third on the ▲ in DOWN · cheap (I1). No → 9."),
    ("PAID, STALLING or DISTRIBUTION?", "Trim toward 0.75, or exit toward 0.25 (I4). Otherwise hold, and rebalance on the calendar (I5)."),
]))

READ = [
    ("CVG " + chip("Buy 3.40", "bull") + " · WHY <i>sellers running · turning up</i> · PUSH ↓ · the pane tinted a deeper green.", "Which family is this? Is the ▲'s condition present? What does the unshaded cell hold? Should an investor wait for PUSH ↑?"),
    ("CVG " + chip("Hold 1.31", "neut") + " · WHY <i>buyers pausing · held</i> (gold).", "What happened to the conviction tape, and what does an investor do?"),
    ("AUCTION · STATE <i>Balance</i> · WHY <i>trail ↑ · probe, not accepted</i> · CHART " + chip("FLAT · disagree", "neut") + ".", "Name the regime. What is the system's position, and what does the probe say about longs?"),
    ("AUCTION · STATE <i>Migrating ↓</i> · WHY <i>trail ↓ · below value</i> · CHART " + chip("SHORT 0.55", "bear") + ". The previous close was inside value.", "Which setup card is in context?"),
    ("OI " + chip("Short covering", "gold") + " · WHY <i>exits · book 41 pct</i> · PUSH +1.2σ · the histogram's columns cast toward gold.", "What is the flow, and what should it change?"),
    ("OI " + chip("Warming · building its baseline", "gold") + ".", "What does the OI layer contribute today?"),
    ("A gold label at the pane's right edge: <i>SIGNALS PAUSED · value model building</i>.", "Which signals are paused? Is the grid readable?"),
    ("CVG " + chip("Exit 0.40", "bear") + " · WHY <i>sellers pausing · still richening</i>.", "Family? Why is it above 0.25 units? What does the investor do?"),
]
CTX = [
    ("The weekly grid reads DISLOCATED. On the daily: CHART " + chip("SHORT 0.45", "bear") + ", CVG " + chip("Buy 2.90", "bull") + " TURNED.", "Name the regime and what each of the trader and the investor does."),
    ("The panel's raw-share row reads QUIET. The trail is 25% below price. CHART " + chip("LONG 0.62", "bull") + ".", "Is the long riskier because the trail is so far away?"),
    ("On a 15-minute chart the CHART cell turns FLAT at 11:30.", "Does the daily trader act?"),
    ("BTC/USDT: CVG " + chip("Buy 3.70", "bull") + " DISLOCATED, the pane tinted gold, then a gold ▲.", "Does the capitulation plan apply?"),
]
FAKE = [
    ("Accepted momentum <b>off</b> (the 20-bar trail). A close 0.8 ATR below an up-trail, participation w = 2.1, the push gate −1, AUCTION Balance.", "Score the break. How often were breaks like it accepted within 20 bars?"),
    ("The same bar, but on the default 126-bar trail.", "What matters now, and what is the likely outcome?"),
    ("You hold LONG 0.40 from the system. A gold × prints below the trail.", "Exit? Add? What does the evidence say happens next?"),
    ("Two days later price closes back above the trail.", "Is this a buy signal?"),
    ("CHART " + chip("LONG 0.38", "bull") + ". Yesterday's close was inside value; today's is above VAH.", "What is this, and what may a discretionary trader do?"),
    ("CHART " + chip("LONG 0.38", "bull") + ". Yesterday's close was above VAH; today's is back inside value.", "Is this a better place to add?"),
]
SIZE = [
    ("CHART " + chip("LONG 0.50", "bull") + ", annualised volatility 25%, slice ₹2,00,000.", "Target weight and notional?"),
    ("CHART " + chip("SHORT 0.30", "bear") + ", annualised volatility 6%, slice ₹2,00,000.", "Target weight and notional?"),
    ("CHART " + chip("LONG 0.90", "bull") + ", annualised volatility 3.5%.", "Target weight?"),
    ("Six names with units 4, 3, 1.5, 1, 0.75 and 0.25.", "Weights, before any per-name cap?"),
    ("It is not a rebalance day, and the CHART cell flips from LONG to SHORT.", "Do you trade at tomorrow's open?"),
    ("Rebalance day: the target moved from 0.40 to 0.43.", "Do you trade?"),
]


def _drills(items, start):
    return "".join(drill(start + i, q, f'<div class="ro">{ro}</div>') for i, (ro, q) in enumerate(items))


S["dr-read"] = sec("dr-read", "Reading drills", objectives(["read eight readouts without the book"]) + _drills(READ, 1))
S["dr-ctx"] = sec("dr-ctx", "Context drills", _drills(CTX, 9))
S["dr-fake"] = sec("dr-fake", "Fakeout drills", _drills(FAKE, 13))
S["dr-size"] = sec("dr-size", "Sizing drills", _drills(SIZE, 19))

ANS = [
    "DISLOCATED (DOWN · cheap), Buy · capitulation. <i>Sellers running</i> confirms the row; <i>turning up</i> is value REVERTING, the ▲'s condition. If value turned at this close, the ▲ prints on it. The deeper tint says the same. The unshaded cell holds 4.00. No: inside the capitulation cell the push's direction made no consistent difference, so a Buy there does not wait for a push ↑ (⟦ref:kb-sig⟧).",
    "The conviction tape has fallen below +30, but conviction's histogram has not confirmed a push down, so the UP row is HELD (⟦ref:kb-grid⟧). The units sit between Hold and half-way to the FAINT row. The investor makes no adds and no changes. Held is caution, not direction.",
    "Transition. The trail is up, momentum's S is not, and the system is flat. A probe below an up-trail is a caution on the long side: on the default trail, the side did worse than usual for 10–20 bars after probes (⟦ref:fk-num⟧). No long trade.",
    "T2, the break of value with the trend (⟦ref:ts-break⟧). The system is short, and the close has left value in the trend's direction. The system trades on its rebalance; a discretionary trader may take the next part within the target.",
    "Price is up while open interest falls: shorts are closing. Colouring it as self-limiting is a hypothesis {U}; pushes paid for by exits lagged other pushes in the v9 audit {X}. It changes size, never direction: a step smaller, or later.",
    "Nothing. The feed is live, but it has fewer than ten accepted changes for its baseline. Skip the layer (⟦ref:kb-oi⟧).",
    "The ▲▼ (they need both level tapes) and the ◆, R and H. The grid is not readable while a level tape is not ready (⟦ref:kb-limits⟧).",
    "DISTRIBUTION (DOWN · rich). Both edges are unconfirmed, sellers pausing and value still richening, so the position sits half-way toward the middle and the units are above the cell's 0.25. The investor exits toward a token weight; the ▼ marked the entry (⟦ref:is-trim⟧).",
    "A dislocation inside a downtrend: Matrix A's TURNED × AM SHORT, the classic conflict between horizons (⟦ref:mx-a⟧). The trader stays short by the system's rules. The investor builds in stages, with small tranches.",
    "No. The quiet regime shuts the push gate, so the trail cannot step and its distance means nothing. The side and S carry the position. Stops come from structure (⟦ref:stops⟧), and the book's risk from the drawdown ladder (⟦ref:pos-heat⟧).",
    "No. The daily trader decides at the daily close. On a 15-minute chart the 126-bar trail and S's horizons are measured in 15-minute bars: a different and untested engine (⟦ref:ctx-tf⟧).",
    "No. The capitulation reading failed on crypto, which is why its tint and ▲ are drawn gold (⟦ref:ctx-class⟧).",
    "Three of four conditions: depth ≥ 0.5 ATR, weight ≥ 1.5, and the push against the trail; migration toward the break is missing. On the 20-bar trail, breaks meeting three conditions were accepted about 70% of the time within 20 bars, against about 50% with none (⟦ref:fk-check⟧).",
    "On the 126-bar trail only migration toward the break mattered, and here it is Balance. Fewer than one probe in twenty was accepted within 20 bars. Hard, heavy breaks were if anything less likely to flip it. Expect no flip, and treat the probe as a caution on longs.",
    "Neither exit nor add. The system does not exit on a probe; a discretionary trader may take one step off (T4). After probes the trail's side did 0.05 to 0.09σ worse than usual over 10–20 bars (⟦ref:fk-num⟧).",
    "No. The rejection entry, the first bar back after a probe, measured nothing and was negative in HA (⟦ref:fk-entry⟧).",
    "A break of value with the trend, the setup lab's S4: +0.06σ over 10 bars beyond the trend's average bar in all three sets, though it was not predicted. A discretionary trader may take the next part of the position, within the target (⟦ref:ts-break⟧).",
    "No. A pullback into value carried no edge beyond the trend's average bar, and breakouts beat it everywhere (⟦ref:fk-entry⟧).",
    "0.50 × 10% ÷ 25% = 0.20. Notional = 0.20 × ₹2,00,000 = ₹40,000 long.",
    "0.30 × 10% ÷ 6% = 0.50, short: −0.50 × ₹2,00,000 = −₹1,00,000. Low volatility gives large weights.",
    "0.90 × 10% ÷ 3.5% = 2.57, capped at 2.",
    "The sum is 10.5, so the weights are 38.1%, 28.6%, 14.3%, 9.5%, 7.1% and 2.4%. A per-name cap of about a tenth would redistribute the first two (⟦ref:inv-book⟧).",
    "No. In the tested system every change waits for the weekly rebalance, flips included (⟦ref:pos-time⟧).",
    "No. The change is 0.03, which is 7% of the new target, inside the 10% band.",
]
S["dr-ans"] = sec("dr-ans", "Answers", "".join(f'<div class="ans"><p><b class="an">{i}</b>{a}</p></div>' for i, a in enumerate(ANS, 1)))

S["checklists"] = sec("checklists", "Checklists", f"""
<h4>Every close (trader)</h4>
{checklist(["Bar closed; every layer readable", "CHART cell on every market in the book", "Rebalance day? Targets that moved more than 10%", "Probes against positions noted; no exits on them", "Breaks of value with the trend noted (T2)", "Journal line written"])}
<h4>Every week (investor)</h4>
{checklist(["Weekly chart read first for each name", "CVG STATE, units and WHY at the week's close", "▲▼ and tint changes since last week", "Weights = units ÷ sum, capped; move half the gap", "Trend filter applied, if used (I2)", "Clusters counted"])}
<h4>Before any trade</h4>
{checklist(["Which setup card? (name it)", "Context holds (regime, location)", "Size from the formula, rounded down", "Invalidation written", "Not a trap from ⟦chap:c17⟧"])}
<h4>Before going live</h4>
{checklist(["Six months of paper trading at the test's costs", "Markets chosen and fixed; clusters capped", "Drawdown ladder and kill rule written down", "Book volatility target chosen (the tested 1.3–1.6%, or scaled)", "Start at a tenth of the intended size"])}
""")


# ── Part XI: the complete settings reference, generated from the script ─────
def _inputs():
    here = os.path.dirname(os.path.abspath(__file__))
    src = open(os.path.join(here, "..", "..", "..", "pragati.pine"), encoding="utf-8").read()
    groups = dict(re.findall(r'var string (G_\w+)\s*=\s*"([^"]+)"', src))
    out = []
    for line in src.split("\n"):
        if line.lstrip().startswith("//"):
            continue
        m = re.search(r'input\.(\w+)\((.*)\)\s*$', line)
        if not m:
            continue
        kind, args = m.groups()
        dm = re.match(r'\s*("([^"]*)"|[^,]+),\s*"([^"]*)"', args)
        if not dm:
            continue
        g = re.search(r'group\s*=\s*(G_\w+)', args)
        opts = re.search(r'options\s*=\s*\[([^\]]*)\]', args)
        mn = re.search(r'minval\s*=\s*([-\d.]+)', args)
        mx = re.search(r'maxval\s*=\s*([-\d.]+)', args)
        tt = re.search(r'tooltip\s*=\s*"((?:[^"\\]|\\.)*)"', args)
        tip = (tt.group(1) if tt else "").replace("\\n", " ").replace("\\'", "'").replace('\\"', '"')
        first = re.split(r"(?<=[.!?])\s+(?=[A-Z])", tip.strip())
        short = " ".join(first[:2]) if first and first[0] else ""
        if len(short) > 300:
            short = short[:297].rsplit(" ", 1)[0] + " …"
        d = dm.group(1).strip().strip('"')
        d = {"true": "On", "false": "Off"}.get(d, d) or "—"
        rng = (opts.group(1).replace('"', "").replace(", ", " · ") if opts else
               (f"{mn.group(1)} to {mx.group(1)}" if mn and mx else ""))
        out.append((groups.get(g.group(1), "?") if g else "?", dm.group(3).strip(), d, rng, short))
    return out


def settings_all():
    rows, last = [], None
    parts = []
    inp = _inputs()
    for grp in dict.fromkeys(x[0] for x in inp):
        rr = [[f"<b>{t}</b>", d, r or "—", s] for g, t, d, r, s in inp if g == grp]
        parts.append(tbl(["Setting", "Default", "Range or options", "What it does"], rr, grp, [20, 13, 20, 47]))
    return len(inp), "".join(parts)


_N, _SET = settings_all()
S["settings"] = sec("settings", "Every setting", objectives(["find any setting, its default and its range"]) +
                    f"<p>All {_N} inputs, in the order of the settings page, generated from the script itself. The defaults are the measured configuration; the engines' groups sit last because tuning them does not transfer between eras {X}. Each entry gives the first sentences of the setting's own tooltip.</p>" + _SET)

S["ev-lab"] = sec("ev-lab", "The setup lab's verdicts", tbl(["Test", "Question", "Verdict", "Where"], [
    ["F1", "Is a probe a fakeout?", "The opposite: the trend's side did worse after probes, on both trails " + M, "⟦ref:fk-num⟧"],
    ["F2a–d (20-bar)", "What gets accepted?", "Depth and weight confirmed; push and migration consistent " + M, "⟦ref:fk-check⟧"],
    ["F2a–d (126-bar)", "What gets accepted?", "Migration consistent; depth, weight and push not supported " + M, "⟦ref:fk-check⟧"],
    ["S1", "Enter on the rejection", "Not supported " + M, "⟦ref:fk-entry⟧"],
    ["S2", "Enter on the acceptance", "Consistent " + M, "⟦ref:ts-accept⟧"],
    ["S3", "Buy the pullback into value", "Not supported " + M, "⟦ref:fk-entry⟧"],
    ["S4", "Buy the breakout from value", "Positive with t ≥ 2 in all three sets at 10 bars; not predicted " + M, "⟦ref:ts-break⟧"],
    ["S5", "Migration in a trend", "Consistent " + M, "⟦ref:kb-prof⟧"],
    ["I1", "An investor's trend filter", "Not confirmed: drawdown halved, Sharpe lower in 2020–26 " + M, "⟦ref:is-filter⟧"],
], "Pre-registered in docs/setup-lab.md, run once on 119 markets to 2019, the same markets in 2020–26, and 411 unseen markets", [14, 26, 44, 16]))

ORDER_FOUND = ["thesis", "engines", "path"]
ORDER_DRILL = ["dr-read", "dr-ctx", "dr-fake", "dr-size"]
ORDER_ANS = ["dr-ans", "checklists"]
