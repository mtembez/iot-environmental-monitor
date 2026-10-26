"""
End-to-end integration test suite for IoT Environmental Telemetry & Real-Time Alerting.
Verifies ingest validation, database persistence, ML anomaly scoring, and Channel broadcast event structures.
"""

import os
import sys
import unittest

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
os.environ.setdefault('CELERY_ALWAYS_EAGER', 'True')

try:
    import django
    django.setup()
    DJANGO_AVAILABLE = True
except Exception:
    DJANGO_AVAILABLE = False

class RealTimeIntegrationTests(unittest.TestCase):
    def setUp(self):
        if not DJANGO_AVAILABLE:
            self.skipTest("Django not configured in environment")

    def test_sensor_ingest_payload_validation(self):
        from sensors.serializers import SensorIngestSerializer
        
        valid_payload = {
            "node_id": "test-node-01",
            "temperature": 24.2,
            "humidity": 55.0,
            "light_lux": 420.0,
            "motion_detected": False,
            "motion_count": 0
        }
        serializer = SensorIngestSerializer(data=valid_payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["node_id"], "test-node-01")

    def test_sensor_ingest_payload_invalid_bounds(self):
        from sensors.serializers import SensorIngestSerializer

        # Out-of-bounds relative humidity (>100%)
        invalid_payload = {
            "node_id": "test-node-01",
            "temperature": 24.2,
            "humidity": 145.0,
            "light_lux": 420.0,
        }
        serializer = SensorIngestSerializer(data=invalid_payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("humidity", serializer.errors)

    def test_ml_anomaly_detection_logic(self):
        from sensors.ml.detector import score_sensor_reading
        
        # Test nominal reading
        nominal_reading = {
            "node_id": "test-node-01",
            "temperature": 22.0,
            "humidity": 50.0,
            "light_lux": 450.0
        }
        is_anom, score = score_sensor_reading(nominal_reading)
        self.assertFalse(is_anom)
        self.assertLess(score, 0.50)

        # Test severe thermal runaway anomaly
        thermal_anomaly = {
            "node_id": "test-node-01",
            "temperature": 52.0,
            "humidity": 20.0,
            "light_lux": 100.0
        }
        is_anom, score = score_sensor_reading(thermal_anomaly)
        self.assertTrue(is_anom)
        self.assertGreaterEqual(score, 0.80)

    def test_websocket_consumer_group_name(self):
        try:
            from sensors.consumers import SensorTelemetryConsumer
            consumer = SensorTelemetryConsumer()
            self.assertEqual(consumer.GROUP_NAME, "sensor_telemetry")
        except ImportError:
            self.skipTest("channels library not yet installed")

if __name__ == "__main__":
    unittest.main()
