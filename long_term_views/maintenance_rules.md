# Long-Term View Maintenance Rules

Last updated: 2026-07-05

These rules define how future agents should maintain the durable PTR signal
layer under `long_term_views/`.

## Purpose

`long_term_views/` is not a daily report folder and not a raw-data archive. It is
the maintained interpretation layer derived from official STOCK Act PTR
disclosures.

Use it to track:

- repeated ticker or sector activity across multiple filers;
- large, options, or unusually timely disclosures;
- member-level behavior that persists across multiple filings;
- policy, committee, geography, or sector relevance when independently known;
- stale disclosures, amendments, and date anomalies that should be downweighted;
- invalidation risks and evidence gaps.

## Source Hierarchy

Use local project artifacts first:

1. `reports/latest_report.md`: report-ready daily summary.
2. `data/latest_records.json`: latest selected filing records.
3. `data/latest_transactions.json`: parsed transaction-level rows.
4. `pdfs/`: official PDFs for audit when a candidate matters.
5. `state/memory.md`: operational cursor and previous-run notes.

Do not update long-term views from memory alone. Always cite the local source
report or date range used for the update.

## Update Triggers

Generate a candidate update under `long_term_views/pending_updates/<date>.md`
when the daily run completes. Merge it into
`long_term_views/congress_ptr_signal_map.md` only after review when one of these
happens:

- the same ticker has same-direction activity from 2+ distinct filers;
- a ticker or sector appears repeatedly across separate daily runs;
- a member files a large, options, or unusually timely transaction;
- a stale or anomalous disclosure changes how an earlier signal should be read;
- a non-ticker asset points to a durable macro theme such as Treasuries,
  municipal bonds, private funds, or structured notes;
- committee, district, state, or policy context materially changes the
  interpretation;
- an existing watchpoint is validated, contradicted, or should be retired.

Do not update the long-term map for one-off small trades unless they connect to
an existing theme or invalidate a previous pattern.

## Required Fields For Maintained Themes

Each maintained theme should include:

- official source window;
- tickers/assets and affected members;
- signal status: active, watch-only, stale, contradicted, or retired;
- evidence summary;
- interpretation notes;
- invalidation or downweighting conditions;
- next manual review task.

If information is uncertain, say so explicitly. Do not convert PTR disclosures
into investment recommendations.

## Daily Automation Behavior

Daily runs should:

1. Execute `scripts/congress_ptr_monitor.py`.
2. Generate `reports/latest_report.md`, `data/latest_records.json`, and
   `data/latest_transactions.json`.
3. Generate `long_term_views/pending_updates/<date>.md`.
4. Leave `long_term_views/congress_ptr_signal_map.md` unchanged.
5. Send the suite digest through the existing delivery path.

## Manual Integration Cadence

Review `pending_updates/` periodically, usually weekly or after a dense filing
cluster. Merge only durable items into `congress_ptr_signal_map.md`, then leave
the pending files as an audit trail.

Recommended manual merge checklist:

- [ ] Re-open the official PDF for any high-conviction or disputed item.
- [ ] De-duplicate against existing themes.
- [ ] Separate buy/sell direction, stale disclosures, and date anomalies.
- [ ] Mark one-off small trades as watch-only unless repeated.
- [ ] Add invalidation conditions.
- [ ] Preserve the risk caveat: PTR is disclosure-time, not trade-time.

## Privacy And Git Rules

- `long_term_views/` is commit-safe because it contains summarized thesis work,
  not raw PDF text or private runtime state.
- `pending_updates/` is a staging area rather than the maintained source of
  truth.
- Do not paste Feishu chat ids, credentials, raw PDFs, or full extracted PDF
  text into long-term view files.
