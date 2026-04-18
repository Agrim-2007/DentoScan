from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ImageDimensions(BaseModel):
    width: int
    height: int


class Prediction(BaseModel):
    x: float
    y: float
    width: float
    height: float
    confidence: float
    class_name: str = Field(alias="class")

    model_config = ConfigDict(populate_by_name=True)


class PredictResponse(BaseModel):
    predictions: list[Prediction]
    png_url: str
    report: str
    image_dimensions: ImageDimensions


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    providers: dict[str, str]
