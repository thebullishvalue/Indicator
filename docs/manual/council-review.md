# Field manual · council review (manual 1.0 → 1.3)

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

## 1.2 · the print edition

**The owner's verdict on 1.1:** the PDF content was misaligned on its pages and did not look finished.

**Cause.** The PDF was the responsive web page printed as it stood:
- paragraphs kept a web reading width, so text, tables and figures ended at different right edges;
- grids of cards and steps reflowed into uneven columns;
- process diagrams wrapped with orphaned arrows;
- tables sized their columns to their contents;
- there was no cover, no contents and no part opener.

**1.2 is a book designed for A4**, built from the same content by `src/print_edition.py`:
- **One grid.** A single 176 mm text column with every block on its edges, and fixed column widths for all 24 tables (shared with the web page).
- **Components redrawn for print.** Ruled step rows, aligned two-column timelines in place of arrow flows, and fixed two- and three-column card grids.
- **A designed cover**, rendered on its own and joined in front.
- **Part openers** that list their chapters, and a running header and footer.
- **A contents page with real page numbers.** The body is laid out once, each chapter's page is read back with `pdftotext`, the numbers are written in, and the build checks that the second layout lands every chapter on the same page.

The result is 24 pages, down from 29, with no stranded headings or widowed list items. The only short pages are the last pages of Parts I, III and V, where the next part begins.

`src/print_edition.py` was replaced in 1.3 by `src/book.py`.

## 1.3 · the book

**The owner's verdict on 1.2:** "it's a book, but there are no publishing rules applied". Parts, chapters and sections were not placed as a book places them, and the spacing did not follow book conventions.

**What 1.2 lacked.** It was a well-aligned A4 document, not a book:
- parts and chapters fell on whichever page came next, left or right;
- the folios had no front-matter numbering and no rule about where they go;
- there was one running header for every page;
- sections were unnumbered, and figures and tables had no numbers or titles to cite;
- there was no index, and the back matter was in no set order.

**1.3 applies the conventions of book typography**, following the Chicago Manual of Style's order and placement. `src/book.py` builds it from the same content as the web page.

| Rule | 1.3 |
|---|---|
| Order | Cover · title page · imprint · contents · how to use · six parts, fourteen chapters · quick reference card · glossary · index · colophon · back cover |
| Parts | A recto of their own, listing their chapters with page numbers. The verso behind each is blank, so every part's first chapter opens on a recto. A blank verso is added before a part that would land on the left |
| Chapters | Each opens a new page with its title sunk about a quarter of the way down, a drop folio and no running head |
| Sections | Numbered 1.1 to 14.1, with the number set inline in the heading's own face. Cross-references name them: "section 9.1", "chapter 5" |
| Figures and tables | Figures 2.1 to 9.1 are captioned below; 23 tables (4.1 to 14.1) are titled above, all numbered by chapter. Tables are ruled top, head and foot only. A table of five rows or fewer is never split; a longer one splits with its head repeated and at least two rows on each side of the break |
| Folios | Roman in the front matter, with none on the title page or imprint. Arabic from 1 at Part I. None on part or blank pages, centred on openings, outer corners elsewhere |
| Running heads | The part on the verso, the chapter on the recto (the book title in the back matter); none on openings or blanks |
| Margins | Mirrored: inner 24 mm, outer 28 mm, top 24 mm, bottom 26 mm |
| Text | IBM Plex Serif 10.4/15 pt, justified and hyphenated, with the first paragraph after a heading flush and the rest indented. Headings, tables and captions in Plex Sans |
| Back matter | The quick reference card (an appendix) comes before the glossary, which is now alphabetical. The index of 68 terms is read from the laid-out pages and opens on a recto. The colophon says how the book was made |
| Imposition | 60 pages, an even count, with the back cover on the last verso |

**How the page numbers are made true.**
1. The body is laid out once with symmetric margins and no heads. Mirrored margins keep the same text width, so the lines break the same way.
2. Every part, chapter, section and back-matter opening is found on its page with `pdftotext`.
3. Parts are moved to rectos and the index to a recto. The contents, the part pages' lists and the index are written from what was found.
4. The book is laid out again, and this repeats until the index it prints is the index of the pages it prints. A first draft of the build printed an index taken from one layout too early, and some of its locators pointed at the wrong pages; the settle rule fixed that.
5. Each page is rendered with its own margins, running head and folio, and the pages are joined.

**Checked on the final PDF:**
- 39 of 39 contents entries match the folio printed on their page;
- 350 of 350 index locators were found on their page;
- all six parts are on rectos with blank versos, and the index is on a recto;
- no table cell has a word wider than its column;
- the web edition has no horizontal scroll at 390 px.

Rebuild with `python3 src/book.py OUT.pdf`. It needs Playwright's Chromium and poppler's `pdftotext` and `pdfunite`. The fonts (SIL Open Font License) are fetched on first run into `src/fonts/`. `python3 src/build.py OUT.html` builds the web page.
