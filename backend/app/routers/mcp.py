from datetime import date

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlmodel import Session

from app.database import get_session
from app.models.user import User
from app.services import mcp_service
from app.services.api_key_service import verify_api_key

router = APIRouter()


def _get_mcp_user(
    x_api_key: str = Header(..., alias="X-API-Key"),
    session: Session = Depends(get_session),
) -> User:
    user = verify_api_key(x_api_key, session)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return user


@router.get("/manifest")
def get_manifest():
    """No auth. Returns the MCP server manifest."""
    return {
        "name": "ZeroWhisper",
        "version": "0.1.0",
        "description": "Personal financial data — balance, spending, net worth",
        "capabilities": {"resources": True, "tools": True, "prompts": False},
    }


@router.get("/resources")
def list_resources(user: User = Depends(_get_mcp_user)):
    """Returns list of available MCP resources."""
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
    user: User = Depends(_get_mcp_user),
    session: Session = Depends(get_session),
):
    """Fetch a specific resource by its URI path."""
    today = date.today()

    if resource_path == "balance":
        return mcp_service.get_balance(session, user.id)
    elif resource_path == "transactions/recent":
        return mcp_service.get_recent_transactions(session, user.id)
    elif resource_path == "transactions/by-category":
        return mcp_service.get_spending_by_category(session, user.id, today.month, today.year)
    elif resource_path == "net-worth":
        return mcp_service.get_net_worth(session, user.id)
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")


@router.post("/tools/call")
def call_tool(
    body: dict,
    user: User = Depends(_get_mcp_user),
    session: Session = Depends(get_session),
):
    """Invoke an MCP tool by name with optional args."""
    today = date.today()
    tool = body.get("tool", "")
    args = body.get("args", {}) or {}

    if tool == "get_balance":
        return mcp_service.get_balance(session, user.id)
    elif tool == "get_recent_transactions":
        return mcp_service.get_recent_transactions(session, user.id, limit=args.get("limit", 10))
    elif tool == "get_spending_by_category":
        return mcp_service.get_spending_by_category(
            session,
            user.id,
            args.get("month", today.month),
            args.get("year", today.year),
        )
    elif tool == "get_net_worth":
        return mcp_service.get_net_worth(session, user.id)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown tool")


@router.get("/prompts")
def list_prompts(user: User = Depends(_get_mcp_user)):
    """Returns empty list — no pre-defined prompts yet."""
    return []
