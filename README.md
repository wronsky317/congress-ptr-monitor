# Congress PTR Monitor

Source-first monitor for US congressional Periodic Transaction Reports (PTRs).

The monitor fetches official House Clerk disclosure indexes, downloads official
PTR PDFs, parses transaction rows, writes machine-readable JSON, renders a
Chinese report, and sends it to Feishu.

## Purpose

- Monitor official STOCK Act PTR disclosures from source.
- Prefer official House/Senate sources over CapitolTrades/UnusualWhales.
- Extract transaction-level fields from official PDFs:
  member, chamber, district/state, asset, ticker, asset type, buy/sell,
  transaction date, filing date, amount range, owner, disclosure delay, DocID,
  and official PDF URL.
- Highlight actionable monitoring signals while labeling stale, anomalous, or
  unparsed data.

## Project Interface

Other agents should start from:

- [AGENT.md](AGENT.md): operational contract and exact workflow.
- [scripts/congress_ptr_monitor.py](scripts/congress_ptr_monitor.py): source monitor.
- [prompts/daily_monitor.md](prompts/daily_monitor.md): scheduled-agent prompt.
- [reports/latest_report.md](reports/latest_report.md): latest rendered report.
- [data/latest_records.json](data/latest_records.json): latest filing records.
- [data/latest_transactions.json](data/latest_transactions.json): parsed transactions.
- [long_term_views](long_term_views): durable signal map and daily pending
  updates for manual long-term integration.
- [state/state.json](state/state.json): seen DocID state.
- [state/memory.md](state/memory.md): scheduled-agent run memory.

## Manual Run

Use the bundled Python runtime because it includes `pypdf`:

```bash
/Users/wronsky/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  /Users/wronsky/Documents/codes/congress-ptr-monitor/scripts/congress_ptr_monitor.py \
  --state /Users/wronsky/Documents/codes/congress-ptr-monitor/state/state.json \
  --report /Users/wronsky/Documents/codes/congress-ptr-monitor/reports/latest_report.md \
  --records /Users/wronsky/Documents/codes/congress-ptr-monitor/data/latest_records.json \
  --transactions /Users/wronsky/Documents/codes/congress-ptr-monitor/data/latest_transactions.json \
  --pdf-dir /Users/wronsky/Documents/codes/congress-ptr-monitor/pdfs \
  --lookback-days 14 \
  --max-items 25
```

Generate the reviewable long-term signal candidate from the latest outputs:

```bash
/Users/wronsky/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  /Users/wronsky/Documents/codes/congress-ptr-monitor/scripts/update_long_term_candidates.py \
  --report /Users/wronsky/Documents/codes/congress-ptr-monitor/reports/latest_report.md \
  --records /Users/wronsky/Documents/codes/congress-ptr-monitor/data/latest_records.json \
  --transactions /Users/wronsky/Documents/codes/congress-ptr-monitor/data/latest_transactions.json \
  --output-dir /Users/wronsky/Documents/codes/congress-ptr-monitor/long_term_views/pending_updates
```

For a complete recent refresh even when DocIDs were already seen:

```bash
bash /Users/wronsky/Documents/codes/congress-ptr-monitor/bin/run_force_lookback.sh
```

## Feishu Delivery

```bash
bash /Users/wronsky/Documents/codes/congress-ptr-monitor/bin/send_latest.sh
```

## Schedule

Codex automation: `congress-ptr-source-monitor-to-feishu`

- Runs daily at 21:30 Asia/Shanghai.
- Working directory: `/Users/wronsky/Documents/codes/congress-ptr-monitor`.
- Writes report to `reports/latest_report.md`.
- Writes JSON data to `data/`.
- Writes a reviewable long-term candidate to
  `long_term_views/pending_updates/YYYY-MM-DD.md`.
- Commits and pushes the generated pending update file when it changes.
- Updates memory at `state/memory.md`.

## Long-Term View Integration

Daily automation only creates pending candidates. Periodic manual review should
merge durable items into `long_term_views/congress_ptr_signal_map.md`.

Use the long-term layer for repeated ticker/member signals, large/options
activity, non-ticker macro assets, stale/anomalous disclosures, and invalidation
conditions. Do not paste raw PDF text or overwrite the maintained signal map
automatically.

Daily runs commit only the generated `pending_updates/YYYY-MM-DD.md` file and
push the current git branch. Runtime outputs under `data/`, `pdfs/`, `reports/`,
and `state/` remain ignored.

## Current Source Coverage

- House: official annual ZIP/XML and official PTR PDFs.
- Senate: not fully automated yet. If official Senate eFD access is blocked by
  session/search constraints, report that explicitly and do not invent records.

## Signal Logic

The report highlights:

- Buy resonance: same ticker bought by 2+ filers, excluding stale/anomalous rows.
- Sell warnings: clustered same-ticker selling, excluding stale/anomalous rows.
- Large/options trades.
- Recent disclosure windows.
- Stale disclosures over 45 days, preserved in detail but downweighted.
- Official date anomalies, preserved for manual review and excluded from scoring.

PTR disclosure timing is not trade timing and is not investment advice.
