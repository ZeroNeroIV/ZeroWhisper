"""Import routes — CSV upload and template download."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlmodel import Session

from app.api.deps import get_current_user, get_session, _get_csv_import_service
from app.application.csv_import_service import CsvImportService
from app.core.domain.user import User

router = APIRouter(prefix="/api/imports", tags=["imports"])

_TEMPLATE_PATH = Path(__file__).parent.parent.parent / "static" / "template.csv"


@router.get("/template")
def download_template(
    _current_user: User = Depends(get_current_user),
):
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
    service: CsvImportService = Depends(_get_csv_import_service),
):
    file_content = await file.read()
    try:
        result = service.import_csv(current_user.id, file_content)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return {"imported": result.imported, "errors": result.errors}
