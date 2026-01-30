import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './Analyze.css';

// Use environment variable or fallback to 127.0.0.1
const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:5000';

// State display configuration
const STATE_MESSAGES = {
  JOB_STARTED: { text: 'Starting analysis...', icon: '🚀' },
  EXTRACTION_COMPLETE: { text: 'Audio extracted', icon: '🎵' },
  FACE_READY: { text: 'Face analyzed', icon: '😊' },
  AUDIO_READY: { text: 'Voice analyzed', icon: '🎤' },
  TRANSCRIPT_READY: { text: 'Speech transcribed', icon: '📝' },
  PRIMARY_EMOTION_READY: { text: 'Primary emotion detected', icon: '💭' },
  INCONGRUENCE_READY: { text: 'Analyzing patterns...', icon: '🔍' },
  THERAPEUTIC_RESPONSE_READY: { text: 'Generating insights...', icon: '💡' },
  JOB_COMPLETE: { text: 'Analysis complete!', icon: '✅' },
};

const Analyze = () => {
  const [video, setVideo] = useState(null);
  const [videoName, setVideoName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [currentState, setCurrentState] = useState(null);
  const [progress, setProgress] = useState(0);
  const [stateHistory, setStateHistory] = useState([]);
  const [partialResults, setPartialResults] = useState({});
  const [currentJobId, setCurrentJobId] = useState(null);
  const eventSourceRef = useRef(null);
  const navigate = useNavigate();

  // Cleanup EventSource on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

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

  const fetchAndNavigate = async (jobId) => {
    try {
      setLoading(true); // Ensure loading stays true while fetching
      const resultRes = await axios.get(`${API_URL}/status/${jobId}`);
      if (resultRes.data.result) {
        navigate('/results', { state: { data: resultRes.data.result } });
      } else {
        setError('Result not fully ready yet. Please wait...');
        // If getting here, maybe waiting a bit and retrying or letting user click button is best
        setLoading(false); // Let them click button
      }
    } catch (fetchErr) {
      console.error("Fetch error:", fetchErr);
      setError('Failed to fetch results. Keep the page open.');
      setLoading(false);
    }
  };

  const handleStateUpdate = (data) => {
    const { state, payload, progress_percent } = data;

    setCurrentState(state);
    setProgress(progress_percent || 0);
    setStateHistory(prev => [...prev, { state, timestamp: new Date().toISOString() }]);

    if (payload) {
      setPartialResults(prev => ({ ...prev, [state]: payload }));
    }

    console.log(`[SSE] ${state}: ${progress_percent}%`);
  };

  const handleAnalyze = async () => {
    if (!video) return;

    setLoading(true);
    setError(null);
    setCurrentState(null);
    setProgress(0);
    setStateHistory([]);
    setPartialResults({});
    setCurrentJobId(null);

    const formData = new FormData();
    formData.append("video", video);

    try {
      // 1. Submit Job
      const response = await axios.post(`${API_URL}/analyze_full_video`, formData);
      const { job_id, stream_url } = response.data;
      setCurrentJobId(job_id);

      // 2. Connect to SSE Stream
      const sseUrl = `${API_URL}${stream_url || `/stream/${job_id}`}`;
      console.log(`[SSE] Connecting to ${sseUrl}`);

      const eventSource = new EventSource(sseUrl);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        console.log('[SSE] Connection established');
      };

      eventSource.addEventListener('connected', (event) => {
        console.log('[SSE] Connected event:', event.data);
      });

      eventSource.addEventListener('state_update', (event) => {
        try {
          const data = JSON.parse(event.data);
          handleStateUpdate(data);

          // Aggressive check: if job complete, try to close and fetch 
          if (data.state === 'JOB_COMPLETE') {
            eventSource.close();
            // Small delay to ensure DB consistency if needed, then fetch
            setTimeout(() => fetchAndNavigate(job_id), 500);
          }
        } catch (e) {
          console.error('[SSE] Parse error:', e);
        }
      });

      eventSource.addEventListener('complete', async (event) => {
        console.log('[SSE] Complete event received');
        eventSource.close();
        fetchAndNavigate(job_id);
      });

      eventSource.addEventListener('error', (event) => {
        console.log('[SSE] Error event:', event.data);
      });

      eventSource.onerror = (err) => {
        console.error('[SSE] Connection error:', err);
        eventSource.close();

        // Fall back to polling if SSE fails
        console.log('[SSE] Falling back to polling...');
        fallbackToPolling(job_id);
      };

    } catch (err) {
      console.error(err);
      const errorMessage = err.response?.data?.message ||
        err.message ||
        'Submission failed. Please try again.';
      setError(errorMessage);
      setLoading(false);
    }
  };

  // Fallback polling for browsers that don't support SSE well
  const fallbackToPolling = async (jobId) => {
    const pollInterval = setInterval(async () => {
      try {
        const statusRes = await axios.get(`${API_URL}/status/${jobId}`);
        const { status, result, error: jobError, progress_percent, latest_state } = statusRes.data;

        if (latest_state) {
          setCurrentState(latest_state);
        }
        if (progress_percent) {
          setProgress(progress_percent);
        }

        if (status === 'completed') {
          clearInterval(pollInterval);
          navigate('/results', { state: { data: result } });
        } else if (status === 'failed') {
          clearInterval(pollInterval);
          setLoading(false);
          setError(jobError || 'Analysis failed unexpectedly.');
        }
      } catch (pollErr) {
        clearInterval(pollInterval);
        setLoading(false);
        setError('Network error while checking status');
      }
    }, 2000);
  };

  const getStateDisplay = () => {
    if (!currentState) return { text: 'Preparing...', icon: '⏳' };
    return STATE_MESSAGES[currentState] || { text: currentState, icon: '⚙️' };
  };

  const stateDisplay = getStateDisplay();

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

            {/* Current State Display */}
            <motion.div
              className="state-indicator"
              key={currentState}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}
            >
              {stateDisplay.icon}
            </motion.div>

            <h2>{stateDisplay.text}</h2>

            {/* Progress Bar */}
            <div style={{
              width: '80%',
              maxWidth: '300px',
              height: '6px',
              background: 'rgba(255,255,255,0.1)',
              borderRadius: '3px',
              marginTop: '1.5rem',
              overflow: 'hidden'
            }}>
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.3 }}
                style={{
                  height: '100%',
                  background: 'linear-gradient(90deg, #818cf8, #c084fc)',
                  borderRadius: '3px'
                }}
              />
            </div>
            <p style={{ marginTop: '0.5rem', opacity: 0.7 }}>{progress}%</p>

            {/* Manual Navigation Button (Fallback) */}
            {(currentState === 'JOB_COMPLETE' || progress === 100) && (
              <motion.button
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                onClick={() => fetchAndNavigate(currentJobId)}
                style={{
                  marginTop: '2rem',
                  padding: '1rem 2.5rem',
                  background: '#10B981',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '50px',
                  fontSize: '1.1rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  boxShadow: '0 4px 15px rgba(16, 185, 129, 0.4)'
                }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                See Results ✨
              </motion.button>
            )}

            {/* State History (compact) */}
            <div style={{
              marginTop: '2rem',
              display: 'flex',
              gap: '0.5rem',
              flexWrap: 'wrap',
              justifyContent: 'center',
              maxWidth: '300px'
            }}>
              {stateHistory.slice(-5).map((item, idx) => (
                <motion.span
                  key={idx}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 0.6, scale: 1 }}
                  style={{ fontSize: '1rem' }}
                >
                  {STATE_MESSAGES[item.state]?.icon || '⚙️'}
                </motion.span>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Analyze;

