import logging
from celery import shared_task
from .models import SensorReading, AnomalyEvent, AlertThreshold
from .ml.detector import score_sensor_reading

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def process_sensor_anomaly_task(self, reading_id: int):
    """
    Asynchronous Celery task that scores new sensor readings via Isolation Forest,
    updates the anomaly flag & score, and evaluates against threshold alerts.
    """
    try:
        reading = SensorReading.objects.get(id=reading_id)
    except SensorReading.DoesNotExist:
        logger.error(f"SensorReading {reading_id} not found.")
        return

    sample = {
        "node_id": reading.node_id,
        "temperature": reading.temperature,
        "humidity": reading.humidity,
        "light_lux": reading.light_lux,
        "motion_detected": reading.motion_detected,
    }

    # Evaluate reading against trained anomaly detection model
    is_anomaly, score = score_sensor_reading(sample)

    reading.anomaly_score = score
    reading.is_anomaly = is_anomaly
    reading.save(update_fields=['anomaly_score', 'is_anomaly'])

    # Evaluate static alert thresholds
    threshold_breached = False
    reasons = []

    active_thresholds = AlertThreshold.objects.filter(is_active=True)
    for th in active_thresholds:
        val = getattr(reading, th.metric, None)
        if val is not None:
            if th.min_value is not None and val < th.min_value:
                reasons.append(f"{th.metric} ({val}) below min limit ({th.min_value})")
                threshold_breached = True
            if th.max_value is not None and val > th.max_value:
                reasons.append(f"{th.metric} ({val}) above max limit ({th.max_value})")
                threshold_breached = True

    if is_anomaly or threshold_breached:
        desc = "; ".join(reasons) if reasons else f"Statistical anomaly detected (Score: {score:.2f})"
        severity = 'critical' if score >= 0.85 or (reading.temperature > 45.0 or reading.temperature < 0.0) else 'medium'
        
        AnomalyEvent.objects.update_or_create(
            reading=reading,
            defaults={
                'anomaly_score': score,
                'description': desc,
                'severity': severity,
            }
        )
        logger.warning(f"ALERT logged for node {reading.node_id}: {desc} (Severity: {severity})")

        # Broadcast real-time anomaly alert event to connected WebSocket clients
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    "sensor_telemetry",
                    {
                        "type": "anomaly.alert",
                        "payload": {
                            "reading_id": reading.id,
                            "node_id": reading.node_id,
                            "temperature": reading.temperature,
                            "humidity": reading.humidity,
                            "anomaly_score": score,
                            "description": desc,
                            "severity": severity,
                            "created_at": reading.created_at.isoformat() if reading.created_at else None,
                        }
                    }
                )
        except Exception:
            pass

    return {"reading_id": reading_id, "is_anomaly": is_anomaly, "score": score}
