"""Core API views."""

from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.http import HttpResponse
from django.shortcuts import render
from .models import LogEntry, Configuration
from .services import MarketService
from .serializers import LogEntrySerializer, ConfigurationSerializer


def home_view(request):
    """Home page view with navigation and platform overview."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Django Trading Platform</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
            .container { max-width: 1200px; margin: 0 auto; padding: 40px 20px; }
            .header { text-align: center; margin-bottom: 50px; color: white; }
            .header h1 { font-size: 3rem; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
            .header p { font-size: 1.2rem; opacity: 0.9; }
            .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 25px; margin-bottom: 40px; }
            .card { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.1); transition: all 0.3s ease; }
            .card:hover { transform: translateY(-5px); box-shadow: 0 15px 35px rgba(0,0,0,0.15); }
            .card h3 { color: #2c3e50; margin: 0 0 15px 0; font-size: 1.4rem; display: flex; align-items: center; }
            .card p { color: #7f8c8d; margin-bottom: 20px; line-height: 1.6; }
            .btn { display: inline-block; background: #3498db; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; transition: all 0.3s; font-weight: 500; }
            .btn:hover { background: #2980b9; transform: translateY(-2px); }
            .status-bar { background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); padding: 20px; border-radius: 15px; margin-bottom: 30px; color: white; }
            .status-item { display: inline-block; margin-right: 30px; }
            .api-section { background: rgba(255,255,255,0.95); padding: 30px; border-radius: 15px; }
            .api-section h3 { color: #2c3e50; margin-bottom: 20px; }
            .api-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }
            .api-item { background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #3498db; }
            .api-item a { color: #3498db; text-decoration: none; font-weight: 500; }
            .api-item a:hover { text-decoration: underline; }
            .emoji { font-size: 1.2em; margin-right: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 Django Trading Platform</h1>
                <p>Advanced Algorithmic Trading System for Indian Stock Markets</p>
            </div>
            
            <div class="status-bar">
                <div class="status-item"><strong>✅ Server:</strong> Running</div>
                <div class="status-item"><strong>🐍 Django:</strong> 5.2.3</div>
                <div class="status-item"><strong>📊 Market:</strong> Ready</div>
                <div class="status-item"><strong>🤖 Bot:</strong> Available</div>
            </div>
            
            <div class="cards">
                <div class="card">
                    <h3><span class="emoji">🔧</span>Admin Dashboard</h3>
                    <p>Configure trading strategies, manage user accounts, monitor system performance, and access comprehensive administrative tools.</p>
                    <a href="/admin/" class="btn">Access Admin Panel</a>
                </div>
                
                <div class="card">
                    <h3><span class="emoji">📊</span>Angel One Integration</h3>
                    <p>Real-time market data, order placement, portfolio tracking, and seamless integration with Angel One trading platform.</p>
                    <a href="/api/angel/setup/" class="btn">Setup Angel One API</a>
                </div>
                
                <div class="card">
                    <h3><span class="emoji">💼</span>Portfolio Management</h3>
                    <p>Track multiple portfolios, analyze performance metrics, monitor positions, and review detailed transaction history.</p>
                    <a href="/api/portfolio/" class="btn">Manage Portfolios</a>
                </div>
                
                <div class="card">
                    <h3><span class="emoji">🤖</span>Trading Automation</h3>
                    <p>Deploy automated trading strategies, configure risk management, backtest algorithms, and monitor bot performance.</p>
                    <a href="/api/trading/" class="btn">Trading Strategies</a>
                </div>
            </div>
            
            <div class="api-section">
                <h3>📡 Available API Endpoints</h3>
                <div class="api-list">
                    <div class="api-item">
                        <strong>Angel One API</strong><br>
                        <a href="/api/angel/">/api/angel/</a><br>
                        <small>Market data, orders, portfolio</small>
                    </div>
                    <div class="api-item">
                        <strong>Portfolio API</strong><br>
                        <a href="/api/portfolio/">/api/portfolio/</a><br>
                        <small>Portfolio management</small>
                    </div>
                    <div class="api-item">
                        <strong>Trading API</strong><br>
                        <a href="/api/trading/">/api/trading/</a><br>
                        <small>Strategies and automation</small>
                    </div>
                    <div class="api-item">
                        <strong>Core API</strong><br>
                        <a href="/api/core/">/api/core/</a><br>
                        <small>System utilities</small>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html_content)


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
