import React, { useRef, useState, useEffect } from 'react';
import './ImageWithBoundingBoxes.css';

const ImageWithBoundingBoxes = ({ imageUrl, predictions, imageDimensions }) => {
  const containerRef = useRef(null);
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 });

  const handleImageLoad = (event) => {
    const { naturalWidth, naturalHeight } = event.target;
    const containerWidth = containerRef.current ? containerRef.current.clientWidth : naturalWidth;
    const scaleFactor = containerWidth / naturalWidth;
    const scaledHeight = naturalHeight * scaleFactor;
    setImageSize({ width: containerWidth, height: scaledHeight, naturalWidth, naturalHeight });
  };

  useEffect(() => {
    console.log('Image Size:', imageSize);
    console.log('Image Dimensions from backend:', imageDimensions);
    console.log('Predictions:', predictions);
  }, [imageSize, imageDimensions, predictions]);

  if (!imageUrl) return null;

  const scaleX = imageSize.width && imageDimensions?.width ? imageSize.width / imageDimensions.width : 1;
  const scaleY = imageSize.height && imageDimensions?.height ? imageSize.height / imageDimensions.height : 1;

  return (
    <div
      ref={containerRef}
      style={{
        position: 'relative',
        display: 'inline-block',
        width: '100%',
        maxWidth: '600px',
        height: imageSize.height || 'auto',
        border: '1px solid #ccc',
        boxSizing: 'border-box',
      }}
    >
      <img
        src={imageUrl}
        alt="Processed X-ray"
        style={{ display: 'block', width: '100%', height: 'auto' }}
        onLoad={handleImageLoad}
      />
      {predictions &&
        predictions.map((prediction, index) => {
          const { x, y, width, height, class: className, confidence } = prediction;
          const boxLeft = (x - width / 2) * scaleX;
          const boxTop = (y - height / 2) * scaleY;
          const boxWidth = width * scaleX;
          const boxHeight = height * scaleY;

          let color = 'lime';
          if (className.toLowerCase() === 'cavity') color = 'red';
          else if (className.toLowerCase() === 'periapical lesion') color = 'blue';

          return (
            <div
              key={index}
              className="bounding-box"
              style={{
                position: 'absolute',
                left: boxLeft,
                top: boxTop,
                width: boxWidth,
                height: boxHeight,
                border: `2px solid ${color}`,
                boxSizing: 'border-box',
                pointerEvents: 'none',
              }}
            >
              <div
                className="bounding-box-label"
                style={{
                  backgroundColor: color,
                  color: 'white',
                  fontSize: '12px',
                  padding: '2px 4px',
                  position: 'absolute',
                  top: '-20px',
                  left: 0,
                  whiteSpace: 'nowrap',
                  pointerEvents: 'auto',
                }}
              >
                {className} - {Math.round(confidence * 100)}%
              </div>
            </div>
          );
        })}
    </div>
  );
};

export default ImageWithBoundingBoxes;
