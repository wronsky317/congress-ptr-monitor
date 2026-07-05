#!/usr/bin/env bash
set -euo pipefail

/Users/wronsky/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  /Users/wronsky/Documents/codes/congress-ptr-monitor/scripts/congress_ptr_monitor.py \
  --state /Users/wronsky/Documents/codes/congress-ptr-monitor/state/state.json \
  --report /Users/wronsky/Documents/codes/congress-ptr-monitor/reports/latest_report.md \
  --records /Users/wronsky/Documents/codes/congress-ptr-monitor/data/latest_records.json \
  --transactions /Users/wronsky/Documents/codes/congress-ptr-monitor/data/latest_transactions.json \
  --pdf-dir /Users/wronsky/Documents/codes/congress-ptr-monitor/pdfs \
  --lookback-days 14 \
  --max-items 25

/Users/wronsky/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  /Users/wronsky/Documents/codes/congress-ptr-monitor/scripts/update_long_term_candidates.py \
  --report /Users/wronsky/Documents/codes/congress-ptr-monitor/reports/latest_report.md \
  --records /Users/wronsky/Documents/codes/congress-ptr-monitor/data/latest_records.json \
  --transactions /Users/wronsky/Documents/codes/congress-ptr-monitor/data/latest_transactions.json \
  --output-dir /Users/wronsky/Documents/codes/congress-ptr-monitor/long_term_views/pending_updates \
  | tee /tmp/congress_ptr_pending_update.out

/Users/wronsky/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  /Users/wronsky/Documents/codes/congress-ptr-monitor/scripts/commit_pending_update.py \
  --from-generator-output /tmp/congress_ptr_pending_update.out
