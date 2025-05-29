import React from 'react';
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch';

const ZoomPanWrapper = ({ children }) => {
  return (
    <TransformWrapper
      wheel={{ disabled: true }}
      doubleClick={{ disabled: true }}
      pinch={{ disabled: true }}
      pan={{ disabled: false }}
      zoomIn={{ step: 0.1 }}
      zoomOut={{ step: 0.1 }}
      minScale={0.5}
      maxScale={4}
      centerOnInit={true}
      onZoomStop={(ref) => {
        // You can add any callback here if needed
      }}
      onPanningStop={(ref) => {
        // You can add any callback here if needed
      }}
      options={{
        limitToBounds: true,
        transformEnabled: true,
      }}
    >
      {({ zoomIn, zoomOut, resetTransform, ...rest }) => (
        <>
          <div style={{ marginBottom: '10px' }}>
            <button onClick={zoomIn}>Zoom In</button>
            <button onClick={zoomOut}>Zoom Out</button>
            <button onClick={resetTransform}>Reset</button>
          </div>
          <TransformComponent>
            {children}
          </TransformComponent>
        </>
      )}
    </TransformWrapper>
  );
};

export default ZoomPanWrapper;
