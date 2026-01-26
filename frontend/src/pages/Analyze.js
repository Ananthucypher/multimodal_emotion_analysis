import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './Analyze.css';

const Analyze = () => {
  const [video, setVideo] = useState(null);
  const [videoName, setVideoName] = useState('');
  const [loading, setLoading] = useState(false);
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

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setVideo(file);
      setVideoName(file.name);
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setVideo(file);
      setVideoName(file.name);
    }
  };

  const handleAnalyze = async () => {
    if (!video) return;

    setLoading(true);
    const formData = new FormData();
    formData.append("video", video);

    try {
      const response = await axios.post("http://127.0.0.1:5000/analyze_full_video", formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      navigate('/results', { state: { data: response.data } });
    } catch (error) {
      console.error(error);
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
