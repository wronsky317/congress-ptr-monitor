Create a daily Chinese source-first congressional trading disclosure report. During scheduled Hermes runs, Hermes cron delivers the final suite response to the configured Feishu group via Atlas.

Primary objective: monitor official STOCK Act Periodic Transaction Report (PTR) disclosures from source, not from CapitolTrades/UnusualWhales. Use third-party sites only as optional enrichment, never as the primary source.

Official source workflow:

1. Run the local source monitor script with the bundled Python runtime:

```bash
/Users/wronsky/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 /Users/wronsky/Documents/codes/congress-ptr-monitor/scripts/congress_ptr_monitor.py --state /Users/wronsky/Documents/codes/congress-ptr-monitor/state/state.json --report /Users/wronsky/Documents/codes/congress-ptr-monitor/reports/latest_report.md --records /Users/wronsky/Documents/codes/congress-ptr-monitor/data/latest_records.json --transactions /Users/wronsky/Documents/codes/congress-ptr-monitor/data/latest_transactions.json --pdf-dir /Users/wronsky/Documents/codes/congress-ptr-monitor/pdfs --lookback-days 14 --max-items 25
```

2. The script fetches the House Clerk official annual ZIP/XML, selects House PTR filings (`FilingType=P`), downloads official PTR PDFs, and parses transaction rows when possible. If the script fails because shell network/DNS is blocked, use browsing/search against official House Clerk URLs as a fallback and write a report explaining the failure and official source status.
3. Generate the long-term signal candidate from the latest local outputs:

```bash
/Users/wronsky/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 /Users/wronsky/Documents/codes/congress-ptr-monitor/scripts/update_long_term_candidates.py --report /Users/wronsky/Documents/codes/congress-ptr-monitor/reports/latest_report.md --records /Users/wronsky/Documents/codes/congress-ptr-monitor/data/latest_records.json --transactions /Users/wronsky/Documents/codes/congress-ptr-monitor/data/latest_transactions.json --output-dir /Users/wronsky/Documents/codes/congress-ptr-monitor/long_term_views/pending_updates
```

4. For Senate, try to inspect official Senate eFD/search/public disclosure sources. If access is blocked by session/search restrictions, say so explicitly and do not invent Senate records.

Report content requirements:

- Title: `国会议员 PTR 源头监测日报`.
- Include generated time, coverage/source status, and whether House/Senate official sources were accessible.
- List newly disclosed official PTR filings with member, chamber, district/state, filing date, DocID, and official PDF link.
- Summarize parsed transaction-level data from official PDFs: tickers/assets, buy/sell direction, amount range, transaction date, disclosure delay, owner type, and official link.
- Include scored priority signals, `买入共振`, `卖出预警`, `大额/期权交易待复核`, `逐笔交易明细`, and `待人工复核`.
- Label stale disclosures over 45 days, official date anomalies, non-ticker/private assets, and unparsed PDFs.
- Add a risk caveat: PTR is disclosure-time, not trade-time; filings may lag up to 45 days; not investment advice.

Delivery requirement: write `reports/latest_report.md` and include the report in the final Hermes suite response. Manual fallback only: `bin/send_latest.sh` sends `reports/latest_report.md` to `CONGRESS_PTR_FEISHU_CHAT_ID` if a human explicitly requests a resend. Do not use the fallback during Hermes scheduled runs.

Long-term view requirement: write one reviewable pending update to `long_term_views/pending_updates/YYYY-MM-DD.md` after each daily run. Never overwrite `long_term_views/congress_ptr_signal_map.md` automatically; that file is for periodic manual integration after reviewing pending updates and official PDFs.

Git requirement: after generating the pending update, commit and push only that pending update file when it changed. Do not stage runtime artifacts from `data/`, `pdfs/`, `reports/`, or `state/`.

After every run, update `/Users/wronsky/Documents/codes/congress-ptr-monitor/state/memory.md` with: last run time Asia/Shanghai, official sources used, House PTR count, newest DocIDs processed, parsed transaction count, Senate status, delivery status, and next-run notes. Never stay silent; if no new PTRs, send a short no-new-disclosures report.
