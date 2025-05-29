import React, { useState } from 'react';

const DiagnosticReport = ({ report }) => {
  const [showReport, setShowReport] = useState(false);

  const handleDownload = () => {
    const element = document.createElement("a");
    const file = new Blob([report], { type: "text/plain" });
    element.href = URL.createObjectURL(file);
    element.download = "diagnostic_report.txt";
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div style={{ padding: '1rem', border: '1px solid #ccc', borderRadius: '8px' }}>
      <button onClick={() => setShowReport(!showReport)} style={{ marginBottom: '1rem' }}>
        {showReport ? 'Hide' : 'Show'} Diagnostic Report
      </button>
      {showReport && (
        <div style={{ whiteSpace: 'pre-wrap', backgroundColor: '#f9f9f9', padding: '1rem', borderRadius: '4px', maxHeight: '300px', overflowY: 'auto' }}>
          {report}
        </div>
      )}
      <button onClick={handleDownload} style={{ marginTop: '1rem' }}>
        Download Report
      </button>
    </div>
  );
};

export default DiagnosticReport;
