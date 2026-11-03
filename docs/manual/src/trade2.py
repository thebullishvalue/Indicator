"""Part VI additions · initiating and positioning, the trading setups, exits and the journal."""
import cases
from kit import M, X, U, sec, tbl, chip, k, note, steps, flow, objectives, checklist, setup_card, math

S = {}

S["pos-time"] = sec("pos-time", "From the close to the order", objectives([
    "run the tested system's daily timeline without improvising",
    "handle a gap, a missed open, a holiday and a partial fill",
]) + f"""
<p>The tested system decides at the close of bar <i>t</i> and holds from the open of <i>t</i>+1 to the open of <i>t</i>+2. Every result in ⟦chap:c18⟧ was computed that way. The timeline below keeps you inside it.</p>
{tbl(["When", "What", "Notes"], [
    ["At the close", "Read the AUCTION row's CHART cell on every market in the book", "A forming bar is not a decision (⟦ref:kb-repaint⟧)"],
    ["After the close", "Compute each target weight (⟦ref:pos-size⟧). Is today a rebalance day?", "The test rebalanced weekly, every fifth bar; pick a fixed weekday and keep it"],
    ["After the close", "On a rebalance day, change only the markets whose target moved more than 10% of itself. That includes flips and going flat", "Between rebalance days the position is left alone, flips included"],
    ["Next open", "Place the orders at or near the open", "The test traded the open. A market-on-open order is the closest match"],
], "The tested timeline", [18, 46, 36])}
<h4>When reality does not match the test</h4>
{tbl(["Situation", "Do this", "Why"], [
    ["The market gaps at the open", "Execute anyway", "The test's returns are open to open: gaps are already in its numbers"],
    ["You miss the open", "Execute at the next price you can, the same day; do not wait for a better one", "Waiting for a better price is a new, untested rule"],
    ["A holiday on one market", "Trade it at its next open", "Each market keeps its own calendar"],
    ["A partial fill, or a lot larger than the target", "Round down to whole lots; leave a remainder flat", "Rounding up adds risk the sizing did not ask for"],
    ["Crypto, which never closes", "Use the exchange's daily bar (UTC) as the close", "That is how the test's crypto bars were built"],
    ["The weight is below one lot", "Skip the market, or use a smaller contract", "A slice too small to trade is common with large lots"],
], "Departures from the timeline", [28, 40, 32])}
""")


def inr(x):
    """Indian digit grouping: 1,03,962."""
    neg, x = x < 0, abs(round(x))
    t = str(x)
    head, tail = t[:-3], t[-3:]
    while len(head) > 2:
        tail = head[-2:] + "," + tail
        head = head[:-2]
    out = (head + "," + tail) if head else tail
    return ("−₹" if neg else "₹") + out


def _now_rows():
    rows, tot = [], 0.0
    for sym in ("NIFTY_50", "RELIANCE", "GOLD", "USDINR", "BTCUSDT", "BANKBEES"):
        j = cases.load(sym)
        n = j["now"]
        pos = n["am"] or 0.0
        side = "FLAT · disagree" if abs(pos) < 1e-9 else ("LONG" if pos > 0 else "SHORT") + f" {abs(pos):.2f}"
        tone = "neut" if abs(pos) < 1e-9 else ("bull" if pos > 0 else "bear")
        tgt = n["target"] or 0.0
        notional = tgt * 166_667
        tot += abs(notional)
        rows.append([cases.NAMES[sym], chip(side, tone), f"{n['vol_ann'] * 100:.1f}%", "0" if abs(tgt) < 1e-9 else f"{tgt:+.3f}".replace("-", "−"), inr(notional)])
    return rows, tot


_ROWS, _GROSS = _now_rows()

S["pos-size"] = sec("pos-size", "Sizing, with real numbers", objectives([
    "turn a CHART cell into a weight, a notional and a number of lots",
    "say how much risk the tested sizing actually takes",
]) + f"""
{math("weight   = size × 10% ÷ annualised volatility,  capped at ±2       (size = the CHART cell's number, with its side)" + chr(10) + "notional = weight × the capital slice for that market                  (slice = capital ÷ number of markets)" + chr(10) + "lots     = notional ÷ (price × lot size), rounded down")}
<p>Volatility is the EWMA (span 60) of daily returns, annualised by √252. On TradingView, the built-in Historical Volatility indicator with length 60 is a close stand-in. The 10% is a <i>per-market</i> volatility target at full size. Because size is usually well below 1, most positions run far below it.</p>
<p><b>Real numbers, 30 October 2026.</b> The six case-study markets, read from the reference engine at that close, on ₹10,00,000 split into six slices of ₹1,66,667 {M}:</p>
{tbl(["Market", "CHART cell", "Volatility (annual)", "Target weight", "Target notional"], _ROWS, "A six-market book on 30 October 2026", [20, 24, 18, 18, 20])}
<p>The gross exposure is about {inr(_GROSS)}, roughly {_GROSS / 1_000_000 * 100:.0f}% of capital, with two of six markets flat. That is typical. The tested book's volatility at 10% per market was only about 1.3% to 1.6% a year, because sizes are small and markets diversify one another {M}. Scaled up to 10% for the whole book, the same paths would have drawn down roughly 16% to 29%. Decide which you are running before you start.</p>
<h4>Lots</h4>
<p>With NIFTY at 23,053, a single index-futures lot is worth several times a ₹1.67 lakh slice (check the exchange's current lot size). Small accounts cannot hold index futures at the tested size. Use the ETF (NIFTYBEES), fewer and larger slices, or accept that the book holds fewer markets. Fewer markets means more single-market noise (⟦ref:am-book⟧). Every rounding should go down, never up.</p>
""")

S["pos-scale"] = sec("pos-scale", "Scaling in, adding and taking off", objectives([
    "know which scaling the system already does for you",
    "add or reduce discretionarily without breaking the tested rules",
]) + f"""
<p><b>Accepted momentum already scales.</b> Its size is momentum's score, so as a trend strengthens over weeks the weekly rebalance adds, and as it weakens the rebalance takes off. Pyramiding and partial exits are built in. On the tested system, do nothing beyond the rebalance.</p>
<p>Discretionary traders who want to time inside the system's position, entering it or adding to it, have one measured tool and one measured caution {M}:</p>
{tbl(["Moment", "Action", "Evidence"], [
    ["The CHART cell turns LONG or SHORT", "Take the first part of the position at the next open", "The system's own decision " + M],
    ["A close out of value in the trend's direction, AM agreeing", "Take the next part", "Breakouts from value beat the trend's average bar " + M],
    ["A pullback into value", "Do not add because of it", "No edge measured " + M],
    ["A probe against the position (126-bar trail)", "Do not add; optionally take a step off", "The side did worse than usual afterwards " + M],
    ["The next weekly rebalance", "Bring the whole position to the tested target", "Ends the discretion: you are back on the system"],
], "Discretion inside the system", [32, 38, 30])}
{note("<b>Never average down against the system.</b> Adding to a long that Accepted momentum has taken flat or short is a new strategy with no test behind it. The only measured buy-the-dip in Pragati is the investor's capitulation plan (⟦ref:inv-cap⟧), which lives on the grid and at a different horizon.")}
""")

S["pos-heat"] = sec("pos-heat", "Portfolio heat and correlation", objectives([
    "cap correlated exposure",
    "set a drawdown ladder before the first trade",
]) + f"""
<p>The tested portfolio gave every market equal risk. In a real account, markets come in clusters that move together: Indian banks, oil and gas, precious metals, INR pairs. Ten bank stocks are not ten markets.</p>
{steps([
    ("Count clusters, not tickers", "Group markets that move together. Sizing treats each cluster as at most two or three slices in total, however many names it holds " + U + "."),
    ("Cap gross exposure", "Set a ceiling on the sum of |weight| across the book, for example 1.5× capital, so that low-volatility markets at their cap of 2 cannot dominate " + U + "."),
    ("Write the drawdown ladder now", "At the backtest's worst drawdown, halve all weights. At 1.5× it, stop and review: the system's kill rule (⟦ref:mg-exit⟧)."),
    ("Shorts need instruments", "Shorting Indian cash stocks overnight needs futures. Without them, run long and flat only, and expect a different return profile from the test."),
])}
""")

# ── the setup catalogue ──────────────────────────────────────────────────────
S["ts-card"] = sec("ts-card", "How to read a setup card", objectives([
    "read any setup card in this book and know exactly how much to trust it",
]) + f"""
<p>Every setup is written as a card. The fields are always the same, and none is optional.</p>
{tbl(["Field", "What it holds"], [
    ["Context", "The regime and readings that must hold first (⟦chap:c15⟧)"],
    ["Trigger", "The closed-bar event that starts the setup"],
    ["Entry", "When and how the order is placed"],
    ["Size", "How large, in the tested formula or a stated fraction of it"],
    ["Stop / invalidation", "What proves the setup wrong, and where the risk is cut"],
    ["Exit", "What ends the trade when it works"],
    ["Evidence", "The tag, with numbers. <b>Measured</b> results name their verdict: confirmed, consistent, positive but unpredicted, or not supported"],
    ["Fails when", "The conditions under which it is known, or expected, to fail"],
], "The setup card", [24, 76])}
{note("<b>Only T1 is a system.</b> T1, Accepted momentum, passed a held-out test as a whole system. T2 to T4 are measured refinements of <i>when</i> to act inside it. T5 and T6 rest on the v9 audit's evidence for the grid's states, with trade rules that are a house plan. T7 is unmeasured structure. Size them in that order of trust.", rule=True)}
""")

CARDS = [
    ("ts-am", "T1", "Accepted momentum", M, "the tested system", [
        ("Context", "Any regime. The system is flat by design when the trail and momentum disagree"),
        ("Trigger", "The CHART cell at the close: LONG x, SHORT x or FLAT"),
        ("Entry", "Next open, on the weekly rebalance day, or at once on the first day of the book"),
        ("Size", "x × 10% ÷ annualised volatility, capped at 2, per market, every market alike"),
        ("Stop / invalidation", "None per trade: the side flips, or the size falls to flat. The book has a kill rule (⟦ref:mg-exit⟧)"),
        ("Exit", "When the CHART cell says FLAT or the opposite side, at the next rebalance"),
        ("Evidence", "411 unseen markets: Sharpe +0.79 (t 4.0); 2020–26: +1.21 (t 3.7), net of costs. Timing beyond leaning long: t 4.1 and 2.2. Did not beat plain momentum"),
        ("Fails when", "Run on one market (median Sharpe +0.23 to +0.38; a quarter lost); INR pairs; sharp reversals, which every trend system pays for"),
    ]),
    ("ts-break", "T2", "Break of value with the trend", M, "positive everywhere, unpredicted", [
        ("Context", "Accepted momentum LONG or SHORT (it agrees with the trail)"),
        ("Trigger", "A close out of the value ribbon in the trend's direction, the bar before inside it"),
        ("Entry", "Next open: the first part of a new position, or an add inside the system's target"),
        ("Size", "Within the system's target weight; never above it"),
        ("Stop / invalidation", "A close back inside value within a few bars is the first warning; the system's flat is the exit " + U),
        ("Exit", "With the system"),
        ("Evidence", "+0.06σ over 10 bars beyond the trend's average bar: t 4.1 (DEV), 2.5 (2020–26), 10.4 (HA). Beat pullbacks into value everywhere. Hit rate 51–54%"),
        ("Fails when", "In balance (not tested); when the trend is FLAT · disagree; as a standalone trade outside the system (not tested)"),
    ]),
    ("ts-accept", "T3", "The acceptance entry", M, "consistent", [
        ("Context", "A 126-bar trail flip: the trail has just changed side"),
        ("Trigger", "The flip bar (a ring on the chart; AUCTION WHY \"accepted\")"),
        ("Entry", "Next open, if Accepted momentum also turns that way. A flip with momentum disagreeing is FLAT"),
        ("Size", "The system's target"),
        ("Stop / invalidation", "The trail flipping back, which is rare at 126 bars"),
        ("Exit", "With the system"),
        ("Evidence", "+0.02 · +0.09 · +0.08σ over 10 bars (t 0.6 · 1.6 · 4.4); +0.05 · +0.11 · +0.11σ over 20. The predicted sign in all three sets, significant only in HA. 949 · 477 · 5,189 flips"),
        ("Fails when", "Flips are rare: on the six case markets, one every 1.3 to 2.2 years on the 126-bar trail. A single market gives few chances"),
    ]),
    ("ts-probe", "T4", "The probe caution", M, "the opposite of fakeout-fading", [
        ("Context", "You hold a position on the trail's side"),
        ("Trigger", "A gold × against your side"),
        ("Entry", "None. This is a management card"),
        ("Size", "Hold the system's size. A discretionary trader may take one step off " + U),
        ("Stop / invalidation", "The flip, if the probe is accepted; on the 126-bar trail fewer than 1 in 20 are"),
        ("Exit", "With the system"),
        ("Evidence", "After a probe the trail's side did worse than its average bar: −0.08σ (DEV), −0.05σ (2020–26), −0.07σ (HA, t −8.5) over 10 bars. Fading the probe measured nothing"),
        ("Fails when", "Read as an exit signal: it does not flip the side, and the system does not exit on it"),
    ]),
    ("ts-cap", "T5", "The capitulation swing (long only)", X, "state measured, trade rules a house plan", [
        ("Context", "Not crypto. The grid in DOWN · cheap: Buy 4, green tint"),
        ("Trigger", "The ▲ at the close: value momentum reverting"),
        ("Entry", "Next open"),
        ("Size", "Small: a half or a third of a normal slice, since the measured lean is about +0.05σ over 10–20 bars " + U),
        ("Stop / invalidation", "Below the capitulation's low, or 2 ATR, whichever is nearer " + U),
        ("Exit", "After 20 bars (the measured horizon), or when the grid reaches BUILDING or PAID " + U),
        ("Evidence", "Capitulation followed by gains in all three eras outside crypto (+0.06 to +0.08σ over 10–20 bars); the turn +0.046 to +0.056σ over 10 bars"),
        ("Fails when", "Crypto (the reading failed); a downtrend holding SHORT, where it is a counter-trend trade; one name at a time. The edge is across many events"),
    ]),
    ("ts-dist", "T6", "The distribution avoid", X, "state measured", [
        ("Context", "The grid in DOWN · rich: Exit 0.25, red tint"),
        ("Trigger", "The ▼"),
        ("Entry", "No new longs. Investors trim toward a token weight"),
        ("Size", "—"),
        ("Stop / invalidation", "The grid leaving DOWN · rich toward the buyers"),
        ("Exit", "—"),
        ("Evidence", "As a state, followed by underperformance in every era; too rare to measure as an event"),
        ("Fails when", "Read as a short signal: shorting on the ▼ was never tested"),
    ]),
    ("ts-session", "T7", "Session-profile levels", U, "reference structure", [
        ("Context", "Intraday or swing, for traders who use profile levels already"),
        ("Trigger", "A test of VAH, VAL, the POC, VWAP, a naked POC or the IB edges"),
        ("Entry", "Your own rules"),
        ("Size", "Small, and never in conflict with the daily system's side"),
        ("Stop / invalidation", "Your own rules"),
        ("Exit", "Your own rules"),
        ("Evidence", "None in this repository. The naked-POC and VWAP \"measured\" labels are PVOI's and were not re-verified"),
        ("Fails when", "Costs below daily (⟦ref:kb-limits⟧); trading against the daily side"),
    ]),
]

for sid, code, name, ev, verdict, fields in CARDS:
    S[sid] = sec(sid, f"{code} · {name}", setup_card(code, name, ev, verdict, fields))

S["ts-none"] = sec("ts-none", "When not to trade", objectives(["list the conditions under which no setup applies"]) + checklist([
    "Any layer you need is paused, warming or grey (⟦ref:ctx-stack⟧).",
    "A non-standard chart.",
    "Accepted momentum reads FLAT · disagree, and you trade trends.",
    "The bar has not closed.",
    "Only one market would carry the risk of a portfolio's edge.",
    "Expiry week, if your read leans on OI.",
    "A crypto symbol, if your read leans on the capitulation state.",
    "You cannot say which setup card you are trading.",
]))

S["mg-exit"] = sec("mg-exit", "Exits, kill rules and re-entry", objectives([
    "write down every exit rule before the first entry",
]) + f"""
{tbl(["Exit", "Rule", "Evidence"], [
    ["The system's exit", "The CHART cell reads FLAT or the other side; act at the next rebalance", M],
    ["The kill rule", "Stop the book if its drawdown passes 1.5× the backtest's worst, or if the rolling 12-month Sharpe stays below zero for two quarters", "A rule written before results, not a measured edge"],
    ["Time stop (T5)", "20 bars after a capitulation entry", "The measured horizon " + X],
    ["Structural stop (discretionary)", "Beyond the swing extreme or the opposite value edge (⟦ref:stops⟧)", U],
    ["Probe against you", "Not an exit (⟦ref:ts-probe⟧)", M],
], "Exits", [24, 56, 20])}
<p><b>After a kill.</b> Stop trading the book. Paper-trade it again for at least six months at the same costs, then restart at a tenth of the intended size. A system stopped by its kill rule is not restarted because the next signal looks good.</p>
""")

S["mg-journal"] = sec("mg-journal", "The journal and the weekly review", objectives([
    "keep a journal that can tell skill from luck",
]) + f"""
<p>Record every decision, including the decision not to act. The one-line reading from the routine (⟦ref:ctx-routine⟧) is the core of each entry.</p>
{tbl(["Field", "Example"], [
    ["Date, market, timeframe", "2026-10-30 · RELIANCE · D"],
    ["One-line reading", "readable · trend down (SHORT 0.50) · below value, no probe · Accumulate 1.5, sellers running, still cheapening · no OI · no trigger"],
    ["Setup card", "T1 (rebalance day)"],
    ["Decision and size", "Short, target −0.22 of the slice; rounded to 0 lots of futures, executed in the ETF"],
    ["Execution", "Next open, filled at …; slippage …"],
    ["Expectation", "The system's; no single-trade target"],
    ["Outcome (filled later)", "Return, days held, the readings at exit"],
], "A journal entry", [26, 74])}
<h4>Weekly review</h4>
{checklist([
    "Did every action match a setup card? List the ones that did not.",
    "Book drawdown against the ladder (⟦ref:pos-heat⟧).",
    "Costs and slippage against the test's assumptions (5 to 20 bps one way by class).",
    "The share of markets in each regime: are you trading trends in a book that is mostly balance?",
    "Any gold readings that you acted through?",
])}
""")

ORDER_POS = ["pos-time", "pos-size", "pos-scale", "pos-heat"]
ORDER_TS = ["ts-card", "ts-am", "ts-break", "ts-accept", "ts-probe", "ts-cap", "ts-dist", "ts-session", "ts-none"]
ORDER_MG = ["mg-exit", "mg-journal"]
