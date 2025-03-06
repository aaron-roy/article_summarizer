import React, { useState, useRef } from 'react';
import axios from 'axios';
import ChatAssistant from './ChatAssistant';
import ArticleCarousel from './ArticleCarousel';

// Create an axios instance with the base URL
const api = axios.create({
  baseURL: 'http://127.0.0.1:8000', 
});

function FileProcessor() {
  const [fileName, setFileName] = useState('Drag and drop a file here, or click to select');
  const [file, setFile] = useState(null);
  const [fileId, setFileId] = useState(null);
  const [status, setStatus] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [downloadUrl, setDownloadUrl] = useState(null);
  const [processingMessage, setProcessingMessage] = useState('');

  // Create a reference for the file input
  const fileInputRef = useRef(null);

  // Reset all states to start over
  const resetProcessing = () => {
    setFileName('Drag and drop a file here, or click to select');
    setFile(null);
    setFileId(null);
    setStatus(null);
    setIsUploading(false);
    setIsProcessing(false);
    setError(null);
    setDownloadUrl(null);
    setProcessingMessage('');
    
    // Reset the file input field
    if (fileInputRef.current) {
      fileInputRef.current.value = '';  // This clears the selected file
    }
  };

  // Handle file selection
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      if (selectedFile.type === 'text/csv' || selectedFile.name.endsWith('.csv') || 
          selectedFile.type === 'application/vnd.ms-excel' || selectedFile.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' || 
          selectedFile.name.endsWith('.xls') || selectedFile.name.endsWith('.xlsx')) {
        setFileName(selectedFile.name);
        setFile(selectedFile);
        setError(null);
        // Reset states when a new file is selected
        setFileId(null);
        setStatus(null);
        setDownloadUrl(null);
        setProcessingMessage('');
      } else {
        setError('Please select a CSV, XLS, or XLSX file');
        setFileName('Drag and drop a file here, or click to select');
        setFile(null);
      }
    }
  };

  // Upload file to server
  const uploadFile = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setIsUploading(true);
    setError(null);
    setProcessingMessage('Uploading file...');
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post('/process-file/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      if (response.data && response.data.file_id) {
        setFileId(response.data.file_id);
        setIsProcessing(true);
        setProcessingMessage(`File uploaded successfully with file_id: ${response.data.file_id}`);
        checkStatus(response.data.file_id);
      } else {
        setError('Invalid response from server: No file_id returned');
      }
    } catch (err) {
      setError(`Upload failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  // Check processing status
  const checkStatus = async (id) => {
    setProcessingMessage('Checking status...');
    
    try {
      const response = await api.get(`/status/${id}`);
      
      const currentStatus = response.data.status;
      setStatus(currentStatus);
      setProcessingMessage(`Current status: ${currentStatus}`);
      
      if (currentStatus === 'completed') {
        setIsProcessing(false);
        setDownloadUrl(`/download/${id}`);
        setProcessingMessage('Processing completed. You can now download the file.');
      } else {
        // If still processing, check again after 5 seconds
        setProcessingMessage('Processing not complete. Checking again in 5 seconds...');
        setTimeout(() => checkStatus(id), 5000);
      }
    } catch (err) {
      setIsProcessing(false);
      setError(`Failed to check status: ${err.response?.data?.detail || err.message}`);
    }
  };

  // Handle file download
  const downloadFile = async () => {
    if (downloadUrl) {
      try {
        setProcessingMessage('Downloading the processed file...');
        
        // Using a more controlled approach for the download
        const response = await api.get(downloadUrl, {
          responseType: 'blob', // Important for handling file downloads
        });
        
        // Create a URL for the blob
        const url = window.URL.createObjectURL(new Blob([response.data]));
        
        // Create a temporary link element and trigger the download
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `processed_${fileName}`);
        document.body.appendChild(link);
        link.click();
        
        // Clean up
        window.URL.revokeObjectURL(url);
        document.body.removeChild(link);
        
        setProcessingMessage('File downloaded successfully.');
      } catch (err) {
        setError(`Download failed: ${err.message}`);
      }
    }
  };

  // Handle drag and drop events
  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      if (droppedFile.type === 'text/csv' || droppedFile.name.endsWith('.csv') || 
          droppedFile.type === 'application/vnd.ms-excel' || droppedFile.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' || 
          droppedFile.name.endsWith('.xls') || droppedFile.name.endsWith('.xlsx')) {
        setFileName(droppedFile.name);
        setFile(droppedFile);
        setError(null);
        // Reset states when a new file is dropped
        setFileId(null);
        setStatus(null);
        setDownloadUrl(null);
        setProcessingMessage('');
      } else {
        setError('Please select a CSV, XLS, or XLSX file');
      }
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6 text-center">Article Summarizer</h1>
      
      {/* File Input Component */}
      <div className="mb-6">
        <div 
          className={`border-2 border-dashed ${error ? 'border-red-500' : 'border-blue-500'} rounded-lg p-8 text-center cursor-pointer`}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          <input 
            type="file" 
            accept=".csv, .xls, .xlsx"
            onChange={handleFileChange} 
            className="hidden"
            id="file-upload"
            ref={fileInputRef}  // Attach ref to the file input
          />
          <label htmlFor="file-upload" className="cursor-pointer text-blue-500 font-medium">
            {file ? fileName : 'Drag and drop a CSV, XLS, or XLSX file here, or click to select'}
          </label>
        </div>
        {error && <p className="text-red-500 mt-2">{error}</p>}
      </div>
    
      {/* Action Buttons */}
      <div className="flex justify-center gap-4 mb-6">
        <button
          onClick={uploadFile}
          disabled={!file || isUploading || isProcessing}
          className={`px-4 py-2 rounded font-medium ${!file || isUploading || isProcessing ? 'bg-gray-300 cursor-not-allowed' : 'bg-blue-500 text-white hover:bg-blue-600'}`}
        >
          {isUploading ? 'Uploading...' : 'Upload and Process'}
        </button>
        
        {downloadUrl && (
          <button
            onClick={downloadFile}
            className="px-4 py-2 bg-green-500 text-white rounded font-medium hover:bg-green-600"
          >
            Download Processed File
          </button>
        )}

        {/* Reset Button - visible after a file has been uploaded */}
        {fileId && (
          <button
            onClick={resetProcessing}
            className="px-4 py-2 bg-red-500 text-white rounded font-medium hover:bg-red-600"
          >
            Reset & Upload New File
          </button>
        )}
      </div>

      {fileId && status === 'completed' && (
        <div className="mt-8">
          <h2 className="text-xl font-bold mb-4">Ask Questions About Your Data</h2>
          <ArticleCarousel/>
        </div>
      )}
      
      {fileId && status === 'completed' && (
        <div className="mt-8">
          <h2 className="text-xl font-bold mb-4">Ask Questions About Your Data</h2>
          <ChatAssistant fileId={fileId} />
        </div>
      )}

<div className="my-4"/>

      {/* Status Display */}
      {(processingMessage || isProcessing || status) && (
        <div style={{ border: '1px solid #e0e0e0' }} className="border rounded-lg p-4 bg-gray-50">
          <h2 className="font-semibold mb-2">Processing Status</h2>
          
          {processingMessage && (
            <div className="mb-2">{processingMessage}</div>
          )}
          
          {isProcessing && (
            <div className="flex items-center text-blue-500 mt-2">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Processing...
            </div>
          )}
          
          {fileId && !isProcessing && status === 'completed' && (
            <div className="text-green-500 font-medium mt-2">
              ✓ Processing completed successfully!
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default FileProcessor;
