from __future__ import annotations

import logging
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile

from ..core.config import Settings, get_settings
from ..core.exceptions import InvalidFileError
from ..schemas import HealthResponse, PredictResponse
from ..services.dicom_service import convert_dicom_to_png, convert_raster_to_png
from ..services.llm_service import generate_report
from ..services.roboflow_service import get_predictions


router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"dcm", "rvg", "png", "jpg", "jpeg"}
DICOM_EXTENSIONS = {"dcm", "rvg"}
UPLOAD_CHUNK_SIZE = 1024 * 1024


def build_health_payload(settings: Settings) -> dict[str, object]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "providers": {
            "roboflow": "configured" if settings.roboflow_api_key else "missing_api_key",
            "groq": "configured" if settings.groq_api_key else "fallback_mode",
        },
    }


def _sanitize_stem(filename: str) -> str:
    stem = Path(filename).stem or "upload"
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._")
    return sanitized or "upload"


async def _save_upload_to_disk(file: UploadFile, destination: Path, settings: Settings) -> None:
    total_written = 0
    try:
        with destination.open("wb") as buffer:
            while True:
                chunk = await file.read(UPLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                total_written += len(chunk)
                if total_written > settings.max_upload_size_bytes:
                    raise InvalidFileError(
                        f"File size exceeds the {settings.max_upload_size_mb}MB upload limit."
                    )
                buffer.write(chunk)
    except InvalidFileError:
        destination.unlink(missing_ok=True)
        raise
    except Exception as exc:
        destination.unlink(missing_ok=True)
        raise InvalidFileError(f"Could not save file: {exc}") from exc
    finally:
        await file.close()


@router.get("/health", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_settings)) -> dict[str, object]:
    return build_health_payload(settings)


@router.post("/predict", response_model=PredictResponse)
async def predict(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
) -> PredictResponse:
    filename = file.filename or "upload"
    file_extension = Path(filename).suffix.lower().lstrip(".")

    if file_extension not in ALLOWED_EXTENSIONS:
        raise InvalidFileError(
            "Invalid file type. Only .dcm, .rvg, .png, .jpg, or .jpeg files are allowed."
        )

    for directory in (settings.upload_dir, settings.static_dir, settings.temp_dir):
        directory.mkdir(parents=True, exist_ok=True)

    request_id = uuid.uuid4().hex
    safe_stem = _sanitize_stem(filename)
    temp_path = settings.temp_dir / f"{request_id}_{safe_stem}.{file_extension or 'bin'}"

    await _save_upload_to_disk(file, temp_path, settings)

    try:
        if file_extension in DICOM_EXTENSIONS:
            prepared_image = convert_dicom_to_png(
                dicom_path=temp_path,
                output_dir=settings.static_dir,
                output_stem=f"{request_id}_{safe_stem}",
            )
        else:
            prepared_image = convert_raster_to_png(
                image_path=temp_path,
                output_dir=settings.static_dir,
                output_stem=f"{request_id}_{safe_stem}",
            )

        predictions = await get_predictions(prepared_image.path, settings)
        report = await generate_report(
            predictions=predictions,
            image_dimensions=prepared_image.image_dimensions,
            original_filename=filename,
            settings=settings,
        )

        return PredictResponse(
            predictions=predictions,
            png_url=f"/static/{prepared_image.path.name}",
            report=report,
            image_dimensions=prepared_image.image_dimensions,
        )
    finally:
        temp_path.unlink(missing_ok=True)
