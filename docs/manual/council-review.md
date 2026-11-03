# Field manual · council review (manual 1.0 → 1.1)

**The question.** Is manual 1.0 the edition to publish?

**Seats.** The manual was read by seven, each against its own brief:
1. **Evidence quant:** every number against `docs/trail-lab.md`, `docs/trail-tradability.md` and the script's quoted audit figures.
2. **Pine engineer:** every described behaviour against `pragati.pine` v9.9 and `research/trail_lab.py`.
3. **Trader:** can the trading rules be followed as written?
4. **Investor:** can the investment guide be run?
5. **First-time reader.**
6. **Risk and compliance.**
7. **Designer:** the page and the printed PDF, from contact sheets of every page.

**Verdict on 1.0: not to be published.** Its rules and numbers had five errors that would have misled a reader. It also lacked what a trader needs to act.

## Accuracy, fixed

| # | Finding | Evidence | Fix in 1.1 |
|---|---|---|---|
| A1 | Said the trading system "changes sides at once" | The frozen engine is continuous (`variant("T126xTS", 3, False, …)`). Under `weights_trade`, every change waits for the weekly rebalance, flips and going flat included, and happens only when the target moved more than 10% | The rule now reads as tested. A new note covers what to do when an alert arrives between rebalances |
| A2 | Attached the investor drawdown result (−35% vs −73.5%) to Accepted momentum | That was T-LO, the **20-bar** trail held long-only (`docs/trail-tradability.md` §7). Accepted momentum was never tested long-only | Attributed correctly, and the evidence table is relabelled |
| A3 | Matrix D said "positive, all eras" for every asset class | The ▲ was positive in 4–5 of the 5 non-crypto classes per era. ETFs were not a v9 class; US stocks and world indices were | The table is rebuilt from what each test actually covered |
| A4 | Printed portfolio drawdowns of −2.5% / −3.7% without context | The diluted book ran at about 1.3–1.6% volatility. At 10% book volatility the same paths draw down roughly 16–29% | Both are now stated together |
| A5 | "Short, usually small (S is small)" had no basis; house rules carried no tag | — | The claim is removed. The cadence, rebalance band and weight cap are tagged Unmeasured |

## Usability, added

- **Where sizing gets its volatility:** the tested EWMA (span 60), with TradingView's Historical Volatility at length 60 as a tagged stand-in.
- **The costs the test charged**, by class.
- **How many markets** the edge needs.
- A **sixty-second reading routine**, worked on Plate 2's readout.
- A **troubleshooting table** of 13 symptoms.
- **Four worked scenarios** over time: a capitulation dip in an uptrend; distribution while still long; nothing to do; aligned with a crowded book.
- **Glossary additions:** VWAP/TWAP, IB, HVN/LVN, and the OI terms.
- A **contents page** for phones and print.
- Chapter numbers and cross-references are now generated, so additions cannot leave a stale reference.

## Print, fixed

- In 1.0 many pages were half empty: long tables were kept whole and jumped to fresh pages, and chapter labels were stranded at page bottoms.
- In 1.1 tables break between rows and repeat their headers, and each chapter head stays with what follows. The added material fits in 29 pages.

## Before calling it final

1. **Confirm v9.9 loads on TradingView** after the RE10045 fix. The manual describes v9.9 behaviour.
2. **Optional:** replace the synthetic plates with screenshots of a real chart. That needs the owner's charts.
