# Agent Operating Contract

You are running the Congress PTR source monitor.

## Inputs

- Official House annual disclosure ZIP/XML:
  `https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.zip`
- Official House PTR PDF:
  `https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{year}/{DocID}.pdf`
- Primary script: `scripts/congress_ptr_monitor.py`.
- Delivery chat: configured outside git. Manual fallback uses
  `CONGRESS_PTR_FEISHU_CHAT_ID`.

## Required Workflow

1. Run `scripts/congress_ptr_monitor.py` with the bundled Python runtime.
2. Ensure the report and JSON outputs exist:
   - `reports/latest_report.md`
   - `data/latest_records.json`
   - `data/latest_transactions.json`
3. Generate the daily long-term signal candidate:
   - `long_term_views/pending_updates/YYYY-MM-DD.md`
   - Use `scripts/update_long_term_candidates.py`.
   - Do not automatically edit `long_term_views/congress_ptr_signal_map.md`;
     that file is for periodic manual integration.
4. Inspect failures. If House source/network/PDF parsing fails, write a failure
   report instead of staying silent.
5. For Senate, try official source access only. If session/search restrictions
   block automation, label Senate as blocked/unavailable.
6. During Hermes scheduled runs, do not call `scripts/send_feishu_text.py`; write the report locally and let Hermes cron deliver the final response to Feishu via Atlas. For manual fallback only, `bin/send_latest.sh` can send to `CONGRESS_PTR_FEISHU_CHAT_ID`.
7. Update `state/memory.md` with last run time, sources, House PTR count, newest
   DocIDs, parsed transaction count, Senate status, delivery status, and next
   run notes.

## Quality Bar

- Use official sources first.
- Do not invent Senate records or missing PDF rows.
- Label parse errors, non-ticker assets, stale disclosures, and date anomalies.
- Keep official DocID/PDF links in the report so users can audit every item.
- Keep daily long-term candidates summarized and commit-safe. No raw PDF text,
  credentials, Feishu chat ids, or automatic thesis-map overwrites.
