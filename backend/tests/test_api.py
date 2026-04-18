import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from main import app


client = TestClient(app, raise_server_exceptions=False)


def _override_storage(tmp_path):
    settings = app.state.settings
    settings.upload_dir = tmp_path / "uploads"
    settings.static_dir = tmp_path / "static"
    settings.temp_dir = tmp_path / "temp"
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.static_dir.mkdir(parents=True, exist_ok=True)
    settings.temp_dir.mkdir(parents=True, exist_ok=True)


def test_health_check():
    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "DentoScan API"
    assert "providers" in payload


def test_root_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"


def test_predict_endpoint_invalid_file_type():
    dummy_txt_content = b"dummy text data"
    files = {"file": ("test.txt", dummy_txt_content, "text/plain")}

    response = client.post("/api/predict", files=files)

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Invalid file type. Only .dcm, .rvg, .png, .jpg, or .jpeg files are allowed."
    }


@patch("app.api.routes.generate_report", new_callable=AsyncMock)
@patch("app.api.routes.get_predictions", new_callable=AsyncMock)
@patch("app.api.routes.convert_dicom_to_png")
def test_predict_endpoint_success(
    mock_convert_dicom_to_png,
    mock_get_predictions,
    mock_generate_report,
    tmp_path,
):
    _override_storage(tmp_path)

    output_path = tmp_path / "static" / "converted.png"
    output_path.write_bytes(b"png")

    mock_convert_dicom_to_png.return_value = type(
        "PreparedImage",
        (),
        {"path": output_path, "image_dimensions": {"width": 640, "height": 480}},
    )()
    mock_get_predictions.return_value = [
        {
            "class": "cavity",
            "confidence": 0.95,
            "x": 10.0,
            "y": 20.0,
            "width": 50.0,
            "height": 60.0,
        }
    ]
    mock_generate_report.return_value = "Mock diagnostic report."

    files = {"file": ("test.dcm", b"dummy dicom data", "application/octet-stream")}

    response = client.post("/api/predict", files=files)

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["report"] == "Mock diagnostic report."
    assert response_json["png_url"] == "/static/converted.png"
    assert response_json["image_dimensions"] == {"width": 640, "height": 480}
    assert response_json["predictions"][0]["class"] == "cavity"

    mock_convert_dicom_to_png.assert_called_once()
    mock_get_predictions.assert_awaited_once()
    mock_generate_report.assert_awaited_once()


@patch("app.api.routes.convert_dicom_to_png", side_effect=Exception("DICOM conversion failed"))
def test_predict_endpoint_dicom_conversion_error(mock_convert_dicom_to_png, tmp_path):
    _override_storage(tmp_path)

    files = {"file": ("test.dcm", b"dummy dicom data", "application/octet-stream")}

    response = client.post("/api/predict", files=files)

    assert response.status_code == 500
    assert response.json() == {
        "detail": "An unexpected error occurred. Please try again later."
    }
    mock_convert_dicom_to_png.assert_called_once()


@patch("app.api.routes.generate_report", new_callable=AsyncMock)
@patch("app.api.routes.get_predictions", new_callable=AsyncMock)
@patch("app.api.routes.convert_raster_to_png")
def test_predict_endpoint_png_success(
    mock_convert_raster_to_png,
    mock_get_predictions,
    mock_generate_report,
    tmp_path,
):
    _override_storage(tmp_path)

    output_path = tmp_path / "static" / "converted.png"
    output_path.write_bytes(b"png")

    mock_convert_raster_to_png.return_value = type(
        "PreparedImage",
        (),
        {"path": output_path, "image_dimensions": {"width": 800, "height": 600}},
    )()
    mock_get_predictions.return_value = []
    mock_generate_report.return_value = "No findings."

    files = {"file": ("test.png", b"fake png data", "image/png")}

    response = client.post("/api/predict", files=files)

    assert response.status_code == 200
    payload = response.json()
    assert payload["png_url"] == "/static/converted.png"
    assert payload["image_dimensions"] == {"width": 800, "height": 600}
    assert payload["report"] == "No findings."
    assert payload["predictions"] == []

    mock_convert_raster_to_png.assert_called_once()
    mock_get_predictions.assert_awaited_once()
    mock_generate_report.assert_awaited_once()
