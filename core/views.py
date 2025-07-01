"""Core API views."""

from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from .models import LogEntry, Configuration
from .services import MarketService
from .serializers import LogEntrySerializer, ConfigurationSerializer


class LogEntryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing log entries."""
    queryset = LogEntry.objects.all()
    serializer_class = LogEntrySerializer
    filterset_fields = ['level', 'logger_name']
    ordering = ['-created_at']


class ConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing configuration."""
    queryset = Configuration.objects.all()
    serializer_class = ConfigurationSerializer
    filterset_fields = ['is_active']


class MarketStatusView(APIView):
    """View to get current market status."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        market_service = MarketService()
        status_data = market_service.get_market_status()
        return Response(status_data)


class HealthCheckView(APIView):
    """Health check endpoint."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now(),
            'version': '1.0.0'
        })
