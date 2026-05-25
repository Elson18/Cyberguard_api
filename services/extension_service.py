import os
import tempfile
import zipfile
from datetime import datetime, timezone

from services.threat_scanner import analyze_url

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT_SRC = os.path.join(BASE_DIR, "chrome-extension", "chrome-extension")

_scan_reports: list[dict] = []


def build_extension_zip() -> str:
    if not os.path.isdir(EXT_SRC):
        raise FileNotFoundError(f"Extension source not found: {EXT_SRC}")

    tmp_dir = tempfile.mkdtemp(prefix="neuroguard_ext_")
    zip_path = os.path.join(tmp_dir, "neuroguard-extension.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for root, _, files in os.walk(EXT_SRC):
            for filename in files:
                full_path = os.path.join(root, filename)
                arcname = os.path.join(
                    "neuroguard-extension",
                    os.path.relpath(full_path, EXT_SRC),
                )
                archive.write(full_path, arcname=arcname)

    return zip_path


def get_extension_status() -> dict:
    manifest_exists = os.path.isfile(os.path.join(EXT_SRC, "manifest.json"))
    return {
        "version": "1.0.0",
        "manifest": 3,
        "path": EXT_SRC,
        "ready": manifest_exists and os.path.isdir(EXT_SRC),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }


async def scan_url(url: str, user_id: str | None = None) -> dict:
    result = await analyze_url(url)
    if user_id:
        result["userId"] = user_id
    return result


def save_report(payload: dict, user_id: str | None = None) -> dict:
    entry = {
        **payload,
        "userId": user_id,
        "receivedAt": datetime.now(timezone.utc).isoformat(),
    }
    _scan_reports.append(entry)
    if len(_scan_reports) > 1000:
        del _scan_reports[: len(_scan_reports) - 1000]
    return {"status": "ok", "message": "Report received"}
