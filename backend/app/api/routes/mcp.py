"""MCP API routes — Model Context Protocol for AI agent access."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlmodel import Session

from app.api.deps import get_current_user_by_api_key, get_session
from app.application.mcp_service import MCPService
from app.core.domain.user import User

router = APIRouter(prefix="/mcp", tags=["mcp"])


def _get_service(request: Request, session: Session = Depends(get_session)) -> MCPService:
    return request.app.state.container.mcp_service(session)


@router.get("/manifest")
def get_manifest():
    return {
        "name": "ZeroWhisper",
        "version": "0.1.0",
        "description": "Personal financial data — balance, spending, net worth",
        "capabilities": {"resources": True, "tools": True, "prompts": False},
    }


@router.get("/resources")
def list_resources(_user: User = Depends(get_current_user_by_api_key)):
    return [
        {
            "uri": "zerowhisper://balance",
            "name": "Account Balance",
            "description": "Current JOD balance",
        },
        {
            "uri": "zerowhisper://transactions/recent",
            "name": "Recent Transactions",
            "description": "Last 10 transactions (no descriptions)",
        },
        {
            "uri": "zerowhisper://transactions/by-category",
            "name": "Spending by Category",
            "description": "Current month spending grouped by category",
        },
        {
            "uri": "zerowhisper://net-worth",
            "name": "Net Worth",
            "description": "Lifetime income vs expenses",
        },
    ]


@router.get("/resources/{resource_path:path}")
def get_resource(
    resource_path: str,
    user: User = Depends(get_current_user_by_api_key),
    service: MCPService = Depends(_get_service),
):
    today = date.today()
    mapping = {
        "balance": lambda: service.get_balance(user.id),
        "transactions/recent": lambda: service.get_recent_transactions(user.id),
        "transactions/by-category": lambda: service.get_spending_by_category(user.id, today.month, today.year),
        "net-worth": lambda: service.get_net_worth(user.id),
    }
    handler = mapping.get(resource_path)
    if not handler:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return handler()


@router.post("/tools/call")
def call_tool(
    body: dict,
    user: User = Depends(get_current_user_by_api_key),
    service: MCPService = Depends(_get_service),
):
    today = date.today()
    tool = body.get("tool", "")
    args = body.get("args", {}) or {}

    if tool == "get_balance":
        return service.get_balance(user.id)
    elif tool == "get_recent_transactions":
        return service.get_recent_transactions(user.id, limit=args.get("limit", 10))
    elif tool == "get_spending_by_category":
        return service.get_spending_by_category(
            user.id,
            args.get("month", today.month),
            args.get("year", today.year),
        )
    elif tool == "get_net_worth":
        return service.get_net_worth(user.id)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown tool")


@router.get("/prompts")
def list_prompts(_user: User = Depends(get_current_user_by_api_key)):
    return []
