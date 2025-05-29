from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import pydicom
from PIL import Image
import os
import shutil
import uuid
import requests
import base64
import time
from datetime import datetime, timedelta
import asyncio
from pathlib import Path
import logging
from dotenv import load_dotenv
import google.generativeai as genai
from app.api.routes import router as api_router


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


UPLOAD_DIR = Path("uploads")
CONVERTED_DIR = Path("converted")
MAX_FILE_AGE_HOURS = 24  


UPLOAD_DIR.mkdir(exist_ok=True)
CONVERTED_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="DentoScan API",
    description="API for dental X-ray analysis using Roboflow and LLM",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")

if not os.path.exists("converted"):
    os.makedirs("converted")
app.mount("/converted", StaticFiles(directory="converted"), name="converted")

if not os.path.exists("temp"):
    os.makedirs("temp")





async def cleanup_old_files():
    """Remove files older than MAX_FILE_AGE_HOURS"""
    while True:
        try:
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(hours=MAX_FILE_AGE_HOURS)
            

            for file_path in UPLOAD_DIR.glob("*"):
                if file_path.is_file():
                    file_age = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_age < cutoff_time:
                        file_path.unlink()
                        logger.info(f"Removed old upload file: {file_path}")
            

            for file_path in CONVERTED_DIR.glob("*"):
                if file_path.is_file():
                    file_age = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_age < cutoff_time:
                        file_path.unlink()
                        logger.info(f"Removed old converted file: {file_path}")
            
            logger.info("Cleanup completed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
        

        await asyncio.sleep(3600)

@app.on_event("startup")
async def startup_event():
    """Start background tasks on application startup"""
    asyncio.create_task(cleanup_old_files())



@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler to provide consistent error responses"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )


app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port) 