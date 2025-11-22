import React from 'react'
import './AppointmentConfirmation.css'

const AppointmentConfirmation = ({ appointment, onClose }) => {
  if (!appointment) return null

  const formatDate = (dateStr) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    })
  }

  const formatTime = (timeStr) => {
    const [hours, minutes] = timeStr.split(':')
    const hour = parseInt(hours)
    const ampm = hour >= 12 ? 'PM' : 'AM'
    const displayHour = hour % 12 || 12
    return `${displayHour}:${minutes} ${ampm}`
  }

  const getAppointmentTypeLabel = (type) => {
    const labels = {
      consultation: 'General Consultation',
      followup: 'Follow-up Visit',
      physical: 'Physical Exam',
      specialist: 'Specialist Consultation'
    }
    return labels[type] || type
  }

  return (
    <div className="confirmation-overlay">
      <div className="confirmation-modal">
        <div className="confirmation-header">
          <div className="success-icon">✓</div>
          <h2>Appointment Confirmed!</h2>
        </div>

        <div className="confirmation-details">
          <div className="detail-row">
            <span className="detail-label">Confirmation Code:</span>
            <span className="detail-value confirmation-code">{appointment.confirmation_code}</span>
          </div>

          <div className="detail-row">
            <span className="detail-label">Booking ID:</span>
            <span className="detail-value">{appointment.booking_id}</span>
          </div>

          <div className="detail-row">
            <span className="detail-label">Patient Name:</span>
            <span className="detail-value">{appointment.patient_name}</span>
          </div>

          <div className="detail-row">
            <span className="detail-label">Date:</span>
            <span className="detail-value">{formatDate(appointment.date)}</span>
          </div>

          <div className="detail-row">
            <span className="detail-label">Time:</span>
            <span className="detail-value">{formatTime(appointment.start_time)}</span>
          </div>

          <div className="detail-row">
            <span className="detail-label">Duration:</span>
            <span className="detail-value">{appointment.duration_minutes} minutes</span>
          </div>

          <div className="detail-row">
            <span className="detail-label">Appointment Type:</span>
            <span className="detail-value">{getAppointmentTypeLabel(appointment.appointment_type)}</span>
          </div>

          <div className="detail-row">
            <span className="detail-label">Reason:</span>
            <span className="detail-value">{appointment.reason}</span>
          </div>
        </div>

        <div className="confirmation-footer">
          <p className="confirmation-note">
            A confirmation email has been sent to <strong>{appointment.patient_email}</strong>
          </p>
          <p className="reminder-text">
            Please arrive 15 minutes early. For any changes, call +1-555-123-4567
          </p>
          <button onClick={onClose} className="close-button">Close</button>
        </div>
      </div>
    </div>
  )
}

export default AppointmentConfirmation
