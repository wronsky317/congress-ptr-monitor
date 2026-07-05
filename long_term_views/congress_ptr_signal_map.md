# Congress PTR Long-Term Signal Map

Last manually reviewed: 2026-07-05.

> This is the maintained long-term interpretation layer for official Congress
> PTR disclosures. Daily automation writes candidate updates under
> `pending_updates/`; manual review periodically merges durable items here.
> PTR data is disclosure-time, not trade-time, and does not constitute
> investment advice.

## Source Scope

- Source basis: local official House PTR PDF cache plus local report artifacts.
- Local PDF cache reviewed: 56 official House PDFs under `pdfs/`.
- Parsed transaction rows: 432 rows from 51 parsed PDFs.
- Parsed members: 42 disclosed names.
- Coverage window in local cache: mainly 2026 filings through
  `reports/latest_report.md` generated 2026-07-04 21:17 CST.
- Latest pending candidate incorporated: `pending_updates/2026-07-04.md`.
- Non-parsed local PDFs: 5 `911...` documents with no standard transaction rows
  extracted in the current parser pass.

## Coverage Status

- House: official House Clerk ZIP/XML + official PTR PDFs are monitored by the
  local source workflow.
- Senate: not fully automated. Do not infer Senate records unless official
  access is implemented and cited.
- Committee enrichment: not implemented yet. Committee relevance is unknown
  unless verified independently.
- Data caveat: current long-term map is built from cached local PDFs and local
  reports, not a full-year independently rehydrated database.

## Active Cross-Filer Ticker Signals

- **MSFT**
  - Status: active, two-sided, high-priority watchpoint.
  - Source window: local cached PTRs through 2026-07-04.
  - Members: Hon. Josh Gottheimer, Hon. Gilbert Cisneros, Cleo Fields,
    Hon. Jonathan Jackson, Hon. Matthew Robert Van Epps.
  - Direction and amount ranges:
    - Sell side: 5 parsed MSFT sells across 4 filers; upper-bound total around
      $1.615M, driven by Josh Gottheimer options-sized sells plus smaller sells
      from Jackson, Van Epps, and Cisneros.
    - Buy side: 5 parsed MSFT buys across 3 filers; upper-bound total around
      $1.63M, driven by Josh Gottheimer options-sized buys plus smaller buys
      from Cisneros and Cleo Fields.
  - Evidence: Gottheimer has large same-day MSFT buy and sell option rows
    (DocID 20034693); Jackson and Van Epps created the earlier MSFT sell
    resonance; Cisneros added another MSFT sell in the 2026-07-04 latest run.
  - Interpretation: this is not a clean directional signal. It is a durable
    "mega-cap/options portfolio activity" watchpoint because both buy and sell
    disclosures appear across multiple filers.
  - Invalidation/downweighting: downgrade if future MSFT rows are isolated
    small rebalancing trades or if the large options rows are confirmed as
    paired hedges with no net directional exposure.
  - Next review: reopen Gottheimer DocID 20034693 and classify whether the
    large MSFT rows are paired option structures, partial sales, or separate
    exposures.

- **SPCX / Space Exploration Technologies Corp.**
  - Status: active, watch-only private-company resonance.
  - Source window: latest run dated 2026-07-04.
  - Members: Hon. Daniel Meuser and Hon. Gilbert Cisneros.
  - Direction and amount ranges: 2 buys; upper-bound total around $65K.
  - Evidence: Meuser bought SPCX $15,001-$50,000 on 2026-06-15 (DocID
    20034774); Cisneros bought SPCX $1,001-$15,000 on 2026-06-18 (DocID
    20034906).
  - Interpretation: cross-filer same-direction interest in a private SpaceX
    share class, but still small and not public-ticker actionable.
  - Invalidation/downweighting: keep watch-only unless additional filers or
    larger follow-on rows appear.
  - Next review: if SPCX appears again, consolidate as a private-space exposure
    theme rather than a normal equity ticker signal.

- **GOOGL**
  - Status: watch-only sell resonance.
  - Source window: local cached PTRs through 2026-07-04.
  - Members: Hon. David J. Taylor, Hon. Gilbert Cisneros, Hon. Matthew Robert
    Van Epps.
  - Direction and amount ranges: 4 sell rows across 3 filers; upper-bound total
    around $95K.
  - Evidence: Taylor and Van Epps broad sell baskets overlap with a Cisneros
    GOOGL sell.
  - Interpretation: signal is lower conviction than MSFT because amounts are
    mostly small and likely part of broader portfolio rebalancing.
  - Invalidation/downweighting: do not upgrade unless future GOOGL sells are
    larger, timely, and not embedded in broad multi-stock cleanup baskets.
  - Next review: compare future GOOGL rows against AMZN/AAPL/NVDA/INTC broad
    mega-cap sell clusters.

- **ABT**
  - Status: watch-only sell resonance.
  - Source window: local cached PTRs through 2026-07-04.
  - Members: Hon. Josh Gottheimer, Hon. Julie Johnson, Hon. Gilbert Cisneros.
  - Direction and amount ranges: 3 sell rows across 3 filers; all currently
    small-to-mid amount ranges.
  - Evidence: low-size ABT sell overlap across separate filers.
  - Interpretation: possible health-care rebalancing marker, not a standalone
    negative thesis.
  - Invalidation/downweighting: downgrade if no repeated health-care cluster
    follows.
  - Next review: watch for repeated ABT, GILD, COR, BIIB, or other health-care
    names in future runs.

- **AAPL**
  - Status: watch-only, mixed mega-cap activity.
  - Source window: local cached PTRs through 2026-07-04.
  - Members: Cleo Fields, Hon. Ed Case, Hon. Gilbert Cisneros, Hon. David J.
    Taylor, Hon. Matthew Robert Van Epps, Hon. Tim Walberg.
  - Direction and amount ranges: 7 rows total; 4 buys and 3 sells.
  - Evidence: multiple filers touched AAPL, but Tim Walberg's old 2025 purchase
    rows are severely stale and should not be used for timely resonance.
  - Interpretation: durable mega-cap portfolio activity, not directional.
  - Invalidation/downweighting: exclude stale 2025 rows from timely scoring;
    require fresh cross-filer same-direction activity to upgrade.
  - Next review: separate stale legacy rows from new disclosures in the next
    aggregation pass.

## Member-Level Watchpoints

- **Hon. Gilbert Cisneros**
  - Status: active broad-portfolio activity watchpoint.
  - Source window: multiple cached filings including DocIDs 20034713 and
    20034906.
  - Evidence: largest local row count by member, with 169 parsed rows in the
    cache reconstruction. Latest run added 66 rows, including broad equity
    buys/sells, LLY buy, MSFT sell, MSTR buy, and municipal-bond rows.
  - Interpretation: treat individual Cisneros ticker rows cautiously because
    many appear to be part of broad portfolio rotation. Cross-filer overlaps
    matter more than standalone rows.
  - Next review: track whether Cisneros repeats specific themes across separate
    filings, especially SPCX, MSFT, health care, and municipal bonds.

- **Hon. Josh Gottheimer**
  - Status: active options/mega-cap watchpoint.
  - Source window: DocID 20034693 in local cache.
  - Evidence: large MSFT buy and sell option-sized rows; BRK.B/PINS and other
    rows also appear in cached parsing.
  - Interpretation: likely portfolio/option-structure activity. It is important
    for MSFT signal context but should not be treated as plain directional
    buying or selling until the official PDF is manually reviewed.
  - Next review: classify MSFT option exposure net direction, expiration/strike
    if available from PDF text, and whether paired rows cancel out.

- **Hon. Nancy Pelosi**
  - Status: high-visibility options watchpoint.
  - Source window: local cache DocID 20034836.
  - Evidence: INTC buy $1M-$5M and UBER buy $500K-$1M, both parsed as OP type
    rows.
  - Interpretation: large options activity should stay on the manual review
    list. INTC has later small sell overlap from other filers, so treat the
    broader INTC picture as mixed and size-weighted.
  - Next review: manually verify option details and compare against any later
    INTC/UBER disclosures.

- **Hon. Scott H. Peters**
  - Status: municipal-bond and Treasury portfolio watchpoint.
  - Source window: DocID 20034784.
  - Evidence: 30 parsed rows dominated by GS-type municipal bonds and Treasury
    bills, including multiple $500K-$1M rows.
  - Interpretation: this is a durable macro/municipal-bond portfolio theme, not
    an equity or political-sector signal.
  - Invalidation/downweighting: several rows are near or over 45-day lag; keep
    stale rows out of timely resonance scoring.
  - Next review: keep CA Infrastructure and San Juan stale rows in manual
    follow-up for amendment or timing clarification.

- **Hon. Jefferson Shreve**
  - Status: very-large structured-note watchpoint.
  - Source window: DocID 20034653.
  - Evidence: JP Morgan 3-Year Auto Callable Buffer Note linked to
    INDU/NDX/RTY at $5M-$25M and Morgan Stanley 37-Month One-time Callable
    Note linked to INDU/SPX at $1M-$5M.
  - Interpretation: highest nominal notional exposure in the local cache, but
    structured-note payoff is not the same as a simple index long.
  - Next review: keep as a separate structured-product theme; do not merge into
    ordinary equity buy/sell resonance.

- **Hon. Matthew Robert Van Epps**
  - Status: broad sell-basket watchpoint.
  - Source window: DocID 20034807.
  - Evidence: 13 parsed sell rows including mega-cap and industrial/energy
    names, with overlaps into MSFT, GOOGL, AAPL, AMZN, NVDA, INTC, IBM and
    others.
  - Interpretation: likely broad portfolio cleanup rather than a set of
    standalone negative ticker views.
  - Next review: future reverse buys from the same member would change the read
    from "de-risking" toward "rebalance."

## Sector And Macro Watchpoints

- **Mega-cap technology and AI-adjacent equities**
  - Status: active but mixed.
  - Core names observed: MSFT, AAPL, GOOGL, AMD, INTC, NVDA, AMZN, IBM, MSTR,
    UBER.
  - Evidence: MSFT is the strongest durable cross-filer ticker due to repeated
    buy and sell rows plus large options; INTC has Pelosi large option buy but
    smaller sells from Evans/Van Epps; GOOGL/AAPL/AMZN show more broad-basket
    activity than clean direction.
  - Interpretation: monitor as "Congress portfolio activity in mega-cap tech,"
    not as a single directional thesis.
  - Invalidation/downweighting: small rows embedded in broad portfolio baskets
    should not be upgraded without repetition or size.

- **Municipal bonds, Treasuries, and public finance**
  - Status: active macro watchpoint.
  - Members/assets: Scott Peters municipal/Treasury portfolio; Steve Cohen
    $500K-$1M US Treasury bill buy; Richard W. Allen Treasury note rows; Thomas
    H. Kean Jr U.S. Treasury note; Gilbert Cisneros municipal notes/bonds.
  - Evidence: multiple GS-type rows across separate members, with several
    large amounts.
  - Interpretation: this is one of the clearest non-equity patterns in the
    cache. It likely reflects portfolio income/liquidity management more than
    company-specific political information.
  - Invalidation/downweighting: rows with >45-day delay should be treated as
    timing-stale; do not mix municipal bond activity with equity resonance.

- **Structured notes and corporate/agency notes**
  - Status: active high-notional watchpoint.
  - Members/assets: Jefferson Shreve structured notes; Kevin Hern Morgan
    Stanley zero-coupon note redemption; Suzan DelBene Pacific Co bond; Debbie
    Dingell FNMA pool row.
  - Evidence: largest nominal rows in the cache are structured-note or
    credit-like instruments.
  - Interpretation: high nominal size does not equal simple equity direction.
    These rows need payoff-structure review before any market implication.
  - Next review: tag CS-type rows separately in future automation.

- **Private funds and private-company exposure**
  - Status: active watch-only.
  - Members/assets: Nicholas Begich III Listen Ventures IV LP; Ann Wagner KKR
    Private Equity Conglomerate and Partners Group; Scott Peters Torch Capital
    III LP / Kent Street Group; SPCX private-company rows from Meuser and
    Cisneros.
  - Interpretation: useful for long-term exposure mapping but generally not
    public-equity actionable.
  - Next review: keep private funds and private company rows separate from
    ticker resonance.

- **Health care and biopharma**
  - Status: watch-only.
  - Names observed: ABT, BIIB, LLY, GILD, COR, BDX and related rows.
  - Evidence: ABT has cross-filer sell overlap; BIIB has repeated buys from
    Salazar plus Cisneros; latest run includes a larger LLY buy by Cisneros.
  - Interpretation: not yet a durable sector thesis, but repeated health-care
    rows justify continued monitoring.
  - Next review: upgrade only if multiple filers repeat same-direction health
    care trades in fresh disclosures.

## Stale, Anomalous, Or Manual-Review Items

- **Severely stale Tim Walberg 2025 rows**
  - Status: stale; exclude from timely resonance.
  - Evidence: DocID 20034660 includes multiple February 2025 rows disclosed in
    June 2026, with 481-day delays in the reconstructed cache.
  - Interpretation: preserve for audit, but do not use for current market
    signals.

- **Daniel Webster stale REXR row**
  - Status: stale; exclude from timely resonance.
  - Evidence: DocID 20034562, REXR sell row with roughly 460-day delay.

- **Richard W. Allen stale April rows**
  - Status: stale/manual review.
  - Evidence: DocID 20034473 includes AMP, ABT, INTU, PG, SPGI and Treasury
    note sell rows with 50-51 day delays.
  - Interpretation: slightly over the 45-day threshold; keep as stale rather
    than timely cross-filer signal.

- **Scott Peters late municipal rows**
  - Status: stale/manual review.
  - Evidence: CA Infrastructure sell row at 49-day delay and San Juan / U.S.
    Treasury Bill rows over 45 days.
  - Interpretation: material amounts, but timing-stale. Watch for amendments.

- **Christian D. Menefee date anomaly**
  - Status: date anomaly; exclude from signal scoring.
  - Evidence: one parsed row has transaction date after filing date in local
    reconstruction, likely due to PDF text-layout ambiguity around explanatory
    text.
  - Next review: manually inspect DocID 20034099 before using Menefee anomaly
    rows.

- **Unparsed `911...` PDFs**
  - Status: manual review backlog.
  - Evidence: local cached PDFs `9115901`, `9116141`, `9116142`, `9116146`,
    and `9116197` produced no standard transaction rows in this parser pass.
  - Interpretation: likely amendments, complex forms, or non-standard PDF
    layouts. Do not infer missing trades.

## Manual Integration Log

- 2026-07-05: Long-term view mechanism created.
- 2026-07-05: Manually consolidated existing local results into this signal
  map. Inputs: 56 cached official House PDFs, `reports/latest_report.md`,
  `data/latest_records.json`, `data/latest_transactions.json`, and
  `pending_updates/2026-07-04.md`.
