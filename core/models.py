"""Core utility models and mixins for the trading platform."""

from django.db import models
from django.utils import timezone
import logging


class TimeStampedModel(models.Model):
    """Abstract base class with created_at and updated_at fields."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class LogEntry(TimeStampedModel):
    """Model to store application logs."""
    level = models.CharField(max_length=20, choices=[
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ])
    logger_name = models.CharField(max_length=100)
    message = models.TextField()
    module = models.CharField(max_length=100, blank=True)
    function = models.CharField(max_length=100, blank=True)
    line_number = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['level', '-created_at']),
            models.Index(fields=['logger_name', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.level} - {self.logger_name} - {self.message[:50]}"


class Configuration(TimeStampedModel):
    """Model to store dynamic configuration values."""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['key']
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}"
