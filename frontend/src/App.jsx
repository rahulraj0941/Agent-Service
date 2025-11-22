import React from 'react'
import ChatInterface from './components/ChatInterface'
import './App.css'

function App() {
  return (
    <div className="app-container">
      <div className="app-header">
        <h1>HealthCare Plus Clinic</h1>
        <p>Intelligent Appointment Scheduling Assistant</p>
      </div>
      <ChatInterface />
    </div>
  )
}

export default App
