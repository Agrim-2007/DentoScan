# Full-Stack Dental X-ray Application

## Overview
This project is a full-stack web application for dental X-ray analysis. It allows users to upload Dental X-ray DICOM images, sends them to a Roboflow object detection model to detect pathologies, visualizes bounding boxes on the images, and generates a diagnostic report using a Large Language Model (LLM). The app is built with FastAPI backend and ReactJS frontend.

## Features
- Upload and convert DICOM (.dcm, .rvg) images to PNG for viewing.
- Call Roboflow API for object detection (cavities, periapical lesions).
- Visualize bounding boxes with labels and confidence scores on images.
- Zoom and pan functionality for image viewer.
- Generate diagnostic reports using OpenAI GPT or a mock LLM.
- Download diagnostic reports.
- Support for multiple file uploads.
- Backend caching and cleanup of temporary files.
- Dockerized backend and frontend for easy deployment.

## Tech Stack
- Backend: FastAPI (Python)
- Frontend: ReactJS with Vite
- Object Detection: Roboflow API
- LLM: OpenAI GPT (or mock)
- Image Format: DICOM (.dcm, .rvg)
- Visualization: Canvas/SVG bounding boxes
- Packaging: Docker

## Setup Instructions

### Prerequisites
- Python 3.9+
- Node.js 16+
- Docker (optional, for containerized deployment)
- Roboflow API key
- OpenAI API key (optional)

### Backend Setup
1. Navigate to the backend directory:
   ```
   cd backend
   ```
2. Create and activate a virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Set environment variables for API keys:
   ```
   export ROBOFLOW_API_KEY=your_roboflow_api_key
   export OPENAI_API_KEY=your_openai_api_key
   ```
5. Run the backend server:
   ```
   uvicorn main:app --reload
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```
   cd frontend
   ```
2. Install dependencies:
   ```
   npm install
   ```
3. Run the frontend development server:
   ```
   npm run dev
   ```
4. Open your browser at `http://localhost:5173`

### Docker Setup (Optional)
1. Build and run containers using docker-compose:
   ```
   docker-compose up --build
   ```

## API Endpoints
- `POST /api/predict`: Uploads a DICOM image, returns predictions, annotated image URL, and diagnostic report.
- `GET /api/health`: Health check endpoint.

## Testing
- Backend tests are located in `backend/tests/`.
- Run tests with:
  ```
  pytest backend/tests
  ```

## Future Improvements
- Add user authentication and analysis history.
- Support more dental conditions in the detection model.
- Export reports in PDF and CSV formats.
- Enhance image preprocessing (contrast, noise reduction).
- Add unit and integration tests for frontend.

## Contact
For questions or support, please contact Agrim Kumar Malhotra at agrim.malhotra2024@nst.rishihood.edu.in
