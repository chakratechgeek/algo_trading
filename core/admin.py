"""Core admin configuration."""

from django.contrib import admin
from .models import LogEntry, Configuration


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ['level', 'logger_name', 'message', 'created_at']
    list_filter = ['level', 'logger_name', 'created_at']
    search_fields = ['message', 'logger_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'is_active', 'updated_at']
    list_filter = ['is_active', 'updated_at']
    search_fields = ['key', 'description']
    readonly_fields = ['created_at', 'updated_at']
