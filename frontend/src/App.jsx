import { useState, useRef, useEffect } from 'react'
import { CircularProgress, Typography, Alert, Snackbar, List, ListItem, ListItemText, Paper } from '@mui/material'
import CloudUploadIcon from '@mui/icons-material/CloudUpload'
import { styled } from '@mui/material/styles'
import Button from '@mui/material/Button'
import CloseIcon from '@mui/icons-material/Close'
import { v4 as uuidv4 } from 'uuid'

import DicomViewer from './components/DicomViewer'
import ImageWithBoundingBoxes from './components/ImageWithBoundingBoxes'

import './App.css'

const VisuallyHiddenInput = styled('input')({
  clip: 'rect(0 0 0 0)',
  clipPath: 'inset(50%)',
  height: 1,
  overflow: 'hidden',
  position: 'absolute',
  bottom: 0,
  left: 0,
  whiteSpace: 'nowrap',
  width: 1,
})

function App() {
  const [selectedFiles, setSelectedFiles] = useState([])
  const [processingResults, setProcessingResults] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [errorTimeout, setErrorTimeout] = useState(null)
  const [filePreviews, setFilePreviews] = useState([])
  const [selectedResult, setSelectedResult] = useState(null)

  const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50MB
  const SUPPORTED_FORMATS = ['.dcm', '.rvg']

  const handleFileSelect = async (event) => {
    const files = Array.from(event.target.files || []);
    const filesToAdd = [];
    const errors = [];
    const previewPromises = [];

    for (const file of files) {
      // Check if file is already uploaded
      const isDuplicate = selectedFiles.some(existingFile => 
        existingFile.file.name === file.name && 
        existingFile.file.size === file.size
      );

      if (isDuplicate) {
        // Clear any existing timeout
        if (errorTimeout) {
          clearTimeout(errorTimeout);
        }
        // Set the error message
        setError(`${file.name} is already uploaded`);
        // Set a new timeout to clear the error
        const timeout = setTimeout(() => setError(null), 1000);
        setErrorTimeout(timeout);
        continue;
      }

      if (file.size > MAX_FILE_SIZE) {
        errors.push(`${file.name}: File size exceeds 50MB limit.`);
        continue;
      }

      const fileExtension = file.name.toLowerCase().slice(file.name.lastIndexOf('.'));
      if (!SUPPORTED_FORMATS.includes(fileExtension)) {
        errors.push(`${file.name}: Unsupported file format. Please upload ${SUPPORTED_FORMATS.join(', ')}`);
        continue;
      }

      // Add file with new ID
      const id = uuidv4();
      filesToAdd.push({ file, id });

      // Generate preview
      if (['.png', '.jpg', '.jpeg'].includes(fileExtension)) {
        const preview = await new Promise((resolve) => {
          const reader = new FileReader();
          reader.onload = (e) => {
            resolve({ id, fileName: file.name, url: e.target.result });
          };
          reader.readAsDataURL(file);
        });
        previewPromises.push(Promise.resolve(preview));
      } else {
        previewPromises.push(Promise.resolve({ id, fileName: file.name, url: null }));
      }
    }

    const newPreviews = await Promise.all(previewPromises);

    if (errors.length > 0) {
      setError(errors.join(' '));
    }

    setSelectedFiles(prevFiles => [...prevFiles, ...filesToAdd]);
    setFilePreviews(prevPreviews => [...prevPreviews, ...newPreviews]);
  };

  const handlePredict = async () => {
    if (selectedFiles.length === 0) {
      setError('Please select files to analyze.')
      return
    }

    setIsLoading(true)
    setProcessingResults([])
    setError(null)
    setSelectedResult(null)

    const initialResults = selectedFiles.map(fileItem => ({
      fileName: fileItem.file.name,
      id: fileItem.id,
      imageUrl: null,
      predictions: null,
      imageDimensions: null,
      report: null,
      error: null,
      isLoading: true
    }))
    setProcessingResults(initialResults)

    const processingPromises = selectedFiles.map(async (fileItem) => {
      const formData = new FormData()
      formData.append('file', fileItem.file)
      let result = initialResults.find(r => r.id === fileItem.id) || { id: fileItem.id, fileName: fileItem.file.name, isLoading: true }; 

      try {
        const response = await fetch(`http://localhost:8000/api/predict`, {
          method: 'POST',
          body: formData
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}))
          throw new Error(errorData.detail || 'Failed to analyze file')
        }

        const data = await response.json()
        result = { 
          ...result, 
          imageUrl: `http://localhost:8000${data.png_url}`, 
          predictions: data.predictions, 
          imageDimensions: data.image_dimensions, 
          report: data.report, 
          isLoading: false 
        }
      } catch (error) {
        console.error(`Error processing ${fileItem.file.name}:`, error)
        result = { ...result, error: error.message || 'Error processing file.', isLoading: false }
      } finally {
        // Update the specific file's result in the state
        setProcessingResults(currentResults =>
          currentResults.map(item => (item.id === fileItem.id ? result : item))
        )
      }
      return result; // Return the final result for this file
    })


    const results = await Promise.all(processingPromises)

    if (results.length > 0) {
      setSelectedResult(results[0])
    }

    setIsLoading(false);
  }

  const handleCloseError = () => {
    setError(null);
    if (errorTimeout) {
      clearTimeout(errorTimeout);
      setErrorTimeout(null);
    }
  };

  const handleRemoveFile = (idToRemove) => {
    setSelectedFiles(prevFiles => prevFiles.filter(fileItem => fileItem.id !== idToRemove));
    setFilePreviews(prevPreviews => prevPreviews.filter(previewItem => previewItem.id !== idToRemove));
    setProcessingResults(prevResults => prevResults.filter(resultItem => resultItem.id !== idToRemove));
    setSelectedResult(null);
  };

  const renderBoundingBoxes = (predictions, imageElement, imageDimensions) => {
    if (!predictions || !imageElement || !imageDimensions || !imageDimensions.width || !imageDimensions.height) return null

    const imageSize = { width: imageElement.offsetWidth, height: imageElement.offsetHeight }
    // Calculate scale based on rendered image size and original image dimensions
    const scaleX = imageSize.width / imageDimensions.width;
    const scaleY = imageSize.height / imageDimensions.height;

    return predictions.map((prediction, index) => {
      const { x, y, width, height, class: className, confidence } = prediction
      // Calculate top-left coordinates from center coordinates
      const boxLeft = (x - width / 2) * scaleX;
      const boxTop = (y - height / 2) * scaleY;
      const boxWidth = width * scaleX;
      const boxHeight = height * scaleY;

      return (
        <div
          key={index}
          className="bounding-box"
          style={{ left: `${boxLeft}px`, top: `${boxTop}px`, width: `${boxWidth}px`, height: `${boxHeight}px` }}
        >
          <div className="bounding-box-label">
            {className} - {Math.round(confidence * 100)}%
          </div>
        </div>
      )
    })
  }

  return (
    <div className="outside-container" style={{height: '100vh', display: 'flex', flexDirection: 'column'}}>
      <header style={{padding: '1rem', textAlign: 'center', fontWeight: 'bold', fontSize: '2rem'}}>
        DentoScan
        <p style={{margin: 0, fontSize: '1rem', fontWeight: 'normal', color: '#6200ea'}}>Powered by ROBOFLOW and GEMINI</p>
      </header>
      <div className="app-container" style={{flex: 1, display: 'flex', overflow: 'hidden'}}>
        <Snackbar 
          open={!!error} 
          autoHideDuration={6000} 
          onClose={handleCloseError}
          anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        >
          <Alert onClose={handleCloseError} severity="error" sx={{ width: '100%' }}>
            {error}
          </Alert>
        </Snackbar>

        <div className="image-panel panel" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          <Typography variant="h5" className="title" style={{ flexShrink: 1 }}>
            Dental X-ray Viewer
          </Typography>
          
          <div className="upload-area" onClick={() => document.getElementById('fileInput')?.click()} style={{ flexShrink: 1 }}>
            <input
              id="fileInput"
              type="file"
              multiple
              accept={SUPPORTED_FORMATS.join(',')}
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
            <CloudUploadIcon className="upload-icon" />
            <Typography variant="body1" className="upload-text">
              Click to select X-ray image(s) ({SUPPORTED_FORMATS.join(', ')})
            </Typography>
            <Typography variant="caption" color="textSecondary">
              Maximum file size: 50MB per file
            </Typography>
          </div>

          {filePreviews.length > 0 && (
            <aside className="selected-files-previews" style={{ flexShrink: 1 }}>
              <Typography variant="h6">Selected Files:</Typography>
              <div className="previews-container">
                {filePreviews.map((preview) => (
                  <div 
                    key={preview.id} 
                    className={`file-preview-item ${selectedResult?.id === preview.id ? 'selected' : ''}`}
                    onClick={() => {
                      const result = processingResults.find(r => r.id === preview.id);
                      if (result) setSelectedResult(result);
                    }}
                  >
                    <div className="preview-content-container">
                      {preview.url ? (
                        <div style={{ position: 'relative' }}>
                          <img src={preview.url} alt={preview.fileName} className="preview-thumbnail" />
                          {selectedResult?.id === preview.id && selectedResult.predictions && selectedResult.imageDimensions && (
                            {/* Bounding boxes are rendered on the main image preview below */}
                          )}
                        </div>
                      ) : (
                        <div className="preview-placeholder">
                          <Typography variant="caption">{preview.fileName}</Typography>
                          <Typography variant="caption">(Preview N/A)</Typography>
                        </div>
                      )}
                      <button
                        className="remove-file-button"
                        onClick={(event) => {
                          event.stopPropagation();
                          handleRemoveFile(preview.id);
                        }}
                      >
                        <CloseIcon fontSize="small" />
                      </button>
                    </div>
                    <Typography variant="caption">{preview.fileName}</Typography>
                  </div>
                ))}
              </div>
            </aside>
          )}

          <button
            className="predict-button"
            onClick={handlePredict}
            disabled={selectedFiles.length === 0 || isLoading}
            style={{ flexShrink: 1 }}
          >
            {isLoading ? <CircularProgress size={24} color="inherit" /> : 'Analyze X-ray'}
          </button>

          {/* Display all Roboflow processed images with bounding boxes below the analyze button */}
          {processingResults.length > 0 && (
            <div className="all-images-container" style={{ 
              marginTop: '20px', 
              display: 'flex', 
              flexDirection: 'column',
              gap: '20px', 
              overflowY: 'auto', 
              maxHeight: '600px', 
              paddingRight: '10px',
              border: '1px solid #ddd',
              borderRadius: '8px',
              flex: '0 0 50%'
            }}>
              {processingResults.map((result) => (
                result.imageUrl && !result.error && (
                  <div key={result.id} className="image-preview" style={{ 
                    position: 'relative', 
                    minWidth: '400px', 
                    height: '100%', 
                    border: '1px solid #ccc', 
                    borderRadius: '8px', 
                    overflow: 'hidden',
                    flexShrink: 0
                  }}>
                    <ImageWithBoundingBoxes
                      imageUrl={result.imageUrl}
                      predictions={result.predictions}
                      imageDimensions={result.imageDimensions}
                    />
                  </div>
                )
              ))}
            </div>
          )}
          {(processingResults.length > 0 || selectedFiles.length > 0) && (
            <div style={{ paddingTop: '20px', textAlign: 'center' }}>
              <button
                onClick={() => {
                  setSelectedFiles([]);
                  setFilePreviews([]);
                  setProcessingResults([]);
                  setSelectedResult(null);
                  window.location.reload();
                }}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#6200ea',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '16px',
                  width: '100%',
                  maxWidth: '300px',
                }}
              >
                Reanalyze
              </button>
            </div>
          )}

          {selectedResult && selectedResult.error && ( !selectedResult.isLoading &&
            <Alert severity="error" sx={{ marginTop: '20px' }}>{selectedResult.error}</Alert>
          )}

          {selectedResult && selectedResult.isLoading && ( !selectedResult.error &&
            <div className="loading-container" style={{ marginTop: '20px' }}>
              <CircularProgress size={24} />
              <Typography variant="body2">Analyzing...</Typography>
            </div>
          )}

        </div>

        <div className="report-panel panel">
          <Typography variant="h5" className="title">
            Diagnostic Report
          </Typography>
          
          <div className="report-content">
            {processingResults.length === 0 ? (
              <Typography variant="body1" className="report-text">
                Select and analyze X-ray images to view diagnostic reports.
              </Typography>
            ) : (
              processingResults.map((result) => (
                <Paper 
                  key={result.id} 
                  elevation={3} 
                  sx={{
                    padding: '20px', 
                    marginBottom: '20px',
                    backgroundColor: selectedResult?.id === result.id ? '#f0e6ff' : 'white'
                  }}
                  onClick={() => setSelectedResult(result)}
                >
                  <Typography variant="h6">{result.fileName}</Typography>
                  {result.isLoading ? (
                    <div className="loading-container">
                      <CircularProgress size={24} />
                      <Typography variant="body2">Processing...</Typography>
                    </div>
                  ) : result.error ? (
                    <Alert severity="error">{result.error}</Alert>
                  ) : (
                    <>
                      <Typography variant="body1" className="report-text" style={{ whiteSpace: 'pre-wrap' }}>
                        {result.report}
                      </Typography>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          const element = document.createElement("a");
                          const file = new Blob([result.report], { type: "text/plain" });
                          element.href = URL.createObjectURL(file);
                          element.download = `${result.fileName || 'diagnostic_report'}.txt`;
                          document.body.appendChild(element);
                          element.click();
                          document.body.removeChild(element);
                        }}
                        style={{
                          marginTop: '10px',
                          padding: '6px 12px',
                          backgroundColor: '#6200ea',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                        }}
                      >
                        Download Report
                      </button>
                    </>
                  )}
                </Paper>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}


export default App;
