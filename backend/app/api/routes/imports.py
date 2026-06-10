from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.api.deps import ContainerDep, SessionDep, UserDep
from app.application.csv_import_service import CsvImportService

router = APIRouter(prefix="/api/imports", tags=["imports"])

_TEMPLATE_PATH = Path(__file__).parent.parent.parent / "static" / "template.csv"


@router.get("/template")
def download_template(
    _current_user: UserDep,
):
    return FileResponse(
        path=str(_TEMPLATE_PATH),
        media_type="text/csv",
        filename="template.csv",
        headers={"Content-Disposition": "attachment; filename=template.csv"},
    )


@router.post("/csv")
async def upload_csv(
    container: ContainerDep,
    session: SessionDep,
    file: UploadFile,
    current_user: UserDep,
):
    file_content = await file.read()
    service: CsvImportService = container.csv_import_service(session)
    try:
        result = service.import_csv(current_user.id, file_content)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return {"imported": result.imported, "errors": result.errors}
