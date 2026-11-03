# Field manual 2.0 · the council

**The owner's brief (2026-11-03):** "a lot more explanation … a very more
granular knowledge base … more case studies of indicator, more on how to
initiate trade and positioning, more on how to read contextually, how to
figure fake out setups and avoid, various trading setups using the indicator,
investing setups using the indicator … The one can entirely be master of the
indicator when it reads the guide."

**The test the council set itself.** A reader who has only this book, and has
never opened the code, can do six things:

1. say what every mark, colour, row and number on the chart means, and why it
   is there;
2. say which engine produced it and from what inputs;
3. read a chart in context, top-down, and say what kind of market it is;
4. tell a probe that will fail from one that is being accepted, and know what
   that difference is worth;
5. initiate, size, manage and exit a trade or an investment with Pragati, by
   rules that are written down and whose evidence is stated;
6. know where the evidence stops.

---

## The tiers

| Tier | Seat | Owns |
|---|---|---|
| **0 · Charter** | Editor-in-chief | The brief, the mastery test above, and four non-negotiables: (1) no claim beyond its evidence, and every claim carries its tag; (2) no fabricated result: a case study is real data, or is labelled *constructed*; (3) every mechanic is traceable to the code; (4) nothing is advice |
| **1 · Curriculum** | Master educator | The mastery path: Foundations → Knowledge → Reading → Context → Traps → Application → Cases → Mastery. Each chapter opens with what the reader will be able to do |
| | Instructional designer | Drills with answer keys, checklists, decision trees, and a journal template. The learner practises, rather than only reads |
| **2 · Domain masters** (authors) | Auction and market-profile practitioner | The auction engine, value, migration, the trail, probes, the session profile, naked POCs, VWAP and IB |
| | Flow and derivatives specialist | Open interest: build, cover, unwind, crowding, expiry, trust |
| | Systematic trader | Accepted momentum, sizing, rebalancing, portfolio construction and kill rules |
| | Discretionary swing trader | The setup catalogue, entries, stops, management and re-entry |
| | Long-term investor and allocator | The grid as an allocation map, investing setups, staging, trimming, rebalancing and watchlists |
| | Risk manager | Position sizing, portfolio heat, correlation clusters, drawdown control and the kill rules |
| **3 · Evidence and code** | Quant statistician | Pre-registered the setup lab (`docs/setup-lab.md`) before any run. Ran it once. Owns every number |
| | Pine code auditor | Checks every mechanic, threshold and default against `pragati.pine` |
| | Case-study editor | Real-data reconstructions under a selection rule fixed in advance, losers included |
| **4 · Red team and production** | Skeptic | Asks of every page: "how would a reader lose money following this?" |
| | Compliance | Risk disclosure, and the line between education and advice |
| | Technical editor and book designer | Plain language, structure, and the 1.3 typesetting rules |

## Round 1 · gap audit of Manual 1.3

Each seat listed what a master needs that 1.3 does not give:

| Seat | Gap in 1.3 |
|---|---|
| Curriculum | No mastery path, no learning objectives, no practice. The reader cannot check what they know |
| Auction practitioner | The trail is explained in a paragraph. Its start, step, probe and flip rules are not stated; the 126- versus 20-bar window is not explained; migration is a table without its geometry; the session profile is two lines |
| Flow specialist | The OI states are listed, but not how ΔOI becomes σ, what "structural" means, what trust is, or how expiry distorts the book |
| Systematic trader | Sizing is given, but not execution: decision time, order type, gaps, lot rounding, rebalance days, what to do on a missed day |
| Swing trader | No setup catalogue. "Discretionary overlays" is one table with no entry, stop or exit for any of them |
| Investor | Families and a capitulation plan, but no setups: no trend filter, no staging rule, no trim discipline, no calendar, no watchlist method |
| Risk manager | No portfolio heat, no correlation limits, no rule for adding to losers, no drawdown ladder |
| Quant | Fakeouts are named (probes) but never measured. "What makes a break real" is unanswered |
| Case editor | Four constructed scenarios and no real chart. The reader never sees a reading unfold on a real market |
| Code auditor | The engines are described without their formulas, warm-ups and limits, so a reader cannot reason about an edge case |
| Skeptic | A reader could trade the probe ×, the ◆ or the 20-bar trail, all measured null, because no chapter is about traps |

## Round 2 · the blueprint

Manual 2.0 grows from 6 parts and 14 chapters to **11 parts and 32
chapters**. Kept material is marked ◦; everything else is new.

| Part | Chapters |
|---|---|
| I · Foundations | Getting started ◦ · The visual language ◦ · How Pragati thinks (the engines ◦, the thesis, the mastery path) |
| II · The knowledge base | The conviction engine · The value engine · The ladder and the four tapes · The grid engine and the signals · The auction engine and Accepted momentum · The session profile and open interest · Timing, repainting and limits |
| III · Reading every state | The grid ◦ · The readout ◦ · Panel, marks and troubleshooting ◦ |
| IV · Reading in context | The context stack and the top-down routine · Regimes, and how meaning changes |
| V · Fakeouts and traps | Probes and acceptance, measured · The trap catalogue |
| VI · Trade guide | Accepted momentum ◦ · Initiating and positioning · The trading setups · Managing and reviewing (overlays ◦, stops ◦, exits, the journal) |
| VII · Investment guide | Investing with the grid ◦ · The investing setups · The book and its risk ◦ |
| VIII · Case studies | Real markets, reconstructed (six markets, selection rule fixed in advance) · Full-stack walkthroughs (constructed, labelled) |
| IX · Permutations and combinations | The four matrices ◦ · Conflicts and the decision tree |
| X · Mastery | Drills · Answers and checklists |
| XI · Reference | Alerts and the complete settings reference (all 80 inputs) · What is measured ◦, with the setup lab |

## Round 3 · evidence

The statistician's ruling, accepted by the chair:

> A setup chapter that the code cannot test is opinion. A setup chapter that the code *can* test, but did not, is negligence.

The auction engine, the trail, the push gate and Accepted momentum are
reproduced bar for bar by the repository's reference code. So every setup
built only from them was put to a pre-registered test before the chapters
were written: `docs/setup-lab.md`, committed as `ce9ab7a` before the run.

Setups built on the tapes, the grid or the ▲▼ cannot be tested here. Those
engines need TradingView's intrabar data and Samanvaya's macro drivers. They
carry the v9 audit's External evidence, or the tag Unmeasured.

A null test on eight driftless random walks came first. The measuring stick
read about 0 there, with a mean excess of −0.02σ for F1, so it does not
manufacture an edge. Results: §6 of the protocol, and Round 3's notes below.

### What the evidence changed

The setup lab's verdicts (§6 of the protocol) are in Part V, Part VI and chapter 32:

| Belief before the test | What the data said | Where the book teaches it |
|---|---|---|
| A probe is a fakeout: fade it | **The opposite.** After a probe the trend's side did 0.05 to 0.09σ worse than usual over 10 to 20 bars, in all three sets. Yet the 126-bar trail almost never flips on one (under 5% within 20 bars) | 16.2, T4 |
| Hard, heavy breaks get accepted | **True on the 20-bar trail** (confirmed): a break of 0.5 ATR or more flipped it 71% of the time against 54%, and a heavy one 62% against 57%. **Not on the 126-bar trail**, where only migration toward the break mattered | 16.3, the checklist |
| Buy the pullback into value | **Nothing.** A close out of value in the trend's direction did better everywhere (not predicted, so it awaits a fresh holdout) | 16.4, T2 |
| Enter on the rejection of a probe | Not supported | 16.4 |
| Enter on the acceptance (the flip) | Consistent | T3 |
| A trend filter for investors | Drawdown roughly halved and return roughly halved; Sharpe lower than buy-and-hold in 2020–26. Not confirmed | I2 |

**Amendment 1, stated plainly.** Run 1 produced invalid HA cells, because
frozen prices in suspended stocks drove σ to zero. The fix was written,
committed and given a sensitivity run before run 2, with run 1 kept
unchanged. All of run 1 had been seen. The amendment touches only stale bars,
and both rules give the same verdicts.

## Round 4 · authoring

- **Size:** from 9,010 words on 60 pages (1.3) to about 35,000 words on 158
  pages.
- **Structure:** 11 parts, 32 chapters, 128 numbered sections.
- **New content:**
  - every chapter opens with its objectives;
  - the knowledge base (Part II) gives every engine its formula, defaults,
    warm-up and limits, checked against `pragati.pine`;
  - the settings reference lists all 80 inputs, generated from the script
    itself, so it cannot drift from the code.
- **Case studies (Part VIII):** six real markets reconstructed by the
  reference engine (`research/case_extract.py`), under the rule fixed before
  any plot.
  - The selection rule produced losing campaigns, and a six-market book that
    lost 0.69% over ten months. The book shows them, and explains why that is
    what a portfolio's edge looks like on six markets.
  - Constructed walkthroughs, labelled as such, cover the grid and OI, which
    the reference cannot reproduce.

## Round 5 · red team

| Finding | Seat | Fix |
|---|---|---|
| 1.3 said a probe "often fails back" (unmeasured) | Quant | Replaced by the measured F1 result wherever probes are discussed |
| The default trail can sit far from price for months. On real data the quiet regime shut the push gate on 85% of NIFTY's last 300 bars, so the trail cannot step | Case editor, found while plotting | Taught in 8.2, 15.1 and every case; "the trail's level is not a stop" is now a trap in 17.1. **For the indicator itself:** a design question for a future version. Nothing in the script changed |
| The traded weight lags the CHART cell until the weekly rebalance | Systematic trader | Taught in the RELIANCE case and in 19.1 |
| A worked units figure was wrong (2.6; correct 2.35), and one evidence chip was mislabelled | Code auditor | Fixed. The arithmetic was re-derived from the Pine formula |
| A lot size was quoted that could not be verified | Compliance | Removed; the reader is told to check the exchange |
| "Best picture" and "strongest picture" overstated two unmeasured combinations | Skeptic | Reworded |
| "Accepted momentum was not tested as a filter" was no longer true | Quant | Points to I2 and its numbers |

## Round 6 · production

| Defect | Fix |
|---|---|
| **The final pages could reflow against the layout pass.** Chromium rounds 26 + 26 mm and 24 + 28 mm margins to different whole pixels, so text columns were a pixel apart and some lines broke differently. 1.3 escaped by luck | Margins are now whole pixels (98 + 98 in the layout pass, 91 + 105 mirrored in the final). A new check confirms that every body page of the final book holds exactly the layout pass's text |
| Hyphenation split a part title ("knowl‐edge"), and the page locator could not find it | Titles and headings no longer hyphenate; the locator ignores U+2010 |
| Long lists could not break, leaving half-empty pages | Lists break between items, never inside one |
| An objectives box could be stranded at a page foot | It is kept with what follows |
| Wide tables were crushed on phones | They scroll sideways |

**Checked on the final PDF:**
- all 128 contents entries match their folios;
- all 1,208 index locators are on their pages;
- the layout pass equals the final book on all 146 body pages;
- all 11 parts are on rectos with blank versos;
- the index opens on a recto;
- the book has 158 pages, an even count;
- the web edition has no horizontal scroll at 390 px.

## Limitations, stated

- The grid, the tapes and the ▲▼ cannot be reconstructed from this
  repository, so their setups carry the v9 audit's External evidence or the
  tag Unmeasured. Their walkthroughs are constructed.
- S4 (the breakout from value) was not predicted, so it needs a fresh
  holdout before it can be called confirmed.
- The setup lab covers daily bars only. HA is NSE stocks and crypto, today's
  listings (survivorship).
- Pragati v9.9's run on TradingView after the RE10045 fix is still
  unconfirmed. The book describes v9.9.
