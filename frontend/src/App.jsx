import React, { useState, useEffect } from 'react'
import MetricCard from './components/MetricCard'
import SensorTimeline from './components/SensorTimeline'
import AnomalyHeatmap from './components/AnomalyHeatmap'
import ThresholdSettings from './components/ThresholdSettings'

export default function App() {
  const [readings, setReadings] = useState([])
  const [latest, setLatest] = useState({
    node_id: 'iot-enviro-01',
    temperature: 23.4,
    humidity: 52.1,
    light_lux: 480.0,
    motion_detected: false,
    anomaly_score: 0.12,
    is_anomaly: false,
  })
  const [heatmapStats, setHeatmapStats] = useState({
    window_hours: 24,
    total_samples: 1420,
    anomaly_samples: 48,
    anomaly_rate_pct: 3.38,
  })
  const [anomalies, setAnomalies] = useState([
    { id: 1, node_id: 'iot-enviro-01', anomaly_score: 0.88, description: 'Sudden thermal divergence (+14.2°C)', created_at: new Date().toISOString() },
    { id: 2, node_id: 'iot-enviro-01', anomaly_score: 0.74, description: 'Relative humidity saturation breach (>92%)', created_at: new Date().toISOString() },
  ])
  const [isConnected, setIsConnected] = useState(true)

  // Fetch telemetry from backend API
  const fetchTelemetry = async () => {
    try {
      const respLatest = await fetch('/api/v1/sensors/latest/')
      if (respLatest.ok) {
        const data = await respLatest.json()
        const nodeLatest = Array.isArray(data) ? data[0] : data
        if (nodeLatest) {
          setLatest(nodeLatest)
          setIsConnected(true)
        }
      }

      const respHistory = await fetch('/api/v1/sensors/readings/?limit=50')
      if (respHistory.ok) {
        const historyData = await respHistory.json()
        if (historyData.results) {
          setReadings(historyData.results)
        }
      }

      const respHeatmap = await fetch('/api/v1/sensors/heatmap/')
      if (respHeatmap.ok) {
        const stats = await respHeatmap.json()
        setHeatmapStats(stats)
      }

      const respAnom = await fetch('/api/v1/sensors/anomalies/')
      if (respAnom.ok) {
        const anomList = await respAnom.json()
        setAnomalies(anomList)
      }
    } catch (err) {
      // Offline fallback: keep local telemetry active
      setIsConnected(false)
    }
  }

  useEffect(() => {
    fetchTelemetry()
    const interval = setInterval(fetchTelemetry, 3000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="dashboard-container">
      {/* Top Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 700, letterSpacing: '-0.02em' }}>
              IoT Environmental Telemetry
            </h1>
            <span className="badge" style={{ backgroundColor: '#1e293b', color: 'var(--accent-cyan)' }}>
              Node: {latest.node_id}
            </span>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '0.25rem' }}>
            Arduino C++ Firmware • Python Daemon • DRF • Isolation Forest ML • React
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
            <span style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              backgroundColor: isConnected ? 'var(--accent-green)' : 'var(--accent-amber)',
              boxShadow: isConnected ? '0 0 8px var(--accent-green)' : 'none'
            }}></span>
            <span style={{ color: 'var(--text-muted)' }}>
              {isConnected ? 'Live Telemetry Stream' : 'Fallback Emulation'}
            </span>
          </div>
        </div>
      </header>

      {/* Primary Telemetry Metric Grid */}
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>
        <MetricCard
          title="Ambient Temperature"
          value={latest.temperature?.toFixed(1)}
          unit="°C"
          status={latest.temperature > 32 ? 'anomaly' : 'nominal'}
          icon="🌡️"
          subtitle="DHT11 Sensor Calibrated"
        />
        <MetricCard
          title="Relative Humidity"
          value={latest.humidity?.toFixed(1)}
          unit="%"
          status={latest.humidity > 80 ? 'anomaly' : 'nominal'}
          icon="💧"
          subtitle="Capacitive Humidity Grid"
        />
        <MetricCard
          title="Ambient Luminosity"
          value={latest.light_lux?.toFixed(0)}
          unit="Lux"
          status="nominal"
          icon="☀️"
          subtitle="Photo-resistor ADC 10-bit"
        />
        <MetricCard
          title="Motion Detection"
          value={latest.motion_detected ? 'ACTIVE' : 'IDLE'}
          unit=""
          status={latest.motion_detected ? 'anomaly' : 'nominal'}
          icon="🏃"
          subtitle="Interrupt-driven PIR (Pin 2)"
        />
      </section>

      {/* Interactive Charts & Heatmaps */}
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        <SensorTimeline readings={readings} />
        <AnomalyHeatmap stats={heatmapStats} recentAnomalies={anomalies} />
      </section>

      {/* Setpoints & Configuration */}
      <section>
        <ThresholdSettings />
      </section>
    </div>
  )
}
