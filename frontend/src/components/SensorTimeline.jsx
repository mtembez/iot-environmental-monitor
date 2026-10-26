import React from 'react'

export default function SensorTimeline({ readings = [] }) {
  if (!readings || readings.length === 0) {
    return (
      <div className="card" style={{ height: '280px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p style={{ color: 'var(--text-muted)' }}>Awaiting telemetry streams...</p>
      </div>
    )
  }

  // Reverse readings to render chronologically left to right
  const data = [...readings].reverse().slice(-40)
  const width = 800
  const height = 220
  const padding = 35

  const temps = data.map(d => d.temperature)
  const minTemp = Math.min(...temps, 15)
  const maxTemp = Math.max(...temps, 35)

  const getX = (idx) => padding + (idx / Math.max(data.length - 1, 1)) * (width - 2 * padding)
  const getY = (val) => height - padding - ((val - minTemp) / Math.max(maxTemp - minTemp, 1)) * (height - 2 * padding)

  const points = data.map((d, i) => `${getX(i)},${getY(d.temperature)}`).join(' ')

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Real-Time Sensor Timeline</h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Temperature (°C) with Isolation Forest Anomaly Detection Overlays
          </p>
        </div>
        <div style={{ display: 'flex', gap: '1rem', fontSize: '0.8rem' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#00f2fe' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#00f2fe' }}></span> Nominal
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#ef4444' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#ef4444' }}></span> Anomaly Triggered
          </span>
        </div>
      </div>

      <div style={{ width: '100%', overflowX: 'auto' }}>
        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
          {/* Grid lines */}
          <line x1={padding} y1={padding} x2={width - padding} y2={padding} stroke="#1e293b" strokeDasharray="4 4" />
          <line x1={padding} y1={height / 2} x2={width - padding} y2={height / 2} stroke="#1e293b" strokeDasharray="4 4" />
          <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#1e293b" />

          {/* Temperature sparkline */}
          <polyline
            fill="none"
            stroke="#00f2fe"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            points={points}
          />

          {/* Data points & Anomaly markers */}
          {data.map((d, i) => {
            const x = getX(i)
            const y = getY(d.temperature)
            const isAnom = d.is_anomaly || d.anomaly_score >= 0.70

            return (
              <g key={d.id || i}>
                <circle
                  cx={x}
                  cy={y}
                  r={isAnom ? 6 : 3}
                  fill={isAnom ? '#ef4444' : '#00f2fe'}
                  stroke={isAnom ? '#ffffff' : '#0f172a'}
                  strokeWidth={isAnom ? 2 : 1}
                />
                {isAnom && (
                  <circle
                    cx={x}
                    cy={y}
                    r={12}
                    fill="none"
                    stroke="#ef4444"
                    strokeWidth="1.5"
                    opacity="0.6"
                  />
                )}
              </g>
            )
          })}
        </svg>
      </div>
    </div>
  )
}
