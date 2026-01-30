import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './Analyze.css';

// Use environment variable or fallback to localhost
// Use environment variable or fallback to 127.0.0.1 to avoid localhost IPv6 issues
const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:5000';

const Analyze = () => {
  const [video, setVideo] = useState(null);
  const [videoName, setVideoName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const navigate = useNavigate();

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    setError(null);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setVideo(file);
      setVideoName(file.name);
    }
  };

  const handleChange = (e) => {
    setError(null);
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setVideo(file);
      setVideoName(file.name);
    }
  };

  const handleAnalyze = async () => {
    if (!video) return;

    setLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append("video", video);

    try {
      // 1. Submit Job
      // 1. Submit Job
      // Note: Do NOT set Content-Type header manually for FormData; Axios handles it.
      const response = await axios.post(`${API_URL}/analyze_full_video`, formData);

      const { job_id } = response.data;

      // 2. Poll Status
      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await axios.get(`${API_URL}/status/${job_id}`);
          const { status, result, error: jobError, progress } = statusRes.data;

          if (status === 'completed') {
            clearInterval(pollInterval);
            navigate('/results', { state: { data: result } });
          } else if (status === 'failed') {
            clearInterval(pollInterval);
            setLoading(false);
            setError(jobError || 'Analysis failed unexpectedly.');
          } else {
            // Optional: Update loading UI with progress if you add state for it
            console.log(`Processing: ${progress}%`);
          }
        } catch (pollErr) {
          clearInterval(pollInterval);
          setLoading(false);
          setError('Network error while checking status');
        }
      }, 2000); // Check every 2s

    } catch (err) {
      console.error(err);
      const errorMessage = err.response?.data?.message ||
        err.message ||
        'Submission failed. Please try again.';
      setError(errorMessage);
      setLoading(false);
    }
  };

  return (
    <div className="analyze-page">
      <AnimatePresence mode="wait">
        {!loading ? (
          <motion.div
            key="upload"
            className="upload-container"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.5 }}
          >
            <h1 className="analyze-title">Share Your Moment</h1>
            <p className="analyze-subtitle">Upload a video to begin your emotional journey</p>

            <motion.div
              className={`dropzone ${dragActive ? 'active' : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              whileHover={{ scale: 1.02 }}
            >
              <input
                type="file"
                accept="video/*"
                onChange={handleChange}
                id="file-input"
                style={{ display: 'none' }}
              />
              <label htmlFor="file-input" className="dropzone-label">
                <motion.div
                  className="upload-icon"
                  animate={{ y: [0, -10, 0] }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  📹
                </motion.div>
                <p>{videoName || 'Drop your video here or click to browse'}</p>
              </label>
            </motion.div>

            <motion.button
              className="analyze-button"
              onClick={handleAnalyze}
              disabled={!video}
              whileHover={{ scale: video ? 1.05 : 1 }}
              whileTap={{ scale: video ? 0.95 : 1 }}
            >
              Begin Analysis
            </motion.button>

            {error && (
              <motion.div
                className="error-toast"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                style={{
                  marginTop: '1rem',
                  padding: '1rem 1.5rem',
                  background: 'rgba(239, 68, 68, 0.15)',
                  border: '1px solid rgba(239, 68, 68, 0.4)',
                  borderRadius: '12px',
                  color: '#fca5a5',
                  textAlign: 'center'
                }}
              >
                <span style={{ marginRight: '0.5rem' }}>⚠️</span>
                {error}
              </motion.div>
            )}
          </motion.div>
        ) : (
          <motion.div
            key="processing"
            className="processing-container"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="breathing-circle"
              animate={{
                scale: [1, 1.2, 1],
                opacity: [0.5, 0.8, 0.5]
              }}
              transition={{ duration: 2, repeat: Infinity }}
            />
            <h2>MIRO is listening...</h2>
            <p>Analyzing your emotions across multiple dimensions</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Analyze;
