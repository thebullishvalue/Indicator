"""Part VII additions · the investing setups."""
from kit import M, X, U, sec, tbl, chip, k, note, steps, flow, objectives, checklist, setup_card

S = {}

S["is-filter"] = sec("is-filter", "I2 · The trend filter", setup_card("I2", "Accepted momentum as an investor's filter", M, "not confirmed: drawdown halved, return halved", [
    ("Context", "A long-only book of stocks, ETFs or indices"),
    ("Rule", "Hold a name while its CHART cell reads LONG; hold cash (or the rest of the book) while it reads FLAT or SHORT"),
    ("Check", "Weekly, at the close, and immediately when the state changes; trade the next open"),
    ("Size", "Unlevered: the name's ordinary weight, or its grid units (⟦ref:inv-book⟧)"),
    ("Evidence", "Below. Max drawdown smaller in all three sets; Sharpe about equal except 2020–26, where buy-and-hold's was 0.23 higher. Invested 43–53% of the time"),
    ("Fails when", "Long, strong bull markets (it sits out the recoveries' first legs); the cost is about half the compound return"),
]) + tbl(["Set", "Markets", "Invested", "Filter: CAGR · max DD · Sharpe", "Buy-and-hold: CAGR · max DD · Sharpe"], [
    ["DEV, 1992–2019", "106", "46%", "11.5% · −31% · 0.82", "20.0% · −58% · 0.79"],
    ["HB, 2020–26", "106", "53%", "7.4% · −29% · 0.81", "18.2% · −36% · 1.04"],
    ["HA, 391 NSE stocks, 1997–2026", "391", "43%", "16.5% · −28% · 1.36", "37.8% · −64% · 1.39"],
], "The filter against buy-and-hold (setup lab I1; equal-weight, daily-rebalanced portfolios)", [26, 12, 12, 25, 25]) + note(
    "<b>Read it as insurance, priced.</b> The filter roughly halves the deepest drawdown and roughly halves the return. It is a choice about which pain you can sit through. It is not a better portfolio. HA is today's NSE listings, so it carries survivorship; only the comparison on the same markets is meaningful. The 20-bar trail made the same trade, −35% against −73.5% drawdown at 13.5% against 24.4% growth (⟦ref:inv-risk⟧)."))

S["is-stage"] = sec("is-stage", "I3 · Staging and averaging", setup_card("I3", "Entering in stages", U, "a house rule", [
    ("Context", "Any name you intend to hold; the grid reads"),
    ("Rule", "Divide the intended weight into thirds. Each third needs a different, closed-bar reason"),
    ("First third", "The grid enters a Buy or Accumulate family (DISLOCATED, TURNED, BASING, FADING)"),
    ("Second third", "The ▲ (in DOWN · cheap), or the trend filter turning LONG, or a push ↑ that moves the row"),
    ("Last third", "The family improves (for example BASING to TURNED), or a weekly close confirms it"),
    ("Averaging down", "Allowed only inside the capitulation plan, and only while the grid stays in a Buy family. Never because the price is lower"),
    ("Evidence", "The families' units and the ▲ " + X + "; the thirds themselves are a house rule"),
    ("Fails when", "On crypto; in a held row; when a family is reached from above (TURNED falling to BASING is weakening, not a new entry)"),
]))

S["is-trim"] = sec("is-trim", "I4 · Trimming and exiting", setup_card("I4", "Trim and exit discipline", X, "states measured; the trims are units", [
    ("Trim", "PAID or STALLING: bring the name toward 0.75 units' share of the book"),
    ("Exit", "DISTRIBUTION (▼ marks its entry): toward 0.25 units, a token weight"),
    ("Hold", "BUILDING and IDLE change nothing. Do not add in BUILDING: buyers at a fair price lagged in v8"),
    ("Speed", "Trims are gradual: at each weekly review, move half the gap to the target " + U),
    ("Evidence", "Distribution was followed by underperformance in every era; the graded units positive in all three eras outside crypto"),
    ("Fails when", "A trim is read as a short; taxes and costs are ignored. Small trims in a large book are often cheaper skipped"),
]))

S["is-rebal"] = sec("is-rebal", "I5 · The rebalancing calendar", objectives(["run the investor's week in twenty minutes"]) + steps([
    ("Friday's close (or the week's last close)", "Read every name's CVG STATE, units and WHY. Note ▲▼ and tint changes during the week."),
    ("Compute weights", "Weight = units ÷ the sum of units, capped at about a tenth of the book per name (⟦ref:inv-book⟧)."),
    ("Move half the gap", "For each name, trade half the difference between current and target weight " + U + ". Skip trades smaller than your cost threshold."),
    ("Apply the trend filter, if you use it", "Names whose CHART cell is not LONG go to cash, or keep only their capitulation tranches (⟦ref:is-filter⟧)."),
    ("Monday's open", "Execute."),
    ("Monthly", "Review the drawdown ladder, the clusters and the watchlist."),
]))

S["is-watch"] = sec("is-watch", "I6 · Building a watchlist", objectives(["turn one indicator into a scan across many names"]) + f"""
<p>Pragati reads one chart at a time; it has no screener. A watchlist routine makes it scale.</p>
{steps([
    ("Choose a universe and keep it", "An index's members or a fixed list of ETFs. Changing the list because of recent winners is survivorship you add yourself."),
    ("One alert per name", "Create Pragati's <span class=\"k\">Any alert() function call</span> alert on each chart with <span class=\"k\">Alert on capitulation state entry / exit</span> on. Every ▲▼ and every capitulation entry and exit arrives with the ticker, the grid's action and units, and both tapes."),
    ("A weekly sweep", "Open each name on the weekly chart once a week and log its one-line reading (⟦ref:ctx-routine⟧)."),
    ("Rank by units", "Highest units first. That is the order the grid would allocate in."),
    ("Note the clusters", "Five capitulations in one sector are one bet."),
])}
""")

ORDER = ["inv-cap", "is-filter", "is-stage", "is-trim", "is-rebal", "is-watch"]
