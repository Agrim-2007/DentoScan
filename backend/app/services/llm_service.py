from __future__ import annotations

import asyncio
import logging
from typing import Any

from groq import AsyncGroq

from ..core.config import Settings


logger = logging.getLogger(__name__)


def _describe_region(prediction: dict[str, Any], image_dimensions: dict[str, int]) -> str:
    width = max(image_dimensions.get("width", 1), 1)
    height = max(image_dimensions.get("height", 1), 1)

    relative_x = float(prediction["x"]) / width
    relative_y = float(prediction["y"]) / height

    horizontal = "left" if relative_x < 1 / 3 else "central" if relative_x < 2 / 3 else "right"
    vertical = "upper" if relative_y < 1 / 3 else "middle" if relative_y < 2 / 3 else "lower"
    return f"{vertical} {horizontal} third of the image"


def _fallback_report(
    predictions: list[dict[str, Any]],
    image_dimensions: dict[str, int],
    original_filename: str,
) -> str:
    if not predictions:
        return (
            "Diagnostic Report\n\n"
            "Findings:\n"
            "No radiographic anomalies were detected by the current object detection model.\n\n"
            "Impression:\n"
            "No model-detected abnormalities on this upload. Correlate clinically with the original X-ray.\n\n"
            "Recommendation:\n"
            "Review alongside the patient history and confirm with a licensed dental professional."
        )

    findings = []
    for prediction in predictions:
        findings.append(
            "- {label} in the {region} (confidence {confidence:.1f}%).".format(
                label=prediction["class"],
                region=_describe_region(prediction, image_dimensions),
                confidence=prediction["confidence"] * 100,
            )
        )

    return "\n".join(
        [
            "Diagnostic Report",
            "",
            f"Source file: {original_filename}",
            "",
            "Findings:",
            *findings,
            "",
            "Impression:",
            "Automated analysis detected the findings listed above. These detections should be treated as decision support rather than a definitive diagnosis.",
            "",
            "Recommendation:",
            "Correlate the detections with the original radiograph, symptoms, and a clinician review before making treatment decisions.",
        ]
    )


def _build_messages(
    predictions: list[dict[str, Any]],
    image_dimensions: dict[str, int],
    original_filename: str,
) -> list[dict[str, str]]:
    if not predictions:
        anomaly_summary = "No anomalies detected by the object detection model."
    else:
        anomaly_lines = []
        for prediction in predictions:
            anomaly_lines.append(
                "- {label}: confidence {confidence:.1f}% | location {region} | box center ({x:.1f}, {y:.1f}) | size {width:.1f}x{height:.1f}".format(
                    label=prediction["class"],
                    confidence=prediction["confidence"] * 100,
                    region=_describe_region(prediction, image_dimensions),
                    x=prediction["x"],
                    y=prediction["y"],
                    width=prediction["width"],
                    height=prediction["height"],
                )
            )
        anomaly_summary = "\n".join(anomaly_lines)

    system_prompt = (
        "You are assisting with dental radiograph triage reports.\n"
        "Write a concise clinical-style report using only the provided detections and image metadata.\n"
        "Do not invent teeth numbers, anatomy, or treatment certainty when that information is not available.\n"
        "State limitations clearly and avoid definitive diagnosis language.\n"
        "Use this exact structure:\n"
        "Findings:\n"
        "<short paragraph>\n\n"
        "Impression:\n"
        "<short paragraph>\n\n"
        "Recommendation:\n"
        "<1-2 sentences>"
    )

    user_prompt = (
        f"File name: {original_filename}\n"
        f"Image dimensions: {image_dimensions['width']}x{image_dimensions['height']} pixels\n"
        "Model detections:\n"
        f"{anomaly_summary}"
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


async def generate_report(
    predictions: list[dict[str, Any]],
    image_dimensions: dict[str, int],
    original_filename: str,
    settings: Settings,
) -> str:
    fallback = _fallback_report(predictions, image_dimensions, original_filename)

    if not settings.groq_api_key:
        logger.warning("GROQ_API_KEY not configured. Returning deterministic fallback report.")
        return fallback

    messages = _build_messages(predictions, image_dimensions, original_filename)

    last_error: Exception | None = None

    try:
        async with AsyncGroq(api_key=settings.groq_api_key) as client:
            for model_name in settings.report_models:
                try:
                    completion = await asyncio.wait_for(
                        client.chat.completions.create(
                            model=model_name,
                            messages=messages,
                            temperature=0.2,
                            max_completion_tokens=600,
                        ),
                        timeout=settings.groq_timeout_seconds,
                    )
                    content = completion.choices[0].message.content if completion.choices else None
                    if content and content.strip():
                        return content.strip()
                except Exception as exc:
                    last_error = exc
                    logger.warning("Groq report generation failed for model %s: %s", model_name, exc)
    except Exception as exc:
        last_error = exc

    logger.warning("Falling back to deterministic report after Groq failure: %s", last_error)
    return fallback
