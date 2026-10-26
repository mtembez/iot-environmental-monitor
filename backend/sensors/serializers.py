from rest_framework import serializers
from .models import SensorReading, AlertThreshold, AnomalyEvent

class SensorReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorReading
        fields = [
            'id',
            'node_id',
            'temperature',
            'humidity',
            'light_lux',
            'motion_detected',
            'motion_count',
            'anomaly_score',
            'is_anomaly',
            'created_at',
        ]
        read_only_fields = ['id', 'anomaly_score', 'is_anomaly', 'created_at']

class SensorIngestSerializer(serializers.Serializer):
    node_id = serializers.CharField(max_length=64)
    temperature = serializers.FloatField()
    humidity = serializers.FloatField(min_value=0.0, max_value=100.0)
    light_lux = serializers.FloatField(min_value=0.0)
    motion_detected = serializers.BooleanField(default=False)
    motion_count = serializers.IntegerField(min_value=0, default=0)
    timestamp = serializers.FloatField(required=False)

class AlertThresholdSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertThreshold
        fields = ['id', 'metric', 'min_value', 'max_value', 'is_active', 'updated_at']

class AnomalyEventSerializer(serializers.ModelSerializer):
    node_id = serializers.CharField(source='reading.node_id', read_only=True)
    temperature = serializers.FloatField(source='reading.temperature', read_only=True)
    humidity = serializers.FloatField(source='reading.humidity', read_only=True)

    class Meta:
        model = AnomalyEvent
        fields = [
            'id',
            'reading_id',
            'node_id',
            'temperature',
            'humidity',
            'anomaly_score',
            'description',
            'severity',
            'acknowledged',
            'created_at',
        ]
