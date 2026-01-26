import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
// import AnimatedBackground from '../components/AnimatedBackground';
import './Home.css';

const Home = ({ theme }) => {
  const navigate = useNavigate();

  const features = [
    { icon: '😊', title: 'Face Analysis', desc: 'Detect emotions from facial expressions' },
    { icon: '🎵', title: 'Voice Tone', desc: 'Analyze emotional cues in speech' },
    { icon: '💬', title: 'Text Sentiment', desc: 'Understand sentiment from words' }
  ];

  return (
    <div className="home-page">
      {/* <AnimatedBackground /> */}

      <motion.section
        className="hero-section"
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
      >
        <h1 className="hero-title">Understand Your Emotions.<br />Find Your Clarity.</h1>
        <p className="hero-subtitle">MIRO is your empathetic AI listener, helping you explore and understand your emotional landscape.</p>

        <motion.button
          className="cta-button"
          onClick={() => navigate('/analyze')}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          animate={{
            boxShadow: [
              '0 0 20px rgba(107, 155, 209, 0.3)',
              '0 0 30px rgba(107, 155, 209, 0.5)',
              '0 0 20px rgba(107, 155, 209, 0.3)'
            ]
          }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          Analyze Your First Video
        </motion.button>
      </motion.section>

      <motion.section
        className="features-section"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: '-100px' }}
        variants={{
          hidden: {},
          visible: { transition: { staggerChildren: 0.2 } }
        }}
      >
        {features.map((feature, idx) => (
          <motion.div
            key={idx}
            className="feature-card"
            variants={{
              hidden: { opacity: 0, y: 50 },
              visible: { opacity: 1, y: 0 }
            }}
            whileHover={{ y: -10 }}
          >
            <div className="feature-icon">{feature.icon}</div>
            <h3>{feature.title}</h3>
            <p>{feature.desc}</p>
          </motion.div>
        ))}
      </motion.section>

      <motion.section
        className="trust-section"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 1 }}
      >
        <h2>Your Privacy, Our Priority</h2>
        <p>All analysis happens locally. Your videos are never stored or shared.</p>
      </motion.section>
    </div>
  );
};

export default Home;
