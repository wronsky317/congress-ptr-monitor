#!/usr/bin/env python3
"""Create a reviewable long-term PTR signal candidate update.

This script intentionally stops before editing the maintained signal map. It
reads the latest monitor outputs and writes a commit-safe Markdown draft to:

    long_term_views/pending_updates/<date>.md

The draft is meant for periodic manual review and later merge into
long_term_views/congress_ptr_signal_map.md.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore[assignment]


PROJECT_ROOT = Path("/Users/wronsky/Documents/codes/congress-ptr-monitor")
DEFAULT_REPORT = PROJECT_ROOT / "reports" / "latest_report.md"
DEFAULT_RECORDS = PROJECT_ROOT / "data" / "latest_records.json"
DEFAULT_TRANSACTIONS = PROJECT_ROOT / "data" / "latest_transactions.json"
PENDING_DIR = PROJECT_ROOT / "long_term_views" / "pending_updates"


def now_cst() -> datetime:
    if ZoneInfo is None:
        return datetime.now()
    return datetime.now(ZoneInfo("Asia/Shanghai"))


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return path.name


def load_json_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit(f"Expected a JSON list: {path}")
    return [item for item in data if isinstance(item, dict)]


def amount_upper_bound(amount: str) -> int:
    numbers = [int(value.replace(",", "")) for value in re.findall(r"\$([\d,]+)", amount or "")]
    return max(numbers) if numbers else 0


def is_stale(tx: dict[str, Any]) -> bool:
    delay = tx.get("disclosure_delay_days")
    return isinstance(delay, int) and delay > 45


def has_date_anomaly(tx: dict[str, Any]) -> bool:
    delay = tx.get("disclosure_delay_days")
    return isinstance(delay, int) and delay < 0


def display_asset(tx: dict[str, Any], limit: int = 72) -> str:
    label = str(tx.get("ticker") or tx.get("asset") or "N/A")
    label = re.sub(r"\s+", " ", label).strip()
    if len(label) <= limit:
        return label
    return label[: limit - 1].rstrip() + "..."


def direction_cn(direction: str) -> str:
    if direction == "buy":
        return "买入"
    if direction == "sell":
        return "卖出"
    return "其他"


def tx_line(tx: dict[str, Any]) -> str:
    delay = tx.get("disclosure_delay_days")
    delay_text = "N/A" if delay is None else f"{delay}天"
    return (
        f"- {tx.get('member_name', 'Unknown')}｜{direction_cn(str(tx.get('direction', '')))} "
        f"{display_asset(tx)}｜{tx.get('amount', 'N/A')}｜交易 {tx.get('transaction_date', 'N/A')}｜"
        f"披露 {tx.get('filing_date', 'N/A')}｜延迟 {delay_text}｜DocID {tx.get('doc_id', 'N/A')}"
    )


def group_by_direction_ticker(transactions: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for tx in transactions:
        ticker = str(tx.get("ticker") or "").strip()
        direction = str(tx.get("direction") or "").strip()
        if not ticker or not direction or is_stale(tx) or has_date_anomaly(tx):
            continue
        grouped[(direction, ticker)].append(tx)
    return dict(grouped)


def cross_filer_resonance(transactions: list[dict[str, Any]]) -> list[tuple[str, str, list[dict[str, Any]]]]:
    rows: list[tuple[str, str, list[dict[str, Any]]]] = []
    for (direction, ticker), items in group_by_direction_ticker(transactions).items():
        members = {str(tx.get("member_name") or "") for tx in items}
        if len(members) >= 2:
            rows.append((direction, ticker, items))
    rows.sort(
        key=lambda row: (
            len({str(tx.get("member_name") or "") for tx in row[2]}),
            len(row[2]),
            sum(amount_upper_bound(str(tx.get("amount") or "")) for tx in row[2]),
        ),
        reverse=True,
    )
    return rows


def notable_transactions(transactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        tx
        for tx in transactions
        if amount_upper_bound(str(tx.get("amount") or "")) >= 50_000 or tx.get("asset_type") == "OP"
    ]
    rows.sort(key=lambda tx: amount_upper_bound(str(tx.get("amount") or "")), reverse=True)
    return rows[:15]


def non_ticker_assets(transactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        tx
        for tx in transactions
        if not tx.get("ticker") and (amount_upper_bound(str(tx.get("amount") or "")) >= 50_000 or tx.get("asset_type"))
    ]
    rows.sort(key=lambda tx: amount_upper_bound(str(tx.get("amount") or "")), reverse=True)
    return rows[:12]


def ticker_repetition(transactions: list[dict[str, Any]]) -> list[tuple[str, int, int, int]]:
    counter: Counter[str] = Counter()
    buy_counter: Counter[str] = Counter()
    sell_counter: Counter[str] = Counter()
    for tx in transactions:
        ticker = str(tx.get("ticker") or "").strip()
        if not ticker:
            continue
        counter[ticker] += 1
        if tx.get("direction") == "buy":
            buy_counter[ticker] += 1
        elif tx.get("direction") == "sell":
            sell_counter[ticker] += 1
    rows = [(ticker, count, buy_counter[ticker], sell_counter[ticker]) for ticker, count in counter.items() if count >= 2]
    rows.sort(key=lambda row: (row[1], row[2], row[3]), reverse=True)
    return rows[:15]


def merge_status(transactions: list[dict[str, Any]], records: list[dict[str, Any]]) -> str:
    if not records and not transactions:
        return "暂无新增 PTR，通常无需合并"
    if cross_filer_resonance(transactions):
        return "需要人工复核后合并：出现跨披露人同向 ticker 信号"
    if notable_transactions(transactions):
        return "需要人工复核：出现大额、期权或非普通资产候选"
    if ticker_repetition(transactions):
        return "观察候选：同一 ticker 在本轮多次出现"
    return "通常无需合并：以单次小额披露为主"


def extract_report_status(report: str) -> list[str]:
    wanted_prefixes = (
        "- House PTR 官方索引总数：",
        "- 本次新增/待复核 PTR：",
        "- 成功解析 PDF：",
        "- 已解析交易明细：",
        "- 严重滞后披露",
        "- 官方源日期异常",
        "- PDF 未解析",
    )
    lines = []
    for line in report.splitlines():
        clean = line.strip()
        if clean.startswith(wanted_prefixes):
            lines.append(clean)
    return lines or ["- 未从报告中识别到抓取状态摘要。"]


def build_candidate(
    *,
    date_text: str,
    report_path: Path,
    records_path: Path,
    transactions_path: Path,
    report_markdown: str,
    records: list[dict[str, Any]],
    transactions: list[dict[str, Any]],
) -> str:
    generated = now_cst().strftime("%Y-%m-%d %H:%M")
    status = merge_status(transactions, records)
    resonance = cross_filer_resonance(transactions)
    notable = notable_transactions(transactions)
    non_ticker = non_ticker_assets(transactions)
    repeated = ticker_repetition(transactions)
    stale = [tx for tx in transactions if is_stale(tx)]
    anomalies = [tx for tx in transactions if has_date_anomaly(tx)]
    members = sorted({str(item.get("member_name") or "Unknown") for item in records})

    lines = [
        f"# Congress PTR 长期信号候选更新 - {date_text}",
        "",
        "> 自动生成的待合并草案。请先复核官方 PDF、去重和主文档上下文，再手动合并到 `congress_ptr_signal_map.md`。",
        "",
        "## 状态",
        "",
        f"- 合并建议：{status}",
        f"- 生成时间：{generated} CST",
        f"- 来源报告：`{rel_path(report_path)}`",
        f"- 来源 records：`{rel_path(records_path)}`",
        f"- 来源 transactions：`{rel_path(transactions_path)}`",
        f"- 本轮 PTR：{len(records)} 份；解析交易：{len(transactions)} 笔",
        f"- 覆盖披露人：{', '.join(members) if members else '无新增披露人'}",
        "",
        "## 建议合并动作",
        "",
    ]
    if "需要" in status or "观察" in status:
        lines.extend(
            [
                "- [ ] 对候选 ticker/资产重新打开官方 PDF 复核。",
                "- [ ] 检查是否已存在于 `congress_ptr_signal_map.md`，避免重复升级。",
                "- [ ] 区分及时披露、滞后披露、日期异常和非 ticker 资产。",
                "- [ ] 只把跨日、跨披露人、重大金额或政策相关的部分合并为长期 watchpoint。",
            ]
        )
    else:
        lines.extend(
            [
                "- [ ] 通常无需合并；保留本文件作为当日长期信号审计记录。",
                "- [ ] 如人工复核发现隐藏的持续主题，再补入主文档。",
            ]
        )

    lines.extend(["", "## 抓取状态摘要", ""])
    lines.extend(extract_report_status(report_markdown))

    lines.extend(["", "## 跨披露人同向候选", ""])
    if not resonance:
        lines.append("- 本轮未发现剔除滞后/日期异常后的跨披露人同向 ticker。")
    else:
        for direction, ticker, items in resonance[:10]:
            members_for_ticker = sorted({str(tx.get("member_name") or "Unknown") for tx in items})
            total_upper = sum(amount_upper_bound(str(tx.get("amount") or "")) for tx in items)
            lines.append(
                f"- {ticker}｜{direction_cn(direction)}｜{len(items)} 笔｜"
                f"{len(members_for_ticker)} 名披露人｜金额上限合计约 ${total_upper:,}｜"
                f"披露人：{', '.join(members_for_ticker)}"
            )

    lines.extend(["", "## 大额/期权/非普通资产候选", ""])
    if not notable:
        lines.append("- 本轮未发现金额上限 >= $50,000 或期权候选。")
    else:
        for tx in notable:
            lines.append(tx_line(tx))

    lines.extend(["", "## 同一 Ticker 本轮重复出现", ""])
    if not repeated:
        lines.append("- 本轮没有同一 ticker 出现 2 次以上。")
    else:
        for ticker, count, buys, sells in repeated:
            lines.append(f"- {ticker}: {count} 笔；买入 {buys} 笔，卖出 {sells} 笔。")

    lines.extend(["", "## 非 Ticker / 宏观资产观察", ""])
    if not non_ticker:
        lines.append("- 本轮没有需要优先观察的非 ticker 资产。")
    else:
        for tx in non_ticker:
            lines.append(tx_line(tx))

    lines.extend(["", "## 滞后、异常与降权", ""])
    if not stale and not anomalies:
        lines.append("- 本轮未识别到 >45 天严重滞后披露或日期异常。")
    else:
        for tx in stale[:10]:
            lines.append(f"- 滞后披露：{tx_line(tx)[2:]}")
        for tx in anomalies[:10]:
            lines.append(f"- 日期异常：{tx_line(tx)[2:]}")

    lines.extend(
        [
            "",
            "## 合并备注",
            "",
            "- 本文件只包含报告级摘要和 JSON 字段摘要，不归档 raw PDF 文本。",
            "- 合并时必须保留不确定性，特别是非 ticker 资产、滞后披露和未实现的委员会映射。",
            "- PTR 是披露实时，不是交易实时；本文件不构成投资建议。",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a pending long-term PTR signal update.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Report Markdown path.")
    parser.add_argument("--records", default=str(DEFAULT_RECORDS), help="Filing records JSON path.")
    parser.add_argument("--transactions", default=str(DEFAULT_TRANSACTIONS), help="Transactions JSON path.")
    parser.add_argument("--date", help="Output date, YYYY-MM-DD. Default: current Asia/Shanghai date.")
    parser.add_argument("--output-dir", default=str(PENDING_DIR), help="Pending update output directory.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    report_path = Path(args.report).expanduser()
    records_path = Path(args.records).expanduser()
    transactions_path = Path(args.transactions).expanduser()
    if not report_path.exists():
        raise SystemExit(f"Report not found: {report_path}")

    date_text = args.date or now_cst().strftime("%Y-%m-%d")
    output_dir = Path(args.output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{date_text}.md"

    report_markdown = report_path.read_text(encoding="utf-8", errors="replace")
    records = load_json_list(records_path)
    transactions = load_json_list(transactions_path)
    output_path.write_text(
        build_candidate(
            date_text=date_text,
            report_path=report_path,
            records_path=records_path,
            transactions_path=transactions_path,
            report_markdown=report_markdown,
            records=records,
            transactions=transactions,
        ),
        encoding="utf-8",
    )
    print(f"pending_update={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
