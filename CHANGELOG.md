# Changelog

All notable changes to **Anumaan** are documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

Two things are versioned here, and each entry says which: the **terminal** (1.x), and the **script**,
`anumaan.pine` (2.x; named Kasauti through 2.3, Pragyam through 2.6, and briefly Pramana). Anumaan shares its
interface with the Pragyam family: one stylesheet, one set of components, one console, one way a panel, a table,
a chart or a number looks.

---

## [Terminal 1.3.0] — 2026-11-24 — *The plan as a ticket*
### Changed
- **Plan is a ticket, after VAAYDO** (thebullishvalue/Vaaydo, which takes its stops and ranges from this script). The
  side is yours - the script finds risk forecastable and direction not. Entry at the next open; a **trailing stop** at
  1 + 1.5 × the script's 20%-touch stop distance, from the best close since entry, checked on the close and filled at
  the next open (VAAYDO's ledger rule); a size that loses your risk at the first stop, never more than the **exposure
  dial** allows, in whole **lots** (1 for a share or a coin, the exchange's lot for a futures contract); the 80% range
  in **R**; and the script's cost, in and out, in R. The ticket's stop joins the level ladder, and the headline cards
  carry it and how often it is stopped.
### Added
- **Paths**: the ticket on 4,000 paths at today's risk, by VAAYDO's filtered historical simulation - this chart's own
  gaps and returns over the risk forecast that prevailed when each happened, bootstrapped in blocks of five bars,
  rescaled to today's forecast, with no drift. R by bar after costs (50% and 80% of paths, the median), this chart's
  own median beside it, and the share stopped by each bar.
- **Outcomes**: at one, two and three horizons, simulated and **here** - the same rule opened after every past bar of
  the chart, each with its own stop, overlapping, drift included: stopped, median, mean, 10th and 90th percentile R,
  and how often +1R and +2R were reached. Two claims side by side, the way the script audits its cone and stops.
  On NIFTY daily, long: stopped within 30 bars 28% of the time simulated, 33% here.

---

## [Terminal 1.2.1] — 2026-11-24 — *Log by default*
### Changed
- **The price scale opens logarithmic, with Auto on** - L and A both lit. A long history (BTC from 2014, NIFTY from
  2007) reads in proportion: a 10% move is the same height at any price. Turning L off is remembered in the browser
  as before; the setting moved to a new key, so a choice saved under 1.2.0 (when Regular was the default) does not
  carry over and everyone starts on log once.

---

## [Terminal 1.2.0] — 2026-11-24 — *Log and auto price scale*
### Added
- **A and L under the price scale, as on TradingView.** **L** makes the scale logarithmic, so a move of the same
  percentage is the same height anywhere on the chart; the volume profile, its levels, the cone, the stops and every
  other drawing follow, since each places itself through the series' own price conversion. The choice is remembered in
  the browser. **A** (auto) fits the scale to the bars in view; dragging the scale turns it off, and A, a double-click
  on the scale or *Reset price scale* turns it back on.
- **The price scale's menu.** A right-click on the chart (desktop) or a long press on the price scale (touch) opens it:
  *Reset price scale*, *Auto (fits data to screen)*, *Regular* / *Logarithmic*, *Reset chart view*. A tap or a drag on
  the scale opens nothing, and a press that does not move leaves Auto as it was (the library's scale drag turns it off
  the moment the scale is touched). Menu rows are 42px on a touch screen.
- **Alt+L and Alt+R**, TradingView's keys: log on and off, and the chart's first view with its scales reset.
### Changed
- The status line's cap (1.1.4) is measured again whenever the scale's mode or zoom changes, not only on a resize or a
  scroll: log labels and a dragged scale change the scale's width.
- A double-click on the plot still brings back the first view; on the scale it now resets the scale only.

---

## [Terminal 1.1.4] — 2026-11-24 — *The status line stops at the axis*
### Fixed
- **The chart's status line no longer runs over the price axis.** On a phone the symbol line (NIFTY_MICROCAP250 · D ·
  NSE, then the close and the change) was one unbroken row: the narrow-screen rule even turned wrapping off, under a
  width guessed from the screen, so the quote ran across the axis labels. The line is now capped at the plot's edge,
  measured from the price scale's own width as it draws (and again after a resize or a zoom widens its labels), and
  wraps between its parts, never inside one: on a phone the close and change sit under the symbol as one block. A
  table placed at the right clears the scale the same way. Checked at 320, 390, 834, 1024 and 1440px with the longest
  watchlist name: no text crosses the axis; from 834px up the line is still one row.

---

 — 2026-11-24 — *The help icon, shared*
### Changed
- **The help-icon rule moves into the family's fidelity block.** 1.1.2 fixed the (?) icons in Settings in the
  terminal's own stylesheet; the same leak was in Vyāpti's, Pragyam's, Arthagati's and Nivesa's hints, so the
  rule now lives in the block every member shares, and the terminal's copy goes. Nothing on screen changes.

---

## [Terminal 1.1.2] — 2026-11-24 — *Settings and the axes on Paper*
### Fixed
- **Settings is a panel of the app's own.** No other member of the family opens a dialog, so nothing
  painted one: Streamlit drew it from its static dark base, near-black on Paper, with near-white help
  icons and close button, native-dark unchecked boxes, and a tab-strip fade running from black to
  white. It is now the app's surface, hairline and ink in both appearances, its title in the reading
  face. Each checkbox reads as the option it is, in sentence case (Nivesa's style) rather than as an
  uppercase caption.
- **Help icons show on Paper.** Their ring was drawn with Streamlit's own near-white stroke at 60%,
  whatever their colour; the stroke now follows the colour, the family's quiet ink.
- **The charts' axes read on Paper.** Tick labels and axis titles were near-white, painted by
  Streamlit's Plotly template from its dark base over the layout's font, as the legends were. Every
  axis now names its colours: the page's axis tone, the zero line in the panel's hairline, gridlines
  only. The fan's price axis writes prices in full (27,000, not 27k), as the tables do.

---

 — *The family's mark and tab*
### Fixed
- **The browser tab reads like every member's.** It said "Anumaan · Terminal" beside a "◈" glyph;
  it now says "ANUMAAN | Chart Terminal", the family's "NAME | Descriptor", beside Tattva's cobalt
  ring-and-line icon, in the same bytes as every member's.
- **The mark is the family's.** Under ANU**MAAN** the command bar wrote "अनुमान · terminal"; every
  member's mark carries its name in Devanagari alone, so it now reads "अनुमान".

---

## [Terminal 1.1.0] — 2026-11-23 — *Into the family*
### Added
- **The family console.** `terminal/logger_config.py` is the console every member of the Pragyam family
  shares, byte for byte. Loading a chart now writes its trace to the terminal: the request (symbol, interval,
  the script's inputs), five numbered, timed steps (Looking Up the Symbol, Loading Bars, Running Anumaan,
  Building the Volume Profile, Quoting the Watchlist), a result card (symbol, last price and change, bars,
  exposure, risk, the cone, the profile, the watchlist), the chart's notices, and a closing line with the time,
  warnings and errors. Before, it printed nothing but Yahoo's own errors. A chart already traced (same symbol,
  interval and inputs, no refresh) prints nothing again when a tab or a control reruns the page; yfinance's
  output and Python warnings are routed into the run as dimmed lines instead of raw stderr; the masthead prints
  once per process.
- **The family progress card.** A chart loads under the family's card instead of two spinners: four phases
  (Symbol & Bars, Anumaan Engine, Volume Profile, Watchlist), each step named as it runs, the bar only ever moving
  forward. A fallback or a failure clears it.
- **The family footer**, under the chart library's attribution: © year · Anumaan · @thebullishvalue · version ·
  the time in IST.
### Changed
- **Paper first.** The terminal opens on Paper, and the appearance control reads Paper · Slate, as every
  member's does.
- **The bottom panel's charts hover like the family's.** The tooltip is the panel's own surface in the data face,
  and says what it points at. The fan printed a price as "26.0977k" and "Cone(10, …)"; it now reads "High · in 10
  bars · 26,097.70 (+2.95%)", the close by date, and each stop with its distance. Exposure against buy and hold
  printed raw floats ("6.132423%") and cut "Following exposure" to "Following ex…"; it reads "+6.1%" under the
  series' full names. The two histograms named a bin "−1 - −0.501" and gave whole percentages; they now read
  "−1 to −0.5σ · This state 11.2% · Every state 12.0%", and the surprise chart names its clipped end bins (below
  −2.875, above +2.875). Dates read 17 Aug 2009; risk's rank reads "95 of 100".
- **Every negative number carries the family's typographic minus** (−2.71, not -2.71): the panels' tables and
  headers, the script's table and the tapes' words, the watchlist, the chart's status lines and its price scale.
  Zero carries no sign.
### Fixed
- **Number inputs follow the appearance.** Position size's Equity and Risk per trade, and the numeric inputs in
  Settings, kept near-black steppers on Paper, from Streamlit's static dark base. They are now Nivesa's single
  input well: one border, the field and the steppers inside it, the steppers ruled off by a hairline and painted
  from the app's tokens in both appearances.
- **One rule per table row.** Streamlit's markdown table drew its own rule on every row, from the same dark base
  (near-white on Paper), against the cell's hairline. The cells now carry the only rule.
- **The charts' legends read on Paper.** Streamlit's Plotly template paints a legend from its own dark base, over
  the layout's font: "Every state", "This state", "Buy and hold", "Risk rank" were near-white (250, 250, 250) on
  the white panel, all but invisible. The legend's colour is now named, as in every member.
- **The watchlist fits a 320px phone.** There the frame is 298px, and four columns cut the prices ("25,349…") and
  the changes ("−1,483…"). On a frame under 340px the absolute change steps aside and Chg% carries the move, in
  its colour; 390px and up keep all four.
- **The chart's type is on the family's scale.** The pane's status line was 11.5px and the script's table 10.5px,
  between the family's tiers; both are now 11px.
### Checked
- Paper and Slate at 1920, 1440, 1194, 1024, 834, 390 and 320px, every tab: no colour from Streamlit's native
  base left on either appearance, nothing wider than the page, no console errors. What the family scan still
  reports is by design: the watchlist's descriptions and the panel headers' context end in an ellipsis where they
  run out of room. Type is on the family's tiers, in its two faces, Inter and JetBrains Mono.
### Docs
- The README in the family layout, the indicator's research and reading guide in `docs/GUIDE.md`, the family's
  proprietary `LICENSE` (the three Pine scripts stay under the Mozilla Public License 2.0, as their headers say),
  the family `.gitignore`, and this changelog.

---

## [Terminal 1.0.0] — 2026-11-23 — *The terminal*
### Added
- **A Streamlit chart terminal running the script**, ported to Python bar for bar (`terminal/engine`) and drawn on
  TradingView's open-source Lightweight Charts 5.2.1, on the family's design system. First built as Pramana ·
  Terminal, then renamed with the script.
- **The layout of a trading terminal.** A command bar (instrument, quote, change on the previous session, market
  state, as of); a one-row toolbar in three groups (symbol search and interval; the Anumaan pane and volume;
  refresh, Settings and appearance); the chart beside a rail with the watchlist and the Symbol box; and a bottom
  panel arranged by a trader's questions: Plan, Forecast, Audit, Events. Every panel's height is arithmetic, so
  side-by-side panels meet within a pixel.
- **Settings read from `anumaan.pine` itself**: the same labels, defaults, options, limits, groups and tooltips,
  all 45 inputs.
- **The watchlist**, curated to the TradingView list in sections (India, United States, Commodities, Crypto,
  Recent), as a two-way component with folding sections.
- **It says what went wrong.** Intervals Yahoo lacks for a symbol are dimmed; a symbol with no data keeps the last
  one that loaded; Yahoo's lagging daily bars for NSE and BSE indices are repaired from the hourly bars; the
  chart's conditions are notices under the toolbar, events are toasts. A tab that fails to draw says so while the
  others draw.
- **Every screen.** Desktop, tablet (1100px and below) and phone (640px and below) layouts in one order and one
  spacing rhythm, 40px controls on touch screens, and no sideways scroll from 320 to 1920px.

---

## [Script 2.7] — 2026-11-23 — *Anumaan*
### Changed
- Renamed to Anumaan (`pragyam.pine` stays, identical apart from the name). The forward cone is off by default.
  The script runs on the last 5,000 bars, so daily charts with decades of history stay inside TradingView's time
  limit.
### Fixed
- **The volume profile.** Its row search halved with `(lo + hi) / 2`, which Pine v6 makes fractional: rows went in
  out of order, and POC, VAH and VAL stood at an older session's values while the histogram showed this one. The
  profile is now built only over the stretch it draws from, with about sixteen intrabars per chart bar. No engine
  number changed.

## [Script 2.6.1] — 2026-11-23
### Changed
- Faster, with the same output.

## [Script 2.6] — 2026-11-13 — *The second interface audit*
### Changed
- On the chart the volume profile is the focal element and the cone is consulted; the tapes are green and red
  again. The column-flip signals were tested with tape, risk, midline and VWAP filters (`research/flips.txt`).
  On 17 Nov a pre-registered hyperparameter study kept every default.

## [Script 2.5] — 2026-11-12 — *The first interface audit*
### Changed
- Hierarchy, layout and wording, then the colour system.

## [Script 2.4] — 2026-11-12 — *Pragyam*
### Changed
- Renamed Kasauti → Pragyam, and the palette first set by meaning: gold for risk and nothing else.

## [Script 2.3] — 2026-11-12
### Changed
- The presentation closed: status line, line weights, column colours, a compact table. Stop asymmetry and VWAP
  tested (`research/observations.txt`).

## [Script 2.2] — 2026-11-12
### Added
- The landing band's midline, with its record (`research/midline.txt`).

## [Script 2.1] — 2026-11-12
### Added
- The volume profile, ported from Pragati. An experiment between 2.0 and 2.1 ("Maryada": touch probabilities on
  profile levels, unified tapes, Pragati's palette) was set aside; it remains at commit `7c5340a`.

## [Script 2.0] — 2026-11-11
### Added
- The tapes, a trend-aware cone, a stepped exposure dial, and a wider study.

## [Script 1.0] — 2026-11-11 — *Kasauti*
### Added
- The indicator: calibrated risk, exposure and a self-audit on the chart it is on.

---

## Pragati — 2026-11-02
- `pragati.pine`, the original multi-timeframe conviction oscillator, added. It is unchanged since; it was the
  direction of thought and the benchmark.
