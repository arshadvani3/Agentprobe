"""
Custom Test Suite API
---------------------
Endpoints for companies to upload their own .py test files.

POST   /api/v1/custom-suites          Upload a .py file → parse + store
GET    /api/v1/custom-suites          List all uploaded suites
DELETE /api/v1/custom-suites/{id}     Delete a suite
GET    /api/v1/custom-suites/template Download the Python template
"""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse

from ..core.auth import verify_api_key
from ..models.schemas import CustomSuiteInfo
from ..services import database
from ..services.custom_suite_loader import CustomSuiteValidationError, load_custom_suite

router = APIRouter(prefix="/api/v1", dependencies=[Depends(verify_api_key)])

_TEMPLATE_PATH = Path(__file__).parent.parent.parent / "test_suites" / "custom_template.py"
_MAX_FILE_SIZE = 256 * 1024  # 256 KB


@router.post("/custom-suites", response_model=CustomSuiteInfo, status_code=201)
async def upload_custom_suite(file: UploadFile = File(...)) -> CustomSuiteInfo:
    """
    Upload a .py custom test suite file.
    The file must follow the template structure (SUITE_NAME + TESTS list).
    Returns the created suite info including its ID for use in evaluations.
    """
    if not file.filename or not file.filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="Only .py files are accepted.")

    raw = await file.read()
    if len(raw) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {_MAX_FILE_SIZE // 1024} KB.",
        )

    try:
        source = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded.")

    try:
        parsed = load_custom_suite(source)
    except CustomSuiteValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    suite_id = await database.create_custom_suite(
        name=parsed["suite_name"],
        description=parsed["description"],
        tests=parsed["tests"],
        categories=parsed["categories"],
    )

    return CustomSuiteInfo(
        suite_id=suite_id,
        name=parsed["suite_name"],
        description=parsed["description"],
        test_count=len(parsed["tests"]),
        categories=parsed["categories"],
    )


@router.get("/custom-suites", response_model=list[CustomSuiteInfo])
async def list_custom_suites() -> list[CustomSuiteInfo]:
    """List all uploaded custom test suites."""
    rows = await database.list_custom_suites()
    return [
        CustomSuiteInfo(
            suite_id=r["suite_id"],
            name=r["name"],
            description=r["description"],
            test_count=r["test_count"],
            categories=r.get("categories") or [],
        )
        for r in rows
    ]


@router.delete("/custom-suites/{suite_id}", status_code=204)
async def delete_custom_suite(suite_id: str) -> None:
    """Delete a custom test suite."""
    deleted = await database.delete_custom_suite(suite_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Suite {suite_id} not found.")


@router.get("/custom-suites/template")
async def download_template() -> FileResponse:
    """Download the Python template file companies use to write custom tests."""
    if not _TEMPLATE_PATH.exists():
        raise HTTPException(status_code=404, detail="Template file not found.")
    return FileResponse(
        path=str(_TEMPLATE_PATH),
        media_type="text/x-python",
        filename="agentprobe_custom_template.py",
    )
