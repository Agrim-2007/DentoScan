import pydicom
import numpy as np
from PIL import Image
import os
from pathlib import Path

def convert_dicom_to_png(dicom_path: str) -> str:
    """
    Convert a DICOM file to PNG format.
    Returns the path to the converted PNG file.
    """
    try:
        # Read DICOM file
        ds = pydicom.dcmread(dicom_path)
        
        # Get pixel data
        pixel_array = ds.pixel_array
        
        # Normalize pixel values to 0-255
        if pixel_array.dtype != np.uint8:
            pixel_array = ((pixel_array - pixel_array.min()) * (255.0 / (pixel_array.max() - pixel_array.min()))).astype(np.uint8)
        
        # Create output directory if it doesn't exist
        output_dir = Path("static")
        output_dir.mkdir(exist_ok=True)
        
        # Generate output path
        output_path = output_dir / f"{Path(dicom_path).stem}.png"
        
        # Save as PNG
        image = Image.fromarray(pixel_array)
        image.save(output_path)
        
        return str(output_path)
        
    except Exception as e:
        raise Exception(f"Error converting DICOM to PNG: {str(e)}")
