# Long-Term Views

This directory maintains the durable signal layer for Congress PTR monitoring.

It is separate from runtime artifacts:

- `pdfs/`: cached official PTR PDFs.
- `data/`: latest machine-readable filing and transaction outputs.
- `reports/`: daily report-ready summaries.
- `state/`: runtime cursor and scheduled-agent memory.
- `long_term_views/`: maintained long-term signal map, pending thesis updates,
  watchpoints, and manual-review notes.

## Maintenance Rules

1. Daily automation may write only to `pending_updates/YYYY-MM-DD.md`.
2. Do not automatically overwrite `congress_ptr_signal_map.md`.
3. Do not paste raw PDF text or full daily reports here. Summarize durable
   monitoring implications only.
4. Record the source report, records JSON, transactions JSON, and run date used
   for each candidate update.
5. Keep uncertainty explicit. Distinguish:
   - official disclosed facts;
   - inferred policy/sector implications;
   - watch-only signals;
   - stale, anomalous, or unparsed data.
6. Track invalidation conditions, not only upside catalysts.

## Current Files

- `congress_ptr_signal_map.md`: maintained long-term map of repeated PTR
  signals, policy/sector watchpoints, large/options activity, and invalidation
  rules.
- `maintenance_rules.md`: rules for future agents and manual reviewers.
- `pending_updates/`: daily auto-generated candidate updates for manual review.
