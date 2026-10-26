#!/usr/bin/env python3
import json
import os
import pty
import time
import unittest
from ingestion_daemon import SerialIngestionDaemon

class TestSerialIngestionDaemon(unittest.TestCase):
    def setUp(self):
        self.daemon = SerialIngestionDaemon(mock_mode=True)

    def test_validate_payload_valid(self):
        sample = {
            "node_id": "iot-enviro-01",
            "temp": 23.4,
            "humidity": 55.2,
            "light_adc": 500,
            "motion": 1,
            "motion_count": 12,
            "ts": 1729000000.0,
        }
        res = self.daemon.validate_payload(json.dumps(sample))
        self.assertIsNotNone(res)
        self.assertEqual(res["node_id"], "iot-enviro-01")
        self.assertAlmostEqual(res["temperature"], 23.4)
        self.assertAlmostEqual(res["humidity"], 55.2)
        self.assertTrue(res["motion_detected"])
        self.assertEqual(res["motion_count"], 12)

    def test_validate_payload_malformed(self):
        self.assertIsNone(self.daemon.validate_payload("NOT_JSON"))
        self.assertIsNone(self.daemon.validate_payload("{\"temp\": 25.0}"))

    def test_pty_serial_simulation(self):
        master, slave = pty.openpty()
        slave_name = os.ttyname(slave)
        self.assertTrue(os.path.exists(slave_name))
        
        test_payload = b'{"node_id":"pty-test","temp":21.5,"humidity":49.0,"light_adc":320,"motion":0}\n'
        os.write(master, test_payload)
        
        line = os.read(master, 1024).decode("utf-8")
        parsed = self.daemon.validate_payload(line)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["node_id"], "pty-test")
        
        os.close(master)
        os.close(slave)

if __name__ == "__main__":
    unittest.main()
