import React from 'react'

export default function MetricCard({ title, value, unit, status, icon, subtitle }) {
  const isAnomaly = status === 'anomaly'
  return (
    <div className={`card metric-card ${isAnomaly ? 'border-red-500/50 ring-1 ring-red-500/30' : ''}`}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          {title}
        </span>
        <span style={{ fontSize: '1.25rem' }}>{icon}</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginBottom: '0.5rem' }}>
        <span className="font-mono" style={{ fontSize: '2.25rem', fontWeight: 700, color: isAnomaly ? 'var(--accent-red)' : 'var(--text-main)' }}>
          {value !== undefined && value !== null ? value : '--'}
        </span>
        <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>{unit}</span>
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.5rem' }}>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{subtitle}</span>
        <span className={`badge ${isAnomaly ? 'badge-anomaly' : 'badge-nominal'}`}>
          {status}
        </span>
      </div>
    </div>
  )
}
