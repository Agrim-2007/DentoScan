from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
import numpy as np

from ..core.config import Settings
from ..core.exceptions import ExternalServiceError, ServiceConfigurationError


def compute_iou(box1: np.ndarray, box2: np.ndarray) -> float:
    x1_intersection = max(box1[0], box2[0])
    y1_intersection = max(box1[1], box2[1])
    x2_intersection = min(box1[2], box2[2])
    y2_intersection = min(box1[3], box2[3])

    intersection_width = max(0.0, x2_intersection - x1_intersection)
    intersection_height = max(0.0, y2_intersection - y1_intersection)
    intersection_area = intersection_width * intersection_height

    area_box1 = max(0.0, box1[2] - box1[0]) * max(0.0, box1[3] - box1[1])
    area_box2 = max(0.0, box2[2] - box2[0]) * max(0.0, box2[3] - box2[1])
    union_area = area_box1 + area_box2 - intersection_area

    if union_area <= 0:
        return 0.0

    return intersection_area / union_area


def apply_nms(predictions: list[dict[str, Any]], iou_threshold: float) -> list[dict[str, Any]]:
    if not predictions:
        return []

    boxes = np.array(
        [
            [
                prediction["x"] - prediction["width"] / 2,
                prediction["y"] - prediction["height"] / 2,
                prediction["x"] + prediction["width"] / 2,
                prediction["y"] + prediction["height"] / 2,
            ]
            for prediction in predictions
        ],
        dtype=np.float32,
    )

    confidences = np.array([prediction["confidence"] for prediction in predictions], dtype=np.float32)
    sorted_indices = np.argsort(confidences)[::-1]

    keep_indices: list[int] = []
    while sorted_indices.size > 0:
        current_index = int(sorted_indices[0])
        keep_indices.append(current_index)
        sorted_indices = sorted_indices[1:]

        if sorted_indices.size == 0:
            break

        remaining = [
            idx
            for idx in sorted_indices
            if compute_iou(boxes[current_index], boxes[int(idx)]) <= iou_threshold
        ]
        sorted_indices = np.array(remaining, dtype=np.int64)

    return [predictions[index] for index in keep_indices]


def _normalize_prediction(prediction: dict[str, Any]) -> dict[str, Any] | None:
    required_keys = {"x", "y", "width", "height", "confidence", "class"}
    if not required_keys.issubset(prediction):
        return None

    try:
        return {
            "x": float(prediction["x"]),
            "y": float(prediction["y"]),
            "width": float(prediction["width"]),
            "height": float(prediction["height"]),
            "confidence": float(prediction["confidence"]),
            "class": str(prediction["class"]),
        }
    except (TypeError, ValueError):
        return None


async def get_predictions(image_path: Path, settings: Settings) -> list[dict[str, Any]]:
    if not settings.roboflow_api_key:
        raise ServiceConfigurationError("ROBOFLOW_API_KEY is not configured on the server.")

    try:
        image_bytes = image_path.read_bytes()
    except OSError as exc:
        raise ExternalServiceError(f"Could not read prepared image for inference: {exc}") from exc

    try:
        async with httpx.AsyncClient(timeout=settings.roboflow_request_timeout_seconds) as client:
            response = await client.post(
                f"{settings.roboflow_base_url.rstrip('/')}/{settings.roboflow_model_id}",
                params={
                    "api_key": settings.roboflow_api_key,
                    "confidence": int(settings.roboflow_confidence_threshold * 100),
                    "overlap": int(settings.roboflow_overlap_threshold * 100),
                },
                files={"file": (image_path.name, image_bytes, "image/png")},
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text.strip()[:500] or "No error body returned by Roboflow."
        raise ExternalServiceError(
            f"Roboflow inference failed with status {exc.response.status_code}: {detail}"
        ) from exc
    except httpx.HTTPError as exc:
        raise ExternalServiceError(f"Could not reach Roboflow: {exc}") from exc

    try:
        result = response.json()
    except ValueError as exc:
        raise ExternalServiceError("Roboflow returned a non-JSON response.") from exc

    normalized_predictions = [
        normalized
        for normalized in (_normalize_prediction(item) for item in result.get("predictions", []))
        if normalized and normalized["confidence"] >= settings.roboflow_confidence_threshold
    ]

    return apply_nms(normalized_predictions, settings.roboflow_overlap_threshold)
