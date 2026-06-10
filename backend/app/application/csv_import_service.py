from __future__ import annotations

from uuid import UUID

from app.core.domain.transaction import SOURCE_CSV_IMPORT
from app.application.transaction_service import TransactionService
from app.core.ports.category_repo import CategoryRepository
from app.infrastructure.csv_parser import parse_csv, CsvParseError


class CsvImportResult:
    imported: int
    errors: list[dict]

    def __init__(self, imported: int, errors: list[dict]) -> None:
        self.imported = imported
        self.errors = errors


class CsvImportService:

    def __init__(
        self,
        tx_service: TransactionService,
        cat_repo: CategoryRepository,
    ) -> None:
        self._tx_service = tx_service
        self._cat_repo = cat_repo

    def import_csv(self, user_id: UUID, content: bytes) -> CsvImportResult:
        cats = self._cat_repo.find_by_user(user_id)
        valid_categories = [c.name for c in cats]
        if "Other" not in valid_categories:
            valid_categories.append("Other")

        try:
            result = parse_csv(content, valid_categories)
        except CsvParseError as e:
            raise ValueError(str(e)) from e

        imported = 0
        errors: list[dict] = []

        for parsed in result.rows:
            try:
                self._tx_service.create(
                    user_id=user_id,
                    amount_original=parsed.amount_original,
                    currency_original=parsed.currency_original,
                    category=parsed.category,
                    transaction_date=parsed.transaction_date,
                    description=parsed.description,
                    source=SOURCE_CSV_IMPORT,
                )
                imported += 1
            except Exception as e:
                errors.append({"row": 0, "error": str(e)})

        errors.extend({"row": e.row, "error": e.error} for e in result.errors)

        return CsvImportResult(imported=imported, errors=errors)
