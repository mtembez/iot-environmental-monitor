#!/usr/bin/env python3
"""
IoT Environmental Monitoring - Serial Ingestion Daemon
Reads JSON telemetry frames from hardware serial / PTY, validates schema,
buffers records during network partitions, and relays via authenticated HTTP.
"""

import argparse
import collections
import json
import logging
import os
import signal
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Deque, Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [ingestion_daemon] %(message)s"
)
logger = logging.getLogger("ingestion_daemon")

DEFAULT_API_URL = "http://127.0.0.1:8000/api/v1/sensors/ingest/"
DEFAULT_SERIAL_PORT = "/dev/ttyACM0"
DEFAULT_BAUD = 115200
BUFFER_CAPACITY = 1000

class SerialIngestionDaemon:
    def __init__(
        self,
        port: str = DEFAULT_SERIAL_PORT,
        baud: int = DEFAULT_BAUD,
        api_url: str = DEFAULT_API_URL,
        api_key: str = "enviro-secret-token",
        mock_mode: bool = False,
    ) -> None:
        self.port = port
        self.baud = baud
        self.api_url = api_url
        self.api_key = api_key
        self.mock_mode = mock_mode
        self.running = False
        self.buffer: Deque[Dict[str, Any]] = collections.deque(maxlen=BUFFER_CAPACITY)

    def validate_payload(self, raw_line: str) -> Optional[Dict[str, Any]]:
        raw_line = raw_line.strip()
        if not raw_line:
            return None
        try:
            payload = json.loads(raw_line)
        except json.JSONDecodeError:
            logger.warning(f"Malformed JSON frame received: {raw_line[:80]}")
            return None

        required_keys = {"node_id", "temp", "humidity", "light_adc", "motion"}
        if not required_keys.issubset(payload.keys()):
            logger.warning(f"Payload missing required schema keys: {payload}")
            return None

        try:
            return {
                "node_id": str(payload["node_id"]),
                "temperature": float(payload["temp"]),
                "humidity": float(payload["humidity"]),
                "light_lux": float(payload["light_adc"]) * 0.976, # 1024 ADC approx scale
                "motion_detected": bool(payload["motion"]),
                "motion_count": int(payload.get("motion_count", 0)),
                "timestamp": float(payload.get("ts", time.time())),
            }
        except (ValueError, TypeError) as err:
            logger.warning(f"Type validation failed on payload: {err}")
            return None

    def post_reading(self, reading: Dict[str, Any]) -> bool:
        data = json.dumps(reading).encode("utf-8")
        req = urllib.request.Request(
            self.api_url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "X-Sensor-Key": self.api_key,
                "User-Agent": "IoT-Ingestion-Daemon/1.0",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                return resp.status in (200, 201)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as err:
            logger.warning(f"Relay failed (enqueuing to buffer): {err}")
            return False

    def flush_buffer(self) -> None:
        while self.buffer:
            item = self.buffer[0]
            if self.post_reading(item):
                self.buffer.popleft()
            else:
                break

    def run_mock_stream(self) -> None:
        import random
        logger.info("Starting ingestion daemon in SYNTHETIC/MOCK stream mode.")
        counter = 0
        while self.running:
            counter += 1
            # Generate nominal values with intermittent anomalies
            is_anomaly = (counter % 20 == 0)
            temp = random.uniform(36.0, 48.0) if is_anomaly else random.uniform(21.0, 25.5)
            hum = random.uniform(85.0, 95.0) if is_anomaly else random.uniform(45.0, 60.0)
            light = random.uniform(10.0, 900.0)
            motion = random.choice([True, False])

            sample = {
                "node_id": "iot-enviro-01",
                "temp": round(temp, 2),
                "humidity": round(hum, 2),
                "light_adc": int(light),
                "motion": 1 if motion else 0,
                "motion_count": counter,
                "ts": time.time(),
            }
            raw_line = json.dumps(sample)
            validated = self.validate_payload(raw_line)
            if validated:
                if not self.post_reading(validated):
                    self.buffer.append(validated)
                else:
                    self.flush_buffer()
            time.sleep(1.0)

    def start(self) -> None:
        self.running = True

        def _sig_handler(sig, frame):
            logger.info("Signal received. Initiating graceful shutdown...")
            self.running = False

        signal.signal(signal.SIGINT, _sig_handler)
        signal.signal(signal.SIGTERM, _sig_handler)

        if self.mock_mode or not os.path.exists(self.port):
            if not self.mock_mode:
                logger.warning(f"Device {self.port} not found. Falling back to synthetic mock stream.")
            self.run_mock_stream()
            return

        # Hardware serial ingestion loop
        try:
            import serial
        except ImportError:
            logger.error("pyserial package not installed for physical serial interface. Running mock.")
            self.run_mock_stream()
            return

        while self.running:
            try:
                logger.info(f"Opening serial port {self.port} at {self.baud} baud...")
                with serial.Serial(self.port, self.baud, timeout=1.0) as ser:
                    while self.running:
                        line = ser.readline().decode("utf-8", errors="replace")
                        validated = self.validate_payload(line)
                        if validated:
                            if not self.post_reading(validated):
                                self.buffer.append(validated)
                            else:
                                self.flush_buffer()
            except Exception as err:
                logger.error(f"Serial I/O fault: {err}. Reconnecting in 3s...")
                time.sleep(3.0)

        logger.info("Daemon terminated cleanly.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IoT Environmental Serial Ingestion Daemon")
    parser.add_argument("--port", default=DEFAULT_SERIAL_PORT, help="Serial device path")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD, help="Baud rate")
    parser.add_argument("--url", default=DEFAULT_API_URL, help="Backend ingestion endpoint")
    parser.add_argument("--key", default="enviro-secret-token", help="API key for ingestion auth")
    parser.add_argument("--mock", action="store_true", help="Force synthetic data generator")
    args = parser.parse_args()

    daemon = SerialIngestionDaemon(
        port=args.port,
        baud=args.baud,
        api_url=args.url,
        api_key=args.key,
        mock_mode=args.mock,
    )
    daemon.start()
