from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pydicom
from PIL import Image
from pydicom.pixels import apply_modality_lut, apply_voi_lut

from ..core.exceptions import ProcessingError


@dataclass(frozen=True)
class PreparedImage:
    path: Path
    image_dimensions: dict[str, int]


def _save_png(pixel_array: np.ndarray, output_path: Path) -> PreparedImage:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.fromarray(pixel_array)
    image.save(output_path, format="PNG")
    return PreparedImage(
        path=output_path,
        image_dimensions={"width": image.width, "height": image.height},
    )


def _normalize_dicom_pixels(dataset: pydicom.Dataset) -> np.ndarray:
    try:
        pixel_array = dataset.pixel_array
    except Exception as exc:
        raise ProcessingError(f"Could not read DICOM pixel data: {exc}") from exc

    try:
        pixel_array = apply_modality_lut(pixel_array, dataset)
    except Exception:
        pass

    try:
        pixel_array = apply_voi_lut(pixel_array, dataset)
    except Exception:
        pass

    pixel_array = np.asarray(pixel_array, dtype=np.float32)

    if pixel_array.ndim > 2:
        pixel_array = pixel_array[0]

    if pixel_array.ndim != 2:
        raise ProcessingError("Only single-frame grayscale DICOM images are supported.")

    if str(dataset.get("PhotometricInterpretation", "")).upper() == "MONOCHROME1":
        pixel_array = pixel_array.max() - pixel_array

    minimum = float(np.min(pixel_array))
    maximum = float(np.max(pixel_array))

    if maximum == minimum:
        return np.zeros(pixel_array.shape, dtype=np.uint8)

    normalized = np.clip((pixel_array - minimum) / (maximum - minimum), 0.0, 1.0)
    return (normalized * 255).astype(np.uint8)


def convert_dicom_to_png(dicom_path: Path, output_dir: Path, output_stem: str) -> PreparedImage:
    try:
        dataset = pydicom.dcmread(str(dicom_path), force=True)
    except Exception as exc:
        raise ProcessingError(f"Could not read DICOM file: {exc}") from exc

    if "PixelData" not in dataset:
        raise ProcessingError("The uploaded DICOM file does not contain image pixel data.")

    pixel_array = _normalize_dicom_pixels(dataset)
    output_path = output_dir / f"{output_stem}.png"
    return _save_png(pixel_array, output_path)


def convert_raster_to_png(image_path: Path, output_dir: Path, output_stem: str) -> PreparedImage:
    output_path = output_dir / f"{output_stem}.png"

    try:
        with Image.open(image_path) as image:
            if image.mode not in {"L", "RGB"}:
                target_mode = "L" if image.mode.startswith("I") else "RGB"
                image = image.convert(target_mode)
            image.save(output_path, format="PNG")
            return PreparedImage(
                path=output_path,
                image_dimensions={"width": image.width, "height": image.height},
            )
    except Exception as exc:
        raise ProcessingError(f"Could not process image file: {exc}") from exc
