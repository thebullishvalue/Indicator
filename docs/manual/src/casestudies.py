"""Part VIII · Case studies. Real markets, reconstructed by the repository's reference engine (research/case_extract.py),
under the selection rule fixed in docs/setup-lab.md section 5; and constructed walkthroughs, labelled as such."""
import statistics
import cases
from kit import M, X, U, sec, tbl, chip, k, note, steps, objectives, fig

S = {}


def camp_table(sym, title):
    rows = []
    for c in cases.campaigns(cases.load(sym)):
        side = chip("LONG", "bull") if c["side"] > 0 else chip("SHORT", "bear")
        rows.append([f"{c['start']} → {c['end']}" + (" (open)" if c["open"] else ""), side, str(c["bars"]), f"{c['w_max']:.2f}",
                     f"{c['move'] * 100:+.1f}%".replace("-", "−"), f"{c['ret'] * 100:+.2f}%".replace("-", "−")])
    return tbl(["Campaign", "Side", "Bars", "Largest weight", "Price, open to open", "Return on the slice, net"], rows, title, [30, 12, 10, 14, 17, 17])


def now_kv(sym):
    n = cases.load(sym)["now"]
    j = cases.load(sym)
    ref = j["window"]["close"][-1]
    pos = n["am"] or 0.0
    cell = "FLAT · disagree" if abs(pos) < 1e-9 else ("LONG" if pos > 0 else "SHORT") + f" {abs(pos):.2f}"
    mig = {2: "Migrating ↑", 1: "Shifting ↑", 0: "Balance", -1: "Shifting ↓", -2: "Migrating ↓"}.get(n["mig"], "—")
    loc = "in value" if n["val"] <= n["close"] <= n["vah"] else ("above value" if n["close"] > n["vah"] else "below value")
    items = [("Close", cases.fmt_px(n["close"], ref)), ("Trail", ("up " if n["dir"] > 0 else "down ") + cases.fmt_px(n["lvl"], ref)),
             ("Value area", cases.fmt_px(n["val"], ref) + " – " + cases.fmt_px(n["vah"], ref)), ("Location", loc), ("AUCTION STATE", mig),
             ("S", f"{n['S']:+.2f}".replace("-", "−")), ("CHART cell", cell), ("Volatility", f"{n['vol_ann'] * 100:.1f}% a year"),
             ("Target weight", "0" if not n["target"] else f"{n['target']:+.3f}".replace("-", "−"))]
    return '<div class="kv">' + "".join(f"<div><b>{a}</b><span>{b}</span></div>" for a, b in items) + "</div>"


def ev_table(sym):
    names = {"probe_rejected": "Latest rejected probe", "probe_accepted": "Latest accepted probe", "pullback": "Latest pullback into value (S3)"}
    rows = []
    j = cases.load(sym)
    ref = j["window"]["close"][-1]
    for e in sorted(j["events"], key=lambda e: e["date"], reverse=True):
        f = lambda v: "—" if v is None else f"{v:+.2f}σ".replace("-", "−")
        rows.append([names[e["kind"]], e["date"], ("up" if e["side"] > 0 else "down"), cases.fmt_px(e["close"], ref) + " vs " + cases.fmt_px(e["trail"], ref),
                     f(e["z10"]), f(e["z20"]), e["flip_date"] or "—"])
    return tbl(["Event (selection rule)", "Date", "Trail", "Close vs trail", "10 bars", "20 bars", "Flip"], rows,
               f"{cases.NAMES[sym]}: the most recent event of each type, whatever its outcome", [24, 13, 8, 19, 11, 11, 14])


S["cs-method"] = sec("cs-method", "How the cases were chosen", objectives([
    "know exactly what a real-data case shows, and what it cannot",
]) + f"""
<p>These six cases are real daily bars, run through the repository's reference implementation of the auction engine, the push gate and Accepted momentum. The reference is the same code as the setup lab, and it was parity-tested against the Pine. They are not TradingView screenshots, and they show only what the reference computes:
<ul>
<li>the 126-bar trail, its value area and POC;</li>
<li>probes and flips;</li>
<li>migration;</li>
<li>S and the position;</li>
<li>the weight the tested sizing would have traded.</li>
</ul>
<b>They do not show the tapes, the grid or the ▲▼</b>, which need TradingView's intrabar data and Samanvaya's macro drivers. ⟦Chap:c26⟧'s walkthroughs, which are constructed, cover those.</p>
{tbl(["Rule", "Fixed in advance (docs/setup-lab.md §5)"], [
    ["Markets", "One per class: NIFTY 50 (index), RELIANCE (NSE stock), gold (commodity), USD/INR (FX), BTC/USDT (crypto), BANKBEES (ETF)"],
    ["Window", "The last 300 daily bars to the data's end, 30 October 2026 (31 October for BTC, which trades daily)"],
    ["Events", "The most recent event of each type before 30 September 2026 with a complete 20-bar outcome, whatever the outcome"],
    ["Campaigns", "Every campaign of the traded weight inside the window, winners and losers"],
], "The selection rule", [18, 82])}
<p>So the cases were not picked for looking good. Several lose. The plates draw the trail as Pragati does with Accepted momentum on: hue is the side, intensity the size, grey when flat. Below each plate is the weight the tested sizing would have held. Letters mark the dates the text discusses. Event outcomes are in σ units, as in the setup lab: the move over 10 and 20 bars from the next open, in the event's direction.</p>
""")

CASES = {
    "NIFTY_50": ("cs-nifty", "NIFTY 50: a floor that never moved", [("2025-08-29", "A"), ("2026-01-05", "B"), ("2026-03-09", "C"), ("2026-06-19", "D"), ("2026-07-29", "E")],
        """
<p><b>A · 29 August 2025.</b> The trail flips up at 24,064, with the close at 24,427. Value had shifted up (migration +1), and the window's POC, 24,864, stood above the old ceiling: acceptance. Momentum's S was −0.01, so the CHART cell read <span class="chip c-neut">FLAT · disagree</span> on the flip itself. The long campaign began only at the 3 September rebalance, once S turned up.</p>
<p><b>The floor never stepped.</b> NIFTY rallied to a closing high of 26,329 on 2 January 2026, and the trail stayed at 24,064 throughout. Conviction's quiet regime held on 85% of these 300 bars, the push gate was shut, and a trail can step only through an open gate (⟦ref:kb-trail⟧). The position did not care. With Accepted momentum on, the side and S decide, and the traded weight reached 0.65 during the rally.</p>
<p><b>B · 5 January 2026.</b> The latest pullback into value before the cut-off, a setup-lab S3 event. NIFTY closed back inside value at 26,250, and over the next 10 bars it fell 2.67σ further. The pullback was not a buy, as the setup lab found on average (⟦ref:fk-entry⟧).</p>
<p><b>C · 9 March 2026.</b> The first of seven probes below the floor. Within 20 bars NIFTY traded down to 22,183, 8% below the trail, and still <b>did not flip</b>. Migration stayed +1 (value six months earlier was lower still), so the break was never accepted. S had turned to −0.33, so the system was already FLAT. That is the trail working as designed: acceptance is about value, not distance.</p>
<p><b>D · 19 June 2026.</b> The flip down came with price almost on the line: close 24,013 against the trail's 24,064. The POC (23,968) had moved below and migration read −1. The level did not move; the broken floor became the ceiling.</p>
<p><b>E · 29 July 2026.</b> The latest of five probes <i>above</i> the new ceiling, at 24,250. It was not accepted, and the market drifted (−0.28σ over 10 bars in the trail's direction). The short campaign began at the 18 August rebalance and was still open at the data's end, having made +0.55% on the slice while NIFTY fell 4.9%.</p>""",
        "A six-month trail flips rarely, and never on distance alone. A frozen floor is not a risk measure. The system's size, not the line, carried the position."),
    "RELIANCE": ("cs-rel", "RELIANCE: right side, wrong timing", [("2025-08-20", "A"), ("2025-10-20", "B"), ("2026-03-02", "C"), ("2026-07-16", "D"), ("2026-07-30", "E")],
        """
<p><b>A · 20 August 2025.</b> The trail flips up at 1,292.8 (close 1,406.5), and the CHART cell turns <span class="chip c-bull">LONG 0.11</span>. Yet the traded weight that day was still −0.09, from the earlier short. The traded position waits for the next weekly rebalance. That is the tested rule, and it is why the plate's weight strip lags the trail's colour.</p>
<p><b>B · 20 October 2025.</b> The fourth step since early September, to 1,356.8. RELIANCE's gate was open far more often than NIFTY's (quiet on only 13% of these bars), so its trail ratcheted up behind the move.</p>
<p><b>The long campaign lost.</b> It ran 65 bars from 21 October 2025 to 22 January 2026, and its size peaked as price did: the stock's closing high was 1,585 on 2 January. Net, it made −1.41% on the slice, while the stock moved −6.4% open to open. Momentum is strongest at the top of a move. That is the cost every trend system pays, and the reason the edge is measured on hundreds of markets.</p>
<p><b>C · 2 March 2026.</b> The first of six probes below the floor (close 1,351.75 against 1,356.8), with migration 0. The probes came and went for four months without acceptance.</p>
<p><b>D · 16 July 2026.</b> Acceptance: a close of 1,296.6, the POC at 1,302.4 below the trail and migration −1. The short campaign began at the 20 July rebalance.</p>
<p><b>E · 30 July 2026.</b> A pullback into value on the short side (close 1,292.9). It did nothing measurable: −0.43σ against the trade over 10 bars, +0.14σ over 20. By 30 October the stock was at 1,165, below the value area. The open short campaign had made +0.56% on the slice while the stock fell 11.4%.</p>""",
        "The traded weight lags the CHART cell by up to a week. Being on the right side is not the same as making money on one market. A long probe series can precede acceptance by months."),
    "GOLD": ("cs-gold", "Gold: the size leaves before the line", [("2026-03-02", "A"), ("2026-03-25", "B"), ("2026-05-28", "C"), ("2026-09-28", "D")],
        """
<p><b>The best campaign of the six.</b> Gold's long ran 147 bars, from the window's start on 25 August 2025 to 25 March 2026. The weight reached 0.60, and the campaign made +14.5% on the slice while gold rose 32.9% open to open.</p>
<p><b>A · 2 March 2026.</b> Gold closed at 5,294, near its closing high of 5,318 on 29 January, with S at +0.56. Over the next 20 bars it traded down to 4,101.</p>
<p><b>B · 25 March 2026.</b> S had fallen to +0.09, and the weight with it, to 0.05. The campaign ended by <b>size</b>, not by the trail, which was then at 2,640: 42% below price. A stop at the trail would have given back almost everything. The system did not wait for it.</p>
<p><b>C · 28 May 2026.</b> The trail finally stepped, from 2,640 to 4,256, the first bar in months with the gate open and value migrated. It stepped twice more within days, to 4,304.</p>
<p><b>D · 28 September 2026.</b> The latest probe, at 4,168, below the floor of 4,304. It was not accepted within 20 bars; gold drifted to 4,038 (−0.41σ over 20 bars against the trail's side, as the setup lab's F1 expects). At the data's end gold closed at 3,899, 9% below a trail that still reads up. The POC was 4,440 and migration 0, so the market had not accepted the lower prices. S was −0.32, so the system was flat.</p>""",
        "Accepted momentum exits through S long before the trail is touched. A trail far from price is common, and is not a stop. A price below an up-trail with no acceptance is a probe: caution, and the system flat."),
    "USDINR": ("cs-inr", "USD/INR: a staircase, and a quiet market's large weight", [("2025-10-31", "A"), ("2026-04-14", "B"), ("2026-06-30", "C"), ("2026-07-29", "D")],
        """
<p><b>A textbook managed trend.</b> In 300 bars there were no probes and no flips, and sixteen steps. The trail ratcheted from 85.12 to 91.68 as USD/INR climbed from 86.3 to 95.2. Migration read Shifting or Migrating ↑ on 267 of the 300 bars.</p>
<p><b>A · 31 October 2025.</b> The first step, 85.12 to 86.00. <b>B · 14 April 2026.</b> A step to 88.64. <b>C · 30 June 2026.</b> A step to 90.88.</p>
<p><b>The weight.</b> Annualised volatility was only 4.6% at the window's start, so even modest sizes asked for large weights. The weight reached 1.78, close to the cap of 2. One campaign held the whole window and was still open. Yet it made only +2.1% on the slice against a +10% move. The weight happened to be high on the days the rupee strengthened and low on the days it weakened. In the first quarter of 2026 the pair rose 3.0% and the position made almost nothing. A trend the trail followed perfectly still did not pay much.</p>
<p><b>D · 29 July 2026.</b> The latest pullback into value, at 95.60: +0.01σ over 10 bars, +0.14σ over 20. Nothing to see, as on average.</p>""",
        "Low volatility means large weights: the cap and the gross ceiling matter (⟦ref:pos-heat⟧). A perfect-looking trend can return little. The INR pairs lost money in the full test, whatever this window shows."),
    "BTCUSDT": ("cs-btc", "BTC/USDT: a falling ceiling and a transition", [("2026-01-07", "A"), ("2026-04-02", "B"), ("2026-05-05", "C"), ("2026-08-21", "D")],
        """
<p><b>A · 7 January 2026.</b> The trail flips down at 106,240 (close 91,364): the POC at 88,000 had dropped below the old floor and migration read −1. Crypto trades every day, so these 300 bars span only ten months.</p>
<p><b>A ceiling that stepped.</b> Crypto's push gate was open far more often (quiet on 14% of these bars), and the trail stepped down fifteen times, from 106,240 to 75,200, as BTC fell to a closing low of 58,625 on 30 June. <b>B · 2 April 2026:</b> one of those bars, with S at −0.48 and the trail stepping to 89,600.</p>
<p><b>Two short campaigns, both profitable but small.</b> From 7 January to 16 April (100 bars) the system made +1.04% on the slice while BTC fell 15.6%. From 7 May to 19 August (105 bars) it made +0.17% on a fall of 8.7%. BTC's volatility (about 28% to 29% a year on this measure) kept the weight at 0.17 or below. High-volatility markets carry small weights by design.</p>
<p><b>C · 5 May 2026.</b> A probe above the ceiling at 80,906. S had turned +0.07, so the cell read FLAT. The probe was not accepted, and the ceiling stepped lower again within weeks.</p>
<p><b>D · 21 August 2026.</b> The latest probe above the ceiling (78,338 against 75,200), with S at +0.35. The trail is down and momentum up: <span class="chip c-neut">FLAT · disagree</span>, the transition regime (⟦ref:ctx-regime⟧). It was not accepted within 20 bars, and at the data's end BTC still sat above a down-trail in Balance, flat.</p>""",
        "Volatility sets the size, and crypto's is small. FLAT · disagree is a regime, not an error. No capitulation reading applies to crypto (⟦ref:ctx-class⟧)."),
    "BANKBEES": ("cs-bank", "BANKBEES: a crash that was never accepted", [("2025-10-29", "A"), ("2026-03-12", "B"), ("2026-04-21", "C"), ("2026-07-08", "D"), ("2026-07-29", "E")],
        """
<p><b>A · 29 October 2025.</b> After a long freeze, the gate opened with value migrated, and the trail jumped from 494.4 to 561.6 in one step. A trail that cannot step for months moves all at once when it can.</p>
<p><b>The long campaign</b> ran from the window's start to 6 March 2026 (158 bars), with the weight up to 0.89. It made +0.22% on the slice for a +0.5% move.</p>
<p><b>B · 12 March 2026.</b> A probe below the floor of 572.8. Within 20 bars the ETF fell to 516, 10% below the trail, and the break was still <b>not accepted</b>: migration stayed +1. It recovered to 591 by 21 April.</p>
<p><b>C · 21 April 2026.</b> A step to 588.8. <b>D · 8 July 2026.</b> The flip down at 588.8, with the close at 587.7 and the POC at 561.6 below. Again the flip came with price at the line, not 10% beyond it.</p>
<p><b>E · 29 July 2026.</b> The latest probe above the new ceiling (591.7). It was not accepted, and S was near zero, so the system stayed flat. By 30 October the ETF closed at 565.5, just below the value area's low edge, <span class="chip c-bear">SHORT 0.16</span>.</p>""",
        "Crashes are not acceptance. Flips happen when value moves, often quietly. A frozen trail that unfreezes jumps."),
}

for sym, (sid, title, letters, body, lesson) in CASES.items():
    key = sid.replace("-", "")
    S[sid] = sec(sid, title, fig(key, cases.plate(sym, letters),
                                 f"{cases.NAMES[sym]}, daily, {cases.load(sym)['window']['date'][0]} to {cases.load(sym)['window']['date'][-1]}, reconstructed by the reference engine {M}. "
                                 "Above: close and range; the rolling 126-bar value area (band) and POC (dotted); the trail (hue the side, intensity the size, grey when flat); a gold × at each probe's first bar; a ring at each flip. Below: the weight the tested sizing traded.")
                 + body + camp_table(sym, f"{cases.NAMES[sym]}: every campaign in the window") + ev_table(sym)
                 + "<h4>At the data's end</h4>" + now_kv(sym) + note(f"<b>What it teaches.</b> {lesson}", rule=True))

S["cs-book"] = sec("cs-book", "The six as one book", objectives([
    "see what the tested edge looks like on six markets rather than four hundred",
]) + f"""
<p>Run as one book, with equal slices from 6 January 2026 (the common start of the six windows) to 30 October 2026, net of the test's costs, the six markets made <b>−0.69%</b>. The worst drawdown was −1.29%, at an annualised volatility of 1.6% {M}.</p>
{tbl(["Market", "Contribution on its slice"], [["NIFTY 50", "−1.72%"], ["RELIANCE", "−3.10%"], ["Gold", "+1.76%"], ["USD/INR", "+0.12%"], ["BTC/USDT", "+1.17%"], ["BANKBEES", "−2.71%"]],
    "Six markets, 6 January to 30 October 2026", [50, 50])}
<p>That is a losing ten months, and it was chosen by rule, not for effect. It is also what the evidence predicts for a book this small:
<ul>
<li>on one market the median Sharpe was +0.23 to +0.38, and a quarter of markets lost over the whole test;</li>
<li>the edge appeared across 119 and 411 markets, sized alike;</li>
<li>the book's volatility, 1.6%, is the tested book's own (1.3% to 1.6%), which is why its losses are small too.</li>
</ul>
A trader who scales the book to 10% volatility should expect this kind of stretch to look six times larger.</p>
""")

# ── constructed walkthroughs ────────────────────────────────────────────────
S["wk-more"] = sec("wk-more", "Three more walkthroughs (constructed)", objectives([
    "follow the whole stack, grid and OI included, through a sequence of closes",
]) + note("<b>Constructed, not real.</b> These readouts were written to teach the full stack, including the tapes, the grid and OI, which ⟦chap:c25⟧'s reconstructions cannot show. No market produced them, and no outcome is implied.") + f"""
<h4>5 · A break of value that the grid confirms</h4>
{tbl(["Close", "The readout says", "Trader", "Investor"], [
    ["Day 1", "AUCTION Shifting ↑ · trail ↑ · in value · " + chip("LONG 0.31", "bull") + " · CVG " + chip("Hold 1.42", "neut") + " BUILDING · buyers running", "Hold the target", "Hold"],
    ["Day 4", "Close above VAH: out of value, its way · " + chip("LONG 0.36", "bull") + " · PUSH ↑↑", "T2: take the next part, within the target", "Hold; do not add in BUILDING"],
    ["Day 9", "CVG " + chip("Trim 0.81", "bear") + " PAID · value tape past +θ · trail line still green", "Hold: the system sizes by S", "Trim toward 0.75 units (I4)"],
    ["Day 15", "Probe × below the trail · migration still +2 · " + chip("LONG 0.22", "bull"), "Hold; take a step off if discretionary (T4)", "Hold the trimmed weight"],
], "Walkthrough 5", [10, 46, 22, 22])}
<h4>6 · A capitulation on crypto</h4>
{tbl(["Close", "The readout says", "Reading"], [
    ["Day 1", "CVG " + chip("Buy 3.6", "bull") + " DISLOCATED · pane tint <b>gold</b>, not green · " + chip("SHORT 0.40", "bear"), "Crypto: the capitulation reading failed there. The gold tint says so"],
    ["Day 3", "▲ drawn in gold · value momentum reverting", "Do not buy it as a capitulation (⟦ref:ctx-class⟧)"],
    ["Day 8", "Trail ↓ · probe × above the ceiling · S turning up → " + chip("FLAT · disagree", "neut"), "Transition. The trader is flat by the system; nothing to do"],
], "Walkthrough 6", [10, 52, 38])}
<h4>7 · Crowded and paid for</h4>
{tbl(["Close", "The readout says", "Reading"], [
    ["Day 1", "OI " + chip("Long build-up", "bull") + " · book 84 pct (gold) · CVG " + chip("Trim 0.75", "bear") + " PAID · " + chip("LONG 0.58", "bull"), "Committed buyers, a full book and a rich price: late, not wrong"],
    ["Day 2", "OI " + chip("Short covering", "gold") + " · histogram columns cast gold", "The push is paid for by exits: pushes like this lagged " + X + ". Size down a step if discretionary"],
    ["Day 6", "▼ DISTRIBUTION · CVG " + chip("Exit 0.25", "bear") + " · trail still ↑ · " + chip("LONG 0.41", "bull"), "Matrix A's conflict (⟦ref:mx-a⟧): the investor exits toward a token weight; the trader holds the system until it flips"],
], "Walkthrough 7", [10, 52, 38])}
""")

ORDER_REAL = ["cs-method", "cs-nifty", "cs-rel", "cs-gold", "cs-inr", "cs-btc", "cs-bank", "cs-book"]
ORDER_WALK = ["scen", "wk-more"]
FIGS = {v[0].replace("-", ""): v[0] for v in CASES.values()}
