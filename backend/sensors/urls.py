from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SensorIngestView,
    SensorHistoryView,
    SensorLatestView,
    AnomalyEventListView,
    AlertThresholdViewSet,
    AnomalyHeatmapView,
)

router = DefaultRouter()
router.register(r'thresholds', AlertThresholdViewSet, basename='threshold')

urlpatterns = [
    path('ingest/', SensorIngestView.as_view(), name='sensor-ingest'),
    path('readings/', SensorHistoryView.as_view(), name='sensor-readings'),
    path('latest/', SensorLatestView.as_view(), name='sensor-latest'),
    path('anomalies/', AnomalyEventListView.as_view(), name='sensor-anomalies'),
    path('heatmap/', AnomalyHeatmapView.as_view(), name='sensor-heatmap'),
    path('', include(router.urls)),
]
