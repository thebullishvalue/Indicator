"""Part II · The knowledge base. Every engine from the bar up, with its formula, defaults, warm-up and limits.
Sources: pragati.pine (header, inputs, engine code), docs/auction-trail-spec.md, the audits."""
from kit import M, X, U, sec, tbl, chip, k, note, steps, math, objectives, cards, flow

S = {}

# ── The conviction engine ────────────────────────────────────────────────────
S["kb-bar"] = sec("kb-bar", "From a bar to a share", objectives([
    "compute a bar's conviction and its participation weight by hand",
    "say what the Agreement and Effort denominators measure, and why the default is Agreement",
    "explain why participation is capped",
]) + f"""
<p>Conviction is Pragati's first instrument and its oldest. It asks how much of a bar's travel became displacement, and how consistently bars resolve one way, weighted by how much participation stood behind them.</p>
<h4>One bar</h4>
{math("c   = (close − previous close) ÷ true range         bounded −1 … +1" + chr(10) + "w   = min( volume ÷ EMA20(volume), 3 )            the participation weight")}
<p>A bar that closes at its high after opening at the previous close has <i>c</i> = +1: every tick of its range became net movement. A bar that travels widely and closes where it started has <i>c</i> ≈ 0, however violent it was.</p>
<p>The weight <i>w</i> is the bar's volume against its own 20-bar average. Where a bar prints no volume, the last good print is carried through hollow bars. Where the symbol has no volume at all, as with index spot, relative true range stands in. That is the <span class="k">Auto</span> setting of <span class="k">Participation</span>. <span class="k">Volume</span>, <span class="k">True range</span> and <span class="k">Off</span> force one choice. Off gives equal weights, a control: if the reading barely changes with it off, volume tells you nothing on that symbol.</p>
<p><b>The cap at 3</b> matters more than it looks. Expiry days, index rebalances and block prints carry volume many times normal. Uncapped, one such bar would own the whole window for its full length, and the oscillator would be reporting that one bar. The original author's tests found participation weighting earns its place, with Off the worst setting in all three signal architectures tested {X}.</p>
<h4>The window: the raw share</h4>
{math("Agreement (default)   raw = 100 × Σ(c·w) ÷ Σ(|c|·w)     over the Lookback (20 bars)" + chr(10) + "Effort                raw = 100 × Σ(c·w) ÷ Σ w")}
<p><b>Agreement</b> is Chande's form, the RSI family, applied to range-normalised closes weighted by participation. It asks how <i>consistently</i> bars resolve one way. A bar that went nowhere drops out of both sums, so heavy volume with no progress is invisible to it. Every number in the script's evidence was measured on this form.</p>
<p><b>Effort</b> divides by total participation, which is Wyckoff's law taken literally. A heavy bar that went nowhere dilutes the reading, as Chaikin money flow divides by volume. It is untested {U}. Whichever is chosen, the panel's <span class="k">effort → result</span> row measures absorption under both (⟦ref:kb-hist⟧).</p>
{tbl(["Bar", "Close change", "True range", "c", "Volume ÷ average", "w", "c · w", "|c| · w"], [
    ["1", "+12", "20", "+0.60", "1.2", "1.2", "+0.72", "0.72"],
    ["2", "+3", "15", "+0.20", "0.8", "0.8", "+0.16", "0.16"],
    ["3", "−8", "16", "−0.50", "2.0", "2.0", "−1.00", "1.00"],
    ["4", "+10", "12", "+0.83", "4.5", "3.0 (capped)", "+2.50", "2.50"],
], "A worked raw share over four bars (constructed arithmetic)", [8, 14, 13, 9, 17, 15, 12, 12])}
<p>Over these four bars Σ(c·w) = +2.38 and Σ(|c|·w) = 4.38, so Agreement reads 100 × 2.38 ÷ 4.38 = <b>+54</b>: buyers won most of the weighted travel. Effort divides by Σw = 7.0 and reads <b>+34</b>. Bar 3's heavy, failed sale counts against buyers in both. Bar 4's spike counts as 3, not 4.5.</p>
""")

S["kb-scale"] = sec("kb-scale", "Scaling, zones and the quiet regime", objectives([
    "say what +30 and +60 mean on any instrument",
    "explain why a dead market can read loud, and how Pragati marks it",
]) + f"""
{math("conviction = 100 · tanh( raw ÷ 3σ )        σ = standard deviation of raw over the Normalization window (200)")}
<p>The raw share is divided by three of its own standard deviations and squashed by tanh, so the reading is bounded at ±100 and calibrated to the instrument. The inner zone, <b>±30</b>, is occupied about a third of the time. The outer zone, <b>±60</b>, is occupied about 4% of the time: measured at 3.2% to 4.3% {X}.</p>
<p>Two consequences follow, and both are easy to forget.</p>
<ul>
<li><b>Scaling is relative.</b> +60 is extreme <i>for this instrument over this window</i>. It is not a universal overbought line. Past the outer zone is where trends run, and also where they end.</li>
<li><b>Scaled, not centred.</b> Zero keeps meaning "neither side in control". On a persistently trending instrument one side's zone is simply visited more often.</li>
</ul>
<h4>The quiet regime</h4>
<p>When σ itself collapses, a small imbalance divided by a small σ reads large. Pragati watches for this. The quiet regime is σ in the <b>bottom fifth of its own history</b>, ranked over four Normalization windows (800 bars at the defaults). While it holds:</p>
<ul>
<li>the histogram's columns lose about half their colour, while the trace carries conviction;</li>
<li>the panel's raw-share row reads QUIET;</li>
<li>conviction's <b>push gate shuts</b>. The grid's rows hold, and the acceptance trail cannot step (⟦ref:kb-trail⟧).</li>
</ul>
<p>Quiet is not rare, and it clusters. On the repository's reference code it held on about a fifth of all bars, as designed, but on <b>85% of NIFTY 50's last 300 bars</b> to October 2026 and 58% of gold's {M}. ⟦Chap:c25⟧ shows what that does to the trail.</p>
""")

S["kb-hist"] = sec("kb-hist", "The histogram, its tiers and the push gate", objectives([
    "read a column's hue, lightness and saturation as three separate answers",
    "name the four tiers and say which ones open the push gate",
    "say how long the gate takes to warm up",
]) + f"""
<p>The trace is smoothed by a short EMA (<span class="k">Smoothing</span>, 3) and compared with its own signal line (<span class="k">Signal EMA</span>, 9). The histogram is the gap:</p>
{math("histogram = trace − EMA9(trace)        impulse when |histogram| ≥ k · σ(histogram)    k = 0.5, σ over 200 bars")}
<p>A plain crossing of trace and signal is <b>not</b> a signal here. Two lines near zero cross endlessly, and k = 0 (a plain crossover) was the worst value out of sample in a 900-configuration search {X}.</p>
{tbl(["Tier", "Condition", "Drawn", "Push gate"], [
    ["0 · impulse", "Growing away from zero, past k·σ", "Near-solid", "Open, on its side"],
    ["1 · building", "Growing away from zero, below k·σ", "Moderate", "Open, on its side"],
    ["2 · decelerating", "Shrinking, the trace still moving with it (by more than 0.1σ of its bar-to-bar change)", "Mid", "Open, on its side"],
    ["3 · turning", "Shrinking with the trace flat or against it", "Pale", "<b>Shut</b>"],
], "The histogram's four tiers", [18, 44, 14, 24])}
<p><b>Hue is not control.</b> A column's hue is which side of its signal line the trace is on, which is the direction of the <i>push</i>. A green column with the trace at −45 means sellers are still in control but their grip is easing.</p>
<h4>The push gate</h4>
<p>The gate is the one thing every layer of Pragati that "moves" waits for. The grid's rows move only on it (⟦ref:kb-grid⟧), and the acceptance trail starts and steps only on it (⟦ref:kb-trail⟧):</p>
{math("gate = +1   histogram ≥ 0, tier 0, 1 or 2, not quiet" + chr(10) + "gate = −1   histogram < 0, tier 0, 1 or 2, not quiet" + chr(10) + "gate =  0   tier 3 (turning), or the quiet regime")}
<p>It always reads <b>conviction's own histogram</b>, whichever trace the pane draws. Only on the Conviction trace are the pane's columns the gate's columns.</p>
<p><b>Warm-up.</b> The histogram's σ needs a clean 200-bar window of a histogram that itself needs the trace's 200-bar σ. The gate therefore reads from about <b>450 bars</b>, 1.8 years of daily bars. Until then the grid's rows have no memory, the trail cannot start, and the readout says <span class="k">gate warming</span>.</p>
<h4>Effort → result</h4>
<p>The panel's row Σ|c|·w ÷ Σw is the share of the window's participation that became directional displacement. At 100%, every bar closed at its extreme. In the bottom fifth of its own history the row turns gold and reads <span class="k">ABSORBED</span>: effort met by opposing orders, which can resolve either way. Only the ◆ reads it; requiring absorption did not improve the ▲ {X}.</p>
""")

# ── The value engine ─────────────────────────────────────────────────────────
S["kb-vlegs"] = sec("kb-vlegs", "Samanvaya's two legs", objectives([
    "say what 'cheap' and 'rich' mean in Pragati, and what they do not mean",
    "name the two legs and what each one sees",
]) + f"""
<p>Value is Samanvaya's engine, carried into Pragati line for line. Where conviction asks <i>who is pushing</i>, value asks <i>where price stands against fair</i>. Cheap and rich are statistical statements about this price against a model of it. They are not statements about a company's worth.</p>
{cards([
    ("Leg 1 · Relative value (RV)", "<p>The chart's own return is hedged against a stepwise-selected basket of macro drivers (rates, currencies, commodities and the like). A custom ninth driver can be added. The residual spread is scored over an ensemble of timescales.</p><p class=\"where\">The hedge is applied in proportion to its measured skill, its rolling out-of-sample R² (<span class=\"k\">Macro hedge · Auto</span>). The model is fitted on an anchored clock: one observation per closed day by default, or per week. It spends 22 of Pine's 40 data requests.</p>"),
    ("Leg 2 · Breadth", "<p>Seven causal views of the chart's own price: the Market Strength Factor at five timescales, plus the fastest as momentum only and the slowest as flow only. It is the price-only half of Tattva's Swayam ensemble.</p><p class=\"where\">Breadth is momentum, so it overlaps conviction. The panel's <span class=\"k\">layer overlap</span> row measures by how much rather than assuming it away.</p>"),
])}
<p>The two legs are blended in z-space, with their correlation measured, at <span class="k">Leg mix</span> 0.5: the equal blend Samanvaya measured best (+0.0691 against +0.0637 for RV alone) {X}. Set the mix to 1.0 to see value without momentum.</p>
<h4>On every timeframe</h4>
<p>The model takes one observation per closed anchor period, a day by default, and each observation is the <b>sum</b> of the chart-bar returns inside it. Before the fix, on a 5-minute chart the whole macro fit ran on one closing 5-minute return a day, and value carried no macro information. The panel's <span class="k">value · macro share</span> row shows how much of value is relative value on this chart.</p>
<p><b>Driver timing.</b> On a daily NSE chart many drivers close hours later; TVC:US10Y closes about eleven hours after NSE. A driver whose bar closes more than a third of a bar late is read at its previous close, the value known at the chart's close. The panel's <span class="k">value · driver timing</span> row shows what was lagged.</p>
""")

S["kb-vscale"] = sec("kb-vscale", "From z to θ: the value scale", objectives([
    "convert θ into the pane's units",
    "say when the value tape leaves grey",
]) + f"""
{math("value = 100 · softbound( 0.5 · z )         z = Samanvaya's unified z (RV ⊕ breadth)" + chr(10) + "θ     = 1.5 (in |z|)   →   ±43 on the pane and the tapes")}
<p>Value is positive when price is <b>rich</b> and negative when it is <b>cheap</b>. θ, <span class="k">θ · value threshold</span>, is where Samanvaya calls price cheap or rich: 1.5σ at the default, which lands at ±43. The literature standard for a mean-reversion entry is 1.5 to 2.5. θ sets:</p>
<ul><li>the grid's columns, and with them the ▲ (DOWN · cheap) and the ▼ (DOWN · rich);</li>
<li>the value tape's knee and the ◆'s and H's value tests;</li>
<li>the inner rail of the Value and blended traces.</li></ul>
<p><b>Colours are flipped on purpose.</b> On Pragati's value tape, <span style="color:var(--bull)">green is rich</span> and <span style="color:var(--bear)">red is cheap</span>, the reverse of Samanvaya's own pane. A rally makes price rich <i>and</i> conviction positive, so both tapes turn green together. A split in hue between them is then the thing the eye catches.</p>
<p><b>Warm-up.</b> The value tape stays neutral grey until Samanvaya's model is built: ten anchor periods past a twelve-period hold-out, and the basket settled. While a basket settles after a rotation, a blended trace dims.</p>
<p><b>Measured.</b> The 1.5σ entry and the leg mix are Samanvaya's own measurements on 24 targets {X}. The v9 audit varied θ from 1.0 to 2.0 and kept the capitulation edge at every value; none beat 1.5 in its worst era {X}.</p>
""")

# ── The ladder and the four tapes ────────────────────────────────────────────
S["kb-ladder"] = sec("kb-ladder", "The ladder of timeframes", objectives([
    "list the frames each ladder reads on your chart",
    "explain how a lower frame is read without sampling only its last bar, and a higher one without repainting",
    "recognise a fallback (↺) and the intrabar depth limit",
]) + f"""
<p>Both instruments are read across a fixed ladder of standard frames, the same on every venue. A frame is used only if the larger of the two holds a whole number of the smaller's bars; a reconstruction that split bars across bars would be inventing data.</p>
{tbl(["Chart", "Ladder down (conviction default)", "Ladder up (value default)"], [
    ["3m", "1m · 3m", "4h · 1h · 30m · 15m · 3m"], ["5m", "1m · 5m", "4h · 1h · 30m · 15m · 5m"],
    ["15m", "1m · 3m · 5m · 15m", "4h · 1h · 30m · 15m"], ["30m", "1m · 3m · 5m · 15m · 30m", "4h · 1h · 30m"],
    ["1h", "1m · 3m · 5m · 15m · 30m · 1h", "4h · 1h"], ["4h", "1m … 1h · 4h", "none → falls back ↺"],
    ["D", "1m · 3m · 5m · 15m · 30m · 1h · 4h · D", "W · D"], ["W", "1h · 4h · D · W", "none for conviction ↺; value M · W"],
], "Which frames each ladder reads", [12, 46, 42])}
<p><b>Ladder down</b> asks whether the chart's conviction is <i>built</i> from the horizons inside each bar. It is faster than chart conviction. <b>Ladder up</b> asks whether it is <i>held</i> by the horizons that contain the chart, and is slower. With the defaults (conviction down, value up) every reading spans three horizons: inside the bar, the chart, and above it.</p>
<p>The value ladder keeps Samanvaya's own rungs. Ladder up carries the whole composite on every higher frame. Ladder down reads only the three frames nearest below (daily reads 30m · 1h · 4h · D), breadth leg only: the RV leg cannot be re-run per rung inside Pine's request budget.</p>
<h4>How a lower frame is read</h4>
<p>Sampling a 1-minute rung at the daily close would describe the last few minutes of the day. Instead each lower frame runs the full engine on its own history, and the chart bar takes the <b>participation-weighted average</b> of that frame's reading across all its bars inside the chart bar: the bar seen from inside. TradingView caps the intrabars one request carries, about 100,000 on most plans, so the finest rungs reach back less far than the chart. Older bars run without them, and the panel's <span class="k">rungs live</span> row says how many rungs a bar carried.</p>
<p><b>One disclosed drift.</b> The depth cap counts back from today. As days pass, the oldest bars fall out of a fine rung's reach. After a reload, a ▲▼ at the left edge of that coverage can appear or vanish. A bar inside every rung's reach never changes.</p>
<h4>How a higher frame is read</h4>
<p>A higher frame read the usual way is a staircase, or it repaints. Pragati reconstructs it instead:
<ul>
<li>from the parent frame comes only its <b>settled</b> state as of its last closed bar;</li>
<li>from the chart comes the parent bar now forming, aggregated from the chart's own bars.</li>
</ul>
The result lands on the parent's settled value at its close and is identical in history and in realtime. The panel's <span class="k">ladder · rebuild error</span> row reports how closely it landed, in points.</p>
<p><b>Fallback ↺.</b> A direction with no frames on this chart reads the other direction instead of pausing every signal, and the tape's label shows ↺. That happens with Ladder up on 4h, 45m or monthly, and with Ladder down on 1m. Equal weight goes to every rung. The standard frames are not evenly spaced, so the tape leans toward wherever rungs are dense. That is the price of a familiar ladder, stated rather than hidden.</p>
""")

S["kb-tapes"] = sec("kb-tapes", "The four tapes and the amalgamated view", objectives([
    "read all four tapes' hue and intensity without a legend",
    "tell WIDENING from REVERTING, and RUNNING from PAUSING",
    "read the amalgamated view's TALL tapes",
]) + f"""
{math("conviction tape (+82)   100 · tanh( mean over the ladder of raw ÷ 3σ )       chart rung included" + chr(10) + "value tape (−82)        100 · softbound( 0.5 · mean over the ladder of z )" + chr(10) + "momentum tapes (±89)    Ladder down: tape − chart reading     Ladder up: chart reading − tape")}
<p>Each rung is fused in linear z-space and compressed once, so agreement across frames is <b>rarer</b> than any one frame's reading. A bright tape means the whole ladder is stretched, not one horizon.</p>
{tbl(["Tape", "Hue", "Intensity", "What it answers"], [
    ["MTF conviction (+82)", "Green buyers, red sellers", "Faint inside ±30, a clear step brighter past it, solid past ±60", "Who controls across the ladder, and how far"],
    ["MTF conviction momentum (+89)", "Which way the faster view pulls", "Near-solid while the pull grows past k·σ; moderate while it grows below; pale while it shrinks", "Ladder down: BUILDING or TURNING INSIDE the bar. Ladder up: RUNNING AHEAD or a PULLBACK"],
    ["MTF value (−82)", "<b>Green rich, red cheap</b>", "Faint inside θ, a step brighter at θ, solid toward ±70", "Rich or cheap across the ladder"],
    ["MTF value momentum (−89)", "Green toward rich, red toward cheap", "Near-solid past 0.5σ of its 200-bar history while growing", "WIDENING (agrees with the tape) or REVERTING (opposes it, the fast end turning back to fair)"],
], "The four tapes", [22, 20, 28, 30])}
<h4>Phases: how the grid reads the momentum tapes</h4>
<p>Each momentum has a standing side that changes only past its own knee: k·σ for conviction momentum, 0.5σ for value momentum. Until a knee is calibrated, the side is the sign. That side, read against its level tape's edge, is the phase the grid's WHY cell prints:</p>
{tbl(["Instrument", "Confirmed phase", "Unconfirmed phase"], [
    ["Conviction (rows)", "<b>Running</b>: momentum on the row's side. Buyers or sellers are pressing", "<b>Pausing</b>: momentum against the row. A pullback inside the control"],
    ["Value (columns)", "<b>Reverting</b>: momentum against the dislocation. Turning up from cheap, down from rich", "<b>Widening</b>: momentum with it. Still cheapening, still richening"],
], "Confirmed and unconfirmed phases", [22, 39, 39])}
<p>Note the opposite rules. Conviction's edge is confirmed by <b>the same</b> hue outside it; value's by <b>the opposite</b>. Inside the capitulation cell, value reverting beat widening in every era {X}. That is why the ▲ waits for it.</p>
<h4>Amalgamated</h4>
<p>Each momentum setting can read <span class="k">Separate band</span> (default), <span class="k">Amalgamated</span> or <span class="k">Off</span>. Amalgamated draws the grid's fold for you. Past its edge, a level tape stands <b>TALL</b> while its momentum confirms the edge, and short while it does not. Inside its edge it stays short and faint.</p>
{tbl(["The tape looks", "It means", "Grid reading"], [
    ["Short, faint", "No edge", "FAINT row, or FAIR column"],
    ["Short, bright", "An edge, unconfirmed", "Pausing, or widening"],
    ["TALL, bright", "An edge, confirmed", "Running, or reverting"],
], "Amalgamated tapes", [26, 34, 40])}
<p>A bright red conviction tape over a TALL red value tape is the ▲'s condition, drawn: sellers in control, price cheap, the cheapening turning up. Amalgamated drops the bands' shading and the early TURNING INSIDE read, both unmeasured. Keep Separate if you use them. Switching a band off hides the band, never the reading.</p>
""")

S["kb-trace"] = sec("kb-trace", "The trace and its rails", objectives([
    "choose between the three traces knowing what each changes",
    "say what reads the trace and what always reads conviction",
]) + f"""
{tbl(["Trace", "What the pane draws", "Rails"], [
    ["Conviction × Value (default)", "Both ingredients in σ, blended equally: 100 · softbound(0.5 · (z_c + z_v) ÷ √(2(1 + ρ))), with ρ their correlation over 200 bars, which restores the blend's variance. How <b>stretched</b> the move is, in effort and in price against fair", "±θ (±43) and ±60, a 3σ stretch"],
    ["Conviction", "The single-frame engine alone, bit-identical to Nishchaya v3, on which the original evidence was measured", "The zones, ±30 and ±60"],
    ["Value", "Samanvaya's value on this chart alone", "±θ and ±60"],
], "The three traces", [24, 54, 22])}
<p><b>The blend dims</b> while its ingredients point opposite ways: cheap with buyers pushing is accumulation; rich with sellers pushing is distribution. It also dims while the value basket settles. A dim blend near zero is not necessarily quiet; the panel's <span class="k">trace</span> row gives both ingredients in σ and their ρ. Calibration on Pragyam's panels: the blend sits past θ on 19–21% of days, as value alone does, and past ±60 on only 0.1–0.2% {X}.</p>
<h4>What follows the trace, and what never does</h4>
{tbl(["Follows the drawn trace", "Always reads conviction"], [
    ["The histogram's columns and tiers", "The conviction ladder's chart rung and its momentum"],
    ["The ◆'s impulse gate and pullback", "The ◆'s control test (conviction above zero)"],
    ["The rails and the panel's headline", "R and H pivots, the quiet regime"],
    ["", "<b>The grid, its push gate and the ▲▼</b>: the Trace setting never moves a ▲ or a ▼"],
], "The trace's reach", [50, 50])}
<p>As a position the blended trace and its histogram carry almost no timing information once scored without look-ahead {X}. Read them as description: how far the move is stretched, and which way it is pushed.</p>
""")

# ── The grid engine and the signals ──────────────────────────────────────────
S["kb-grid"] = sec("kb-grid", "Rows, columns and the row memory", objectives([
    "say exactly when the grid's row moves, and when it is HELD",
    "explain why the column has no memory and the row does",
]) + f"""
<p>The grid reads the two level tapes into a 3 × 3 map (⟦ref:grid⟧). It is readable only on a standard chart with both level tapes ready.</p>
{math("target row   UP   if conviction tape ≥ +30      DOWN if ≤ −30      FAINT between" + chr(10) + "column       RICH if value tape ≥ +43 (θ)    CHEAP if ≤ −43      FAIR between")}
<p><b>The column follows the value tape directly</b>, every bar. <b>The row has a memory.</b> It moves to its target only on a push gate (⟦ref:kb-hist⟧) toward it:</p>
{steps([
    ("Target above the row, and the gate is +1", "The row moves up to the target."),
    ("Target below the row, and the gate is −1", "The row moves down to the target."),
    ("Anything else", "The row stays where it is. If the target differs, the row is <b>HELD</b>, and WHY says so in gold."),
    ("No gate yet (warming)", "The row simply equals its target, with no memory. WHY appends <span class=\"k\">gate warming</span>."),
])}
<p>This is why a tape that slips briefly across ±30 does not flip a family. Pragyam's grid ignores a tape move that conviction's own histogram has not confirmed. A row move takes both the tape crossing and a push that way, on the same bar or later.</p>
{note("<b>Held is caution, not direction.</b> A held row means the tape has left the row and the histogram has not confirmed a push that way. The family's units stay between the held row and half-way to the neighbouring row, according to how firmly the push holding it is drawn.", rule=True)}
""")

S["kb-units"] = sec("kb-units", "The 5 × 5 and the graded units", objectives([
    "compute a name's units from its position on the map",
    "explain what PAUSING and WIDENING do to the units",
]) + f"""
<p>Each of the nine families has units (⟦ref:grid⟧), but STATE rarely prints a cell's round number. The name is placed on the map at a <b>position</b>, and the units are read there, bilinearly between cells, as Pragyam does.</p>
<h4>The position</h4>
{steps([
    ("How intensely each tape is drawn", "A tape's ink runs from 0.12 to 0.45 inside its knee (±30 for conviction, θ for value), steps to 0.65 at the knee, and rises to 1.0 toward solid (±60 for conviction, ±70 for value). The row position is the row times conviction's ink; the column position is the column times value's ink."),
    ("Half-way for an unconfirmed edge", "A row that is PAUSING, or a column that is WIDENING, is moved half-way toward the middle: the 5 × 5's in-between cells."),
    ("Held rows", "A HELD row sits between itself and half-way to its neighbour, by how firmly the push is drawn."),
])}
<h4>Reading the units at a position</h4>
{math("rows −1 … +1 (DOWN … UP), columns −1 … +1 (CHEAP … RICH)" + chr(10) + "units = bilinear interpolation of the nine cells at (row position, column position)")}
<p><b>Worked (constructed).</b> Sellers in control, the conviction tape at about −45 and running: row position −0.8. Price cheap, the value tape at about −62 and reverting: column position −0.9. The four surrounding cells are DOWN·cheap 4, DOWN·fair 1.5, FAINT·cheap 1.5 and FAINT·fair 1.</p>
{math("along the column   DOWN row:  0.9 × 4   + 0.1 × 1.5 = 3.75" + chr(10) + "                   FAINT row: 0.9 × 1.5 + 0.1 × 1   = 1.45" + chr(10) + "along the row      0.8 × 3.75 + 0.2 × 1.45 = 3.29 units")}
<p>STATE prints <span class="chip c-bull">Buy 3.29</span>. If value momentum were still widening, the column position would halve to −0.45, and the same name would read 2.35 units. The tooltip shows the unshaded cell too; here, 4.00.</p>
<p><b>Measured.</b> The units table is v8's, re-measured in v9 and kept. The graded units, read as a position, were positive in all three eras outside crypto {X}. Buy · capitulation went from 3 to 4 units in v9.1, because at 4 the grid improved or tied in all three eras on both scorers {X}.</p>
""")

S["kb-sig"] = sec("kb-sig", "The signals, exactly", objectives([
    "state the ▲ and ▼ conditions completely",
    "explain why a ▲ can come days after the grid entered the cell, or never",
    "list what pauses each family, and how the pane tells you",
]) + f"""
{tbl(["Signal", "Fires on the first closed bar where", "Also needs", "Evidence"], [
    ["▲ Capitulation turn", "the grid stands in DOWN · cheap <b>and</b> value momentum is REVERTING, having not been so on the bar before", "A standard chart; both level tapes and conviction warmed up; the bar before readable; the long cooldown (10 bars) clear", X + " +0.046 to +0.056σ over 10 bars, every era, daily; positive weekly"],
    ["▼ Distribution", "the grid enters DOWN · rich (sellers in control of a rich price)", "The same, with the short cooldown", X + " As a state, underperformance in every era; too rare to measure as an event"],
    ["◆ Continuation (off)", "conviction above zero; the histogram dipped below zero within 6 bars and now crosses +k·σ; conviction tape ≥ +30; value tape below +θ; effort not absorbed", "The full stack, including the trace's warm-up", X + " Negative in both eras outside crypto"],
    ["R regular divergence (off)", "a price higher high on a conviction lower high (zone gate), the ladder also lower, value rich (> 0) at the pivot", "Pivots 5 left and 5 right: the divergence is known 5 bars late", X + " About zero in every era"],
    ["H hidden divergence (off)", "a price lower high on a conviction higher high; conviction tape ≤ −30; value not cheap past θ", "As R", X + " Negative or mixed"],
], "The signal families", [16, 38, 26, 20])}
<p><b>Entered means entered.</b> A grid that becomes readable already inside a cell never <i>entered</i> it. Warm-up completing is not a capitulation, so a ▲▼ needs the bar before to be readable too. The ▲ fires on the first bar of the <i>turn</i>, not the first bar of the cell. A market can sit in DOWN · cheap, widening, for weeks with no ▲, and the ▲ comes only when the cheapening eases. It may never come.</p>
<p><b>The declaration</b> is the last ▲ or ▼, standing until the opposite one, with no exit. Held as a position it carried no edge {X}. The state behind the ▲ did, which is why the pane background paints the state by default: green while the grid stands in DOWN · cheap, deeper once value momentum has turned, and red in DOWN · rich.</p>
<p><b>Crypto.</b> The capitulation reading failed on crypto, which trends, so on a crypto symbol its tint and its ▲ are drawn in gold. Nothing that fires changes.</p>
<p><b>Nothing pauses silently.</b> A tape that is warming or switched off, no frames after fallback, or Samanvaya's model still building pauses the families that read it. A gold <span class="k">SIGNALS PAUSED</span> label at the pane's right edge names the layer. While only the trace is warming, the ▲▼ run and the label names just ◆, R and H.</p>
""")

# ── The auction engine and Accepted momentum ────────────────────────────────
S["kb-prof"] = sec("kb-prof", "The rolling profile and migration", objectives([
    "say which window the trail uses with Accepted momentum on and off",
    "draw the five migration states from two value areas",
]) + f"""
<p>The auction engine builds its own volume profile from the chart's bars. It does not read the session profile, whose settings and session change with the timeframe. Its window is <b>126 bars, six months, with Accepted momentum on (the default)</b>, and the conviction Lookback (20 bars) with it off. The ribbon, the probes, the AUCTION row and the trail all use that same window.</p>
{steps([
    ("Weights", "Each bar contributes its capped participation weight <i>w</i> (⟦ref:kb-bar⟧), spread evenly from its low to its high. Raw volume let one expiry print own the POC for the whole window; flips were 2.0× likelier on the bar such a spike left the window, a flip caused by nothing."),
    ("An absolute grid", "Bins are a power of two of the tick nearest ATR(20)/4, at most 300. A bin edge moves only when volatility changes by about √2, never because the window's low did. Anchored at the window's low, 29% of the value area's bin-sized moves had been phantom."),
    ("POC and value area", "The POC is the heaviest bin; ties go to the bin nearest the middle. The value area starts at the POC and adds the heavier neighbour, above or below, until it holds 70%. VAL and VAH are its edges."),
])}
<h4>Migration: this window against the window N bars ago</h4>
{tbl(["State", "Condition (first match)", "Reads"], [
    ["+2 · Migrating ↑", "Today's VAL above the old VAH", "The value areas no longer overlap. Value has moved up"],
    ["+1 · Shifting ↑", "Today's POC above the old VAH", "The centre of value has left the old value area"],
    ["0 · Balance", "Anything else", "Value overlaps where it was"],
    ["−1 · Shifting ↓", "Today's POC below the old VAL", "The mirror"],
    ["−2 · Migrating ↓", "Today's VAH below the old VAL", "The mirror"],
], "The five migration states", [22, 38, 40])}
<p>With a 126-bar window the comparison is with the value area of six months ago: a slow, structural question. In a trend, migration usually reads ±1 or ±2 for months. NIFTY 50 read Shifting or Migrating ↑ on 189 of its last 300 bars, and Balance on only 21 {M}.</p>
<p><b>Measured</b> (setup lab S5, ⟦ref:fk-num⟧). With Accepted momentum agreeing, bars Migrating with the trail did better over 20 bars than bars in Balance, in all three sets. The result was consistent but not confirmed {M}.</p>
""")

S["kb-trail"] = sec("kb-trail", "The acceptance trail: start, step, probe, flip", objectives([
    "apply the trail's four rules to a bar",
    "explain why the default trail can sit far from price for months",
    "read the trail's colour with Accepted momentum on and off",
]) + f"""
<p>The trail is the ratcheted far edge of value: the value-area low while up, the high while down. It is the floor or ceiling of where the market has accepted price. It is updated on closed bars only and never repaints.</p>
{tbl(["Rule", "While up (D = +1); down mirrors", "Effect"], [
    ["Start", "Migration ≥ +1, push gate +1, close ≥ VAL", "D = +1, level = VAL"],
    ["Flip", "Close below the level, <b>and</b> the window's POC below it, <b>and</b> migration ≤ −1", "D = −1. The level is unchanged: the broken floor becomes the ceiling"],
    ["Probe", "Close below the level without both of the flip's other conditions", "Nothing changes; the bar is a probe. Its first bar is marked with a gold ×"],
    ["Step", "Migration ≥ +1, push gate +1, VAL above the level, close ≥ VAL", "Level = VAL. A floor is never lifted above price"],
], "The trail's rules, checked in this order", [12, 56, 32])}
<p>So the trail moves only when value shifts its way <b>and</b> conviction confirms a push that way: the same gate by which the grid moves a row. It flips only on <b>acceptance</b>, meaning price beyond it, the market's value (the POC) following, and value having migrated that way. Price beyond it without all three is a <b>probe</b>: in Market Profile terms, price outside value that has not been accepted.</p>
<h4>Why the trail can sit far from price</h4>
<p>A step needs the push gate open, and the quiet regime shuts it (⟦ref:kb-scale⟧). In a long, orderly trend conviction's σ can sit in its bottom fifth for months, and the trail cannot step at all. On gold, the trail's floor stayed at 2,640 from before August 2025 to 27 May 2026 while price traded as high as 5,586. It stepped to 4,256 on 28 May, the first open gate with value migrated {M}. NIFTY 50's trail sat at 24,064 for the whole of its last 300 bars (⟦chap:c25⟧).</p>
{note("<b>With Accepted momentum on, the trail's level is not a stop.</b> What trades is the side (with momentum's size), not the distance to the line. A trail 30% below price is still long. For stops, use ⟦ref:stops⟧.", rule=True)}
<h4>Colour</h4>
{tbl(["Accepted momentum", "Hue", "Intensity", "Neutral or gold"], [
    ["On (default)", "The side", "The size: solid at 0.5 and above, strong from 0.25, faint below", "<b>Neutral grey when flat</b>: the trail and momentum disagree"],
    ["Off", "The side", "The conviction tape in the trail's direction: solid past ±60, strong past ±30, faint against", "<b>Gold</b> when the value tape is stretched past θ its way: the move is already paid for"],
], "The trail's colour", [18, 12, 42, 28])}
<p>The value ribbon is the rolling value area as a slate band with its POC dotted, over the last 1,500 closed bars. Inside the band is <b>in value</b>; above or below is price the window has not yet accepted. Probe marks keep the latest 40. A probe lasts about four bars, and marking every bar of it turned a quarter of the chart gold.</p>
""")

S["kb-am"] = sec("kb-am", "Accepted momentum, from the inside", objectives([
    "compute S and the position from a chart's numbers",
    "say what each word in the AUCTION row's CHART cell means",
]) + f"""
{math("for h in 21, 63, 126, 252 bars:   s_h = clip( ln(close ÷ close h bars ago) ÷ (σ·√h), −2, +2 )" + chr(10) + "S        = mean(s_h) ÷ 2                      in −1 … +1   (σ: EWMA of daily returns, span 60)" + chr(10) + "position = side × max(0, side × S)           side = the 126-bar trail's D" + chr(10) + "weight   = position × 10% ÷ annualised volatility, capped at 2")}
<p>The <b>side</b> is where value was accepted over six months. The <b>size</b> is how far and how consistently price has gone over one, three, six and twelve months, each in its own volatility. Where the two definitions of trend agree, the position is the trail's side at momentum's size. Where they disagree, it is <b>flat</b>.</p>
{tbl(["CHART cell", "Meaning"], [
    [chip("LONG 0.62", "bull"), "Trail up, S = +0.62: long at size 0.62"],
    [chip("SHORT 0.40", "bear"), "Trail down, S = −0.40"],
    [chip("FLAT · disagree", "neut"), "The trail and S point opposite ways"],
    ["—", "Not ready: the trail has not started, or S needs 252 bars and σ 60"],
], "The AUCTION row's CHART cell with Accepted momentum on", [30, 70])}
<p>The cell is live on the forming bar and final at the close. The tested system decides at the close, trades at the next open, and rebalances weekly with a 10% band (⟦ref:am⟧). Its position alert, through the one <span class="k">Any alert() function call</span> alert, fires on each change of LONG, SHORT or FLAT. It is off by default, because an alert invites trading one chart, and the tested edge is a portfolio's.</p>
""")

# ── The session profile and open interest ────────────────────────────────────
S["kb-vp"] = sec("kb-vp", "The session volume profile", objectives([
    "say which session the profile covers on your timeframe",
    "read POC, VAH, VAL, HVN, LVN, naked POCs, VWAP and IB, and know which are measured",
]) + f"""
<p>The session profile is a price-chart overlay, display only: nothing in the engine reads it. It answers <b>where</b> volume traded in the current session.</p>
{tbl(["Chart timeframe", "Session"], [["Intraday", "The day"], ["Daily", "The week"], ["Weekly", "The month"], ["Monthly and above", "Twelve months"]], "The profile's session", [40, 60])}
<h4>How it is built</h4>
<ul>
<li><b>From intrabars</b>, by actual traded price, when <span class="k">Build from intrabar data</span> is on and the plan delivers them. Otherwise each bar's volume is spread over its range. The panel's <span class="k">Profile Mode</span> row reports which, and the session's intrabar share.</li>
<li><b>Volume or time.</b> Volume is used when at least half of the last 500 bars print it. Otherwise the profile is time-at-price (TPO), automatically, and the session line reads TWAP instead of VWAP.</li>
<li><b>Bins</b> are ATR(20) ÷ 4 wide (<span class="k">Bins per ATR</span>), frozen at the session's start, or a fixed number of ticks. A bar wider than 200 bins is spread over its whole range on every st-th bin, with volume conserved.</li>
<li><b>POC</b>: the first bin to reach the session's maximum. <b>Value area</b>: 70%, walked out from the POC, the larger neighbour first.</li>
<li><b>HVN / LVN</b>: a local peak at least 1.2σ above the mean of the non-empty rows, or a local trough at or below their 10th percentile. These are heuristics; the thresholds are unmeasured.</li>
</ul>
<h4>Levels drawn</h4>
{tbl(["Level", "What it is", "Evidence"], [
    ["POC, VAH, VAL", "The session's most-traded price and its 70% value area", U],
    ["Developing trails", "How POC and value developed through the session; blank on its first bar", U],
    ["Prior session value", "Last session's pPOC, pVAH and pVAL, drawn only across the current session", U],
    ["Naked POC", "A prior session's POC price has not traded back through: at most 5, at most 250 bars old. Since v9.9 a session's POC joins the ledger before its first bar's touch check; before, 27% of drawn naked POCs had already been traded through", U + " (PVOI's \"measured\" label not re-verified)"],
    ["Session VWAP / TWAP", "The session's volume-weighted average price; time-weighted without volume", U],
    ["Initial Balance", "The high and low of the session's first 12 bars, intraday only: on daily bars 12 bars would swallow the week", U],
    ["Delta split", "Each row split into inferred buying and selling, by close location per bar or the tick rule per intrabar. An inference, not order flow", U],
], "Session profile levels", [18, 62, 20])}
<p>The panel's <span class="k">Location</span> row places price: above, below or in value, or at the POC (within one bin). Off value is gold, because unaccepted price can resolve by rejection or by acceptance, and the colour does not pretend to know which.</p>
""")

S["kb-oi"] = sec("kb-oi", "The open-interest engine", objectives([
    "explain how ΔOI becomes a σ figure and a character",
    "recognise every feed state, and why an expiry is not conviction",
    "say when the OI row should be believed",
]) + f"""
<p>Volume answers <i>how much</i> traded. Open interest answers <i>what kind</i>: whether the trading created open risk or destroyed it. The sign of ΔOI is the information volume cannot carry.</p>
{steps([
    ("The companion series", "Built from the chart's prefix and ticker as <span class=\"k\">PREFIX:TICKER_OI</span>, then two alternates. It is never built from the tickerid, which on a modified chart is a JSON envelope. It is requested on the same timeframe, with no look-ahead."),
    ("Is it live?", "At least a fifth of the last 50 bars must carry a change; otherwise the row reads STALE. An end-of-day OI series on a 5-minute chart is a step function."),
    ("The build figure", "The bar's log change, divided by the RMS of the last 50 accepted changes, measured before this bar joins. RMS keeps zero at zero, so the sign is the sign of ΔOI. It needs 10 accepted changes first; until then the row reads WARMING."),
    ("Structural bars", "A bar that moves more than half the book, or one beyond 3σ that also moves more than a fifth of it, is an EXPIRY / ROLLOVER. Such bars are kept out of the baseline, so one roll cannot inflate σ for the next fifty bars."),
    ("The character", "Beyond ±0.5σ, the sign of ΔOI with the sign of the close's change: long build-up, short build-up, short covering, long unwinding. A book that moves while the close does not reads PRICE FLAT."),
    ("Trust", "ρ(|ΔOI|, activity) over 50 bars must reach 0.20, or the row dims. Activity is volume, or true range without it. The signed correlation would be wrong by construction: OI rises on long and short builds alike."),
])}
{tbl(["Feed state", "Meaning", "Colour"], [
    ["live", "A reading", "By character"], ["warming", "Building its baseline (10 changes)", "Gold"],
    ["stale", "Fewer than a fifth of recent bars change", "Gold"], ["daily only", "OI exists on daily bars only", "Gold"],
    ["none", "The symbol has no open interest at all, as on cash equity and spot", "<b>Neutral</b>: the correct answer"],
    ["no symbol / synthetic", "A malformed ticker, or a non-standard chart", "Gold"],
], "OI feed states", [20, 58, 22])}
<p><b>Crowded</b>: the book's level at or above the 80th percentile of its last 250 bars, which prints gold in WHY. <b>The gold cast</b> on the histogram, on by default, tints a column toward gold when exits paid for its push: covering outnumbering long build-ups above zero, or unwinding outnumbering short build-ups below, with at least a third of the window exits. It applies only with the feed live, outside structural bars, and trusted. Pushes it marks did worse than others in both eras on 240 NSE F&amp;O stocks {X}.</p>
<p><b>The four-quadrant reading is a practitioner's framework.</b> The academic evidence lives at a monthly horizon (Hong and Yogo 2012). Nothing validates the bar-level quadrant. "Self-limiting" is a hypothesis this table colours by, not a result {U}. On a continuous front-month future the book falls into each expiry as positions roll, and a fall below the structural cut can read as covering or unwinding. Treat OI in expiry week with caution.</p>
""")

# ── Timing, repainting and limits ────────────────────────────────────────────
S["kb-repaint"] = sec("kb-repaint", "What is live, and what is final", objectives([
    "say for every element whether it can change on the forming bar",
]) + f"""
{tbl(["Element", "On the forming bar", "At the close"], [
    ["Trace, histogram, all four tapes", "Live: they move as the bar forms", "Final"],
    ["Grid STATE, pane background (grid state)", "Live: a tint can come and go", "Final"],
    ["▲ ▼ ◆, R, H, the declaration, every alert", "Not drawn", "Committed; never revised"],
    ["Acceptance trail, probe marks, value ribbon", "Not drawn for this bar", "Committed; never revised"],
    ["AUCTION row, Accepted momentum's CHART cell", "Live; an accepted break reads \"accepted, flips at the close\"", "Final"],
    ["OI row", "Live", "Its baseline is committed at the close"],
    ["Session profile, developing session", "<b>The one disclosed exception</b>: it develops", "—"],
    ["Divergence markers", "Not drawn; they sit on the confirming bar, 5 bars after the pivot", "Committed"],
], "Repaint posture, element by element", [34, 40, 26])}
<p>Higher frames enter only as their last closed bar plus chart bars that exist; lower frames only as intrabars that exist. History and realtime compute the same numbers. The rule that follows is simple: <b>decide at the close</b>.</p>
""")

S["kb-limits"] = sec("kb-limits", "Warm-ups, budgets and where evidence stops", objectives([
    "know how much history each part needs before it reads",
    "know which timeframes and asset classes carry evidence",
]) + f"""
{tbl(["Part", "Needs", "Shows while waiting"], [
    ["Conviction and the zones", "The 200-bar Normalization window", "The trace builds"],
    ["Push gate, grid row memory", "About 450 bars", "gate warming"],
    ["Value tape", "Samanvaya's model: ten anchor periods past a twelve-period hold-out, and the basket settled", "Grey tape; SIGNALS PAUSED names it"],
    ["▲ ▼", "Both level tapes and conviction's warm-up", "SIGNALS PAUSED"],
    ["Acceptance trail (126)", "The gate, then 126 bars, then a start condition", "AUCTION reads no trail yet"],
    ["Accepted momentum", "The trail, 252 bars for S, 60 for σ", "CHART reads —"],
    ["OI", "10 accepted changes", "warming"],
], "Warm-ups", [28, 46, 26])}
<h4>Budgets</h4>
<p>Pine allows 40 unique data requests. Samanvaya spends 22; the ladders up to 10; the profile 1; OI 4. At most 37 execute on any chart, so nothing more can be requested. The plot budget is full at 64 of 64, which is why the momentum tapes' readings live in labels and the panel rather than the Data Window.</p>
<h4>Where the evidence stops</h4>
{tbl(["Question", "Answer"], [
    ["Timeframe", "Daily bars carry the evidence. The ▲ and the grid were also tested on weekly bars. Nothing was measured intraday: twenty years of intrabars exist on no free feed"],
    ["Costs", "At one ATR of stop a round trip costs about 0.02R daily, 0.045R hourly, 0.05R on 15 minutes and 0.09R on 5 minutes, against a best measured edge near 0.05R. Daily is the only timeframe with real headroom " + X],
    ["Asset classes", "The ▲ and the grid were positive in 4 to 5 of the 5 non-crypto classes per era; crypto failed " + X + ". Accepted momentum was tested on 119 markets in six classes, then 411 NSE stocks and crypto " + M],
    ["Tuning", "900 randomised parameter sets: fitted edge and unseen edge correlated at about zero. Lookback ≥ 20 and the inner zone ≤ 40 were the only preferences that held. <b>Do not tune Pragati to a backtest</b> " + X],
    ["Charts", "Heikin Ashi, Renko, Kagi, Point &amp; Figure and range bars hand every engine prices that never traded. Everything pauses and says so"],
], "Limits", [20, 80])}
""")

ORDER = ["kb-bar", "kb-scale", "kb-hist", "kb-vlegs", "kb-vscale", "kb-ladder", "kb-tapes", "kb-trace", "kb-grid", "kb-units", "kb-sig",
         "kb-prof", "kb-trail", "kb-am", "kb-vp", "kb-oi", "kb-repaint", "kb-limits"]
