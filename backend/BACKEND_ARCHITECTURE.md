# DentoScan Backend Architecture

## HLD

### Core flow
1. The frontend uploads a single X-ray file to `POST /api/predict`.
2. The backend saves the upload into a temporary workspace.
3. DICOM and RVG files are normalized into PNG using `pydicom` and `Pillow`.
4. The prepared PNG is sent to Roboflow for object detection.
5. Roboflow predictions are filtered with confidence checks and non-maximum suppression.
6. The prediction set is converted into a concise diagnostic report using Groq.
7. The API returns the static image URL, prediction boxes, image dimensions, and report text.

### Main backend components
- `backend/main.py`: thin entrypoint for `uvicorn`.
- `backend/app/main.py`: FastAPI app factory, CORS, static mounts, lifespan, cleanup, error handling.
- `backend/app/api/routes.py`: API surface and request orchestration.
- `backend/app/services/dicom_service.py`: DICOM and raster normalization into PNG.
- `backend/app/services/roboflow_service.py`: inference call and NMS post-processing.
- `backend/app/services/llm_service.py`: Groq prompt construction, fallback handling, report generation.
- `backend/app/core/config.py`: strongly typed environment and runtime settings.

### Deployment model
- Runtime: FastAPI + Uvicorn
- Image processing: in-process Python service
- Model inference: Roboflow hosted endpoint
- Report generation: Groq hosted LLM endpoint
- Static output: local ephemeral filesystem mounted at `/static`

## LLD

### Request lifecycle
- Upload validation accepts `.dcm`, `.rvg`, `.png`, `.jpg`, `.jpeg`.
- Files are streamed to disk to avoid keeping large uploads entirely in memory.
- Temporary uploads are deleted at the end of the request.
- Converted PNGs remain in `backend/static/` so the frontend can render them by URL.

### DICOM handling details
- `pydicom.dcmread(..., force=True)` tolerates imperfect file headers often seen in X-ray exports.
- Modality and VOI LUT transforms are applied when available.
- `MONOCHROME1` images are inverted to match expected grayscale display behavior.
- Output is normalized to 8-bit PNG for Roboflow and browser display.

### Roboflow integration
- The service validates configuration at request time, not import time.
- Raw predictions are normalized into a stable numeric shape.
- NMS removes overlapping boxes using IoU thresholding.
- External API failures are surfaced as `502` responses with meaningful detail.

### Groq reporting
- Primary model: `openai/gpt-oss-120b`
- Fallback chain: `llama-3.3-70b-versatile`, `openai/gpt-oss-20b`
- If Groq is unavailable or not configured, the API still returns a deterministic local report instead of failing the entire prediction request.
- Report prompts are constrained to avoid invented tooth numbers or definitive diagnosis claims.

### Health and operability
- `/health` and `/api/health` are both available.
- Health responses expose provider readiness at a high level without leaking secrets.
- A background cleanup task removes expired files from upload, temp, and static folders.

## SDLC

### Build
- Install dependencies from `backend/requirements.txt`
- Start locally with `uvicorn main:app --reload`
- Build Docker image from `backend/Dockerfile`

### Test
- Run `pytest backend/tests/`
- Core scenarios:
  - health endpoint availability
  - invalid file rejection
  - successful prediction orchestration
  - conversion error handling

### Deploy
- Ensure `ROBOFLOW_API_KEY` is configured on Render
- Add `GROQ_API_KEY` for LLM-backed reports
- Use the backend folder as the working directory
- Start command: `uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}`
- Health check path: `/health`

### Operate
- Monitor HTTP 5xx rates on `/api/predict`
- Watch for Roboflow or Groq quota/configuration failures
- Rotate API keys via environment variables without code changes

### Improve next
- Persist reports and annotated artifacts to object storage instead of local disk
- Add request IDs and structured logging
- Add contract tests against Roboflow/Groq sandbox environments
- Introduce async job offloading for very large upload batches
