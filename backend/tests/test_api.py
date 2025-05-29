from fastapi.testclient import TestClient
from main import app
import pytest
import os
from unittest.mock import patch, MagicMock

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@patch('app.api.routes.convert_dicom_to_png')
@patch('app.api.routes.get_predictions')
@patch('app.api.routes.generate_report')
def test_predict_endpoint_success(mock_llm, mock_roboflow, mock_dicom_converter):
    # Mock the behavior of the services
    mock_dicom_converter.return_value = "path/to/converted.png"
    mock_roboflow.return_value = [{'class': 'cavity', 'confidence': 0.95, 'x': 10, 'y': 10, 'width': 50, 'height': 50}]
    mock_llm.return_value = "Mock diagnostic report."

    # Create a dummy file for upload
    dummy_dcm_content = b"dummy dicom data"
    files = {'file': ('test.dcm', dummy_dcm_content, 'application/octet-stream')}

    response = client.post("/api/predict", files=files)

    assert response.status_code == 200
    response_json = response.json()
    assert "predictions" in response_json
    assert "report" in response_json
    assert "png_url" in response_json
    assert response_json["report"] == "Mock diagnostic report."

    # Verify that the mock services were called
    mock_dicom_converter.assert_called_once()
    mock_roboflow.assert_called_once_with("path/to/converted.png")
    mock_llm.assert_called_once_with([{'class': 'cavity', 'confidence': 0.95, 'x': 10, 'y': 10, 'width': 50, 'height': 50}])

def test_predict_endpoint_invalid_file_type():
    # Create a dummy file with invalid extension
    dummy_txt_content = b"dummy text data"
    files = {'file': ('test.txt', dummy_txt_content, 'text/plain')}

    response = client.post("/api/predict", files=files)

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid file type. Only .dcm, .rvg, .png, .jpg, or .jpeg files are allowed."}

@patch('app.api.routes.convert_dicom_to_png', side_effect=Exception("DICOM conversion failed"))
def test_predict_endpoint_dicom_conversion_error(mock_dicom_converter):
    # Create a dummy DICOM file for upload
    dummy_dcm_content = b"dummy dicom data"
    files = {'file': ('test.dcm', dummy_dcm_content, 'application/octet-stream')}

    response = client.post("/api/predict", files=files)

    assert response.status_code == 500
    assert response.json() == {"detail": "DICOM conversion failed"}
