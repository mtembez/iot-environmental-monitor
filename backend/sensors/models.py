from django.db import models

class SensorReading(models.Model):
    node_id = models.CharField(max_length=64, db_index=True)
    temperature = models.FloatField(help_text="Ambient temperature in Celsius")
    humidity = models.FloatField(help_text="Relative humidity in percentage (0-100)")
    light_lux = models.FloatField(help_text="Ambient light intensity in Lux")
    motion_detected = models.BooleanField(default=False)
    motion_count = models.PositiveIntegerField(default=0)
    anomaly_score = models.FloatField(default=0.0, db_index=True)
    is_anomaly = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['node_id', '-created_at']),
            models.Index(fields=['is_anomaly', '-created_at']),
        ]

    def __str__(self):
        return f"[{self.node_id}] {self.temperature}°C, {self.humidity}% @ {self.created_at}"

class AlertThreshold(models.Model):
    METRIC_CHOICES = [
        ('temperature', 'Temperature (°C)'),
        ('humidity', 'Humidity (%)'),
        ('light_lux', 'Light Intensity (Lux)'),
    ]

    metric = models.CharField(max_length=32, choices=METRIC_CHOICES, unique=True)
    min_value = models.FloatField(null=True, blank=True)
    max_value = models.FloatField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Threshold for {self.metric}: [{self.min_value} - {self.max_value}] (Active: {self.is_active})"

class AnomalyEvent(models.Model):
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('critical', 'Critical'),
    ]

    reading = models.OneToOneField(SensorReading, on_delete=models.CASCADE, related_name='anomaly_event')
    anomaly_score = models.FloatField()
    description = models.CharField(max_length=255)
    severity = models.CharField(max_length=16, choices=SEVERITY_CHOICES, default='medium')
    acknowledged = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Anomaly [{self.severity.upper()}] Node: {self.reading.node_id} (Score: {self.anomaly_score:.2f})"
