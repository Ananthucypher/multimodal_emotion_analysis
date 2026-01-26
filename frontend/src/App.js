import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import Home from './pages/Home';
import Analyze from './pages/Analyze';
import Results from './pages/Results';
import ThemeToggle from './components/ThemeToggle';
import { themes } from './theme';
import './App.css';

function App() {
  const [theme, setTheme] = useState('light');

  useEffect(() => {
    const root = document.documentElement;
    const selectedTheme = themes[theme];

    Object.entries(selectedTheme).forEach(([key, value]) => {
      root.style.setProperty(`--${key}`, value);
    });
  }, [theme]);

  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <div className="logo">MIRO</div>
          <ThemeToggle theme={theme} setTheme={setTheme} />
        </header>

        <AnimatePresence mode="wait">
          <Routes>
            <Route path="/" element={<Home theme={theme} />} />
            <Route path="/analyze" element={<Analyze />} />
            <Route path="/results" element={<Results />} />
          </Routes>
        </AnimatePresence>
      </div>
    </Router>
  );
}

export default App;
