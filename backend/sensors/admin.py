from django.contrib import admin
from .models import SensorReading, AlertThreshold, AnomalyEvent

@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = ('node_id', 'temperature', 'humidity', 'light_lux', 'motion_detected', 'is_anomaly', 'created_at')
    list_filter = ('node_id', 'is_anomaly', 'created_at')
    search_fields = ('node_id',)

@admin.register(AlertThreshold)
class AlertThresholdAdmin(admin.ModelAdmin):
    list_display = ('metric', 'min_value', 'max_value', 'is_active', 'updated_at')
    list_editable = ('min_value', 'max_value', 'is_active')

@admin.register(AnomalyEvent)
class AnomalyEventAdmin(admin.ModelAdmin):
    list_display = ('reading', 'anomaly_score', 'severity', 'acknowledged', 'created_at')
    list_filter = ('severity', 'acknowledged')
