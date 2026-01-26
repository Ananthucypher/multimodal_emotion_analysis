import React from 'react';
import { motion } from 'framer-motion';
import { useLocation, useNavigate } from 'react-router-dom';
import EmotionChart from '../components/EmotionChart'; // update path as needed

// You may also import this mapping from theme.js or define here
const emotionColors = {
  happy: '#10B981',
  sad: '#3B82F6',
  angry: '#EF4444',
  fear: '#8B5CF6',
  surprise: '#F59E0B',
  disgust: '#84CC16',
  neutral: '#6B7280'
};

const getEmotionGradient = (emotion) => {
  return emotionColors[emotion?.toLowerCase()] || emotionColors.neutral;
};

const Results = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const data = location.state?.data;

  if (!data) {
    navigate('/analyze');
    return null;
  }

  return (
    <motion.div
      className="results-page"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6 }}
      style={{ padding: '4rem 2rem', maxWidth: '1400px', margin: '0 auto' }}
    >
      {/* Overall Card */}
      <motion.div
        className="overall-card"
        style={{
          background: `linear-gradient(120deg, ${getEmotionGradient(data.overall_emotion?.overall_emotion)}70 0%, #fff 80%)`,
          color: '#222', // override as needed for light/dark theme
          borderRadius: 32,
          textAlign: 'center',
          marginBottom: '3rem',
          boxShadow: '0 10px 40px rgba(0,0,0,0.10)'
        }}
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.6 }}
      >
        <h2 style={{ fontSize: '1.4rem', opacity: 0.85 }}>The Overall Feeling</h2>
        <motion.div
          className="emotion-label"
          animate={{ scale: [1, 1.07, 1] }}
          transition={{ duration: 2, repeat: Infinity }}
          style={{ fontSize: '2.8rem', fontWeight: 800, margin: '1.2rem 0', textTransform: 'capitalize' }}
        >
          {data.overall_emotion?.overall_emotion}
        </motion.div>
        <div style={{ fontSize: '1.2rem', opacity: 0.85, marginBottom: 8 }}>
          {(data.overall_emotion?.confidence * 100).toFixed(1)}% Confidence
        </div>
        <p>{data.overall_emotion?.description}</p>
      </motion.div>

      {/* Modular Grid */}
      <div className="modules-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '2rem' }}>
        {/* Face Analysis */}
        <motion.div className="module-card"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h3>😊 Face Analysis</h3>
          <div className="emotion-chip"
            style={{
              display: 'inline-block',
              padding: '0.7rem 1.7rem',
              borderRadius: '50px',
              color: '#fff',
              background: getEmotionGradient(data.face_emotion_result?.dominant_face_emotion),
              fontWeight: 700,
              textTransform: 'capitalize',
              marginBottom: 16
            }}>
            {data.face_emotion_result?.dominant_face_emotion}
          </div>
          <EmotionChart emotionData={data.face_emotion_result?.frame_emotions} />
        </motion.div>

        {/* Audio Tone */}
        <motion.div className="module-card"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h3>🎵 Voice Tone</h3>
          <div className="emotion-chip"
            style={{
              display: 'inline-block',
              padding: '0.7rem 1.7rem',
              borderRadius: '50px',
              color: '#fff',
              background: getEmotionGradient(data.audio_tone_emotion?.predicted),
              fontWeight: 700,
              textTransform: 'capitalize',
              marginBottom: 16
            }}>
            {data.audio_tone_emotion?.predicted}
          </div>
          <EmotionChart emotionData={data.audio_tone_emotion?.probs} />
        </motion.div>

        {/* Speech Transcript */}
        <motion.div className="module-card"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h3>💬 Speech Transcript</h3>
          <div className="transcript-box"
            style={{
              background: '#F5F6FA',
              padding: '1.2rem',
              borderRadius: 13,
              minHeight: 90,
              color: '#333',
              fontStyle: 'italic'
            }}>
            {data.transcript || 'No speech detected'}
          </div>
        </motion.div>

        {/* Text Sentiment */}
        <motion.div className="module-card"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h3>🧠 Text Sentiment</h3>
          <div className="emotion-chip"
            style={{
              display: 'inline-block',
              padding: '0.7rem 1.7rem',
              borderRadius: '50px',
              color: '#fff',
              background: getEmotionGradient(data.transcript_sentiment?.primary_emotion),
              fontWeight: 700,
              textTransform: 'capitalize',
              marginBottom: 16
            }}>
            {data.transcript_sentiment?.primary_emotion}
          </div>
          <div style={{ color: emotionColors[data.transcript_sentiment?.primary_emotion], fontWeight: 600, margin: '10px 0' }}>
            {(data.transcript_sentiment?.score * 100).toFixed(1)}% Confidence
          </div>
          <p style={{ opacity: 0.85 }}>{data.transcript_sentiment?.description}</p>
        </motion.div>
      </div>

      {/* CTA */}
      <motion.button
        className="another-btn"
        onClick={() => navigate('/analyze')}
        whileHover={{ scale: 1.06 }}
        whileTap={{ scale: 0.96 }}
        style={{
          margin: '2.5rem auto 0 auto', display: 'block',
          background: '#10B981', color: '#fff', border: 'none',
          padding: '1.2rem 3rem', fontSize: '1.1rem', fontWeight: 600, borderRadius: 50, cursor: 'pointer'
        }}
      >
        Analyze Another Video
      </motion.button>
    </motion.div>
  );
};

export default Results;
