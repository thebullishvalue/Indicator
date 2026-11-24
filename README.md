<div align="center">

# ANUMAAN

**अनुमान** · *inference*

Calibrated Risk · Stops · Exposure · Self-Audit · Volume Profile

[![Version](https://img.shields.io/badge/version-1.1.2-2B5FD9)](CHANGELOG.md) [![Python](https://img.shields.io/badge/python-3.10%2B-3776AB)](terminal/requirements.txt) [![Streamlit](https://img.shields.io/badge/streamlit-1.52.2-FF4B4B)](terminal/requirements.txt) [![License](https://img.shields.io/badge/license-proprietary-6B7280)](LICENSE) [![Pragyam Family](https://img.shields.io/badge/pragyam-family-0F1217)](#the-pragyam-family)

</div>

> It forecasts only what can be forecast, and keeps a record of whether each forecast came true
> on the chart it is on.

## Overview

*Anumaan*, from *anumāna* (अनुमान), inference: knowing what cannot be seen from what can, as smoke tells of fire. It is
one TradingView indicator (Pine v6) and a chart terminal that runs it, ported to Python bar for bar.

It answers three questions for the chart it is on, and then tests its own answers:

1. **How far can it go?** A cone for the close 10 bars ahead that holds 80% of the time.
2. **Where am I wrong?** A stop level that is touched within 10 bars 20% of the time, and the position size that goes with it.
3. **How much should I hold?** An exposure dial between 0 and 1.

It does not call direction. On 151 instruments over 25 years, nothing on a single chart led the next ten bars in a way
that held in all three eras tested; risk did, forecast out of sample with a log R² of 0.71. So Anumaan forecasts risk,
states it as probabilities, and turns it into a cone, stops, a size and an exposure. The [guide](docs/GUIDE.md#why-it-does-not-call-direction)
has the study.

Built with Streamlit, TradingView's open-source Lightweight Charts and Plotly. Prices from Yahoo Finance, delayed.

## What It Does

| Part | What it is |
|---|---|
| `anumaan.pine` | **The indicator.** The pane, the tapes, the cone and stops, the volume profile and the table, in one script. The only data it requests is the chart symbol's own lower timeframe, for the profile |
| `terminal/` | **Anumaan · Terminal.** The script running in a Streamlit chart terminal, drawn on Lightweight Charts, with a watchlist and a bottom panel that audits it on the chart in front of you |
| `research/` | The data fetch, the Python reference for the script, and the study behind every number in the guide |
| `pragyam.pine` | The same script under its earlier name, Pragyam. Identical apart from the name; kept so charts that use it keep working |
| `pragati.pine` | **Pragati**, the original multi-timeframe conviction oscillator. Unchanged; it was the direction of thought and the benchmark |

**The terminal** is laid out like a trading terminal: a command bar, a toolbar, the chart beside a watchlist rail, and a
bottom panel arranged by the questions a trader brings to a chart.

| Tab | Question | Contents |
|---|---|---|
| **Plan** | What do I do now? | Exposure, risk, trend, the cone and this chart's record · position size at the script's stops · risk and exposure over time · the level ladder |
| **Forecast** | How far can it go? | The four horizons as a fan and a term structure · the stops' record here · what followed the current state |
| **Audit** | Has it been honest here? | Calibration by horizon, risk regime and trend · every surprise in band widths · the exposure against buy and hold · the ledger |
| **Events** | What changed, and when? | Every alert condition as it fired, filterable by kind |

Its settings are read from `anumaan.pine` itself, all 45 inputs. The [terminal's page](terminal/README.md) covers every
screen size, what it does when something does not go as asked, and how faithful the port is.

## Quick Start

```bash
pip install -r terminal/requirements.txt
streamlit run terminal/app.py
```

Python 3.10+. On TradingView, open the Pine Editor, paste `anumaan.pine` and add it to a chart. To reproduce the study,
see the [guide](docs/GUIDE.md#reproduce).

## Project Structure

```
anumaan.pine         the indicator (Pine v6)
pragyam.pine         the same script under its earlier name
pragati.pine         the original conviction oscillator, the benchmark
terminal/            the chart terminal
  app.py             the page: command bar, toolbar, chart and rail, bottom panel, footer
  logger_config.py   the family console (shared byte for byte with every member)
  engine/            the script ported bar for bar: engine, volume profile, table and words,
                     palette, Yahoo data
  ui/                the family's design system (theme.css, theme.py), the terminal's layout
                     (terminal.css), components, panels, the chart payload, and static/
                     (the Lightweight Charts renderer and the watchlist component)
research/            the data fetch, the Python reference, the study and its outputs
docs/                the guide and the images
```

## Documentation

| Document | What it covers |
|---|---|
| [Guide](docs/GUIDE.md) | The indicator: why it does not call direction, the tapes, what the study measured, the observations since, what it does not do, its chart interface, how to read it, its status, and how to reproduce every number |
| [Terminal](terminal/README.md) | The terminal: what is on the screen, what it does when something goes wrong, every screen size, how faithful the port is, what it is built on, its files |
| [Changelog](CHANGELOG.md) | Every release of the terminal and the script, newest first |

## The Pragyam Family

Eleven Streamlit applications built on one design system and one set of components, so a
panel, a table, a chart or a number reads the same in each.

| Product | What it is |
|---|---|
| [**Tattva**](https://github.com/thebullishvalue/Tattva) | Cross-asset fair value, with a call only where its own record supports one |
| [**Nishkarsh**](https://github.com/thebullishvalue/Nishkarsh) | Nifty 50 inference: a top-down forecast and bottom-up breadth, read as one |
| [**Arthagati**](https://github.com/thebullishvalue/Arthagati) | Valuation-anchored market sentiment, tested on data it never saw |
| [**Vyapti**](https://github.com/thebullishvalue/Vyapti) | Market breadth: where participation stands, which way it moves, and what that has meant |
| [**Pragyam**](https://github.com/thebullishvalue/Pragyam) | Portfolio curation that spreads risk rather than predicting returns |
| [**Sanket**](https://github.com/thebullishvalue/Sanket) | A market signal screener: what fired, what is about to, and whether it has paid |
| [**Vaaydo**](https://github.com/thebullishvalue/Vaaydo) | An F&O trade screener on option positioning, with futures tickets |
| **Anumaan** · *this repository* | A chart terminal: calibrated risk, stops and exposure, audited on the chart it is on |
| [**Nivesa**](https://github.com/thebullishvalue/Nivesa) | A bond portfolio ledger: cost, yield, duration and cashflows across accounts |
| [**Samhita**](https://github.com/thebullishvalue/Samhita) | A portfolio tracker: live prices, performance and risk against the benchmark |
| [**Swing**](https://github.com/thebullishvalue/Swing) | A portfolio tracker for the swing book, on the same engine as Samhita |

## License

Proprietary. © 2026 @thebullishvalue. All rights reserved. The source is visible here
for reference only: viewing it grants no right to use, copy, modify or distribute it.
See [LICENSE](LICENSE).

The three Pine scripts (`anumaan.pine`, `pragyam.pine`, `pragati.pine`) are the exception:
each is published under the Mozilla Public License 2.0, as its header states.

## Disclaimer

Anumaan is a research and decision-support tool, not investment advice. Nothing it shows is
a recommendation to buy or sell any security, and past or measured results do not guarantee
future ones. Every decision made with it is your own.

---

<div align="center"><sub>© 2026 @thebullishvalue · Part of the Pragyam product family</sub></div>
