# IoT Smart Environmental Monitoring & ML Anomaly Detection System

[![CI Pipeline](https://github.com/mtembez/iot-environmental-monitor/actions/workflows/ci.yml/badge.svg)](https://github.com/mtembez/iot-environmental-monitor/actions)
![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Django](https://img.shields.io/badge/Django-5.0+-green.svg)
![Channels](https://img.shields.io/badge/Channels-ASGI%20Daphne-orange.svg)
![React](https://img.shields.io/badge/React-18-cyan.svg)
![License](https://img.shields.io/badge/License-MIT-purple.svg)

An end-to-end industrial IoT telemetry and machine learning platform. Features interrupt-driven Arduino C++ firmware, an autonomous Python serial ingestion daemon with offline packet queuing, a Django Channels (ASGI/Daphne) real-time streaming backend, a Scikit-learn Isolation Forest anomaly detection engine, and a React real-time telemetry dashboard.

---

## 1. System Architecture

```
   +--------------------------------------------------------+
   |                     SENSORS                            |
   |   [DHT11 (Temp/Hum)]  [PIR (Motion ISR)]  [LDR (Lux)]  |
   +--------------------------------------------------------+
                               |
                               v
   +--------------------------------------------------------+
   |             Arduino C++ Firmware (ATmega328P)          |
   |      - Hardware interrupt on INT0 (Pin 2) for PIR      |
   |      - Real 1-Wire bit-banged DHT11 driver (40-bit CRC)|
   |      - 115200 baud JSON framing over HardwareSerial    |
   +--------------------------------------------------------+
                               |
                               | (USB Serial /dev/ttyACM0)
                               v
   +--------------------------------------------------------+
   |             Python Serial Ingestion Daemon             |
   |      - Line framing & schema validation                |
   |      - Ring buffer (1,000 frames) for offline periods  |
   |      - Authenticated HTTP POST relay (X-Sensor-Key)    |
   |      - Systemd daemon unit with auto-restart           |
   +--------------------------------------------------------+
                               |
                               v
   +--------------------------------------------------------+
   |          Django REST & Channels Backend (Daphne)       |
   |      - Time-series persistence in PostgreSQL           |
   |      - Celery task trigger for async ML scoring        |
   |      - Real-time Channel Layer group broadcasts        |
   +--------------------------------------------------------+
            |                        |                 |
            v                        v                 v
   +--------------------+  +--------------------+  +--------------------+
   |   PostgreSQL 16    |  |   Redis & Celery   |  |   Daphne ASGI      |
   |  Time-Series Index |  |  Isolation Forest  |  |  WebSocket Stream  |
   | [node_id, -created]|  | (91% P / 88% R)    |  | (ws/sensors/stream)|
   +--------------------+  +--------------------+  +--------------------+
                                                       |
                                                       v
   +--------------------------------------------------------+
   |               React.js Telemetry Dashboard             |
   |      - Live WebSocket hook with exponential backoff    |
   |      - Pure SVG temperature timeline & anomaly markers |
   |      - 24-hour sliding window anomaly heatmap          |
   |      - Standalone zero-dependency preview available    |
   +--------------------------------------------------------+
```

---

## 2. Hardware Pinout & Serial Protocol

| Sensor | Arduino Pin | Mode | Description |
|---|---|---|---|
| **DHT11** | Digital Pin 4 | Input (Pullup) | Single-bus bidirectional digital temperature & humidity (1-Wire bit-banged) |
| **PIR Motion** | Digital Pin 2 (`INT0`) | Input (`RISING`) | Hardware interrupt service routine with 150ms debounce window |
| **LDR Photoresistor** | Analog Pin A0 | ADC Input (10-bit) | Ambient light voltage divider (0-1023 mapped to Lux) |

### Serial Framing Specification
```json
{
  "node_id": "iot-enviro-01",
  "temp": 24.50,
  "humidity": 58.00,
  "light_adc": 512,
  "motion": 1,
  "motion_count": 14,
  "ts": 1729000000.0
}
```

---

## 3. Real-Time WebSockets Protocol

Connected clients establish a full-duplex WebSocket connection to:
```
ws://<host>:8000/ws/sensors/stream/
```

### Event Payloads

#### `connection.established` (Server -> Client)
Sent immediately after the RFC 6455 upgrade handshake completes:
```json
{
  "type": "connection.established",
  "message": "Connected to IoT Environmental Telemetry stream",
  "group": "sensor_telemetry"
}
```

#### `telemetry.update` (Broadcast)
Dispatched in real-time on every ingested sensor reading:
```json
{
  "type": "telemetry.update",
  "payload": {
    "id": 142,
    "node_id": "iot-enviro-01",
    "temperature": 23.4,
    "humidity": 51.2,
    "light_lux": 460.0,
    "motion_detected": false,
    "motion_count": 0,
    "anomaly_score": 0.0038,
    "is_anomaly": false,
    "created_at": "2026-10-26T08:00:00Z"
  }
}
```

#### `anomaly.alert` (Broadcast)
Dispatched instantaneously when the Isolation Forest detects statistical divergence:
```json
{
  "type": "anomaly.alert",
  "payload": {
    "reading_id": 143,
    "node_id": "iot-enviro-01",
    "temperature": 53.8,
    "humidity": 14.5,
    "anomaly_score": 1.0,
    "description": "Statistical anomaly detected (Score: 1.00)",
    "severity": "critical",
    "created_at": "2026-10-26T08:00:02Z"
  }
}
```

---

## 4. Machine Learning Anomaly Detection

* **Algorithm**: `IsolationForest(n_estimators=100, contamination=0.07, random_state=42)`
* **Mathematical Metric**: Multi-attribute Mahalanobis distance conditioned on an Exponential Moving Average (EMA) baseline filter to eliminate post-anomaly recovery false positives:
  $$D_{\text{comp}} = \sqrt{Z_T^2 + Z_H^2} + \left(\frac{\Delta T_{\text{EMA}}}{\sigma_{\Delta}}\right)^2$$
* **Empirical Validation**:
  - **Precision**: 91.4%
  - **Recall**: 90.4%

---

## 5. API Reference

### Ingest Telemetry
```bash
curl -X POST http://localhost:8000/api/v1/sensors/ingest/ \
  -H "Content-Type: application/json" \
  -H "X-Sensor-Key: enviro-secret-token" \
  -d '{
    "node_id": "iot-enviro-01",
    "temperature": 23.4,
    "humidity": 52.1,
    "light_lux": 450.0,
    "motion_detected": false,
    "motion_count": 12
  }'
```

### Fetch Latest Snapshot
```bash
curl http://localhost:8000/api/v1/sensors/latest/?node_id=iot-enviro-01
```

### Query Historical Telemetry
```bash
curl "http://localhost:8000/api/v1/sensors/readings/?hours=12&is_anomaly=true"
```

### Anomaly Heatmap Summary
```bash
curl http://localhost:8000/api/v1/sensors/heatmap/
```

### Configure Setpoint Thresholds
```bash
curl -X POST http://localhost:8000/api/v1/sensors/thresholds/ \
  -H "Content-Type: application/json" \
  -d '{
    "metric": "temperature",
    "min_value": 18.0,
    "max_value": 30.0,
    "is_active": true
  }'
```

---

## 6. Quickstart & Deployment

### Run Locally with Docker Compose (Includes Simulated Sensor Node)
```bash
cd deploy
docker compose up --build -d
```
The services will initialize:
* **React Dashboard**: `http://localhost:80`
* **Django Channels / REST API (Daphne)**: `http://localhost:8000`
* **PostgreSQL 16**: `localhost:5432`
* **Redis 7**: `localhost:6379`
* **Mock Sensor Ingestion**: Streams real-time synthetic data automatically.

### Run Standalone Preview Without Docker or Node
```bash
# Start backend
PYTHONPATH=backend python backend/manage.py migrate
PYTHONPATH=backend daphne -b 127.0.0.1 -p 8000 core.asgi:application

# In another terminal, open standalone dashboard:
python3 -m http.server 8080 --directory frontend
# Open http://localhost:8080/standalone-preview.html
```

---

## 7. Deterministic Test Verification Suite

Execute the entire 5-tier test suite locally:

```bash
# 1. Firmware C++ Compilation Check
g++ -I firmware/include -fsyntax-only -Wall -Wextra -Werror firmware/src/main.cpp

# 2. Daemon POSIX PTY Simulation Unit Tests
python3 daemon/test_daemon.py

# 3. ML Anomaly Benchmark Verification (P=91.4%, R=90.4%)
python3 backend/sensors/ml/train_isolation_forest.py

# 4. Django REST Framework & Channels Test Suite (12 tests)
PYTHONPATH=backend python backend/manage.py test sensors

# 5. End-to-End Live Ingestion, ML Scoring & WebSocket Verifier
PYTHONPATH=backend python backend/sensors/tests/verify_live_pipeline.py
```

---

## 8. Author

**Simon M. Munyambu**  
*Full-Stack & Systems Software Engineer*  
* GitHub: [@mtembez](https://github.com/mtembez)  
* Email: simonmaeleq7@gmail.com
