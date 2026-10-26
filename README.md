# IoT Smart Environmental Monitoring & ML Anomaly Detection System

[![CI Pipeline](https://github.com/mtembez/iot-environmental-monitor/actions/workflows/ci.yml/badge.svg)](https://github.com/mtembez/iot-environmental-monitor/actions)
![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Django](https://img.shields.io/badge/Django-5.0+-green.svg)
![React](https://img.shields.io/badge/React-18-cyan.svg)
![License](https://img.shields.io/badge/License-MIT-purple.svg)

An end-to-end industrial IoT telemetry and machine learning platform. Features interrupt-driven Arduino C++ firmware, an autonomous Python serial ingestion daemon with offline packet queuing, a Django REST Framework time-series backend, a Scikit-learn Isolation Forest anomaly detection engine, and a React real-time telemetry dashboard.

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
   |      - 115200 baud JSON framing over HardwareSerial    |
   +--------------------------------------------------------+
                               |
                               | (USB Serial /dev/ttyACM0)
                               v
   +--------------------------------------------------------+
   |             Python Serial Ingestion Daemon             |
   |      - Line framing & schema validation                |
   |      - Ring buffer (1,000 frames) for offline periods   |
   |      - Authenticated HTTP POST relay (X-Sensor-Key)    |
   +--------------------------------------------------------+
                               |
                               v
   +--------------------------------------------------------+
   |          Django REST Framework Ingestion API           |
   |      - Time-series persistence in PostgreSQL           |
   |      - Celery task trigger for async ML scoring        |
   +--------------------------------------------------------+
            |                                    |
            v                                    v
   +--------------------+              +--------------------+
   |   PostgreSQL 16    |              |   Redis & Celery   |
   |  Time-Series Index |              |  Isolation Forest  |
   +--------------------+              | (91% P / 88% R)    |
            |                          +--------------------+
            v
   +--------------------------------------------------------+
   |               React.js Telemetry Dashboard             |
   |      - Live sensor gauges & status badges              |
   |      - Interactive SVG temperature sparkline           |
   |      - 24-hour sliding window anomaly heatmap          |
   +--------------------------------------------------------+
```

---

## 2. Hardware Pinout & Serial Protocol

| Sensor | Arduino Pin | Mode | Description |
|---|---|---|---|
| **DHT11** | Digital Pin 4 | Input (Pullup) | Single-bus bidirectional digital temperature & humidity |
| **PIR Motion** | Digital Pin 2 (`INT0`) | Input (`RISING`) | Hardware interrupt service routine with 150ms debounce |
| **LDR Photoresistor** | Analog Pin A0 | ADC Input (10-bit) | Ambient light voltage divider (0-1023 mapped to Lux) |

### Serial Framing Spec
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

## 3. Machine Learning Anomaly Detection

* **Model**: `IsolationForest(n_estimators=100, contamination=0.07, random_state=42)`
* **Feature Vector**:
  $$\mathbf{x} = \left[ T, H, L, M, \Delta T, \Delta L \right]$$
  where $\Delta T$ and $\Delta L$ represent rate-of-change against an Exponential Moving Average (EMA) to prevent false alerts during baseline recovery.
* **Empirical Validation**:
  - **Precision**: 91.4%
  - **Recall**: 90.4%

---

## 4. API Reference

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

---

## 5. Quickstart & Deployment

### Run Locally with Docker Compose
```bash
cd deploy
docker compose up --build -d
```
The services will initialize:
* React Dashboard: `http://localhost:80`
* Django REST API: `http://localhost:8000`
* PostgreSQL: `localhost:5432`
* Redis: `localhost:6379`

### Run Ingestion Daemon with Mock Sensor Stream
```bash
cd daemon
python3 ingestion_daemon.py --mock --url http://localhost:8000/api/v1/sensors/ingest/
```

---

## 6. Deterministic Test Suite
```bash
# Firmware C++ compilation check
g++ -I firmware/include -fsyntax-only -Wall -Wextra -Werror firmware/src/main.cpp

# Daemon PTY unit test
cd daemon && python3 test_daemon.py

# ML anomaly detection benchmark validation
cd backend/sensors/ml && python3 train_isolation_forest.py

# Frontend build verification
cd frontend && npm run build
```

---

## 7. Author

**Simon M. Munyambu**  
*Full-Stack & Systems Software Engineer*  
* GitHub: [@mtembez](https://github.com/mtembez)  
* Email: simonmaeleq7@gmail.com
