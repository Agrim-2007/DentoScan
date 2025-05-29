import React, { useRef, useState, useEffect } from 'react';
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch';
import './ImageWithBoundingBoxes.css';

const ImageWithBoundingBoxes = ({ imageUrl, predictions, imageDimensions }) => {
  const containerRef = useRef(null);
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

  if (!imageUrl) return null;

  const scaleX = imageSize.width && imageDimensions?.width ? imageSize.width / imageDimensions.width : 1;
  const scaleY = imageSize.height && imageDimensions?.height ? imageSize.height / imageDimensions.height : 1;

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
        maxWidth: '600px',
        maxHeight: '600px',
        height: '600px',
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
          <img
            src={imageUrl}
            alt="Processed X-ray"
            style={{ display: 'block', width: '90%', height: 'auto' }}
            onLoad={handleImageLoad}
          />
          {predictions &&
            predictions.map((prediction, index) => {
              const { x, y, width, height, class: className, confidence } = prediction;
              const boxLeft = (x - width / 2) * scaleX;
              const boxTop = (y - height / 2) * scaleY;
              const boxWidth = (width * scaleX) * 0.9;
              const boxHeight = (height * scaleY) * 0.9;

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
                    border: className.toLowerCase() === 'cavity' ? '2px solid rgba(255, 0, 0, 0.8)' : `2px solid ${color}`,
                    boxSizing: 'border-box',
                    pointerEvents: 'none',
                    backgroundColor: 'transparent',
                  }}
                >
                  <div
                    className="bounding-box-label"
                    style={{
                      backgroundColor: 'transparent',
                      color: 'black',
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
        </TransformComponent>
      </TransformWrapper>
    </div>
  );
};

export default ImageWithBoundingBoxes;
