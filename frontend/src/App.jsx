import React from 'react'
import ChatInterface from './components/ChatInterface'
import './App.css'

function App() {
  return (
    <div className="app-container">
      <div className="app-header">
        <h1>
          <span className="header-icon">🏥</span>
          HealthCare Plus Clinic
        </h1>
        <p>Intelligent Appointment Scheduling Assistant</p>
        <div className="features-bar">
          <div className="feature-item">
            <span className="feature-icon">📅</span>
            <span>Easy Scheduling</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">💬</span>
            <span>24/7 Support</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">🔒</span>
            <span>Secure & Private</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">⚡</span>
            <span>Instant Confirmation</span>
          </div>
        </div>
      </div>
      <ChatInterface />
    </div>
  )
}

export default App
