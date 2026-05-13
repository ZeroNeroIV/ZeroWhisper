from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import FileResponse
from sqlmodel import Session

from app.database import get_session
from app.dependencies import get_current_user
from app.models.user import User
from app.services.csv_import import import_csv

router = APIRouter()

_TEMPLATE_PATH = Path(__file__).parent.parent / "static" / "template.csv"


@router.get("/template")
def download_template(
    current_user: User = Depends(get_current_user),
):
    """Download the canonical CSV import template."""
    return FileResponse(
        path=str(_TEMPLATE_PATH),
        media_type="text/csv",
        filename="template.csv",
        headers={"Content-Disposition": "attachment; filename=template.csv"},
    )


@router.post("/csv")
async def upload_csv(
    file: UploadFile,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Upload a CSV file and import its transactions."""
    file_content = await file.read()
    try:
        result = import_csv(session, current_user.id, file_content)
    except ValueError as exc:
        return {"error": str(exc)}
    return {"imported": result.imported, "errors": result.errors}
