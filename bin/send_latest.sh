#!/usr/bin/env bash
set -euo pipefail

: "${CONGRESS_PTR_FEISHU_CHAT_ID:?Set CONGRESS_PTR_FEISHU_CHAT_ID to the target Feishu chat id.}"

/Users/wronsky/.codex/feishu-bridge/.venv/bin/python \
  /Users/wronsky/Documents/codes/congress-ptr-monitor/scripts/send_feishu_text.py \
  --chat-id "${CONGRESS_PTR_FEISHU_CHAT_ID}" \
  --title "国会议员 PTR 源头监测日报" \
  --file /Users/wronsky/Documents/codes/congress-ptr-monitor/reports/latest_report.md
