import React, { useState } from 'react';
import './App.css';
import UploadZone from './components/UploadZone';

function App() {
  const [file, setFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [resultReady, setResultReady] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  const handleUpload = async (selectedFile) => {
    setFile(selectedFile);
    setIsProcessing(true);
    setResultReady(false);
    setErrorMsg(null);

    // Prepare FormData
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      // The backend expects the file at this endpoint
      // Using localhost for local execution
      const response = await fetch('http://localhost:8000/api/convert-to-stl', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Conversion failed. Please check the image or backend connection.');
      }

      // Convert response to Blob for downloading
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      
      // Artificial delay for premium feel
      setTimeout(() => {
        setDownloadUrl(url);
        setIsProcessing(false);
        setResultReady(true);
      }, 1500);

    } catch (error) {
      console.error(error);
      setIsProcessing(false);
      setErrorMsg(error.message);
    }
  };

  const resetState = () => {
    setFile(null);
    setResultReady(false);
    setDownloadUrl(null);
    setErrorMsg(null);
  };

  return (
    <>
      <div className="bg-gradient-mesh"></div>
      
      <main className="app-container">
        <header className="app-header text-center">
          <div className="badge glass">AI-Powered</div>
          <h1 className="title">Image to <span className="text-gradient">SOLIDWORKS Part</span></h1>
          <p className="subtitle">Convert any image into a true 3D Solid Model (.stl) instantly.</p>
        </header>

        <section className="main-content glass">
          {!isProcessing && !resultReady && (
            <UploadZone onUpload={handleUpload} error={errorMsg} />
          )}

          {isProcessing && (
            <div className="processing-state">
              <div className="loader-container">
                <div className="spinner"></div>
                <div className="spinner-glow"></div>
              </div>
              <h3>Analyzing Image Features...</h3>
              <p className="text-muted">Extracting edges and generating vector paths.</p>
            </div>
          )}

          {resultReady && (
            <div className="result-state">
              <div className="success-icon">✓</div>
              <h3>Conversion Complete!</h3>
              <p className="text-muted">Your 3D Part file is ready! Import it into SOLIDWORKS as a Solid Body to create Drawings from it.</p>
              
              <div className="action-buttons">
                <a href={downloadUrl} download="engineering_part.stl" className="btn btn-primary">
                  Download 3D Part (.stl)
                </a>
                <button onClick={resetState} className="btn btn-secondary glass">
                  Convert Another
                </button>
              </div>
            </div>
          )}
        </section>

        <footer className="app-footer text-muted">
          <p>This conversion traces pixels and extrudes them into a solid 3D part.</p>
        </footer>
      </main>
    </>
  );
}

export default App;
