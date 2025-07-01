"""Core serializers."""

from rest_framework import serializers
from .models import LogEntry, Configuration


class LogEntrySerializer(serializers.ModelSerializer):
    """Serializer for log entries."""
    
    class Meta:
        model = LogEntry
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for configuration."""
    
    class Meta:
        model = Configuration
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
