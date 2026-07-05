#!/usr/bin/env python3
"""Source-first congressional PTR monitor.

MVP scope:
- Fetch the official House Clerk annual disclosure ZIP.
- Parse the XML index and select `FilingType=P` (Periodic Transaction Reports).
- Maintain a local seen DocID state.
- Emit a Markdown report and machine-readable JSON records for downstream review.

The official House index identifies PTR filings but does not expose structured
transaction rows in the ZIP. The report therefore links to official PDFs for
transaction-level review/enrichment by the automation agent.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import urllib.error
import urllib.request
import zipfile
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - optional runtime dependency
    PdfReader = None  # type: ignore[assignment]

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore[assignment]


BASE_DIR = Path("/Users/wronsky/.codex/automations/congress-ptr-monitor")
DEFAULT_STATE = BASE_DIR / "state.json"
DEFAULT_REPORT = BASE_DIR / "latest_report.md"
DEFAULT_RECORDS = BASE_DIR / "latest_records.json"
DEFAULT_TRANSACTIONS = BASE_DIR / "latest_transactions.json"
DEFAULT_PDF_DIR = BASE_DIR / "pdfs"
HOUSE_ZIP_URL = "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.zip"
HOUSE_PTR_PDF_URL = "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{year}/{doc_id}.pdf"
OWNER_CODES = ("JT", "SP", "DC")
TRANSACTION_RE = re.compile(
    r"(?P<type>S(?: \(partial\))?|S(?: \(full\))?|P|S|E)\s*"
    r"(?P<transaction_date>\d{2}/\d{2}/\d{4})"
    r"(?P<notification_date>\d{2}/\d{2}/\d{4})\s*"
    r"(?P<amount>Over\s+\$[\d,]+|\$[\d,]+\s*-\s*(?:(?P<amount_asset_tail>.*?)(?=\$[\d,]+))?\$[\d,]+)",
    re.IGNORECASE,
)
TRANSACTION_FRAGMENT_RE = re.compile(
    r"(?:S(?: \(partial\))?|S(?: \(full\))?|P|E)\s*\d{2}/\d{2}/\d{4}\d{2}/\d{2}/\d{4}",
    re.IGNORECASE,
)
ASSET_TYPE_RE = re.compile(r"\[(?P<asset_type>[A-Z]{2,})\]")
TICKER_RE = re.compile(r"\((?P<ticker>[A-Z][A-Z0-9.\-]{0,9})\)\s*\[(?P<asset_type>[A-Z]{2,})\]")
MARKET_ASSET_TYPES = {"ST", "OP", "EF", "MF"}


@dataclass(frozen=True)
class PtrFiling:
    chamber: str
    prefix: str
    last: str
    first: str
    suffix: str
    state_district: str
    year: int
    filing_date: str
    doc_id: str
    filing_type: str
    source_url: str

    @property
    def member_name(self) -> str:
        pieces = [self.prefix, self.first, self.last, self.suffix]
        return " ".join(piece for piece in pieces if piece).strip()


@dataclass(frozen=True)
class PtrTransaction:
    chamber: str
    member_name: str
    state_district: str
    filing_date: str
    doc_id: str
    source_url: str
    owner: str
    asset: str
    ticker: str
    asset_type: str
    transaction_type: str
    direction: str
    transaction_date: str
    notification_date: str
    amount: str
    disclosure_delay_days: int | None


def today_cst() -> date:
    if ZoneInfo is None:
        return date.today()
    return datetime.now(ZoneInfo("Asia/Shanghai")).date()


def now_cst_string() -> str:
    if ZoneInfo is None:
        return datetime.now().strftime("%Y-%m-%d %H:%M")
    return datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M")


def parse_house_date(value: str) -> date | None:
    clean = value.strip()
    if not clean:
        return None
    for fmt in ("%m/%d/%Y", "%-m/%-d/%Y"):
        try:
            return datetime.strptime(clean, fmt).date()
        except ValueError:
            continue
    try:
        month, day, year = clean.split("/")
        return date(int(year), int(month), int(day))
    except Exception:
        return None


def parse_pdf_date(value: str) -> date | None:
    clean = value.strip()
    if not clean:
        return None
    try:
        return datetime.strptime(clean, "%m/%d/%Y").date()
    except ValueError:
        return None


def text_of(element: ElementTree.Element, name: str) -> str:
    child = element.find(name)
    return (child.text or "").strip() if child is not None else ""


def fetch_house_ptr_filings(year: int, timeout: int = 45) -> list[PtrFiling]:
    url = HOUSE_ZIP_URL.format(year=year)
    request = urllib.request.Request(url, headers={"User-Agent": "codex-congress-ptr-monitor/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()

    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        xml_name = f"{year}FD.xml"
        xml_bytes = archive.read(xml_name)

    root = ElementTree.fromstring(xml_bytes)
    filings: list[PtrFiling] = []
    for member in root.findall("Member"):
        filing_type = text_of(member, "FilingType")
        if filing_type != "P":
            continue
        doc_id = text_of(member, "DocID")
        if not doc_id:
            continue
        filings.append(
            PtrFiling(
                chamber="House",
                prefix=text_of(member, "Prefix"),
                last=text_of(member, "Last"),
                first=text_of(member, "First"),
                suffix=text_of(member, "Suffix"),
                state_district=text_of(member, "StateDst"),
                year=int(text_of(member, "Year") or year),
                filing_date=text_of(member, "FilingDate"),
                doc_id=doc_id,
                filing_type=filing_type,
                source_url=HOUSE_PTR_PDF_URL.format(year=year, doc_id=doc_id),
            )
        )
    filings.sort(key=lambda item: (parse_house_date(item.filing_date) or date.min, item.doc_id))
    return filings


def fetch_pdf_bytes(url: str, cache_path: Path, timeout: int = 45) -> bytes:
    if cache_path.exists() and cache_path.stat().st_size > 0:
        return cache_path.read_bytes()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "codex-congress-ptr-monitor/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
    cache_path.write_bytes(raw)
    return raw


def extract_pdf_text(raw: bytes) -> str:
    if PdfReader is None:
        raise RuntimeError("pypdf is not available in this Python runtime.")
    reader = PdfReader(io.BytesIO(raw))
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    return text.replace("\x00", "")


def direction_for(transaction_type: str) -> str:
    upper = transaction_type.upper()
    if upper.startswith("P"):
        return "buy"
    if upper.startswith("S"):
        return "sell"
    return "other"


def extract_transactions(filing: PtrFiling, *, pdf_dir: Path) -> list[PtrTransaction]:
    raw = fetch_pdf_bytes(filing.source_url, pdf_dir / f"{filing.year}_{filing.doc_id}.pdf")
    text = extract_pdf_text(raw)
    transactions: list[PtrTransaction] = []
    asset_lines: list[str] = []
    lines = [clean_pdf_line(line) for line in text.splitlines()]
    index = 0
    while index < len(lines):
        line = lines[index]
        if should_skip_pdf_line(line):
            index += 1
            continue
        candidate = re.sub(r"\s+", " ", line)
        advance_to = index + 1
        match = TRANSACTION_RE.search(candidate)
        if not match and TRANSACTION_FRAGMENT_RE.search(candidate):
            combined = candidate
            lookahead = index + 1
            while lookahead < len(lines) and lookahead <= index + 10:
                next_line = lines[lookahead]
                if not should_skip_pdf_line(next_line):
                    combined = re.sub(r"\s+", " ", f"{combined} {next_line}")
                    match = TRANSACTION_RE.search(combined)
                    if match:
                        candidate = combined
                        advance_to = lookahead + 1
                        break
                lookahead += 1
        if not match and index + 1 < len(lines):
            combined = re.sub(r"\s+", " ", f"{line} {lines[index + 1].strip()}")
            match = TRANSACTION_RE.search(combined)
            if match:
                candidate = combined
                advance_to = index + 2
        if not match:
            asset_lines.append(line)
            index += 1
            continue

        pre_asset = candidate[: match.start()].strip()
        amount_asset_tail = (match.groupdict().get("amount_asset_tail") or "").strip()
        asset_parts = asset_lines + ([pre_asset] if pre_asset else []) + ([amount_asset_tail] if amount_asset_tail else [])
        asset = re.sub(r"\s+", " ", " ".join(asset_parts)).strip()
        owner = ""
        for code in OWNER_CODES:
            if asset.startswith(code + " "):
                owner = code
                asset = asset[len(code) + 1 :].strip()
                break
        if not asset:
            index = advance_to
            asset_lines = []
            continue
        ticker, asset_type = parse_asset_identity(asset)
        filing_dt = parse_house_date(filing.filing_date)
        transaction_dt = parse_pdf_date(match.group("transaction_date"))
        delay = (filing_dt - transaction_dt).days if filing_dt and transaction_dt else None
        transaction_type = match.group("type")
        amount = normalize_amount(match.group("amount"))
        transactions.append(
            PtrTransaction(
                chamber=filing.chamber,
                member_name=filing.member_name,
                state_district=filing.state_district,
                filing_date=filing.filing_date,
                doc_id=filing.doc_id,
                source_url=filing.source_url,
                owner=owner,
                asset=asset,
                ticker=ticker,
                asset_type=asset_type,
                transaction_type=transaction_type,
                direction=direction_for(transaction_type),
                transaction_date=match.group("transaction_date"),
                notification_date=match.group("notification_date"),
                amount=amount,
                disclosure_delay_days=delay,
            )
        )
        asset_lines = []
        index = advance_to
    return transactions


def clean_pdf_line(line: str) -> str:
    clean = re.sub(r"[\x00-\x1f\x7f]", "", line)
    return re.sub(r"\s+", " ", clean).strip()


def should_skip_pdf_line(line: str) -> bool:
    clean = clean_pdf_line(line)
    if not clean:
        return True
    exact = {
        "P T R",
        "F I",
        "T",
        "ID Owner Asset Transaction",
        "Type",
        "Date Notification",
        "Date",
        "Amount Cap.",
        "Gains >",
        "$200?",
        "I V D",
        "I P O",
        "Yes No",
        "C S",
    }
    if clean in exact:
        return True
    prefixes = (
        "Clerk of the House",
        "Name:",
        "Status:",
        "State/District:",
        "Filing ID",
        "Digitally Signed:",
        "I CERTIFY",
        "* For the complete list",
        "F S:",
        "Filing Status:",
        "S O:",
        "Subholding Of:",
        "D:",
        "Description:",
        "L:",
        "vest ",
        "vests ",
        "shares vest",
        "can only",
        "quarterly",
    )
    return any(clean.startswith(prefix) for prefix in prefixes) or "can only be" in clean


def normalize_amount(amount: str) -> str:
    numbers = re.findall(r"\$[\d,]+", amount)
    if amount.strip().lower().startswith("over") and numbers:
        return f"Over {numbers[0]}"
    if len(numbers) >= 2:
        return f"{numbers[0]} - {numbers[-1]}"
    return re.sub(r"\s+", " ", amount).strip()


def parse_asset_identity(asset: str) -> tuple[str, str]:
    asset_type_match = ASSET_TYPE_RE.search(asset)
    asset_type = asset_type_match.group("asset_type") if asset_type_match else ""
    ticker = ""
    ticker_match = TICKER_RE.search(asset)
    if ticker_match:
        candidate = ticker_match.group("ticker")
        matched_asset_type = ticker_match.group("asset_type")
        asset_type = asset_type or matched_asset_type
        if matched_asset_type in MARKET_ASSET_TYPES:
            ticker = candidate
    return ticker, asset_type


def amount_upper_bound(amount: str) -> int:
    numbers = [int(value.replace(",", "")) for value in re.findall(r"\$([\d,]+)", amount)]
    return max(numbers) if numbers else 0


def group_by_ticker(transactions: list[PtrTransaction], direction: str) -> list[tuple[str, list[PtrTransaction]]]:
    grouped: dict[str, list[PtrTransaction]] = {}
    for transaction in transactions:
        if transaction.direction != direction or not transaction.ticker:
            continue
        grouped.setdefault(transaction.ticker, []).append(transaction)
    return sorted(
        grouped.items(),
        key=lambda item: (
            len({transaction.member_name for transaction in item[1]}),
            len(item[1]),
            sum(amount_upper_bound(transaction.amount) for transaction in item[1]),
        ),
        reverse=True,
    )


def top_transactions(transactions: list[PtrTransaction], limit: int = 12) -> list[PtrTransaction]:
    return sorted(transactions, key=lambda transaction: amount_upper_bound(transaction.amount), reverse=True)[:limit]


def is_stale(transaction: PtrTransaction) -> bool:
    return transaction.disclosure_delay_days is not None and transaction.disclosure_delay_days > 45


def has_date_anomaly(transaction: PtrTransaction) -> bool:
    return transaction.disclosure_delay_days is not None and transaction.disclosure_delay_days < 0


def ticker_member_counts(transactions: list[PtrTransaction]) -> dict[tuple[str, str], int]:
    grouped: dict[tuple[str, str], set[str]] = {}
    for transaction in transactions:
        if not transaction.ticker:
            continue
        key = (transaction.direction, transaction.ticker)
        grouped.setdefault(key, set()).add(transaction.member_name)
    return {key: len(members) for key, members in grouped.items()}


def signal_score(transaction: PtrTransaction, member_counts: dict[tuple[str, str], int]) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    if has_date_anomaly(transaction):
        return -3, ["日期异常"]
    same_side_members = member_counts.get((transaction.direction, transaction.ticker), 0) if transaction.ticker else 0
    if same_side_members >= 2 and not is_stale(transaction):
        score += 2
        reasons.append(f"{same_side_members}人同向")
    if transaction.disclosure_delay_days is not None:
        if transaction.disclosure_delay_days <= 7:
            score += 2
            reasons.append("披露窗口近")
        elif transaction.disclosure_delay_days <= 14:
            score += 1
            reasons.append("披露较新")
        elif transaction.disclosure_delay_days > 45:
            score -= 2
            reasons.append("严重滞后")
    upper = amount_upper_bound(transaction.amount)
    if upper >= 250_000:
        score += 2
        reasons.append("大额")
    elif upper >= 50_000:
        score += 1
        reasons.append("中额")
    if transaction.asset_type == "OP":
        score += 1
        reasons.append("期权")
    return score, reasons


def display_asset(transaction: PtrTransaction, limit: int = 44) -> str:
    label = transaction.ticker or re.sub(r"\s+", " ", transaction.asset)
    if len(label) <= limit:
        return label
    return label[: limit - 1].rstrip() + "…"


def direction_cn(direction: str) -> str:
    if direction == "buy":
        return "买入"
    if direction == "sell":
        return "卖出"
    return "其他"


def date_sort_value(value: str) -> date:
    return parse_house_date(value) or parse_pdf_date(value) or date.min


def transaction_sort_key(transaction: PtrTransaction) -> tuple[date, int, str, str]:
    return (
        date_sort_value(transaction.filing_date),
        amount_upper_bound(transaction.amount),
        transaction.member_name,
        transaction.ticker or transaction.asset,
    )


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def select_new_filings(
    filings: list[PtrFiling],
    *,
    state: dict[str, Any],
    lookback_days: int,
    max_items: int,
    force_lookback: bool = False,
) -> tuple[list[PtrFiling], bool]:
    seen = set(state.get("seen_house_doc_ids") or [])
    first_run = not seen
    if first_run or force_lookback:
        cutoff = today_cst() - timedelta(days=lookback_days)
        selected = [
            filing
            for filing in filings
            if (parse_house_date(filing.filing_date) or date.min) >= cutoff
        ]
    else:
        selected = [filing for filing in filings if filing.doc_id not in seen]
    selected.sort(key=lambda item: (parse_house_date(item.filing_date) or date.min, item.doc_id), reverse=True)
    return selected[:max_items], first_run


def render_report(
    *,
    records: list[PtrFiling],
    transactions: list[PtrTransaction],
    parse_errors: dict[str, str],
    all_count: int,
    first_run: bool,
    lookback_days: int,
    error: str | None = None,
) -> str:
    lines: list[str] = []
    lines.append("国会议员 PTR 源头监测日报")
    lines.append("")
    lines.append(f"生成时间：{now_cst_string()}（北京时间）")
    lines.append("官方源：House Clerk Public Disclosure 年度 ZIP/XML + PTR PDF 原文链接")
    lines.append("Senate：MVP 阶段暂不自动解析 eFD 搜索站；日报中需单独标注 Senate 源是否可访问。")
    lines.append("")
    if error:
        lines.append("一、抓取状态")
        lines.append(f"- House 官方源抓取失败：{error}")
        lines.append("- 本次不生成交易信号，等待下次自动重试。")
        return "\n".join(lines) + "\n"

    parsed_doc_ids = {transaction.doc_id for transaction in transactions}
    stale_transactions = [transaction for transaction in transactions if is_stale(transaction)]
    non_ticker_transactions = [transaction for transaction in transactions if not transaction.ticker]
    date_anomalies = [transaction for transaction in transactions if has_date_anomaly(transaction)]
    fresh_transactions = [
        transaction
        for transaction in transactions
        if not is_stale(transaction) and not has_date_anomaly(transaction)
    ]

    lines.append("一、抓取与解析状态")
    lines.append(f"- House PTR 官方索引总数：{all_count}")
    if first_run:
        lines.append(f"- 首次运行：仅回看最近 {lookback_days} 天内披露的 PTR，避免全年历史刷屏。")
    lines.append(f"- 本次新增/待复核 PTR：{len(records)}")
    lines.append(f"- 成功解析 PDF：{len(parsed_doc_ids)}/{len(records)} 份")
    lines.append(f"- 已解析交易明细：{len(transactions)} 笔；其中无公开 ticker/非普通证券：{len(non_ticker_transactions)} 笔")
    if stale_transactions:
        lines.append(f"- 严重滞后披露（交易日至披露日 >45 天）：{len(stale_transactions)} 笔，已从及时共振信号中降权")
    if date_anomalies:
        lines.append(f"- 官方源日期异常/需复核：{len(date_anomalies)} 笔，已排除出信号评分和共振统计")
    if parse_errors:
        lines.append(f"- PDF 未解析/需人工复核：{len(parse_errors)} 份")
    lines.append("")

    member_counts = ticker_member_counts(fresh_transactions)
    scored = []
    for transaction in transactions:
        score, reasons = signal_score(transaction, member_counts)
        if score >= 2:
            scored.append((score, reasons, transaction))
    scored.sort(
        key=lambda item: (
            item[0],
            date_sort_value(item[2].filing_date),
            amount_upper_bound(item[2].amount),
        ),
        reverse=True,
    )

    lines.append("二、今日重点信号")
    if not scored:
        lines.append("- 暂无评分达到 2 分以上的交易信号。")
    else:
        for score, reasons, tx in scored[:12]:
            delay = "N/A" if tx.disclosure_delay_days is None else f"{tx.disclosure_delay_days}天"
            lines.append(
                f"- {score}分｜{tx.member_name}｜{direction_cn(tx.direction)} {display_asset(tx)}｜"
                f"{tx.amount}｜交易 {tx.transaction_date}｜披露 {tx.filing_date}｜延迟 {delay}｜"
                f"{'、'.join(reasons)}｜DocID {tx.doc_id}"
            )
    lines.append("")

    buy_groups = group_by_ticker(fresh_transactions, "buy")
    sell_groups = group_by_ticker(fresh_transactions, "sell")
    buy_resonance = [(ticker, txs) for ticker, txs in buy_groups if len({tx.member_name for tx in txs}) >= 2]
    sell_resonance = [(ticker, txs) for ticker, txs in sell_groups if len({tx.member_name for tx in txs}) >= 2]

    lines.append("三、买入共振（剔除 >45 天滞后披露）")
    if not buy_resonance:
        lines.append("- 暂未发现同一 ticker 被 2 名及以上 House 披露人买入。")
    else:
        for ticker, txs in buy_resonance[:10]:
            members = sorted({tx.member_name for tx in txs})
            total_upper = sum(amount_upper_bound(tx.amount) for tx in txs)
            latest_trade = max(date_sort_value(tx.transaction_date) for tx in txs)
            lines.append(
                f"- {ticker}: {len(txs)} 笔买入，{len(members)} 名披露人，"
                f"金额上限合计约 ${total_upper:,}，最近交易日 {latest_trade.isoformat()}。"
                f"披露人：{', '.join(members)}"
            )
    lines.append("")

    lines.append("四、卖出预警（剔除 >45 天滞后披露）")
    if not sell_resonance:
        lines.append("- 暂未发现同一 ticker 被 2 名及以上 House 披露人卖出。")
    else:
        for ticker, txs in sell_resonance[:10]:
            members = sorted({tx.member_name for tx in txs})
            total_upper = sum(amount_upper_bound(tx.amount) for tx in txs)
            latest_trade = max(date_sort_value(tx.transaction_date) for tx in txs)
            lines.append(
                f"- {ticker}: {len(txs)} 笔卖出，{len(members)} 名披露人，"
                f"金额上限合计约 ${total_upper:,}，最近交易日 {latest_trade.isoformat()}。"
                f"披露人：{', '.join(members)}"
            )
    lines.append("")

    lines.append("五、大额/期权交易待复核")
    noteworthy = [
        tx
        for tx in top_transactions(transactions, limit=12)
        if amount_upper_bound(tx.amount) >= 50000 or tx.asset_type == "OP"
    ]
    if not noteworthy:
        lines.append("- 暂无金额上限 >= $50,000 或期权交易的自动解析结果。")
    else:
        for tx in noteworthy:
            delay = "N/A" if tx.disclosure_delay_days is None else str(tx.disclosure_delay_days)
            stale_note = "；注意：滞后披露" if is_stale(tx) else ""
            lines.append(
                f"- {tx.member_name} {direction_cn(tx.direction)} {display_asset(tx, 58)} {tx.amount}；"
                f"交易日 {tx.transaction_date}，披露日 {tx.filing_date}，延迟 {delay} 天，"
                f"Owner={tx.owner or 'N/A'}，DocID={tx.doc_id}{stale_note}"
            )
    lines.append("")

    lines.append("六、逐笔交易明细（自动解析）")
    if not transactions:
        lines.append("- 本次没有解析到可结构化交易行。")
    else:
        sorted_transactions = sorted(transactions, key=transaction_sort_key, reverse=True)
        for idx, tx in enumerate(sorted_transactions, start=1):
            delay = "N/A" if tx.disclosure_delay_days is None else f"{tx.disclosure_delay_days}天"
            stale_note = "，日期异常" if has_date_anomaly(tx) else ("，滞后" if is_stale(tx) else "")
            lines.append(
                f"{idx}. {tx.filing_date}｜{tx.member_name}｜{direction_cn(tx.direction)}｜"
                f"{display_asset(tx)}｜{tx.amount}｜交易 {tx.transaction_date}｜延迟 {delay}{stale_note}｜"
                f"Owner {tx.owner or 'N/A'}｜类型 {tx.asset_type or 'N/A'}｜DocID {tx.doc_id}"
            )
    lines.append("")

    lines.append("七、新增官方 PTR 披露摘要")
    if not records:
        lines.append("- 今日未发现 House 官方索引新增 PTR。")
    else:
        for idx, record in enumerate(records, start=1):
            record_transactions = [tx for tx in transactions if tx.doc_id == record.doc_id]
            buys = [tx for tx in record_transactions if tx.direction == "buy"]
            sells = [tx for tx in record_transactions if tx.direction == "sell"]
            lines.append(
                f"{idx}. {record.member_name}（{record.state_district or 'N/A'}）"
            )
            lines.append(f"- 披露日期：{record.filing_date}")
            lines.append(f"- DocID：{record.doc_id}")
            lines.append(f"- 官方 PDF：{record.source_url}")
            if record_transactions:
                buy_tickers = ", ".join(display_asset(tx, 28) for tx in buys[:8]) or "无"
                sell_tickers = ", ".join(display_asset(tx, 28) for tx in sells[:8]) or "无"
                lines.append(
                    f"- 自动解析：{len(record_transactions)} 笔；"
                    f"买入 {len(buys)} 笔（{buy_tickers}）；"
                    f"卖出 {len(sells)} 笔（{sell_tickers}）。"
                )
            else:
                lines.append(
                    f"- 自动解析：0 笔。原因：{parse_errors.get(record.doc_id, 'PDF 无标准交易行或需人工复核')}"
                )
            lines.append("")

    lines.append("八、待人工复核")
    if not parse_errors and not non_ticker_transactions and not date_anomalies:
        lines.append("- 暂无未解析 PDF 或非标准资产行。")
    else:
        for doc_id, reason in parse_errors.items():
            record = next((item for item in records if item.doc_id == doc_id), None)
            member = record.member_name if record else "Unknown"
            lines.append(f"- PDF 未解析：{member} DocID {doc_id}；原因：{reason}")
        for tx in date_anomalies:
            lines.append(
                f"- 日期异常：{tx.member_name} {direction_cn(tx.direction)} {display_asset(tx, 64)} "
                f"{tx.amount}；交易日 {tx.transaction_date} 晚于披露日 {tx.filing_date}；DocID {tx.doc_id}"
            )
        for tx in non_ticker_transactions[:10]:
            lines.append(
                f"- 非公开 ticker/非普通证券：{tx.member_name} {direction_cn(tx.direction)} "
                f"{display_asset(tx, 64)} {tx.amount}；DocID {tx.doc_id}"
            )
        if len(non_ticker_transactions) > 10:
            lines.append(f"- 另有 {len(non_ticker_transactions) - 10} 笔非 ticker 资产已写入 JSON 明细。")
    lines.append("")

    lines.append("九、解析限制")
    lines.append("- 本报告已解析 House 官方 PTR PDF 文本，但委员会关联和 Senate eFD 仍需增强。")
    lines.append("- PDF 版式异常、扫描件、修正披露或空表可能需要人工复核。")
    lines.append("")
    lines.append("十、风险提示")
    lines.append("PTR 是披露实时，不是交易实时；交易可能已经发生数天到 45 天。以上仅为源头披露监测，不构成投资建议。")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Monitor official congressional PTR disclosures.")
    parser.add_argument("--year", type=int, default=today_cst().year)
    parser.add_argument("--state", default=str(DEFAULT_STATE))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--records", default=str(DEFAULT_RECORDS))
    parser.add_argument("--transactions", default=str(DEFAULT_TRANSACTIONS))
    parser.add_argument("--pdf-dir", default=str(DEFAULT_PDF_DIR))
    parser.add_argument("--lookback-days", type=int, default=7)
    parser.add_argument("--max-items", type=int, default=25)
    parser.add_argument("--no-parse-pdfs", action="store_true")
    parser.add_argument("--force-lookback", action="store_true")
    args = parser.parse_args()

    state_path = Path(args.state).expanduser()
    report_path = Path(args.report).expanduser()
    records_path = Path(args.records).expanduser()
    transactions_path = Path(args.transactions).expanduser()
    pdf_dir = Path(args.pdf_dir).expanduser()
    state = load_state(state_path)

    try:
        all_filings = fetch_house_ptr_filings(args.year)
        selected, first_run = select_new_filings(
            all_filings,
            state=state,
            lookback_days=args.lookback_days,
            max_items=args.max_items,
            force_lookback=args.force_lookback,
        )
        seen = set(state.get("seen_house_doc_ids") or [])
        seen.update(filing.doc_id for filing in all_filings)
        state.update(
            {
                "last_run_cst": now_cst_string(),
                "last_house_year": args.year,
                "last_house_ptr_count": len(all_filings),
                "seen_house_doc_ids": sorted(seen),
            }
        )
        transactions: list[PtrTransaction] = []
        parse_errors: dict[str, str] = {}
        if args.no_parse_pdfs:
            parse_errors = {filing.doc_id: "PDF parsing disabled" for filing in selected}
        elif PdfReader is None:
            parse_errors = {filing.doc_id: "pypdf is not available in this Python runtime" for filing in selected}
        else:
            for filing in selected:
                try:
                    extracted = extract_transactions(filing, pdf_dir=pdf_dir)
                    transactions.extend(extracted)
                    if not extracted:
                        parse_errors[filing.doc_id] = "no standard transaction rows extracted"
                except Exception as exc:
                    parse_errors[filing.doc_id] = repr(exc)
        report = render_report(
            records=selected,
            transactions=transactions,
            parse_errors=parse_errors,
            all_count=len(all_filings),
            first_run=first_run,
            lookback_days=args.lookback_days,
        )
        records_payload = [asdict(record) | {"member_name": record.member_name} for record in selected]
        transactions_payload = [asdict(transaction) for transaction in transactions]
    except (urllib.error.URLError, TimeoutError, zipfile.BadZipFile, KeyError, ElementTree.ParseError) as exc:
        report = render_report(
            records=[],
            transactions=[],
            parse_errors={},
            all_count=0,
            first_run=False,
            lookback_days=args.lookback_days,
            error=repr(exc),
        )
        records_payload = []
        transactions_payload = []
        state.update({"last_run_cst": now_cst_string(), "last_error": repr(exc)})

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    records_path.parent.mkdir(parents=True, exist_ok=True)
    records_path.write_text(json.dumps(records_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    transactions_path.parent.mkdir(parents=True, exist_ok=True)
    transactions_path.write_text(json.dumps(transactions_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    save_state(state_path, state)
    sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
