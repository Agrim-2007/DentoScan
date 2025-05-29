import React, { useEffect, useRef, useState } from 'react';
import cornerstone from 'cornerstone-core';
import cornerstoneWADOImageLoader from 'cornerstone-wado-image-loader';

cornerstoneWADOImageLoader.external.cornerstone = cornerstone;

// Configure the web worker for WADO image loader
cornerstoneWADOImageLoader.webWorkerManager.initialize({
  maxWebWorkers: navigator.hardwareConcurrency || 1,
  startWebWorkersOnDemand: true,
  webWorkerPath: '/cornerstoneWADOImageLoaderWebWorker.js',
  taskConfiguration: {
    decodeTask: {
      codecsPath: '/cornerstoneWADOImageLoaderCodecs.js',
    },
  },
});

const DicomViewer = ({ imageId, predictions, imageDimensions }) => {
  const elementRef = useRef(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    setError(null);

    try {
      cornerstone.enable(element);

    // Ensure imageId has wadouri: prefix for HTTP URLs
    let formattedImageId = imageId;
    if (imageId && !imageId.startsWith('wadouri:')) {
      formattedImageId = 'wadouri:' + imageId;
    }

    cornerstone.loadImage(formattedImageId).then(image => {
        cornerstone.displayImage(element, image);

        // Draw bounding boxes overlay
        const canvas = element.querySelector('canvas');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const { width: imageWidth, height: imageHeight } = imageDimensions || {};
        const scaleX = canvas.width / imageWidth;
        const scaleY = canvas.height / imageHeight;

        ctx.lineWidth = 2;
        ctx.font = '14px Arial';
        ctx.textBaseline = 'top';

        predictions.forEach(prediction => {
          const { x, y, width, height, class: className, confidence } = prediction;
          const boxLeft = (x - width / 2) * scaleX;
          const boxTop = (y - height / 2) * scaleY;
          const boxWidth = width * scaleX;
          const boxHeight = height * scaleY;

          let color = 'lime';
          if (className.toLowerCase() === 'cavity') color = 'red';
          else if (className.toLowerCase() === 'periapical lesion') color = 'blue';

          ctx.strokeStyle = color;
          ctx.fillStyle = color;

          ctx.strokeRect(boxLeft, boxTop, boxWidth, boxHeight);

          const label = className + ' - ' + Math.round(confidence * 100) + '%';
          const textWidth = ctx.measureText(label).width;
          const textHeight = 18;
          ctx.fillRect(boxLeft, boxTop - textHeight, textWidth + 6, textHeight);

          ctx.fillStyle = 'white';
          ctx.fillText(label, boxLeft + 3, boxTop - textHeight + 2);
        });
      }).catch(err => {
        setError('Failed to load DICOM image.');
        console.error(err);
      });
    } catch (err) {
      setError('Error initializing DICOM viewer.');
      console.error(err);
    }

    return () => {
      if (element) {
        cornerstone.disable(element);
      }
    };
  }, [imageId, predictions, imageDimensions]);

  if (error) {
    return <div style={{ color: 'red', padding: '10px' }}>Error: {error}</div>;
  }

  return (
    <div
      ref={elementRef}
      style={{ width: '100%', height: '600px', position: 'relative', border: '1px solid #ccc', borderRadius: '8px' }}
    ></div>
  );
};

export default DicomViewer;
