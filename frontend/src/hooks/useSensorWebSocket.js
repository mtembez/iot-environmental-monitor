import { useState, useEffect, useRef, useCallback } from 'react'

/**
 * Resilient React WebSocket Hook for IoT Sensor Telemetry.
 * Enforces exponential back-off reconnection and clean lifecycle management.
 */
export function useSensorWebSocket(onTelemetry, onAnomaly) {
  const [isConnected, setIsConnected] = useState(false)
  const [lastEvent, setLastEvent] = useState(null)
  const [reconnectAttempt, setReconnectAttempt] = useState(0)

  const socketRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)
  const pingIntervalRef = useRef(null)

  const connect = useCallback(() => {
    // Clean up any existing connection
    if (socketRef.current) {
      socketRef.current.close()
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host || 'localhost:8000'
    const wsUrl = `${protocol}//${host}/ws/sensors/stream/`

    try {
      const ws = new WebSocket(wsUrl)
      socketRef.current = ws

      ws.onopen = () => {
        setIsConnected(true)
        setReconnectAttempt(0)

        // Establish 30s heartbeat ping
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ command: 'ping', timestamp: Date.now() }))
          }
        }, 30000)
      }

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          setLastEvent(message)

          if (message.type === 'telemetry.update' && onTelemetry) {
            onTelemetry(message.payload)
          } else if (message.type === 'anomaly.alert' && onAnomaly) {
            onAnomaly(message.payload)
          }
        } catch (err) {
          // Ignored parse error on heartbeat
        }
      }

      ws.onclose = () => {
        setIsConnected(false)
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current)
        }

        // Exponential back-off retry with max 16s cap
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempt), 16000)
        reconnectTimeoutRef.current = setTimeout(() => {
          setReconnectAttempt((prev) => prev + 1)
          connect()
        }, delay)
      }

      ws.onerror = () => {
        ws.close()
      }
    } catch {
      setIsConnected(false)
    }
  }, [reconnectAttempt, onTelemetry, onAnomaly])

  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current)
      if (pingIntervalRef.current) clearInterval(pingIntervalRef.current)
      if (socketRef.current) socketRef.current.close()
    }
  }, [connect])

  return { isConnected, lastEvent }
}
