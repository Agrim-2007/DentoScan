import os
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv
import numpy as np

from PIL import Image
import io
from inference_sdk import InferenceHTTPClient

# Load environment variables
load_dotenv()

# Get configuration from environment variables
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")
ROBOFLOW_MODEL_ID = os.getenv("ROBOFLOW_MODEL_ID", "adr/6")
ROBOFLOW_CONFIDENCE_THRESHOLD = float(os.getenv("ROBOFLOW_CONFIDENCE_THRESHOLD", "0.3"))
ROBOFLOW_OVERLAP_THRESHOLD = float(os.getenv("ROBOFLOW_OVERLAP_THRESHOLD", "0.5"))

if not ROBOFLOW_API_KEY:
    raise ValueError("ROBOFLOW_API_KEY environment variable is not set")

CLIENT = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key=ROBOFLOW_API_KEY
)

def compute_iou(box1, box2):
    """Computes the Intersection over Union (IoU) of two bounding boxes.
    Boxes are expected in [x1, y1, x2, y2] format.
    """
    x1_i = max(box1[0], box2[0])
    y1_i = max(box1[1], box2[1])
    x2_i = min(box1[2], box2[2])
    y2_i = min(box1[3], box2[3])

    inter_width = max(0, x2_i - x1_i)
    inter_height = max(0, y2_i - y1_i)
    inter_area = inter_width * inter_height

    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])

    union_area = box1_area + box2_area - inter_area

    # Avoid division by zero
    if union_area == 0:
        return 0

    return inter_area / union_area

def apply_nms(predictions: List[Dict[str, Any]], iou_threshold: float) -> List[Dict[str, Any]]:
    """
    Applies Non-Maximum Suppression to a list of predictions.
    Predictions are expected to have 'x', 'y', 'width', 'height', 'confidence', 'class'.
    """
    if not predictions:
        return []

    # Convert bounding boxes from center format to [x1, y1, x2, y2]
    boxes = np.array([[
        p["x"] - p["width"] / 2,
        p["y"] - p["height"] / 2,
        p["x"] + p["width"] / 2,
        p["y"] + p["height"] / 2
    ] for p in predictions])

    confidences = np.array([p["confidence"] for p in predictions])

    # Sort by confidence
    sorted_indices = np.argsort(confidences)[::-1]

    keep_indices = []
    while len(sorted_indices) > 0:
        # Pick the box with the highest confidence
        current_index = sorted_indices[0]
        keep_indices.append(current_index)

        # Remove the current index from consideration
        sorted_indices = sorted_indices[1:]

        if len(sorted_indices) == 0:
            break

        # Compare current box with remaining boxes and remove those with high overlap
        iou_scores = [compute_iou(boxes[current_index], boxes[i]) for i in sorted_indices]
        overlap_indices = [sorted_indices[j] for j, iou in enumerate(iou_scores) if iou > iou_threshold]

        # Remove overlapping indices from consideration
        sorted_indices = np.array([i for i in sorted_indices if i not in overlap_indices])

    # Return the predictions that were kept
    return [predictions[i] for i in keep_indices]

async def get_predictions(image_path: str):
    """
    Sends image file to Roboflow as multipart upload for inference.
    Applies Non-Maximum Suppression (NMS) to filter overlapping boxes.
    """
    try:
        with open(image_path, "rb") as image_file:
            response = requests.post(
                url=f"https://detect.roboflow.com/{ROBOFLOW_MODEL_ID}",
                params={
                    "api_key": ROBOFLOW_API_KEY,
                    "confidence": int(ROBOFLOW_CONFIDENCE_THRESHOLD * 100),
                    "overlap": int(ROBOFLOW_OVERLAP_THRESHOLD * 100)
                },
                files={"file": ("image.png", image_file, "image/png")}
            )
            response.raise_for_status()
            result = response.json()

        raw_predictions = result.get("predictions", [])
        # Apply NMS with configured overlap threshold
        filtered_predictions = apply_nms(raw_predictions, ROBOFLOW_OVERLAP_THRESHOLD)
        return filtered_predictions

    except Exception as e:
        raise Exception(f"Error sending image to Roboflow: {str(e)}")
