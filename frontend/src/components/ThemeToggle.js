import React from 'react';
import { motion } from 'framer-motion';
import './ThemeToggle.css';

const ThemeToggle = ({ theme, setTheme }) => {
  const themes = ['light', 'dark', 'calm'];

  return (
    <div className="theme-toggle-container">
      {themes.map((t) => (
        <motion.button
          key={t}
          className={`theme-btn ${theme === t ? 'active' : ''}`}
          onClick={() => setTheme(t)}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <span className="theme-icon">
            {t === 'light' && '☀️'}
            {t === 'dark' && '🌙'}
            {t === 'calm' && '🌿'}
          </span>
        </motion.button>
      ))}
    </div>
  );
};

export default ThemeToggle;
