"""
DI Container — the composition root for the application.

Creates and wires all service instances. Instantiated once during FastAPI
lifespan and stored on app.state. This is the only place where concrete
implementations are bound to abstract ports.
"""
from __future__ import annotations

from sqlmodel import Session

from app.core.config import settings
from app.database import _db_manager
from app.infrastructure.database import DatabaseManager
from app.infrastructure.vault.manager import SqlCipherVaultManager
from app.infrastructure.repositories.transaction_repo import SQLModelTransactionRepository
from app.infrastructure.repositories.category_repo import SQLModelCategoryRepository
from app.infrastructure.repositories.user_repo import SQLModelUserRepository
from app.infrastructure.ai.factory import ConfigDrivenAIProviderFactory
from app.application.transaction_service import TransactionService
from app.application.whisper_service import WhisperService
from app.application.analytics_service import AnalyticsService
from app.application.mcp_service import MCPService
from app.application.category_service import CategoryService
from app.application.auth_service import AuthService
from app.application.csv_import_service import CsvImportService
from app.application.bank_sync_service import BankSyncService
from app.application.bank_connection_service import BankService as BankConnectionService
from app.application.wallet_service import WalletService
from app.application.exchange_rate_service import ExchangeRateService
from app.application.api_key_service import ApiKeyService
from app.infrastructure.repositories.exchange_rate_repo import SQLModelExchangeRateRepository
from app.infrastructure.repositories.api_key_repo import SQLModelApiKeyRepository
from app.infrastructure.repositories.bank_repo import SQLModelBankConnectionRepository
from app.infrastructure.repositories.wallet_repo import SQLModelWalletRepository
from app.infrastructure.exchange_rate_api import FrankfurterClient


class Container:
    """Holds all application-level singletons. Created once per server process."""

    def __init__(self) -> None:
        self._db = _db_manager
        self._vault_manager = SqlCipherVaultManager(self._db, settings.setup_state_path)
        self._ai_factory = ConfigDrivenAIProviderFactory()

    # ── Infrastructure (instantiated once) ────────────────────────────────────────

    @property
    def db(self) -> DatabaseManager:
        return self._db

    @property
    def vault_manager(self) -> SqlCipherVaultManager:
        return self._vault_manager

    @property
    def ai_factory(self) -> ConfigDrivenAIProviderFactory:
        return self._ai_factory

    # ── Per-session services (created per request) ────────────────────────────────

    def _transaction_repo(self, session: Session) -> SQLModelTransactionRepository:
        return SQLModelTransactionRepository(session)

    def category_repo(self, session: Session) -> SQLModelCategoryRepository:
        return SQLModelCategoryRepository(session)

    def _exchange_rate_repo(self, session: Session) -> SQLModelExchangeRateRepository:
        return SQLModelExchangeRateRepository(session)

    def _user_repo(self, session: Session) -> SQLModelUserRepository:
        return SQLModelUserRepository(session)

    def _api_key_repo(self, session: Session) -> SQLModelApiKeyRepository:
        return SQLModelApiKeyRepository(session)

    def _bank_connection_repo(self, session: Session) -> SQLModelBankConnectionRepository:
        return SQLModelBankConnectionRepository(session)

    def _wallet_repo(self, session: Session) -> SQLModelWalletRepository:
        return SQLModelWalletRepository(session)

    # ── Application services (created per request with session) ───────────────────

    def transaction_service(self, session: Session) -> TransactionService:
        tx_repo = self._transaction_repo(session)
        cat_repo = self.category_repo(session)
        rate_repo = self._exchange_rate_repo(session)
        rate_service = ExchangeRateService(rate_repo)
        return TransactionService(tx_repo, cat_repo, rate_service)

    def whisper_service(self, session: Session) -> WhisperService:
        tx_repo = self._transaction_repo(session)
        cat_repo = self.category_repo(session)
        rate_repo = self._exchange_rate_repo(session)
        rate_service = ExchangeRateService(rate_repo)
        tx_service = TransactionService(tx_repo, cat_repo, rate_service)
        provider = self._ai_factory.create_provider()
        return WhisperService(tx_service, tx_repo, cat_repo, provider)

    def analytics_service(self, session: Session) -> AnalyticsService:
        return AnalyticsService(
            self._transaction_repo(session),
            self.category_repo(session),
        )

    def mcp_service(self, session: Session) -> MCPService:
        return MCPService(
            self._transaction_repo(session),
            self.category_repo(session),
        )

    def category_service(self, session: Session) -> CategoryService:
        return CategoryService(self.category_repo(session))

    def auth_service(self, session: Session) -> AuthService:
        return AuthService(self._user_repo(session))

    def api_key_service(self, session: Session) -> ApiKeyService:
        return ApiKeyService(self._api_key_repo(session))

    def bank_connection_service(self, session: Session) -> BankConnectionService:
        return BankConnectionService(self._bank_connection_repo(session))

    def wallet_service(self, session: Session) -> WalletService:
        return WalletService(self._wallet_repo(session))

    def exchange_rate_service(self, session: Session) -> ExchangeRateService:
        return ExchangeRateService(self._exchange_rate_repo(session), FrankfurterClient())

    def csv_import_service(self, session: Session) -> CsvImportService:
        return CsvImportService(
            self.transaction_service(session),
            self.category_repo(session),
        )

    def bank_sync_service(self, session: Session) -> BankSyncService:
        return BankSyncService(
            self.transaction_service(session),
            self.category_repo(session),
        )
