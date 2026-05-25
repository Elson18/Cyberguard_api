import os

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field, HttpUrl

from services.extension_service import (
    build_extension_zip,
    get_extension_status,
    save_report,
    scan_url,
)
from utils.rate_limit import limiter
from utils.security import optional_user_id

router = APIRouter(prefix="/api/extension", tags=["extension"])


class ScanUrlRequest(BaseModel):
    url: HttpUrl
    tab_id: int | None = Field(default=None, alias="tabId")

    class Config:
        populate_by_name = True


class ReportRequest(BaseModel):
    url: HttpUrl
    decision: str
    explanation: str | None = None
    serp_risky: bool = Field(default=False, alias="serpRisky")
    serp_match_count: int = Field(default=0, alias="serpMatchCount")
    domain: str | None = None
    risk_level: str | None = Field(default=None, alias="riskLevel")

    class Config:
        populate_by_name = True


@router.get("/download")
async def download_extension():
    try:
        zip_path = build_extension_zip()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename="neuroguard-extension.zip",
    )


@router.get("/status")
async def extension_status():
    return get_extension_status()


@router.post("/scan-url")
@limiter.limit("30/minute")
async def scan_url_endpoint(
    request: Request,
    body: ScanUrlRequest,
    x_user_id: str | None = Header(None, alias="X-User-Id"),
):
    user_id = optional_user_id(x_user_id)
    return await scan_url(str(body.url), user_id=user_id)


@router.post("/report")
@limiter.limit("60/minute")
async def report_endpoint(
    request: Request,
    body: ReportRequest,
    x_user_id: str | None = Header(None, alias="X-User-Id"),
):
    user_id = optional_user_id(x_user_id)
    return save_report(body.model_dump(by_alias=True), user_id=user_id)
