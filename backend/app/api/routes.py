
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import os
import shutil
import uuid
import pydicom
from PIL import Image
import logging


from ..services.dicom_service import convert_dicom_to_png
from ..services.roboflow_service import get_predictions
from ..services.llm_service import generate_report

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

@router.post("/predict")
async def predict(file: UploadFile = File(...)):
    allowed_extensions = ["dcm", "rvg"]
    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file type. Only .dcm, .rvg files are allowed.")

    temp_filename = f"temp/{uuid.uuid4()}_{file.filename}"

    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")

    image_to_predict = temp_filename
    png_url = None
    image_dimensions = None
    if file_extension in ["dcm", "rvg"]:
        try:
            png_path = convert_dicom_to_png(temp_filename)
            image_to_predict = png_path
            png_url = f"/static/{os.path.basename(png_path)}"
            # Get image dimensions after conversion
            try:
                with Image.open(png_path) as img:
                    image_dimensions = {"width": img.width, "height": img.height}
            except Exception as img_e:
                logger.error(f"Error getting image dimensions: {img_e}")
                image_dimensions = None # Or handle as appropriate
        except Exception as e:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
            raise HTTPException(status_code=500, detail=f"Could not convert DICOM to PNG: {e}")

    elif file_extension in ["png", "jpg", "jpeg"]:
        converted_filename = f"static/{uuid.uuid4()}.{file_extension}"
        shutil.copy(temp_filename, converted_filename)
        png_url = f"/static/{os.path.basename(converted_filename)}"
        image_to_predict = converted_filename
        # Get image dimensions for direct image upload
        try:
            with Image.open(image_to_predict) as img:
                image_dimensions = {"width": img.width, "height": img.height}
        except Exception as img_e:
            logger.error(f"Error getting image dimensions: {img_e}")
            image_dimensions = None # Or handle as appropriate

    predictions = []
    try:
        predictions = await get_predictions(image_to_predict)
    except Exception as e:
        logger.error(f"Error during Roboflow inference: {e}")
        raise HTTPException(status_code=500, detail=f"Error during image analysis: {e}")

    diagnostic_report = "Error generating report." 
    try:
        diagnostic_report = await generate_report(predictions)
    except Exception as e:
        logger.error(f"Error generating report with LLM: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating diagnostic report: {e}")

    finally:

        if os.path.exists(temp_filename):
            os.remove(temp_filename)

        # Commenting out deletion of image_to_predict so frontend can access the image
        # if image_to_predict and os.path.exists(image_to_predict) and image_to_predict != temp_filename:
        #      os.remove(image_to_predict)

    return JSONResponse(content={
        "predictions": predictions,
        "png_url": png_url,
        "report": diagnostic_report,
        "image_dimensions": image_dimensions
    })
