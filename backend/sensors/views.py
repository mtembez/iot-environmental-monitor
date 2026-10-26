from datetime import timedelta
from django.conf import settings
from django.db.models import Count, Q, Avg
from django.utils import timezone
from rest_framework import status, views, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import SensorReading, AlertThreshold, AnomalyEvent
from .serializers import (
    SensorReadingSerializer,
    SensorIngestSerializer,
    AlertThresholdSerializer,
    AnomalyEventSerializer,
)
from .tasks import process_sensor_anomaly_task

class SensorIngestView(views.APIKeyProtectedView if hasattr(views, 'APIKeyProtectedView') else views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Authenticate via custom header
        auth_key = request.headers.get('X-Sensor-Key')
        expected_key = getattr(settings, 'SENSOR_INGEST_API_KEY', 'enviro-secret-token')
        if not auth_key or auth_key != expected_key:
            return Response(
                {"error": "Unauthorized. Valid X-Sensor-Key header required."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = SensorIngestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        reading = SensorReading.objects.create(
            node_id=data['node_id'],
            temperature=data['temperature'],
            humidity=data['humidity'],
            light_lux=data['light_lux'],
            motion_detected=data.get('motion_detected', False),
            motion_count=data.get('motion_count', 0),
        )

        # Trigger Celery anomaly scoring task asynchronously (or eager if CELERY_TASK_ALWAYS_EAGER)
        process_sensor_anomaly_task.delay(reading.id)

        # Refresh from DB if eager
        reading.refresh_from_db()

        return Response(
            {
                "status": "ingested",
                "reading_id": reading.id,
                "node_id": reading.node_id,
                "is_anomaly": reading.is_anomaly,
                "anomaly_score": reading.anomaly_score,
                "created_at": reading.created_at,
            },
            status=status.HTTP_201_CREATED
        )

class SensorHistoryView(views.APIView):
    """
    Returns historical telemetry records with query filtering by node_id, anomaly status,
    and ISO-8601 time windows.
    """
    def get(self, request):
        queryset = SensorReading.objects.all()

        node_id = request.query_params.get('node_id')
        if node_id:
            queryset = queryset.filter(node_id=node_id)

        is_anomaly = request.query_params.get('is_anomaly')
        if is_anomaly is not None:
            if is_anomaly.lower() in ('true', '1'):
                queryset = queryset.filter(is_anomaly=True)
            elif is_anomaly.lower() in ('false', '0'):
                queryset = queryset.filter(is_anomaly=False)

        hours = request.query_params.get('hours')
        if hours:
            try:
                since = timezone.now() - timedelta(hours=float(hours))
                queryset = queryset.filter(created_at__gte=since)
            except ValueError:
                pass

        limit = min(int(request.query_params.get('limit', 100)), 1000)
        readings = queryset[:limit]
        serializer = SensorReadingSerializer(readings, many=True)
        return Response({"count": len(serializer.data), "results": serializer.data})

class SensorLatestView(views.APIView):
    """
    Returns latest telemetry snapshot for polling clients.
    """
    def get(self, request):
        node_id = request.query_params.get('node_id')
        if node_id:
            latest = SensorReading.objects.filter(node_id=node_id).first()
            if not latest:
                return Response({"error": "Node not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response(SensorReadingSerializer(latest).data)

        # Unique latest readings for each active node
        active_nodes = SensorReading.objects.values_list('node_id', flat=True).distinct()
        results = []
        for n in active_nodes:
            latest = SensorReading.objects.filter(node_id=n).first()
            if latest:
                results.append(SensorReadingSerializer(latest).data)
        return Response(results)

class AnomalyEventListView(views.APIView):
    def get(self, request):
        events = AnomalyEvent.objects.select_related('reading').all()[:100]
        serializer = AnomalyEventSerializer(events, many=True)
        return Response(serializer.data)

class AlertThresholdViewSet(viewsets.ModelViewSet):
    queryset = AlertThreshold.objects.all()
    serializer_class = AlertThresholdSerializer

class AnomalyHeatmapView(views.APIView):
    """
    Aggregates anomaly frequency into hourly buckets for dashboard heatmap rendering.
    """
    def get(self, request):
        since = timezone.now() - timedelta(hours=24)
        readings = SensorReading.objects.filter(created_at__gte=since)
        
        total_count = readings.count()
        anomaly_count = readings.filter(is_anomaly=True).count()
        avg_temp = readings.aggregate(Avg('temperature'))['temperature__avg'] or 0.0
        avg_hum = readings.aggregate(Avg('humidity'))['humidity__avg'] or 0.0

        return Response({
            "window_hours": 24,
            "total_samples": total_count,
            "anomaly_samples": anomaly_count,
            "anomaly_rate_pct": round((anomaly_count / total_count * 100), 2) if total_count > 0 else 0.0,
            "avg_temperature": round(avg_temp, 2),
            "avg_humidity": round(avg_hum, 2),
        })
