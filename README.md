# DentoScan

## Objective
Build a full-stack web application that allows users to upload a Dental X-ray DICOM image, sends it to a Roboflow object detection model, displays bounding boxes for detected pathologies on the image, and passes the image + annotations to an LLM to generate a textual diagnostic report, which will be shown in a panel on the dashboard.

## 🔍 How It Works

1. **Upload X-ray**
   - Users upload dental X-ray files (`.dcm`, `.rvg`, `.png`, `.jpg`, `.jpeg`) through the frontend.

2. **DICOM Conversion**
   - If the file is in DICOM format, it is converted to PNG using `pydicom` and `Pillow` in the backend.

3. **Object Detection (Roboflow)**
   - The image is sent to Roboflow’s object detection model (e.g., for detecting cavities, periapical lesions).
   - The model returns bounding boxes and labels of detected conditions.

4. **Diagnostic Report Generation (LLM)**
   - The predictions are sent to Groq for clinical-style report generation.
   - The backend uses `openai/gpt-oss-120b` by default, with production-safe Groq fallbacks if needed.
   - The report includes findings, approximate image-region references, and clinical suggestions.

5. **Display Results**
   - The annotated image with bounding boxes is shown on the left panel.
   - The generated diagnostic report is shown on the right panel.
   - The reports are dsiplayed on the right panel with the option to download it


## Tech Stack
- Backend: FastAPI (Python)  
- Frontend: ReactJS  
- Object Detection Model: Roboflow API (cavities and periapical lesion detection)  
- LLM (Large Language Model): Groq (`openai/gpt-oss-120b` primary, `llama-3.3-70b-versatile` fallback)  
- Image Format: DICOM (.dcm)  
- Accepted Uploads: `.dcm`, `.rvg`, `.png`, `.jpg`, `.jpeg`  
- Visualization: Bounding boxes overlaid on original image  
- Packaging: Docker 

## Features
- Upload and convert DICOM (.dcm or .rvg) images to viewable PNG/JPG format  
- Allow direct PNG/JPG/JPEG uploads for local testing and demo workflows  
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
4. Copy the environment template and add your keys:  
   ```bash
   cp .env.example .env
   ```
5. Run the FastAPI server:  
   ```bash
   uvicorn main:app --reload
   ```  

### Frontend
1. Navigate to the `frontend` directory.  
2. Install dependencies:  
   ```bash
   npm install
   ```  
3. Run the development server:  
   ```bash
   npm run dev
   ```  
   The Vite dev server proxies `/api`, `/static`, and `/health` to `http://127.0.0.1:8000` by default for local development.  

### Docker 
- Use `docker-compose.yml` to build and run backend and frontend containers:  
  ```bash
  docker-compose up --build
  ```  

## API Endpoints
- `GET /health` - root health endpoint for Render/Docker health checks
- `GET /api/health` - API-scoped health endpoint
- `POST /api/predict` - Upload DICOM image, process with Roboflow, generate report  
  - Request: multipart/form-data with file  
  - Response: JSON with image URL, predictions, image dimensions, and diagnostic report  

## Usage
- [Image1](https://drive.google.com/file/d/1x7PV8UmOe6YfVH2yjqPLR1ZZfndCIH3d/view) [Image2](https://drive.google.com/file/d/1P_lYOhMdQgOxZXs78rLTEZhs__Pf79Cm/view) donwload link for demo (safe to download) and upload the images(s)
- Click "Analyze X-ray" to process images  
- View original and annotated images with bounding boxes in the left panel  
- Click on an image to toggle pinch zoom for detailed inspection  
- View generated diagnostic reports in the right panel  
- Download reports using the "Download Report" button  

## Testing
- Backend tests located in `backend/tests/`  
- Run tests using pytest:  
  ```bash
  cd backend && ./.venv/bin/pytest -q
  ```  
- Frontend manual testing recommended for UI interactions and integration  

## Notes
- Emptying the `backend/static` folder will remove cached rendered images but will not break the app; images will be regenerated on upload  
- Ensure `ROBOFLOW_API_KEY` is configured in the backend environment  
- Add `GROQ_API_KEY` if you want LLM-generated reports; otherwise the backend will return a deterministic fallback report  
- `REQUEST_TIMEOUT_SECONDS`, `ROBOFLOW_TIMEOUT_SECONDS`, and `GROQ_TIMEOUT_SECONDS` can be tuned to avoid long waits when external APIs are slow  
- Backend architecture, low-level design, and deployment notes live in [backend/BACKEND_ARCHITECTURE.md](backend/BACKEND_ARCHITECTURE.md)  
- Pinch zoom toggles on image click for better user experience  

We welcome contributions to make DentoScan even better!
- Fork the repo and submit pull requests for improvements, bug fixes, or new features.
- Please ensure your code follows existing style guidelines.  

## Links
- [Deployment URL](https://dento-scan.netlify.app/) 
- deployed using Netlify 

- [Backend Deployment](https://dentoscan.onrender.com)
- deployed using Render
