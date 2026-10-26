"""
Comprehensive Django REST Framework API Test Suite for IoT Environmental Monitor.
Tests all endpoints: Ingest, Query, Latest, Heatmap, Anomalies, and Thresholds.
"""

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
os.environ.setdefault('CELERY_ALWAYS_EAGER', 'True')

import django
django.setup()

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from sensors.models import SensorReading, AlertThreshold, AnomalyEvent

class SensorAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.api_key = "enviro-secret-token"

        # Seed sample baseline telemetry
        self.reading_nominal = SensorReading.objects.create(
            node_id="iot-enviro-01",
            temperature=22.5,
            humidity=50.0,
            light_lux=450.0,
            motion_detected=False,
            motion_count=0,
            anomaly_score=0.10,
            is_anomaly=False,
        )
        self.reading_anomaly = SensorReading.objects.create(
            node_id="iot-enviro-01",
            temperature=48.0,
            humidity=15.0,
            light_lux=100.0,
            motion_detected=True,
            motion_count=1,
            anomaly_score=0.92,
            is_anomaly=True,
        )
        self.anomaly_event = AnomalyEvent.objects.create(
            reading=self.reading_anomaly,
            anomaly_score=0.92,
            description="Extreme thermal runaway",
            severity="critical",
        )

    def test_ingest_unauthorized_without_key(self):
        payload = {
            "node_id": "iot-enviro-01",
            "temperature": 23.0,
            "humidity": 51.0,
            "light_lux": 400.0,
        }
        res = self.client.post("/api/v1/sensors/ingest/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ingest_success_with_key(self):
        payload = {
            "node_id": "iot-enviro-01",
            "temperature": 23.5,
            "humidity": 52.0,
            "light_lux": 420.0,
            "motion_detected": False,
            "motion_count": 0,
        }
        res = self.client.post(
            "/api/v1/sensors/ingest/",
            payload,
            format="json",
            HTTP_X_SENSOR_KEY=self.api_key
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["status"], "ingested")
        self.assertEqual(res.data["node_id"], "iot-enviro-01")

    def test_get_readings_history(self):
        res = self.client.get("/api/v1/sensors/readings/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(res.data["count"], 2)

    def test_get_readings_filtered_by_anomaly(self):
        res = self.client.get("/api/v1/sensors/readings/?is_anomaly=true")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for r in res.data["results"]:
            self.assertTrue(r["is_anomaly"])

    def test_get_latest_snapshot(self):
        res = self.client.get("/api/v1/sensors/latest/?node_id=iot-enviro-01")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["node_id"], "iot-enviro-01")

    def test_get_anomaly_events(self):
        res = self.client.get("/api/v1/sensors/anomalies/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["severity"], "critical")

    def test_get_heatmap_summary(self):
        res = self.client.get("/api/v1/sensors/heatmap/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("total_samples", res.data)
        self.assertIn("anomaly_rate_pct", res.data)
        self.assertIn("avg_temperature", res.data)

    def test_threshold_crud(self):
        # Create threshold
        res = self.client.post("/api/v1/sensors/thresholds/", {
            "metric": "temperature",
            "min_value": 18.0,
            "max_value": 30.0,
            "is_active": True,
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        th_id = res.data["id"]

        # Read threshold
        res_get = self.client.get(f"/api/v1/sensors/thresholds/{th_id}/")
        self.assertEqual(res_get.status_code, status.HTTP_200_OK)
        self.assertEqual(res_get.data["max_value"], 30.0)
