import React, { useRef, useState, useEffect } from 'react';
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch';

const ImageWithBoundingBoxes = ({ imageUrl, predictions, imageDimensions }) => {
  const containerRef = useRef(null);
  const imageRef = useRef(null);
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 });
  const [zoomEnabled, setZoomEnabled] = useState(false);

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

  if (!imageUrl || !imageDimensions?.width || !imageDimensions?.height) return null;

  const scaleX = imageSize.width / imageDimensions.width;
  const scaleY = imageSize.height / imageDimensions.height;

  const toggleZoom = () => {
    setZoomEnabled(!zoomEnabled);
  };

  return (
    <div
      ref={containerRef}
      style={{
        position: 'relative',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        width: '100%',
        maxWidth: '400px', // Smaller max width for the image
        height: 'auto',
        border: '1px solid #ccc',
        boxSizing: 'border-box',
        overflowY: 'auto',
        overflowX: 'hidden',
        cursor: zoomEnabled ? 'grab' : 'default',
      }}
      onClick={toggleZoom}
    >
      <TransformWrapper
        wheel={{ step: 0.1 }}
        doubleClick={{ disabled: true }}
        pinch={{ step: 5 }}
        minScale={0.5}
        maxScale={5}
        disabled={!zoomEnabled}
        wheelActivationKeys={[]}
        panningActivationKey=" "
      >
        <TransformComponent>
          <div style={{ position: 'relative', width: '100%' }}>
            <img
              ref={imageRef}
              src={imageUrl}
              alt="Processed X-ray"
              style={{ display: 'block', width: '100%', height: 'auto' }}
              onLoad={handleImageLoad}
            />
            {predictions?.map((prediction, index) => {
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
                    left: `${boxLeft}px`,
                    top: `${boxTop}px`,
                    width: `${boxWidth}px`,
                    height: `${boxHeight}px`,
                    border: `2px solid ${color}`,
                    boxSizing: 'border-box',
                    pointerEvents: 'none',
                    backgroundColor: 'transparent',
                  }}
                >
                  <div
                    className="bounding-box-label"
                    style={{
                      backgroundColor: 'transparent', // unchanged
                      color: 'black', // unchanged
                      fontWeight: 'normal',
                      fontSize: '12px',
                      padding: '2px 4px',
                      position: 'absolute',
                      top: '110%',
                      left: -10,
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
        </TransformComponent>
      </TransformWrapper>
    </div>
  );
};

export default ImageWithBoundingBoxes;
