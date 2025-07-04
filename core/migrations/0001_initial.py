# Generated by Django 5.2.3 on 2025-07-01 23:31

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Configuration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('key', models.CharField(max_length=100, unique=True)),
                ('value', models.TextField()),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['key'],
            },
        ),
        migrations.CreateModel(
            name='LogEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('level', models.CharField(choices=[('DEBUG', 'Debug'), ('INFO', 'Info'), ('WARNING', 'Warning'), ('ERROR', 'Error'), ('CRITICAL', 'Critical')], max_length=20)),
                ('logger_name', models.CharField(max_length=100)),
                ('message', models.TextField()),
                ('module', models.CharField(blank=True, max_length=100)),
                ('function', models.CharField(blank=True, max_length=100)),
                ('line_number', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['level', '-created_at'], name='core_logent_level_bc0a5a_idx'), models.Index(fields=['logger_name', '-created_at'], name='core_logent_logger__142b50_idx')],
            },
        ),
    ]
