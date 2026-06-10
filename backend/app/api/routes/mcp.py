from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import ApiKeyUserDep, ContainerDep, SessionDep
from app.application.mcp_service import MCPService
from app.core.domain.user import User

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.get("/manifest")
def get_manifest():
    return {
        "name": "ZeroWhisper",
        "version": "0.1.0",
        "description": "Personal financial data — balance, spending, net worth",
        "capabilities": {"resources": True, "tools": True, "prompts": False},
    }


@router.get("/resources")
def list_resources(_user: ApiKeyUserDep):
    return [
        {"uri": "zerowhisper://balance", "name": "Account Balance", "description": "Current JOD balance"},
        {"uri": "zerowhisper://transactions/recent", "name": "Recent Transactions", "description": "Last 10 transactions (no descriptions)"},
        {"uri": "zerowhisper://transactions/by-category", "name": "Spending by Category", "description": "Current month spending grouped by category"},
        {"uri": "zerowhisper://net-worth", "name": "Net Worth", "description": "Lifetime income vs expenses"},
        {"uri": "zerowhisper://wallets", "name": "Wallets", "description": "Wallets with type, currency and current balance"},
    ]


@router.get("/resources/{resource_path:path}")
def get_resource(
    resource_path: str,
    container: ContainerDep,
    session: SessionDep,
    user: ApiKeyUserDep,
):
    today = date.today()
    service: MCPService = container.mcp_service(session)
    mapping = {
        "balance": lambda: service.get_balance(user.id),
        "transactions/recent": lambda: service.get_recent_transactions(user.id),
        "transactions/by-category": lambda: service.get_spending_by_category(user.id, today.month, today.year),
        "net-worth": lambda: service.get_net_worth(user.id),
        "wallets": lambda: service.get_wallets(user.id),
    }
    handler = mapping.get(resource_path)
    if not handler:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return handler()


@router.post("/tools/call")
def call_tool(
    container: ContainerDep,
    session: SessionDep,
    body: dict,
    user: ApiKeyUserDep,
):
    today = date.today()
    tool = body.get("tool", "")
    args = body.get("args", {}) or {}
    service: MCPService = container.mcp_service(session)

    mapping = {
        "get_balance": lambda: service.get_balance(user.id),
        "get_recent_transactions": lambda: service.get_recent_transactions(user.id, limit=args.get("limit", 10)),
        "get_spending_by_category": lambda: service.get_spending_by_category(user.id, args.get("month", today.month), args.get("year", today.year)),
        "get_net_worth": lambda: service.get_net_worth(user.id),
        "get_wallets": lambda: service.get_wallets(user.id),
    }
    handler = mapping.get(tool)
    if not handler:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown tool")
    return handler()


@router.get("/prompts")
def list_prompts(_user: ApiKeyUserDep):
    return []
