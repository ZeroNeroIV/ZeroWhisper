from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

VALID_CURRENCIES = frozenset({"JOD", "USD"})
REQUIRED_FIELDS = frozenset({"transaction_date", "amount_original"})

TEMPLATE_HEADERS = [
    "transaction_date", "amount_original", "currency_original",
    "category", "description",
]

HEADER_ALIASES: dict[str, str] = {
    "date": "transaction_date",
    "trans date": "transaction_date",
    "transaction date": "transaction_date",
    "value date": "transaction_date",
    "amount": "amount_original",
    "debit": "amount_original",
    "credit": "amount_original",
    "currency": "currency_original",
    "ccy": "currency_original",
    "memo": "description",
    "details": "description",
    "narration": "description",
    "particulars": "description",
    "type": "category",
    "trans type": "category",
}

DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y")


class CsvParseError(ValueError):
    """A row or file could not be parsed."""


@dataclass(frozen=True)
class ParsedRow:
    transaction_date: date
    amount_original: Decimal
    currency_original: str
    category: str
    description: str | None


@dataclass
class RowError:
    row: int
    error: str


@dataclass
class ParseResult:
    rows: list[ParsedRow]
    errors: list[RowError]


@dataclass
class HeaderMapping:
    transaction_date: int
    amount_original: int
    currency_original: int | None
    category: int | None
    description: int | None


def map_headers(raw_headers: list[str]) -> HeaderMapping:
    mapping: dict[str, int] = {}
    for idx, raw in enumerate(raw_headers):
        normalized = raw.strip().lower()
        if normalized in TEMPLATE_HEADERS:
            mapping[normalized] = idx
        elif normalized in HEADER_ALIASES:
            canonical = HEADER_ALIASES[normalized]
            if canonical not in mapping:
                mapping[canonical] = idx
    return HeaderMapping(
        transaction_date=mapping.get("transaction_date", -1),
        amount_original=mapping.get("amount_original", -1),
        currency_original=mapping.get("currency_original"),
        category=mapping.get("category"),
        description=mapping.get("description"),
    )


def _parse_date(s: str) -> date:
    s = s.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise CsvParseError(f"Cannot parse date: {s!r}")


def _parse_amount(s: str) -> Decimal:
    s = s.strip().replace(",", "").replace(" ", "")
    s = s.lstrip("-").lstrip("+")
    try:
        val = Decimal(s)
        if val <= 0:
            raise CsvParseError(f"Amount must be positive, got {s!r}")
        return val
    except InvalidOperation:
        raise CsvParseError(f"Cannot parse amount: {s!r}")


def _lookup(row: list[str], idx: int | None) -> str | None:
    if idx is None or idx >= len(row):
        return None
    val = row[idx].strip()
    return val or None


def parse_row(
    row: list[str],
    header_map: HeaderMapping,
    valid_categories: list[str],
) -> ParsedRow:
    date_str = _lookup(row, header_map.transaction_date)
    if not date_str:
        raise CsvParseError("Missing transaction_date")
    tx_date = _parse_date(date_str)

    amount_str = _lookup(row, header_map.amount_original)
    if not amount_str:
        raise CsvParseError("Missing amount_original")
    amount = _parse_amount(amount_str)

    currency_raw = _lookup(row, header_map.currency_original)
    currency = (currency_raw or "JOD").upper()
    if currency not in VALID_CURRENCIES:
        currency = "JOD"

    category_raw = _lookup(row, header_map.category)
    category = "Other"
    if category_raw:
        lower_cat = category_raw.strip().lower()
        for valid in valid_categories:
            if valid.lower() == lower_cat:
                category = valid
                break

    description = _lookup(row, header_map.description)

    return ParsedRow(
        transaction_date=tx_date,
        amount_original=amount,
        currency_original=currency,
        category=category,
        description=description,
    )


def parse_csv(
    content: bytes,
    valid_categories: list[str],
) -> ParseResult:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        raise CsvParseError("CSV file is empty")

    header_map = map_headers(rows[0])
    if header_map.transaction_date < 0 or header_map.amount_original < 0:
        missing = []
        if header_map.transaction_date < 0:
            missing.append("transaction_date")
        if header_map.amount_original < 0:
            missing.append("amount_original")
        raise CsvParseError(
            f"CSV is missing required columns: {missing}. "
            "Download the template to see required headers."
        )

    parsed: list[ParsedRow] = []
    errors: list[RowError] = []

    for row_num, row in enumerate(rows[1:], start=2):
        if not any(cell.strip() for cell in row):
            continue
        try:
            parsed.append(parse_row(row, header_map, valid_categories))
        except CsvParseError as e:
            errors.append(RowError(row=row_num, error=str(e)))

    return ParseResult(rows=parsed, errors=errors)
