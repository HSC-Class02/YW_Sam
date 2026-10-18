#!/usr/bin/env python3
"""Collect Samsung Electronics financial statements from OpenDART.

The API key is read only from the OPENDART_API_KEY environment variable.
Generated amounts remain in KRW in CSV/JSON; the dashboard formats them in KRW trillion.
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
API_URL = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"
CORP_CODE = "00126380"
COMPANY = "삼성전자"
STOCK_CODE = "005930"
START_YEAR = int(os.getenv("START_YEAR", "2015"))
END_YEAR = datetime.now().year
REPORTS = {
    "11011": ("annual", "FY"),
    "11012": ("halfyear", "H1"),
    "11013": ("quarterly", "Q1"),
    "11014": ("quarterly", "9M"),
}
FLOW_FIELDS = (
    "revenue", "cost_of_sales", "gross_profit", "operating_income",
    "pretax_income", "net_income", "operating_cash_flow",
    "investing_cash_flow", "financing_cash_flow",
)
METRIC_LABELS = {
    "revenue": "매출액",
    "cost_of_sales": "매출원가",
    "gross_profit": "매출총이익",
    "operating_income": "영업이익",
    "pretax_income": "법인세비용차감전순이익",
    "net_income": "당기순이익",
    "current_assets": "유동자산",
    "cash_and_equivalents": "현금및현금성자산",
    "assets": "자산총계",
    "current_liabilities": "유동부채",
    "liabilities": "부채총계",
    "equity": "자본총계",
    "operating_cash_flow": "영업활동 현금흐름",
    "investing_cash_flow": "투자활동 현금흐름",
    "financing_cash_flow": "재무활동 현금흐름",
    "gross_margin_pct": "매출총이익률(%)",
    "operating_margin_pct": "영업이익률(%)",
    "net_margin_pct": "순이익률(%)",
    "debt_ratio_pct": "부채비율(부채/자산, %)",
    "debt_to_equity_pct": "부채/자본(%)",
    "current_ratio_pct": "유동비율(%)",
    "operating_cashflow_to_sales_pct": "영업현금흐름/매출(%)",
}
ALIASES = {
    "revenue": ["매출액", "수익(매출액)", "영업수익", "매출"],
    "cost_of_sales": ["매출원가", "매출원가(영업수익)"],
    "gross_profit": ["매출총이익", "매출총이익(손실)"],
    "operating_income": ["영업이익", "영업이익(손실)", "영업손익"],
    "pretax_income": [
        "법인세비용차감전순이익", "법인세비용차감전순이익(손실)",
        "법인세비용차감전이익(손실)",
    ],
    "net_income": [
        "당기순이익", "당기순이익(손실)", "분기순이익", "반기순이익",
        "당기순손익",
    ],
    "current_assets": ["유동자산"],
    "cash_and_equivalents": [
        "현금및현금성자산", "현금 및 현금성자산", "현금및현금성자산 합계",
    ],
    "assets": ["자산총계"],
    "current_liabilities": ["유동부채"],
    "liabilities": ["부채총계"],
    "equity": ["자본총계"],
    "operating_cash_flow": [
        "영업활동으로 인한 현금흐름", "영업활동 현금흐름",
        "영업활동으로 인한 순현금흐름",
    ],
    "investing_cash_flow": [
        "투자활동으로 인한 현금흐름", "투자활동 현금흐름",
        "투자활동으로 인한 순현금흐름",
    ],
    "financing_cash_flow": [
        "재무활동으로 인한 현금흐름", "재무활동 현금흐름",
        "재무활동으로 인한 순현금흐름",
    ],
}
STATEMENTS = {
    "revenue": ["CIS", "IS"],
    "cost_of_sales": ["CIS", "IS"],
    "gross_profit": ["CIS", "IS"],
    "operating_income": ["CIS", "IS"],
    "pretax_income": ["CIS", "IS"],
    "net_income": ["CIS", "IS"],
    "current_assets": ["BS"],
    "cash_and_equivalents": ["BS"],
    "assets": ["BS"],
    "current_liabilities": ["BS"],
    "liabilities": ["BS"],
    "equity": ["BS"],
    "operating_cash_flow": ["CF"],
    "investing_cash_flow": ["CF"],
    "financing_cash_flow": ["CF"],
}
CSV_FIELDS = [
    "period", "period_end", "year", "period_type", "fs_div",
    *ALIASES.keys(),
    "gross_margin_pct", "operating_margin_pct", "net_margin_pct",
    "debt_ratio_pct", "debt_to_equity_pct", "current_ratio_pct",
    "operating_cashflow_to_sales_pct",
]

def amount_value(row: dict[str, Any], cumulative: bool = False) -> float | None:
    # Interim income and cash-flow statements need year-to-date values for deriving quarters.
    fields = ("thstrm_add_amount", "thstrm_amount") if cumulative else ("thstrm_amount", "thstrm_add_amount")
    for field in fields:
        raw = row.get(field)
        if raw is None or str(raw).strip() in ("", "-", "—", "N/A"):
            continue
        raw = str(raw).strip().replace(",", "")
        negative = raw.startswith("(") and raw.endswith(")")
        raw = raw.strip("()")
        try:
            value = float(raw)
            return -value if negative else value
        except ValueError:
            continue
    return None

def get_field(rows: list[dict[str, Any]], metric: str) -> float | None:
    aliases = ALIASES[metric]
    by_statement = []
    for statement in STATEMENTS[metric]:
        by_statement.extend([r for r in rows if r.get("sj_div") == statement])
    search_rows = by_statement or rows
    for alias in aliases:
        for row in search_rows:
            if str(row.get("account_nm", "")).strip() == alias:
                value = amount_value(row, cumulative=metric in FLOW_FIELDS)
                if value is not None:
                    return value
    for alias in aliases:
        for row in search_rows:
            account_name = str(row.get("account_nm", "")).strip()
            if alias and alias in account_name:
                value = amount_value(row, cumulative=metric in FLOW_FIELDS)
                if value is not None:
                    return value
    return None

def get_report(session: requests.Session, api_key: str, year: int, report_code: str) -> tuple[list[dict[str, Any]], str] | None:
    for fs_div in ("CFS", "OFS"):
        params = {
            "crtfc_key": api_key,
            "corp_code": CORP_CODE,
            "bsns_year": str(year),
            "reprt_code": report_code,
            "fs_div": fs_div,
        }
        response = session.get(API_URL, params=params, timeout=45)
        response.raise_for_status()
        payload = response.json()
        status = str(payload.get("status", ""))
        if status == "000" and isinstance(payload.get("list"), list) and payload["list"]:
            return payload["list"], fs_div
        if status not in ("013",):
            raise RuntimeError(
                "OpenDART error: year=%s report=%s fs_div=%s status=%s message=%s"
                % (year, report_code, fs_div, status, payload.get("message", "unknown"))
            )
        time.sleep(0.12)
    return None

def calc_ratios(record: dict[str, Any]) -> dict[str, Any]:
    def ratio(numerator: str, denominator: str) -> float | None:
        a, b = record.get(numerator), record.get(denominator)
        if a is None or b in (None, 0):
            return None
        return round(a / b * 100.0, 4)

    record["gross_margin_pct"] = ratio("gross_profit", "revenue")
    record["operating_margin_pct"] = ratio("operating_income", "revenue")
    record["net_margin_pct"] = ratio("net_income", "revenue")
    record["debt_ratio_pct"] = ratio("liabilities", "assets")
    record["debt_to_equity_pct"] = ratio("liabilities", "equity")
    record["current_ratio_pct"] = ratio("current_assets", "current_liabilities")
    record["operating_cashflow_to_sales_pct"] = ratio("operating_cash_flow", "revenue")
    return record

def record_from_rows(rows: list[dict[str, Any]], fs_div: str, year: int, label: str, period_end: str, period_type: str) -> dict[str, Any]:
    record: dict[str, Any] = {
        "period": label,
        "period_end": period_end,
        "year": year,
        "period_type": period_type,
        "fs_div": fs_div,
    }
    for metric in ALIASES:
        record[metric] = get_field(rows, metric)
    return calc_ratios(record)

def subtract_value(later: float | None, earlier: float | None) -> float | None:
    if later is None or earlier is None:
        return None
    return later - earlier

def build_quarterly(raw: dict[int, dict[str, dict[str, Any]]]) -> list[dict[str, Any]]:
    quarter_defs = [
        ("Q1", "11013", None, "03-31"),
        ("Q2", "11012", "11013", "06-30"),
        ("Q3", "11014", "11012", "09-30"),
        ("Q4", "11011", "11014", "12-31"),
    ]
    result: list[dict[str, Any]] = []
    for year in sorted(raw):
        year_reports = raw[year]
        for quarter, source_code, prior_code, mmdd in quarter_defs:
            current = year_reports.get(source_code)
            if not current:
                continue
            prior = year_reports.get(prior_code) if prior_code else None
            row = dict(current)
            row["period"] = "%d %s" % (year, quarter)
            row["period_end"] = "%d-%s" % (year, mmdd)
            row["period_type"] = quarter
            if quarter != "Q1":
                for metric in FLOW_FIELDS:
                    row[metric] = subtract_value(
                        current.get(metric), prior.get(metric) if prior else None
                    )
            result.append(calc_ratios(row))
    return sorted(result, key=lambda item: (item["year"], item["period_type"]))

def write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

def main() -> int:
    api_key = os.getenv("OPENDART_API_KEY", "").strip()
    if not api_key:
        print("ERROR: OPENDART_API_KEY secret is missing. Add it under Settings > Secrets and variables > Actions.", file=sys.stderr)
        return 2

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "YW_Sam-Samsung-Financial-Dashboard/1.0"})
    raw_by_year: dict[int, dict[str, dict[str, Any]]] = {}
    annual: list[dict[str, Any]] = []
    halfyear: list[dict[str, Any]] = []

    for year in range(START_YEAR, END_YEAR + 1):
        raw_by_year[year] = {}
        for code, (_, suffix) in REPORTS.items():
            try:
                fetched = get_report(session, api_key, year, code)
            except Exception as exc:
                print("Failed: %s report %s: %s" % (year, code, exc), file=sys.stderr)
                raise
            if not fetched:
                continue
            rows, fs_div = fetched
            if suffix == "FY":
                label, period_end, kind = "%d FY" % year, "%d-12-31" % year, "annual"
            elif suffix == "H1":
                label, period_end, kind = "%d H1" % year, "%d-06-30" % year, "halfyear"
            elif suffix == "Q1":
                label, period_end, kind = "%d Q1" % year, "%d-03-31" % year, "quarterly"
            else:
                label, period_end, kind = "%d 9M" % year, "%d-09-30" % year, "nine_month_cumulative"
            record = record_from_rows(rows, fs_div, year, label, period_end, kind)
            raw_by_year[year][code] = record
            if code == "11011":
                annual.append(record)
            elif code == "11012":
                halfyear.append(record)
            time.sleep(0.12)
        print("Processed %s" % year)

    quarterly = build_quarterly(raw_by_year)
    annual.sort(key=lambda item: (item["year"], item["period_end"]))
    halfyear.sort(key=lambda item: (item["year"], item["period_end"]))
    quarterly.sort(key=lambda item: item["period_end"])

    write_csv(DATA_DIR / "annual.csv", annual)
    write_csv(DATA_DIR / "halfyear.csv", halfyear)
    write_csv(DATA_DIR / "quarterly.csv", quarterly)
    generated_at = datetime.now(timezone.utc).astimezone(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")
    all_records = annual + halfyear + quarterly
    output = {
        "company": COMPANY,
        "stock_code": STOCK_CODE,
        "corp_code": CORP_CODE,
        "source": "OpenDART",
        "source_url": "https://opendart.fss.or.kr/",
        "generated_at": generated_at,
        "start_year": START_YEAR,
        "data_status": "정상 수집" if all_records else "공시 데이터 없음",
        "annual": annual,
        "halfyear": halfyear,
        "quarterly": quarterly,
    }
    (DATA_DIR / "metrics.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print("Done. annual=%d halfyear=%d quarterly=%d" % (len(annual), len(halfyear), len(quarterly)))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
