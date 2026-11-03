"""Part IV · Reading in context, and Part V · Fakeouts and traps (with the setup lab's results)."""
from kit import M, X, U, sec, tbl, chip, k, note, steps, flow, objectives, checklist

S = {}

S["ctx-stack"] = sec("ctx-stack", "The six layers, top down", objectives([
    "read any chart in a fixed order, so no layer is skipped and none is read twice",
    "say which layer can veto which",
]) + f"""
<p>Every reading on Pragati belongs to one of six layers. Read them in this order. A higher layer sets the meaning of everything below it, and a layer that cannot be read stops the reading there.</p>
{flow([("1 · Readable?", "Standard chart, warmed up, nothing paused"), ("2 · Regime", "Trend, balance, transition, quiet, dislocation"), ("3 · Location", "In value, out of value, against the trail"), ("4 · Control and value", "The grid family and its phases"), ("5 · Flow", "Open interest, crowding, the gold cast"), ("6 · Trigger", "▲ ▼, a flip, an AM change")])}
{tbl(["Layer", "Where to look", "Questions", "It can veto"], [
    ["1 · Readable", "SIGNALS PAUSED label, grey tapes, gate warming, non-standard chart, the panel's rungs live", "Is every layer I am about to read actually computed?", "Everything. A paused layer is not a neutral reading; it is no reading"],
    ["2 · Regime", "AUCTION STATE (migration), the trail's side, Accepted momentum's CHART cell, the panel's raw-share row (QUIET)", "Is value moving, and do the two definitions of trend agree?", "Trade entries: no trend trade in a FLAT · disagree regime"],
    ["3 · Location", "The value ribbon, the trail, the session profile's Location row", "Is price accepted here, or probing beyond?", "Chasing: a probe is a caution on the trend (⟦ref:fk-num⟧)"],
    ["4 · Control and value", "CVG STATE, WHY and PUSH; the pane's tapes and background", "Who controls the ladder, is price cheap or rich, and are both edges confirmed?", "Adding: no adds into a held row or a widening dislocation"],
    ["5 · Flow", "OI STATE and WHY; gold-cast columns", "Is risk being opened or closed, and is the book crowded?", "Size, never direction"],
    ["6 · Trigger", "▲ ▼ on the pane; the AUCTION row's CHART changes; alerts", "Has a measured event happened at this close?", "—"],
], "The context stack", [16, 30, 30, 24])}
<p><b>Why this order.</b> Readability first, because a paused layer looks like a neutral one. Regime before location, because "below value" means a probe in a trend and a rotation in balance. Location before the grid, because the grid knows nothing about where value was accepted. Flow is a size modifier and never sets direction: the four-quadrant reading is unmeasured at the bar level {U}. The trigger comes last, because a trigger read before its context is a coin flip with a story attached.</p>
""")

S["ctx-routine"] = sec("ctx-routine", "The five-minute top-down routine", objectives([
    "run one routine on every chart, at every close you act on",
    "write the reading down in one line",
]) + f"""
{steps([
    ("Weekly chart, one minute", "Grid family and phases (the ▲ and the grid were tested weekly). Trail side. Is the weekly value tape solid either way? This is the tide."),
    ("Daily chart: readability", "Any gold label, grey tape or <span class=\"k\">gate warming</span>? Note it, and read only what is computed."),
    ("Daily chart: regime", "AUCTION STATE and the CHART cell. Write <i>trend up</i>, <i>trend down</i>, <i>balance</i>, <i>transition (FLAT · disagree)</i> or <i>quiet</i>."),
    ("Daily chart: location", "Close in value, above or below the ribbon? Any probe × in the last five bars? How far is the trail, in ATRs?"),
    ("Daily chart: control and value", "CVG STATE with units; WHY phases; PUSH. Is anything HELD?"),
    ("Daily chart: flow", "Futures only: OI character and crowding. Stale, warming or untrusted means skip this layer."),
    ("Daily chart: trigger", "A ▲ or ▼ at this close? Did the CHART cell change? Did the trail flip?"),
    ("Write one line", "For example: <span class=\"k\">RELIANCE · D · readable · trend down (SHORT 0.50) · below value, no probe · Accumulate 1.5, sellers running, still cheapening · no OI · no trigger</span>."),
])}
<p>The line takes ten seconds once the routine is habit, and it is what your journal stores (⟦ref:mg-journal⟧). Two weeks of lines on the same market teach more than any chapter here.</p>
""")

S["ctx-tf"] = sec("ctx-tf", "Timeframes without double counting", objectives([
    "choose a decision timeframe and an execution timeframe",
    "avoid reading the same horizon twice",
]) + f"""
<p>Pragati already reads several timeframes inside one chart: conviction from inside the bar, value from above it (⟦ref:kb-ladder⟧). Opening a second chart one step up does not add a fresh opinion. A daily chart's value tape <i>is</i> the weekly and the daily. Use other timeframes for different jobs, not for more votes.</p>
{tbl(["Job", "Timeframe", "Why", "Evidence"], [
    ["Investing decisions", "Weekly, then daily", "The ▲ and the grid were measured on both; weekly is calmer", X],
    ["Accepted momentum", "Daily, decided at the close", "The only timeframe it was tested on", M],
    ["Execution", "Intraday (15m to 1h)", "To choose an entry inside the next session: never to change the daily decision", U],
    ["Swing context", "Daily trail and ribbon", "Value over six months", U],
    ["Intraday trading", "5m to 1h", "Nothing was measured, and costs eat most measured edges below daily", "Costs: " + X],
], "Timeframe jobs", [22, 22, 38, 18])}
<p><b>When weekly and daily disagree.</b> The weekly grid in DOWN · cheap while the daily reads UP · cheap means a turn is starting inside a weekly dislocation. That is the picture the capitulation plan is built for, and the daily leads. A weekly Exit · distribution with a daily Buy is a bounce inside distribution: the daily does not overrule the weekly for a holding.</p>
""")

S["ctx-regime"] = sec("ctx-regime", "Five regimes and how to tell them apart", objectives([
    "name the regime from the readout in under a minute",
    "know what each regime does to every other reading",
]) + f"""
{tbl(["Regime", "How it reads", "What it changes"], [
    ["<b>Trend</b>", "Trail side and S agree: " + chip("LONG 0.45", "bull") + " or " + chip("SHORT 0.38", "bear") + ". AUCTION STATE Shifting or Migrating its way, for weeks", "Breakouts from value in its direction did better than pullbacks into it (⟦ref:fk-entry⟧). Probes against it are cautions on the trend, not reversals"],
    ["<b>Balance</b>", "AUCTION STATE Balance; S small; price rotating inside the ribbon; the trail flat or recently flipped", "Edges of value are references, but no setup is measured here " + U + ". The grid's FAINT families dominate"],
    ["<b>Transition</b>", chip("FLAT · disagree", "neut") + ": the trail and momentum point opposite ways. Often follows a flip, or a long probe cluster", "Accepted momentum is flat by design: no trend trade. On the 126-bar trail, a probe with migration already toward it flipped 15–28% of the time within 20 bars, against about 4% otherwise " + M],
    ["<b>Quiet</b>", "Panel raw-share row QUIET; desaturated columns; the push gate shut; the trail frozen far from price", "Readings are amplified: a small imbalance reads large. The grid's rows hold. Do not read the trail's distance as risk " + M],
    ["<b>Dislocation</b>", "The value tape solid past θ; the grid in a CHEAP or RICH family; pane tinted green (capitulation) or red (distribution)", "The investor's regime. Capitulation followed by gains in every era outside crypto; distribution by underperformance " + X],
], "The five regimes", [16, 42, 42])}
<p>Regimes overlap. A market can be in a trend and quiet at once, which is the common case for an orderly index, or in a dislocation inside a downtrend. Write both. The regime that changes your <i>action</i> is the one to lead with.</p>
""")

S["ctx-meaning"] = sec("ctx-meaning", "Same reading, different meaning", objectives([
    "translate a reading through its context before acting on it",
]) + f"""
{tbl(["Reading", "In a trend its way", "Against a trend", "In balance", "In a quiet regime"], [
    ["Probe × (126-bar trail)", "Caution on the trend: it did worse than usual for 10–20 bars " + M, "A probe toward the counter-trend: still rarely accepted (under 5% in 20 bars) " + M, "Rotation inside value", "As in a trend; the trail cannot step anyway"],
    ["Close out of value (beyond the ribbon), its way", "The measured better entry, ahead of pullbacks " + M, "A probe against the trend", "A test of the edge " + U, "Possibly amplified; size smaller"],
    ["Close back into value from outside", "A pullback: no measured edge over the trend's average bar " + M, "—", "Rotation", "—"],
    ["CVG Buy 3+ (TURNED, DISLOCATED)", "A dip bought inside a trend: what the capitulation plan is built for " + U, "A turn against the trend: build in stages " + U, "Accumulate", "Rows held; units unreliable"],
    ["CVG Exit (DISTRIBUTION)", "Early distribution while still long " + X, "Aligned to the downside", "Exit or avoid", "Rows held"],
    ["OI long build-up", "Committed buyers " + U, "Shorts are being met by new longs " + U, "Inside value: positioning", "—"],
    ["OI short covering (gold)", "A rally on exits: fragile; gold-cast pushes lagged " + X, "A squeeze into a downtrend", "—", "—"],
    ["A ▲", "A capitulation dip inside an uptrend: add " + X, "A capitulation inside a downtrend: the classic horizon conflict; stage small " + X, "Stage in " + X, "Fires only on a readable grid; trust it as usual"],
], "Context translates the reading", [20, 20, 20, 20, 20])}
<p>The table's left column never changes on the chart. Its meaning does. When two columns seem to apply, use the stricter one.</p>
""")

S["ctx-class"] = sec("ctx-class", "Asset classes", objectives([
    "know what changes from one class to another before trusting a reading",
]) + f"""
{tbl(["Class", "What to know"], [
    ["Indices", "Spot indices have no volume: participation falls back to relative true range, and the profile to TPO. Accepted momentum was tested on 16 Indian indices. Index futures carry OI"],
    ["NSE stocks", "The bulk of the Accepted momentum holdout (391 stocks) " + M + " and of the OI evidence (NSE F&amp;O) " + X + ". Today's listings only, so survivorship applies. Costs assumed: 15 bps one way"],
    ["Commodities", "The ▲ and the grid were positive in commodities " + X + ". Continuous futures roll: expect structural OI bars at each roll"],
    ["FX", "INR pairs are managed and quiet: σ is low, so the tested weight (10% ÷ volatility) can reach its cap of 2. USD/INR's annualised volatility was 8.6% at the end of October 2026, so a size-0.10 position was already 0.12 of capital " + M + ". The INR pairs lost money in the Accepted momentum test " + M],
    ["Crypto", "Capitulation <b>failed</b> on crypto " + X + "; its tint and ▲ are gold. Crypto trends; Accepted momentum was about flat on crypto " + M + ". Bars run seven days a week, so 300 bars are about ten months"],
    ["ETFs", "Read as their underlying. Thin ETFs print stale prices; check the panel's participation and the ribbon's width"],
], "Class notes", [16, 84])}
""")

# ── Part V ───────────────────────────────────────────────────────────────────
S["fk-life"] = sec("fk-life", "The life of a break", objectives([
    "follow a break from its first bar to its resolution",
    "say how often each outcome happens, on both trails",
]) + f"""
<p>A <b>break</b> is a close beyond the trail. It is resolved in one of two ways. Either the market's value follows and has migrated, and the break is <b>accepted</b>, so the trail flips at that close. Or it does not, and the bar is a <b>probe</b>: a gold × marks its first bar. A probe then either flips the trail later or ends with price back on the trail's side.</p>
{flow([("Probe onset ×", "A close beyond the trail; POC or migration not with it"), ("Probe episode", "A median of 4 bars on the 126-bar trail, 3 on the 20-bar"), ("Rejected", "Back on the trail's side, no flip"), ("or accepted", "POC beyond and value migrated: the trail flips")])}
{tbl(["", "126-bar trail (default)", "20-bar trail (AM off)"], [
    ["Probe onsets measured", "6,012 · 3,019 · 31,961", "11,955 · 5,706 · 62,616"],
    ["Back on the trail's side within 5 bars", "57% · 58% · 57%", "56% · 56% · 55%"],
    ["Flipped within 10 bars", "2.3% · 1.9% · 1.9%", "27% · 28% · 26%"],
    ["Flipped within 20 bars", "<b>4.5% · 3.8% · 4.2%</b>", "<b>59% · 59% · 59%</b>"],
    ["Median probe length", "4 bars", "3 bars"],
], "What breaks become (DEV · HB · HA, setup lab)", [34, 33, 33])}
<p>The two trails behave like different instruments. A six-month floor is almost never broken by a probe: fewer than one probe in twenty is followed by a flip within a month. A twenty-bar trail flips after most probes, and at about the rate the same rules produce on driftless random walks (58%). On the short trail, a probe says little beyond the trail's own mechanics {M}.</p>
""")

S["fk-num"] = sec("fk-num", "What a probe does to the trend", objectives([
    "say what the gold × is worth, measured",
    "stop treating probes as fakeouts to fade",
]) + f"""
<p>The prediction, written before the test, was that probes are fakeouts: after one, the trail's side should do at least as well as it usually does. It came out the other way, in every set and on both trails {M}.</p>
{tbl(["Outcome on the trail's side, beyond its average bar", "DEV (2006–19)", "HB (2020–26)", "HA (411 unseen markets)"], [
    ["126-bar trail, next 10 bars", "−0.076σ (t −3.0)", "−0.048σ (t −1.9)", "−0.070σ (t −8.5)"],
    ["126-bar trail, next 20 bars", "−0.092σ (t −2.2)", "−0.038σ (t −1.4)", "−0.080σ (t −8.7)"],
    ["20-bar trail, next 10 bars", "−0.056σ (t −3.4)", "−0.039σ (t −2.3)", "−0.048σ (t −8.2)"],
], "After a probe onset (setup lab F1)", [34, 22, 22, 22])}
{note("<b>The probe is a caution on the trend, not a fakeout.</b> On the default trail it almost never flips the side, but the side's next two to four weeks are weaker than usual, by about 0.05 to 0.09σ. That is exactly what gold means in Pragati: <i>smaller, or later</i>. Do not add on a probe. Do not fade it either (next section). Hold, and let the trail decide.", rule=True)}
<p>The sizes are small, as every honest edge here is: a lean measured across thousands of events, worth acting on only as a size adjustment across many markets.</p>
""")

S["fk-check"] = sec("fk-check", "What gets accepted: the fakeout checklist", objectives([
    "score a break against four conditions at the close",
    "know which conditions matter on which trail",
]) + f"""
<p>Four features of the break bar were tested, each predicted in advance to make acceptance likelier. A break that will be accepted is the opposite of a fakeout.</p>
{tbl(["At the probe's first bar", "20-bar trail: flips within 20 bars", "Verdict", "126-bar trail", "Verdict"], [
    ["<b>Depth</b>: the close at least 0.5 ATR beyond the trail", "71% vs 54% (HA; t 37.5)", "<b>Confirmed</b> " + M, "4.3% vs 4.1%", "Not supported"],
    ["<b>Weight</b>: participation w ≥ 1.5", "62% vs 57% (HA; t 9.7)", "<b>Confirmed</b> " + M, "3.2% vs 4.5% (fewer)", "Not supported (opposite)"],
    ["<b>Push</b>: the push gate against the trail", "60% vs 55% (HA; t 8.6)", "Consistent " + M, "3.4% vs 4.8% (fewer)", "Not supported (opposite)"],
    ["<b>Migration</b> already toward the break", "62% vs 58% (HA; t 5.1)", "Consistent " + M, "15–28% vs about 4%", "<b>Consistent</b> " + M],
], "The four conditions (setup lab F2; DEV, HB and HA all reported in docs/setup-lab.md)", [30, 22, 14, 20, 14])}
{tbl(["Conditions met", "0", "1", "2", "3", "4"], [
    ["20-bar trail, HA (62,616 probes)", "51%", "56%", "62%", "71%", "72%"],
    ["20-bar trail, DEV", "52%", "57%", "64%", "73%", "77%"],
    ["20-bar trail, HB", "49%", "57%", "63%", "69%", "66%"],
], "Flip rate within 20 bars by the number of conditions met", [30, 14, 14, 14, 14, 14])}
<h4>The checklist</h4>
{checklist([
    "Which trail? On the <b>126-bar</b> default, only migration matters: is AUCTION STATE already Shifting or Migrating toward the break? If not, the break is very unlikely to be accepted within a month.",
    "On the <b>20-bar</b> trail, count: depth ≥ 0.5 ATR · participation ≥ 1.5 · push against the trail · migration toward the break.",
    "Zero or one condition: about one break in two is accepted, the rate of chance. Two or more: about two in three. Three or more: about seven in ten.",
    "Whatever the count: a probe on the 126-bar trail is a caution on the side you hold (⟦ref:fk-num⟧).",
])}
<p>On the six-month trail, hard and heavy breaks were <i>less</i> likely to flip it. A six-month floor is not broken by one day's force; it is broken when value moves.</p>
""")

S["fk-entry"] = sec("fk-entry", "Entries around value, measured", objectives([
    "say which of four entry rules carried timing beyond the trend itself",
]) + f"""
<p>Four entries were tested on the 126-bar trail. Each was measured against the trend's own average bar, so a positive number is timing <i>beyond</i> simply being on the right side.</p>
{tbl(["Entry at the close", "10 bars: DEV · HB · HA", "20 bars: DEV · HB · HA", "Verdict"], [
    ["<b>Rejection</b>: the first bar back on the trail's side after a probe", "−0.03 · +0.02 · −0.04 (t −5.3)", "−0.06 · +0.05 · −0.04", "Not supported " + M],
    ["<b>Acceptance</b>: the flip bar, in the new direction", "+0.02 · +0.09 · +0.08 (t 4.4)", "+0.05 · +0.11 · +0.11 (t 6.7)", "Consistent " + M],
    ["<b>Pullback into value</b>, AM agreeing", "−0.00 · +0.01 · −0.00", "−0.01 · −0.05 · −0.01", "Not supported " + M],
    ["<b>Breakout from value</b>, AM agreeing", "+0.06 (t 4.1) · +0.05 (t 2.5) · +0.06 (t 10.4)", "+0.04 · +0.04 · +0.05", "Positive everywhere; not predicted " + M],
], "Four entries (σ beyond the trend's average bar; setup lab S1–S4)", [34, 26, 22, 18])}
{note("<b>With the trend, the break of value beats the return to it.</b> A close out of value in the trend's direction, with Accepted momentum agreeing, did better than the trend's average bar in all three sets. A pullback into value did not, and the difference between the two was significant everywhere (t −2.5 to −11.5). Buying the dip into value is the intuitive trade, and it measured nothing here. Breakouts were not predicted, so treat the result as strong evidence that a fresh test must still confirm.", rule=True)}
<p>Hit rates sit between 50% and 54%. None of these is a setup that wins most of the time. They change <i>when</i> you act inside a trend that Accepted momentum already holds, and by how much.</p>
""")

TRAPS = [
    ("Chasing the probe ×", "A close beyond the trail looks like a breakout", "On the 126-bar trail fewer than 1 in 20 flip it within 20 bars " + M, "Wait for the flip; treat the probe as a caution on your side"),
    ("Fading the probe", "Price back on the trail's side looks like a failed break to buy", "The rejection entry measured nothing, negative in HA " + M, "Hold what the system holds; do not add on the rejection"),
    ("Buying the dip into value", "\"Value is support\"", "Pullbacks into value: no edge; breakouts from value did better " + M, "Prefer the close out of value in the trend's direction"),
    ("The forming bar", "A ▲, a tint or a probe appears intraday", "Live readings can vanish before the close (⟦ref:kb-repaint⟧)", "Decide at the close"),
    ("The trace as a timing signal", "The trace turning up looks like a buy", "The trace and histogram carry almost no timing information " + X, "Read them as description"),
    ("Trace and signal crossovers", "A crossing looks like a trigger", "k = 0 was the worst setting out of sample " + X, "Ignore plain crosses"),
    ("Divergence", "Price higher, conviction lower", "R about zero, H negative or mixed " + X, "Leave R and H off"),
    ("The ◆", "A pullback resumed with control", "Negative in both eras outside crypto " + X, "Leave it off"),
    ("The 20-bar trail as a trade", "It flips often and looks responsive", "It failed every mark of a pre-registered test " + M, "Use Accepted momentum, or the trail as structure"),
    ("Quiet loudness", "A bright reading in a dead market", "Scaling divides by a collapsed σ " + U, "Check the panel's raw-share row for QUIET"),
    ("Gold read as a direction", "Gold looks like a warning to sell", "Gold means caution only", "Smaller, or later. Never short because of gold"),
    ("Held rows", "The family name looks current", "The row is held against its tape; the histogram has not confirmed", "No adds into a held row"),
    ("Capitulation on crypto", "A ▲ on BTC", "The capitulation reading failed on crypto " + X, "Do not use the ▲ or the grid's Buy 4 on crypto"),
    ("Short-covering rallies", "A green push", "Pushes paid for by exits lagged " + X, "Size down under a gold cast"),
    ("Expiry OI", "A collapsing book reads as unwinding", "Rolls and expiries move the book mechanically", "Ignore OI character in expiry week"),
    ("Non-standard candles", "Heikin Ashi looks smoother", "Every price on it is synthetic", "Use standard candles; Pragati pauses otherwise"),
    ("The trail's level as a stop", "The line looks like support", "The default trail can freeze far from price in a quiet regime " + M, "Stops from ⟦ref:stops⟧, not the trail's distance"),
    ("One-market Accepted momentum", "It worked on the backtest of my favourite stock", "On one market the median Sharpe was +0.23 to +0.38, and a quarter lost " + M, "Run it across many markets, sized alike"),
    ("Tuning to a backtest", "Better settings for this stock", "Fitted and unseen edge correlated at about zero over 900 sets " + X, "Keep the defaults"),
    ("Intraday costs", "More signals on 5-minute bars", "Costs reach 0.09R against a best edge near 0.05R " + X, "Daily for decisions"),
    ("Left-edge ▲s", "A ▲ appears on old history after a reload", "The intrabar depth cap slides with time (⟦ref:kb-ladder⟧)", "Trust ▲s inside every rung's reach"),
]

S["fk-traps"] = sec("fk-traps", "The trap catalogue", objectives([
    "recognise twenty-one ways to lose money with this indicator, and the evidence behind each",
]) + tbl(["Trap", "Why it tempts", "What the evidence says", "Instead"], [[f"<b>{a}</b>", b, c, d] for a, b, c, d in TRAPS],
         "Twenty-one traps", [20, 24, 32, 24]))

S["fk-protocol"] = sec("fk-protocol", "The fakeout protocol", objectives([
    "run a five-question check before acting on any break",
]) + f"""
{steps([
    ("Is this bar closed?", "If not, nothing has happened yet."),
    ("Which trail, and which event?", "A flip is acceptance. A gold × is a probe. A close out of the ribbon with the trail is a break of value, not of the trail."),
    ("If it is a probe against my position", "Do not exit on it, and do not add. On the 126-bar trail it is a caution: if you trade discretionarily, size down by a step, or wait (⟦ref:fk-num⟧)."),
    ("If it is a probe in my favour (against the trail)", "Do not enter on it. Score it (⟦ref:fk-check⟧). On the 126-bar trail, only migration toward it makes acceptance plausible."),
    ("If it is a break of value with the trend", "The measured better entry. Is Accepted momentum agreeing (LONG or SHORT, not FLAT)? Then it is the moment to act if you were waiting to (⟦ref:ts-break⟧)."),
])}
""")

ORDER4 = ["ctx-stack", "ctx-routine", "ctx-tf", "ctx-regime", "ctx-meaning", "ctx-class"]
ORDER5 = ["fk-life", "fk-num", "fk-check", "fk-entry", "fk-traps", "fk-protocol"]
