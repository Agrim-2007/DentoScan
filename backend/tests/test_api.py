from starlette.testclient import TestClient
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@patch('app.api.routes.convert_dicom_to_png')
@patch('app.api.routes.get_predictions')
@patch('app.api.routes.generate_report')
def test_predict_endpoint_success(mock_generate_report, mock_get_predictions, mock_convert_dicom_to_png):
    mock_convert_dicom_to_png.return_value = "path/to/converted.png"
    mock_get_predictions.return_value = [{'class': 'cavity', 'confidence': 0.95, 'x': 10, 'y': 10, 'width': 50, 'height': 50}]
    mock_generate_report.return_value = "Mock diagnostic report."

    dummy_dcm_content = b"dummy dicom data"
    files = {'file': ('test.dcm', dummy_dcm_content, 'application/octet-stream')}

    response = client.post("/api/predict", files=files)

    assert response.status_code == 200
    response_json = response.json()
    assert "predictions" in response_json
    assert "report" in response_json
    assert "png_url" in response_json
    assert response_json["report"] == "Mock diagnostic report."

    mock_convert_dicom_to_png.assert_called_once()
    mock_get_predictions.assert_called_once_with("path/to/converted.png")
    mock_generate_report.assert_called_once_with([{'class': 'cavity', 'confidence': 0.95, 'x': 10, 'y': 10, 'width': 50, 'height': 50}])

def test_predict_endpoint_invalid_file_type():
    dummy_txt_content = b"dummy text data"
    files = {'file': ('test.txt', dummy_txt_content, 'text/plain')}

    response = client.post("/api/predict", files=files)

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid file type. Only .dcm, .rvg, .png, .jpg, or .jpeg files are allowed."}

@patch('app.api.routes.convert_dicom_to_png', side_effect=Exception("DICOM conversion failed"))
def test_predict_endpoint_dicom_conversion_error(mock_convert_dicom_to_png):
    dummy_dcm_content = b"dummy dicom data"
    files = {'file': ('test.dcm', dummy_dcm_content, 'application/octet-stream')}

    response = client.post("/api/predict", files=files)

    assert response.status_code == 500
    assert response.json() == {"detail": "DICOM conversion failed"}
    