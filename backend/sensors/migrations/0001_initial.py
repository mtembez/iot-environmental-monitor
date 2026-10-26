# Generated migration
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AlertThreshold',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('metric', models.CharField(choices=[('temperature', 'Temperature (°C)'), ('humidity', 'Humidity (%)'), ('light_lux', 'Light Intensity (Lux)')], max_length=32, unique=True)),
                ('min_value', models.FloatField(blank=True, null=True)),
                ('max_value', models.FloatField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='SensorReading',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('node_id', models.CharField(db_index=True, max_length=64)),
                ('temperature', models.FloatField(help_text='Ambient temperature in Celsius')),
                ('humidity', models.FloatField(help_text='Relative humidity in percentage (0-100)')),
                ('light_lux', models.FloatField(help_text='Ambient light intensity in Lux')),
                ('motion_detected', models.BooleanField(default=False)),
                ('motion_count', models.PositiveIntegerField(default=0)),
                ('anomaly_score', models.FloatField(db_index=True, default=0.0)),
                ('is_anomaly', models.BooleanField(db_index=True, default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['node_id', '-created_at'], name='sensors_sen_node_id_44f061_idx'),
                    models.Index(fields=['is_anomaly', '-created_at'], name='sensors_sen_is_anom_728ea7_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='AnomalyEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('anomaly_score', models.FloatField()),
                ('description', models.CharField(max_length=255)),
                ('severity', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('critical', 'Critical')], default='medium', max_length=16)),
                ('acknowledged', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('reading', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='anomaly_event', to='sensors.sensorreading')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
