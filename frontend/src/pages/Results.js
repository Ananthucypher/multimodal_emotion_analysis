import React from 'react';
import { motion } from 'framer-motion';
import { useLocation, useNavigate } from 'react-router-dom';
import EmotionChart from '../components/EmotionChart';

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

const DimensionalBar = ({ label, value, color }) => (
  <div style={{ marginBottom: 8 }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', marginBottom: 2 }}>
      <span>{label}</span>
      <span>{value?.toFixed(2)}</span>
    </div>
    <div style={{ width: '100%', background: '#eee', height: 8, borderRadius: 4 }}>
      <div style={{
        width: `${Math.min(Math.max((value + 1) * 50, 0), 100)}%`,
        background: color, height: '100%', borderRadius: 4
      }} />
    </div>
  </div>
);

const Results = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const data = location.state?.data;

  if (!data) {
    navigate('/analyze');
    return null;
  }

  const getTopAUs = (aus) => {
    if (!aus) return [];
    return Object.entries(aus)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5);
  };

  const topAUs = getTopAUs(data.face_emotion_result?.advanced_action_units);

  // Phase 3: Incongruence Data
  const incongruence = data.overall_emotion?.incongruence;

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
          color: '#222', borderRadius: 32, textAlign: 'center', marginBottom: '3rem', boxShadow: '0 10px 40px rgba(0,0,0,0.10)'
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

        {/* Phase 3: Incongruence Alert */}
        {incongruence?.is_incongruent && (
          <motion.div
            initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
            style={{
              background: '#FEE2E2', color: '#B91C1C', display: 'inline-block',
              padding: '0.5rem 1rem', borderRadius: 8, marginBottom: 12, border: '1px solid #FECACA'
            }}>
            ⚠️ <strong>Conflict Pattern:</strong> {incongruence.status} <br />
            <span style={{ fontSize: '0.9rem' }}>{incongruence.suggestion}</span>
          </motion.div>
        )}

        <div style={{ fontSize: '1.2rem', opacity: 0.85, marginBottom: 8 }}>
          {(data.overall_emotion?.confidence * 100).toFixed(1)}% Confidence
        </div>
        <p>{data.overall_emotion?.description}</p>
      </motion.div>

      {/* Modular Grid */}
      <div className="modules-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '2rem' }}>

        {/* Face */}
        <motion.div className="module-card" initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }}>
          <h3>😊 Face Analysis</h3>
          <div className="emotion-chip" style={{
            display: 'inline-block', padding: '0.7rem 1.7rem', borderRadius: '50px',
            color: '#fff', background: getEmotionGradient(data.face_emotion_result?.dominant_face_emotion),
            fontWeight: 700, textTransform: 'capitalize', marginBottom: 16
          }}>
            {data.face_emotion_result?.dominant_face_emotion}
          </div>
          <EmotionChart emotionData={data.face_emotion_result?.frame_emotions} />
          {topAUs.length > 0 && (
            <div style={{ marginTop: '1.5rem', background: '#fafafa', padding: '1rem', borderRadius: 12 }}>
              <h4 style={{ fontSize: '0.95rem', marginBottom: '0.5rem', color: '#555' }}>Micro-Expressions (AUs)</h4>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                {topAUs.map(([au, val]) => (
                  <li key={au} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: 4 }}>
                    <span>{au}</span>
                    <span style={{ fontWeight: 600 }}>{val.toFixed(2)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </motion.div>

        {/* Audio */}
        <motion.div className="module-card" initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }}>
          <h3>🎵 Voice Tone</h3>
          <div className="emotion-chip" style={{
            display: 'inline-block', padding: '0.7rem 1.7rem', borderRadius: '50px',
            color: '#fff', background: getEmotionGradient(data.audio_tone_emotion?.predicted),
            fontWeight: 700, textTransform: 'capitalize', marginBottom: 16
          }}>
            {data.audio_tone_emotion?.predicted}
          </div>
          <EmotionChart emotionData={data.audio_tone_emotion?.probs} />
          {data.audio_tone_emotion?.dimensional_metrics && (
            <div style={{ marginTop: '1.5rem', background: '#fafafa', padding: '1rem', borderRadius: 12 }}>
              <h4 style={{ fontSize: '0.95rem', marginBottom: '0.5rem', color: '#555' }}>Vertical Depth (Wav2Vec)</h4>
              <DimensionalBar label="Valence (Positivity)" value={data.audio_tone_emotion.dimensional_metrics.valence} color="#10B981" />
              <DimensionalBar label="Arousal (Energy)" value={data.audio_tone_emotion.dimensional_metrics.arousal} color="#F59E0B" />
              <DimensionalBar label="Dominance" value={data.audio_tone_emotion.dimensional_metrics.dominance} color="#8B5CF6" />
            </div>
          )}
        </motion.div>

        {/* Speech */}
        <motion.div className="module-card" initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }}>
          <h3>💬 Speech (High Fidelity)</h3>
          <div className="transcript-box" style={{
            background: '#F5F6FA', padding: '1.2rem', borderRadius: 13, minHeight: 70,
            color: '#333', fontStyle: 'italic', marginBottom: '1.5rem', fontSize: '0.9rem'
          }}>
            "{data.transcript || 'No speech detected'}"
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
            <div className="emotion-chip" style={{
              padding: '0.5rem 1.2rem', borderRadius: '50px', fontSize: '0.9rem',
              color: '#fff', background: getEmotionGradient(data.transcript_sentiment?.primary_emotion),
              fontWeight: 600, textTransform: 'capitalize'
            }}>
              {data.transcript_sentiment?.primary_emotion}
            </div>
          </div>

          {/* AI Insight */}
          {data.llm_analysis?.analysis && (
            <div style={{ background: '#E0E7FF', padding: '1rem', borderRadius: 12, borderLeft: '4px solid #4F46E5' }}>
              <h4 style={{ fontSize: '0.9rem', margin: '0 0 0.5rem 0', color: '#4F46E5', display: 'flex', alignItems: 'center', gap: 6 }}>
                ✨ AI Clinical Insight (Flan-T5)
              </h4>
              <p style={{ fontSize: '0.9rem', lineHeight: 1.5, margin: 0, color: '#312E81' }}>
                {data.llm_analysis.analysis}
              </p>
            </div>
          )}
        </motion.div>
      </div>

      {/* Phase 5: Therapeutic Advice (RAG + Llama 3.1) */}
      {data.therapeutic_advice && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          style={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: '#fff',
            padding: '2rem',
            borderRadius: 20,
            marginTop: '2rem',
            boxShadow: '0 10px 40px rgba(102, 126, 234, 0.3)'
          }}
        >
          <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: 8 }}>
            💜 Your Personalized Therapeutic Guidance
          </h2>

          <div style={{
            background: 'rgba(255, 255, 255, 0.15)',
            padding: '1.5rem',
            borderRadius: 12,
            backdropFilter: 'blur(10px)',
            marginBottom: '1rem'
          }}>
            <p style={{ fontSize: '1.1rem', lineHeight: 1.8, margin: 0 }}>
              {data.therapeutic_advice.advice}
            </p>
          </div>

          <div style={{ display: 'flex', gap: '1rem', fontSize: '0.9rem', opacity: 0.9 }}>
            <div>
              <strong>Strategy:</strong> {data.therapeutic_advice.strategy_used}
            </div>
            <div>
              <strong>Technique:</strong> {data.therapeutic_advice.technique}
            </div>
          </div>
        </motion.div>
      )}

      <motion.button className="another-btn" onClick={() => navigate('/analyze')}
        whileHover={{ scale: 1.06 }} whileTap={{ scale: 0.96 }}
        style={{
          margin: '2.5rem auto 0 auto', display: 'block',
          background: '#10B981', color: '#fff', border: 'none',
          padding: '1.2rem 3rem', fontSize: '1.1rem', fontWeight: 600, borderRadius: 50, cursor: 'pointer'
        }}>
        Analyze Another Video
      </motion.button>
    </motion.div>
  );
};

export default Results;
