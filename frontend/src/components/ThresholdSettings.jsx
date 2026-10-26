import React, { useState } from 'react'

export default function ThresholdSettings({ thresholds = [], onUpdate }) {
  const [editing, setEditing] = useState(false)

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Threshold Configuration</h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Supervisory Alert Setpoints
          </p>
        </div>
        <button
          onClick={() => setEditing(!editing)}
          style={{
            background: 'transparent',
            border: '1px solid var(--border-color)',
            color: 'var(--accent-cyan)',
            padding: '0.4rem 0.8rem',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '0.8rem',
          }}
        >
          {editing ? 'Close' : 'Configure'}
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
        <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-secondary)', borderRadius: '8px' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Temperature Bounds</span>
          <p className="font-mono" style={{ fontSize: '1rem', marginTop: '0.25rem', fontWeight: 600 }}>
            18.0°C – 30.0°C
          </p>
        </div>
        <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-secondary)', borderRadius: '8px' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Humidity Bounds</span>
          <p className="font-mono" style={{ fontSize: '1rem', marginTop: '0.25rem', fontWeight: 600 }}>
            35.0% – 70.0%
          </p>
        </div>
        <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-secondary)', borderRadius: '8px' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Light Lux Limits</span>
          <p className="font-mono" style={{ fontSize: '1rem', marginTop: '0.25rem', fontWeight: 600 }}>
            50 – 950 Lux
          </p>
        </div>
      </div>
    </div>
  )
}
