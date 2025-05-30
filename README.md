# DentoScan

## Objective
Build a full-stack web application that allows users to upload a Dental X-ray DICOM image, sends it to a Roboflow object detection model, displays bounding boxes for detected pathologies on the image, and passes the image + annotations to an LLM to generate a textual diagnostic report, which will be shown in a panel on the dashboard.

## 🔍 How It Works

1. **Upload X-ray**
   - Users upload dental X-ray files (`.dcm`, `.rvg`) through the frontend.

2. **DICOM Conversion**
   - If the file is in DICOM format, it is converted to PNG using `pydicom` and `Pillow` in the backend.

3. **Object Detection (Roboflow)**
   - The image is sent to Roboflow’s object detection model (e.g., for detecting cavities, periapical lesions).
   - The model returns bounding boxes and labels of detected conditions.

4. **Diagnostic Report Generation (LLM)**
   - The predictions are then sent to Gemini Flash 2.0 to generate a clinical diagnostic report.
   - The report includes findings, locations, and clinical suggestions.

5. **Display Results**
   - The annotated image with bounding boxes is shown on the left panel.
   - The generated diagnostic report is shown on the right panel.
   - The reports are dsiplayed on the right panel with the option to download it


## Tech Stack
- Backend: FastAPI (Python)  
- Frontend: ReactJS  
- Object Detection Model: Roboflow API (cavities and periapical lesion detection)  
- LLM (Large Language Model): GEMINI (model:- gemini-2.0-flash)
- Image Format: DICOM (.dcm)  
- Visualization: Bounding boxes overlaid on original image  
- Packaging: Docker 

## Features
- Upload and convert DICOM (.dcm or .rvg) images to viewable PNG/JPG format  
- Display original and annotated images with bounding boxes showing pathology name and confidence  
- Pinch zoom feature toggles when clicking on the image for better inspection  
- Generate diagnostic reports using LLM based on image annotations  
- Download diagnostic reports as text files  
- Support multiple file uploads  
- Loading spinners during API calls  
- Dockerized backend and frontend  

## Setup Instructions

### Backend
1. Navigate to the `backend` directory  
2. Create a virtual environment and activate it  
3. Install dependencies:  
   ```bash
   pip install -r requirements.txt
   ```  
4. Run the FastAPI server:  
   ```bash
   uvicorn main:app --reload
   ```  

### Frontend
1. Navigate to the `frontend` directory  
2. Install dependencies:  
   ```bash
   npm install
   ```  
3. Run the development server:  
   ```bash
   npm run dev
   ```  

### Docker 
- Use `docker-compose.yml` to build and run backend and frontend containers:  
  ```bash
  docker-compose up --build
  ```  

## API Endpoints
- `POST /api/predict` - Upload DICOM image, process with Roboflow, generate report  
  - Request: multipart/form-data with file  
  - Response: JSON with image URL, predictions, image dimensions, and diagnostic report  

## Usage
- Upload one or more DICOM images using the file upload area  
- Click "Analyze X-ray" to process images  
- View original and annotated images with bounding boxes in the left panel  
- Click on an image to toggle pinch zoom for detailed inspection  
- View generated diagnostic reports in the right panel  
- Download reports using the "Download Report" button  

## Testing
- Backend tests located in `backend/tests/`  
- Run tests using pytest:  
  ```bash
  pytest backend/tests/
  ```  
- Frontend manual testing recommended for UI interactions and integration  

## Notes
- Emptying the `backend/static` and `backend/converted` folders will remove cached images but will not break the app; images will be regenerated on upload  
- Ensure you have a valid Roboflow API key configured in the backend environment  
- Pinch zoom toggles on image click for better user experience  

## Contribution
- Fork the repo and submit pull requests for improvements or bug fixes  

## License
- Specify license information here if applicable

## Links
- [Deployment URL](https://dento-scan.netlify.app/) 
- deployed using Netlify 

- [Backend Deployment](https://dentoscan.onrender.com)
- deployed using Render