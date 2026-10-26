import json
import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)

class SensorTelemetryConsumer(AsyncJsonWebsocketConsumer):
    GROUP_NAME = "sensor_telemetry"

    async def connect(self):
        """
        Invoked on WebSocket upgrade handshake.
        Joins the sensor telemetry broadcast channel group.
        """
        await self.channel_layer.group_add(
            self.GROUP_NAME,
            self.channel_name
        )
        await self.accept()
        logger.info(f"WebSocket client connected: {self.channel_name}")
        
        # Send initial connection acknowledgment
        await self.send_json({
            "type": "connection.established",
            "message": "Connected to IoT Environmental Telemetry stream",
            "group": self.GROUP_NAME,
        })

    async def disconnect(self, close_code):
        """
        Invoked on WebSocket termination.
        Leaves the telemetry broadcast channel group.
        """
        await self.channel_layer.group_discard(
            self.GROUP_NAME,
            self.channel_name
        )
        logger.info(f"WebSocket client disconnected: {self.channel_name} (Code: {close_code})")

    async def receive_json(self, content):
        """
        Handles incoming messages from the client (e.g. node filter subscription).
        """
        command = content.get("command")
        if command == "ping":
            await self.send_json({"type": "pong", "timestamp": content.get("timestamp")})
        elif command == "subscribe_node":
            node_id = content.get("node_id")
            await self.send_json({
                "type": "subscription.success",
                "node_id": node_id
            })

    async def telemetry_update(self, event):
        """
        Handler for group messages of type 'telemetry.update'.
        Dispatched by Django REST ingestion view.
        """
        await self.send_json({
            "type": "telemetry.update",
            "payload": event["payload"]
        })

    async def anomaly_alert(self, event):
        """
        Handler for group messages of type 'anomaly.alert'.
        Dispatched by Celery ML evaluation task.
        """
        await self.send_json({
            "type": "anomaly.alert",
            "payload": event["payload"]
        })
