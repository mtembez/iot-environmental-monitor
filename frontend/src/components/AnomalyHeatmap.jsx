import React from 'react'

export default function AnomalyHeatmap({ stats, recentAnomalies = [] }) {
  const anomalyRate = stats?.anomaly_rate_pct ?? 0.0
  const totalSamples = stats?.total_samples ?? 0
  const anomalySamples = stats?.anomaly_samples ?? 0

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
        <div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Anomaly Distribution & Heatmap</h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            24-Hour Sliding Window ML Scoring Summary
          </p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <span className="font-mono" style={{ fontSize: '1.5rem', fontWeight: 700, color: anomalyRate > 5 ? 'var(--accent-red)' : 'var(--accent-green)' }}>
            {anomalyRate}%
          </span>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Anomaly Rate</p>
        </div>
      </div>

      {/* Heatmap Matrix Simulation */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: '6px', marginBottom: '1.5rem' }}>
        {Array.from({ length: 24 }).map((_, idx) => {
          // Calculate intensity mock
          const hasAnomaly = idx === 4 || idx === 11 || idx === 19
          const bg = hasAnomaly 
            ? 'rgba(239, 68, 68, 0.85)' 
            : 'rgba(16, 185, 129, 0.25)'
          return (
            <div
              key={idx}
              title={`Hour -${24 - idx}: ${hasAnomaly ? 'Anomaly Flagged' : 'Nominal'}`}
              style={{
                height: '32px',
                borderRadius: '4px',
                backgroundColor: bg,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.7rem',
                fontFamily: 'JetBrains Mono',
                color: '#ffffff',
                border: hasAnomaly ? '1px solid #ef4444' : '1px solid #1e293b'
              }}
            >
              {idx}h
            </div>
          )
        })}
      </div>

      {/* Recent Alerts Feed */}
      <div>
        <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.75rem', textTransform: 'uppercase' }}>
          Recent Telemetry Alerts ({recentAnomalies.length})
        </h4>
        {recentAnomalies.length === 0 ? (
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No critical anomaly events recorded.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {recentAnomalies.slice(0, 4).map((evt) => (
              <div
                key={evt.id}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '0.6rem 0.8rem',
                  borderRadius: '6px',
                  backgroundColor: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.25)',
                  fontSize: '0.8rem',
                }}
              >
                <div>
                  <span style={{ fontWeight: 600, color: '#f87171' }}>[{evt.node_id || 'NODE-01'}]</span>{' '}
                  <span>{evt.description || 'Threshold boundary breach'}</span>
                </div>
                <div className="font-mono" style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                  Score: {evt.anomaly_score ? evt.anomaly_score.toFixed(2) : '0.85'}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
