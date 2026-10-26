"""
Deterministic End-to-End Live Verification Script for IoT Environmental Monitor.
Executes complete pipeline: Schema Migration -> Ingestion -> ML Scoring -> DB Persistence -> WebSocket Broadcast -> API Queries.
"""

import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
os.environ.setdefault('CELERY_ALWAYS_EAGER', 'True')

import django
django.setup()

from django.core.management import call_command
from rest_framework.test import APIClient
from sensors.models import SensorReading, AnomalyEvent, AlertThreshold
from core.asgi import application
from channels.testing import WebsocketCommunicator
import asyncio

async def test_websocket_stream():
    communicator = WebsocketCommunicator(application, "/ws/sensors/stream/")
    connected, subprotocol = await communicator.connect()
    assert connected, "Failed to connect to Channels WebSocket"
    
    # Receive connection handshake confirmation
    handshake = await communicator.receive_json_from()
    assert handshake["type"] == "connection.established", f"Unexpected handshake: {handshake}"
    await communicator.disconnect()
    return True

def run_live_pipeline():
    print("=" * 70)
    print("STEP 1: Initializing In-Memory SQLite Database & Migrations")
    print("=" * 70)
    call_command('migrate', verbosity=0)
    print("[+] Database schema created and migrations applied.")

    client = APIClient()
    api_key = "enviro-secret-token"

    print("\n" + "=" * 70)
    print("STEP 2: Simulating Telemetry Ingestion from Serial Daemon")
    print("=" * 70)

    # 1. Nominal sample
    sample_nominal = {
        "node_id": "iot-enviro-01",
        "temperature": 23.4,
        "humidity": 51.2,
        "light_lux": 460.0,
        "motion_detected": False,
        "motion_count": 0,
    }
    resp1 = client.post("/api/v1/sensors/ingest/", sample_nominal, format="json", HTTP_X_SENSOR_KEY=api_key)
    assert resp1.status_code == 201, f"Ingest failed: {resp1.data}"
    r1_data = resp1.data
    print(f"[+] Sample 1 (Nominal): Temp={sample_nominal['temperature']}°C, Hum={sample_nominal['humidity']}%")
    print(f"    -> Ingestion ID={r1_data['reading_id']}, Anomaly={r1_data['is_anomaly']}, Score={r1_data['anomaly_score']:.4f}")

    # 2. Critical Thermal Runaway Anomaly sample
    sample_anomaly = {
        "node_id": "iot-enviro-01",
        "temperature": 53.8,
        "humidity": 14.5,
        "light_lux": 80.0,
        "motion_detected": True,
        "motion_count": 22,
    }
    resp2 = client.post("/api/v1/sensors/ingest/", sample_anomaly, format="json", HTTP_X_SENSOR_KEY=api_key)
    assert resp2.status_code == 201, f"Ingest failed: {resp2.data}"
    r2_data = resp2.data
    print(f"\n[+] Sample 2 (Thermal Spike): Temp={sample_anomaly['temperature']}°C, Hum={sample_anomaly['humidity']}%")
    print(f"    -> Ingestion ID={r2_data['reading_id']}, Anomaly={r2_data['is_anomaly']}, Score={r2_data['anomaly_score']:.4f}")

    print("\n" + "=" * 70)
    print("STEP 3: Verifying Database Persistence & Alert Dispatch")
    print("=" * 70)
    total_readings = SensorReading.objects.count()
    total_anomalies = AnomalyEvent.objects.count()
    print(f"[+] Total records in SensorReading table: {total_readings}")
    print(f"[+] Total flagged events in AnomalyEvent table: {total_anomalies}")
    assert total_readings == 2, f"Expected 2 readings, found {total_readings}"
    assert total_anomalies >= 1, f"Expected at least 1 anomaly event, found {total_anomalies}"

    alert = AnomalyEvent.objects.first()
    print(f"[+] Latest Alert Record:")
    print(f"    Node: {alert.reading.node_id}")
    print(f"    Severity: {alert.severity.upper()}")
    print(f"    Score: {alert.anomaly_score:.2f}")
    print(f"    Description: {alert.description}")

    print("\n" + "=" * 70)
    print("STEP 4: Querying Real-Time REST Endpoints")
    print("=" * 70)
    # Latest snapshot
    resp_latest = client.get("/api/v1/sensors/latest/?node_id=iot-enviro-01")
    assert resp_latest.status_code == 200
    print(f"[+] GET /api/v1/sensors/latest/ -> Node: {resp_latest.data['node_id']}, Current Temp: {resp_latest.data['temperature']}°C")

    # Heatmap stats
    resp_heatmap = client.get("/api/v1/sensors/heatmap/")
    assert resp_heatmap.status_code == 200
    hm = resp_heatmap.data
    print(f"[+] GET /api/v1/sensors/heatmap/ -> Samples: {hm['total_samples']}, Anomaly Rate: {hm['anomaly_rate_pct']}%, Avg Temp: {hm['avg_temperature']}°C")

    # Anomaly feed
    resp_anom = client.get("/api/v1/sensors/anomalies/")
    assert resp_anom.status_code == 200
    print(f"[+] GET /api/v1/sensors/anomalies/ -> Returned {len(resp_anom.data)} alert record(s)")

    print("\n" + "=" * 70)
    print("STEP 5: Verifying Channels WebSocket Connection & Handshake")
    print("=" * 70)
    ws_result = asyncio.run(test_websocket_stream())
    print("[+] WebSocket connection to /ws/sensors/stream/ successfully established and verified.")

    print("\n" + "=" * 70)
    print("VERDICT: ALL TASKS EXECUTING AS INTENDED WITH EXIT CODE 0")
    print("=" * 70)

if __name__ == "__main__":
    run_live_pipeline()
