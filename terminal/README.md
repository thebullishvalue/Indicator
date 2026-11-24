# Anumaan · Terminal

*Part of [Anumaan](../README.md), in the Pragyam family.*

A chart terminal for `anumaan.pine`, laid out the way a trading terminal is. The script runs in it, ported to Python bar
for bar, and is drawn on TradingView's open-source charting library.

```
streamlit run terminal/app.py
```

![Anumaan terminal, Nifty 50 daily](../docs/terminal_nifty_d.png)

## What is on the screen

| Area | What it is |
|---|---|
| **Command bar** | The instrument, its last price and its change on the previous session's close (on every interval, as a terminal shows it), the exchange, interval, bars calculated (at most 5,000, as `calc_bars_count`), the last bar's time, when Yahoo last priced it (As of), where the profile's intrabars came from, and whether the market is open |
| **Toolbar** | Three groups: what you are looking at (symbol search, which takes `NSE:TCS`, `AAPL`, `GC=F` or any Yahoo ticker, and the interval, 1m 5m 15m 30m 1h 4h D W M), how it is drawn (the Anumaan pane, Surprise or Proof, and volume), and the app's own controls (refresh, **Settings** and Paper / Slate). Intervals Yahoo has no bars for on this symbol are dimmed and struck through |
| **Chart** | Candles and volume, the volume profile with its value area, POC, VWAP, Initial Balance, prior-session and naked-POC levels and their tags, the landing band, midline, stop history, proven-state marks, the forward cone with its stops, and the table. Below it, the Anumaan pane: the surprise columns against the landing band, and the four tapes with their labels. The status lines follow the crosshair |
| **Watchlist** | The TradingView list in its own sections: India, United States, Commodities, Crypto, plus Recent for symbols you search. Click a row to open it; click a section's header to fold it |
| **Symbol** | Exchange and type, the day's range and the 52-week range |
| **Bottom panel** | Arranged by the questions a trader brings to the chart. **Plan**, what do I do now: exposure, risk, trend, the cone and this chart's record; position size at the script's stops for your equity and risk per trade; and a level ladder of every level the script draws, sorted by price, with its distance from the close in % and in σ. **Forecast**, how far can it go: the four horizons as a fan and a term structure, each with its record here, and what followed the current state against every state. **Audit**, has it been honest here: calibration by horizon, risk regime and trend; every surprise in band widths; the exposure against buy and hold; the ledger. **Events**, what changed and when: every alert condition as it fired, filterable by kind |

**Settings** reads its inputs from `anumaan.pine` itself: the same labels, defaults, options, limits, groups and tooltips, all 45 of
them. The **Display** group's **Theme** behaves as in the script: on Auto it follows the terminal's appearance, which opens on
Paper, as every member of the family does.

A chart loads under the family's progress card, four phases (Symbol & Bars, Anumaan Engine, Volume Profile, Watchlist) with
each step named as it runs, and the page closes on the family footer: the year, Anumaan, @thebullishvalue, the version and the
time in IST.

## In the terminal it runs from

Each chart it builds writes a trace to the console, in the family's format (`logger_config.py`, shared byte for byte with
every member): the request (symbol, interval, the script's inputs), five numbered and timed steps, a result card (symbol, last
price and change, bars, exposure, risk, the cone, the profile, the watchlist), the chart's notices, and a closing line with
the time, warnings and errors. A rerun that draws a chart already traced (a tab, a toggle) prints nothing; a refresh traces
again. Yahoo's own output (rate limits, retries) and Python warnings appear as dimmed lines inside the run.

## When something does not go as asked

The terminal says so, rather than drawing nothing or the wrong thing. Events are toasts, at the bottom right; conditions of
the chart in front of you are notices, under the toolbar, for as long as they hold.

| What happened | What the terminal does |
|---|---|
| An interval Yahoo has no bars for on this symbol (a fund has daily bars only) | The interval is dimmed. Clicking it says why and stays put. Opening such a symbol on that interval falls back to D, with a toast |
| An interval with too few bars to calculate | Falls back to D, with a toast |
| A symbol Yahoo does not have | Stays on the last symbol that loaded, with a toast saying why; for TradingView symbols Yahoo lacks (NIFTY1!, GOLD1!, SILVER1!, XAUUSD), what to open instead. TradingView prefixes work: `NSE:NIFTY`, `TVC:GOLD` |
| Yahoo unreachable, or no data on a first visit | An error panel with the reason and **Try again** |
| Yahoo's daily bars a session behind (NSE and BSE indices: on 23 Nov NIFTY's daily bars stopped at 20 Nov, its hourly bars and quote did not) | The missing session is built from the hourly bars and closes at the official close (`regularMarketPrice`); a notice says so. Weekly and monthly bars are rolled up from these daily bars, and the watchlist quotes the same bars, so chart and watchlist agree |
| A chart too short for the risk forecast (fewer than 252 + H bars) | A notice: the cone, stops and exposure are warming up, and which interval has enough |
| The market is open but the last bar is old | A notice: the feed is behind |
| No volume (yields, some indices), no intraday bars for the profile, intrabars failing to load | A notice each |
| Settings applied, defaults restored, data refreshed | A toast |

**Refresh** (the ↻ beside Settings) reloads bars and quotes from Yahoo; they are otherwise kept 5 minutes (quotes 2). The symbol and
interval live in the address bar (`?symbol=GOLD&tf=W`), so a reload keeps your place and a link opens that chart.

## Screens

It works on any screen, and every size is organised the same way, top to bottom: the mark and the market's state, the
instrument and its quote, the toolbar, notices, the chart, the watchlist, the Symbol box, the bottom panel.

| | Desktop (over 1100px) | Tablet (641-1100px) | Phone (640px and under) |
|---|---|---|---|
| Command bar | One line: mark, instrument, quote, details, market state | One line, as on a desktop: mark, instrument, quote, market state; the details move to the Symbol box | Two lines: mark and market state; symbol left, quote right |
| Toolbar | One line in three groups | Two lines: search and the intervals; pane and volume on the left, refresh, Settings and appearance on the right | Three lines: search with refresh and Settings; the nine intervals across the width; pane, volume, appearance. Buttons as icons |
| Rail | Beside the chart, exactly its height | Under the chart, panels at full width; the Symbol box in two columns, carrying the command bar's details (exchange, last bar, as of, bars, currency, profile) | Under the chart; the Symbol box in one column, with the last bar and as-of too |
| Bottom panel | Side-by-side panels with computed, flush heights | Panels stacked at full width; headline cards in one even row | Panels stacked; headline cards two to a row; wide tables scroll sideways with a shadow at the edge and the first column pinned |

On a touch screen the toolbar's controls are 40px high instead of 32. Spacing is one rhythm per size: 12px between blocks on
a desktop or tablet, 10px on a phone, 8px between toolbar lines. Tested at 320 (iPhone SE, Galaxy S9+), 390, 768, 834,
1194, 1280, 1440 and 1920px wide, with no sideways scroll at any of them.

**Price scale.** As on TradingView: **A** and **L** sit in the corner under the price scale. **A** (auto) fits the scale to
the bars in view; dragging the scale turns it off, and A, a double-click on the scale or **Reset price scale** turns it back
on. **L** makes the scale logarithmic, so a move of the same percentage is the same height anywhere on the chart; the
volume profile, levels, cone and stops follow it. Log and Auto are both on by default; turning log off is remembered in
the browser. The scale's menu opens on a
right-click (desktop) or a long press on the price scale (touch): Reset price scale, Auto, Regular / Logarithmic, Reset chart
view. Alt+L toggles log, Alt+R resets the chart view.

**Keys and memory.** `/` jumps to the symbol search from anywhere, Escape leaves it. Folded watchlist sections are remembered
in the browser. A tab that fails to draw says so in its place while the others draw; if the script itself fails on a chart,
the terminal steps back to D, else to the last symbol that ran, and says why.

## How faithful it is

**The engine** (`engine/anumaan.py`) ports sections 1 to 6b of the script in its own order, with Pine's semantics where they decide
a value: `ta.ema` seeded on the first value, `ta.rma` seeded on an SMA, `ta.percentrank` returning na if its window holds one,
`ta.sma` skipping na, comparisons with na false. On six instruments it matches the research reference (`research/anumaan.py`) to
floating-point error on every series. The one exception is the cone widths, which differ by 3e-9. The script starts them from
Acklam's inverse normal, and the port follows the script.

**The volume profile** (`engine/profile.py`) ports section 7: sessions, ATR rows frozen at the session's first bar, the intrabar
spread, POC, value-area walk, prior session, naked POCs, VWAP, Initial Balance, row aggregation, HVN / LVN, and tag collision.

**The table and the tapes' words** (`engine/table.py`) use the script's own text and number formats.

What cannot be identical is the **data**. TradingView's feed is not Yahoo's:

- **Intraday history.** Yahoo serves 1m bars for 7 days, 2m to 30m for 60 days and 1h for 730 days. Daily and longer go back as
  far as Yahoo has them. The script runs on the last 5,000 bars either way.
- **Intrabar timeframes.** The script asks for about sixteen intrabars per chart bar. Where Yahoo has no such interval the terminal
  uses the nearest finer one: 2m for the script's 3, and 5m for its 10. It builds 2h and 4h by resampling 1h. Bars older than the
  intrabar history are spread over their range, as the script does where intrabar data does not reach.
- **Volume.** Yahoo reports no intraday volume for some symbols (indices) whose daily bars carry it. There, the profile shares each
  bar's own volume evenly over its intrabars, and the page says so.
- **Sessions.** A session is the exchange's calendar day on intraday charts, the week on daily, and the month above. Futures
  sessions that open the evening before (CME's 6pm) therefore split where the calendar does, not where the exchange does.
- **Min tick** is Yahoo's price hint.

The port has not been compared bar for bar against TradingView's own output: no Pine runtime is available here. On any chart, the
table's eight rows and the Data Window can be checked against the script's table and data window in TradingView.

## Built on

- **Design system.** The Pragyam family's: `ui/theme.css` is the stylesheet every member shares, with its fidelity block, and
  `ui/terminal.css` is the terminal's own layout on the same tokens. It uses the Graphite and Paper tokens, Inter and
  JetBrains Mono, and Streamlit pinned to exactly 1.52.2 (see `requirements.txt`). Numbers read as in every member: tabular,
  right-aligned, signed changes with a typographic minus (−2.71).
- **Console.** The family's (`logger_config.py`), byte for byte.
- **Charts.** [TradingView Lightweight Charts™](https://www.tradingview.com/) 5.2.1, Apache-2.0, vendored in `ui/static` with its
  licence and notice. The licence's link to tradingview.com is in the page footer. Anumaan's drawings that the library has no series for, such
  as profile rows, level lines and tags, the cone and the tapes' labels, are custom primitives positioned in bar indices and
  prices, as the script positions them.
- **Data.** Yahoo Finance via `yfinance`, delayed.
- **Watchlist.** A two-way Streamlit component in plain JavaScript (`ui/static/watchlist`), with no build step. The list
  lives in `engine/data.py` (`WATCHLIST`) as TradingView names mapped to Yahoo tickers:

  | Section | TradingView | Yahoo | Note |
  |---|---|---|---|
  | India | NIFTY, SENSEX, BANKNIFTY | `^NSEI`, `^BSESN`, `^NSEBANK` | |
  | | CNXMIDCAP, CNXSMALLCAP, NIFTY_MICROCAP250 | `NIFTY_MIDCAP_100.NS`, `^CNXSC`, `NIFTY_MICROCAP250.NS` | Yahoo keeps one daily bar; D, W and M are built from the hourly bars (from Dec 2023), whose closes match Yahoo's daily closes |
  | | INDIAVIX, USDINR | `^INDIAVIX`, `INR=X` | |
  | United States | ES1!, US10Y, DXY | `ES=F`, `^TNX`, `DX-Y.NYB` | |
  | Commodities | CT2!, USOIL, UKOIL | `CT=F`, `CL=F`, `BZ=F` | |
  | | GOLD, SILVER | `GC=F`, `SI=F` | COMEX front-month futures stand in for spot, which Yahoo does not carry |
  | Crypto | BTCUSD | `BTC-USD` | |

  Not on Yahoo, so not in the list: NIFTY1! (GIFT Nifty) and the MCX contracts GOLD1! and SILVER1!.
- **Bad prints.** Yahoo has the odd zero open, high or low (CT=F, the week of 25 May 2020, has a low of 0). Its log is minus
  infinity and would end the risk forecast for good, so a zero price is read as missing when the bars are cleaned.

The terminal is laid out like a trading terminal but carries none of TradingView's branding: its name, logo and trademarks are
TradingView's own. The chart library's attribution, in the footer, is the one exception, and its licence requires it.

## Files

| File | What it is |
|---|---|
| `app.py` | The page: command bar, toolbar, chart and rail, bottom panel, footer, and the run's trace and progress card |
| `logger_config.py` | The family console |
| `engine/anumaan.py` | The script's engine, sections 1 to 6b, and its alerts |
| `engine/profile.py` | Section 7, the volume profile |
| `engine/table.py` | Section 9, the table, and the tapes' words |
| `engine/palette.py` | The script's palette and transparency ladder |
| `engine/data.py` | Timeframes, symbols, Yahoo bars and intrabars |
| `ui/chart.py`, `ui/static/chart.js` | The chart payload and its renderer |
| `ui/inputs.py` | The settings, read from `anumaan.pine` |
| `ui/panels.py` | The bottom panel |
| `ui/theme.css`, `ui/theme.py`, `ui/terminal.css`, `ui/components.py` | The design system, the progress card, and the terminal's layout |

To deploy on Streamlit Community Cloud, set the main file to `terminal/app.py`. Its `requirements.txt` sits beside it, and the
theme config is in `.streamlit/` at the repository root.
