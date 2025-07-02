"""Angel API views."""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.conf import settings
from pyngrok import ngrok, conf
import json

from .models import AngelOneSession, NSESymbol, MarketData, APILog, Order
from .services import AngelOneAPI
from .serializers import (
    AngelOneSessionSerializer, NSESymbolSerializer, MarketDataSerializer,
    APILogSerializer, OrderSerializer, PlaceOrderSerializer, AuthenticationSerializer
)
from .utils import get_callback_urls, update_angel_one_redirect_uri


class NSESymbolViewSet(viewsets.ModelViewSet):
    """ViewSet for NSE symbols."""
    queryset = NSESymbol.objects.all()
    serializer_class = NSESymbolSerializer
    filterset_fields = ['exchange', 'instrument_type']
    search_fields = ['symbol', 'company_name']
    ordering = ['symbol']


class MarketDataViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for market data."""
    queryset = MarketData.objects.all()
    serializer_class = MarketDataSerializer
    filterset_fields = ['symbol', 'data_timestamp']
    ordering = ['-data_timestamp']


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for orders."""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filterset_fields = ['symbol', 'status', 'transaction_type']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter orders by user's portfolio if needed."""
        return self.queryset.all()


class AuthenticationView(APIView):
    """View for Angel One authentication."""
    permission_classes = []  # Allow unauthenticated access for login
    
    def post(self, request):
        serializer = AuthenticationSerializer(data=request.data)
        if serializer.is_valid():
            angel_api = AngelOneAPI()
            
            success, result = angel_api.authenticate(
                client_id=serializer.validated_data['client_id'],
                password=serializer.validated_data['password'],
                totp=serializer.validated_data['totp']
            )
            
            if success:
                return Response({
                    'success': True,
                    'message': 'Authentication successful',
                    'session_data': result
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': result
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LTPView(APIView):
    """View to get Last Traded Price for a symbol."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, symbol):
        try:
            angel_api = AngelOneAPI()
            price = angel_api.get_ltp(symbol)
            
            return Response({
                'symbol': symbol,
                'ltp': price,
                'timestamp': timezone.now()
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PortfolioView(APIView):
    """View to get portfolio holdings."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            angel_api = AngelOneAPI()
            portfolio = angel_api.get_portfolio()
            
            return Response({
                'portfolio': portfolio,
                'timestamp': timezone.now()
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BalanceView(APIView):
    """View to get account balance."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            angel_api = AngelOneAPI()
            balance = angel_api.get_balance()
            
            return Response({
                'balance': balance,
                'timestamp': timezone.now()
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PlaceOrderView(APIView):
    """View to place orders."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = PlaceOrderSerializer(data=request.data)
        if serializer.is_valid():
            try:
                angel_api = AngelOneAPI()
                
                success, result = angel_api.place_order(
                    symbol=serializer.validated_data['symbol'],
                    quantity=serializer.validated_data['quantity'],
                    price=serializer.validated_data.get('price'),
                    order_type=serializer.validated_data['order_type'],
                    transaction_type=serializer.validated_data['transaction_type']
                )
                
                if success:
                    return Response({
                        'success': True,
                        'order_id': result,
                        'message': 'Order placed successfully'
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response({
                        'success': False,
                        'message': result
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except Exception as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AuthCallbackView(APIView):
    """OAuth callback view for Angel One authentication."""
    permission_classes = []  # Allow unauthenticated access
    
    def get(self, request):
        """Handle OAuth callback from Angel One."""
        try:
            # Get authorization code from callback
            auth_code = request.GET.get('code')
            state = request.GET.get('state')
            error = request.GET.get('error')
            
            if error:
                return HttpResponse(f"""
                    <html>
                    <head><title>Angel One Authentication Error</title></head>
                    <body>
                        <h1>❌ Authentication Failed</h1>
                        <p>Error: {error}</p>
                        <p>Please try again or check your Angel One API credentials.</p>
                        <a href="/admin/">← Back to Admin</a>
                    </body>
                    </html>
                """, status=400)
            
            if not auth_code:
                return HttpResponse(f"""
                    <html>
                    <head><title>Angel One Authentication</title></head>
                    <body>
                        <h1>🔑 Angel One Authentication Required</h1>
                        <p>No authorization code received. Please ensure you've completed the OAuth flow.</p>
                        <a href="/admin/">← Back to Admin</a>
                    </body>
                    </html>
                """, status=400)
            
            # Process the authorization code
            # This is where you would exchange the auth code for an access token
            # For now, we'll show a success page
            
            return HttpResponse(f"""
                <html>
                <head>
                    <title>Angel One Authentication Success</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                        .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        .success {{ color: #27ae60; }}
                        .info {{ background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1 class="success">✅ Angel One Authentication Successful!</h1>
                        <p>Authorization code received successfully.</p>
                        
                        <div class="info">
                            <strong>📋 Next Steps:</strong><br>
                            1. Go to Django Admin to configure your Angel One credentials<br>
                            2. Save your client ID, password, and TOTP secret<br>
                            3. Test the API connection<br>
                            4. Start your trading bot
                        </div>
                        
                        <p>
                            <a href="/admin/" style="background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                                📊 Go to Admin Panel
                            </a>
                        </p>
                        
                        <hr>
                        <small>
                            <strong>Auth Code:</strong> <code>{auth_code[:20]}...</code><br>
                            <strong>State:</strong> <code>{state or 'N/A'}</code><br>
                            <strong>Timestamp:</strong> {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
                        </small>
                    </div>
                </body>
                </html>
            """)
            
        except Exception as e:
            return HttpResponse(f"""
                <html>
                <head><title>Angel One Authentication Error</title></head>
                <body>
                    <h1>❌ Authentication Error</h1>
                    <p>An error occurred during authentication: {str(e)}</p>
                    <a href="/admin/">← Back to Admin</a>
                </body>
                </html>
            """, status=500)
    
    def post(self, request):
        """Handle POST callback if needed."""
        return self.get(request)


class AngelOneSetupView(APIView):
    """View to show Angel One API setup instructions."""
    permission_classes = []
    
    def get(self, request):
        """Show setup instructions."""
        redirect_url = request.build_absolute_uri('/api/angel/auth/callback/')
        
        return HttpResponse(f"""
            <html>
            <head>
                <title>Angel One API Setup</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                    .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .code {{ background: #f8f9fa; padding: 10px; border-radius: 5px; font-family: monospace; margin: 10px 0; }}
                    .step {{ margin: 20px 0; padding: 15px; border-left: 4px solid #3498db; background: #f8f9fa; }}
                    .important {{ background: #fff3cd; border-color: #ffc107; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🔑 Angel One API Setup Instructions</h1>
                    
                    <div class="important">
                        <strong>⚠️ Important:</strong> Use this exact redirect URL when setting up your Angel One API application.
                    </div>
                    
                    <div class="step">
                        <h3>Step 1: Angel One Developer Portal</h3>
                        <p>1. Go to <a href="https://smartapi.angelbroking.com/" target="_blank">Angel One SmartAPI Portal</a></p>
                        <p>2. Login with your Angel One credentials</p>
                        <p>3. Create a new app or edit existing app</p>
                    </div>
                    
                    <div class="step">
                        <h3>Step 2: Configure Redirect URL</h3>
                        <p>In the Angel One app configuration, set the <strong>Redirect URL</strong> to:</p>
                        <div class="code">{redirect_url}</div>
                        <p><em>Copy this URL exactly as shown above!</em></p>
                        
                        <div class="important">
                            <strong>⚠️ If Angel One shows "Please enter valid url" error:</strong><br>
                            • Many OAuth providers don't accept localhost URLs<br>
                            • Try using <a href="/api/angel/ngrok-setup/">ngrok</a> to create a public HTTPS URL<br>
                            • Or use the <a href="/api/angel/url-config/">URL Configuration Manager</a> for alternatives
                        </div>
                    </div>
                    
                    <div class="step">
                        <h3>Step 3: Get Your Credentials</h3>
                        <p>From Angel One portal, copy:</p>
                        <ul>
                            <li><strong>API Key</strong> (Client ID)</li>
                            <li><strong>Client Secret</strong></li>
                            <li>Your <strong>Angel One Login Password</strong></li>
                            <li><strong>TOTP Secret</strong> (for 2FA)</li>
                        </ul>
                    </div>
                    
                    <div class="step">
                        <h3>Step 4: Configure Django Settings</h3>
                        <p>Add these environment variables or update settings.py:</p>
                        <div class="code">
                            ANGEL_CLIENT_ID=your_api_key_here<br>
                            ANGEL_PASSWORD=your_password_here<br>
                            ANGEL_TOTP_SECRET=your_totp_secret_here
                        </div>
                    </div>
                    
                    <div class="step">
                        <h3>Step 5: Test Authentication</h3>
                        <p>After configuration, test the API using:</p>
                        <ul>
                            <li><a href="/admin/">Django Admin Panel</a></li>
                            <li><a href="/api/angel/">Angel API Endpoints</a></li>
                        </ul>
                    </div>
                    
                    <p style="text-align: center; margin-top: 40px;">
                        <a href="/" style="background: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">
                            ← Back to Dashboard
                        </a>
                    </p>
                </div>
            </body>
            </html>
        """)


class NgrokSetupView(APIView):
    """View to set up ngrok for OAuth testing."""
    permission_classes = []
    
    def get(self, request):
        """Set up ngrok and display public URL."""
        try:
            # Check if ngrok is already running
            tunnels = ngrok.get_tunnels()
            if tunnels:
                public_url = tunnels[0].public_url
            else:
                # Start a new tunnel
                # Set default config for ngrok
                conf.get_default().auth_token = settings.NGROK_AUTH_TOKEN if hasattr(settings, 'NGROK_AUTH_TOKEN') else None
                public_url = ngrok.connect(8000, bind_tls=True)
                if isinstance(public_url, str):
                    # For older pyngrok versions
                    pass
                else:
                    # For newer pyngrok versions
                    public_url = public_url.public_url
            
            # Get the callback path
            callback_path = reverse('angel_callback')
            
            # Build the full callback URL
            if public_url.endswith('/'):
                public_url = public_url[:-1]
            
            callback_url = f"{public_url}{callback_path}"
            
            # Update settings dynamically
            if hasattr(settings, 'ANGEL_ONE_CONFIG'):
                settings.ANGEL_ONE_CONFIG['REDIRECT_URI'] = callback_url
            
            return HttpResponse(f"""
                <html>
                <head>
                    <title>Ngrok Setup for Angel One API</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        .code {{ background: #f8f9fa; padding: 10px; border-radius: 5px; font-family: monospace; margin: 10px 0; overflow-wrap: break-word; }}
                        .step {{ margin: 20px 0; padding: 15px; border-left: 4px solid #3498db; background: #f8f9fa; }}
                        .important {{ background: #fff3cd; border-color: #ffc107; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                        .success {{ color: #27ae60; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1 class="success">🚀 Ngrok Tunnel Established</h1>
                        
                        <div class="important">
                            <strong>⚠️ Important:</strong> Use this HTTPS URL as your Redirect URL in the Angel One API developer portal.
                        </div>
                        
                        <div class="step">
                            <h3>Your Public Callback URL:</h3>
                            <div class="code">{callback_url}</div>
                            <p><em>Copy this URL and use it as your Redirect URL in Angel One API settings!</em></p>
                        </div>
                        
                        <div class="step">
                            <h3>Ngrok Tunnel Information:</h3>
                            <p><strong>Base Public URL:</strong> {public_url}</p>
                            <p><strong>Local server:</strong> http://localhost:8000</p>
                            <p><strong>Status:</strong> Active</p>
                        </div>
                        
                        <div class="step">
                            <h3>Next Steps:</h3>
                            <ol>
                                <li>Copy the callback URL above</li>
                                <li>Go to the <a href="https://smartapi.angelbroking.com/" target="_blank">Angel One SmartAPI Portal</a></li>
                                <li>Update your app's Redirect URL with the URL above</li>
                                <li>Save your changes and test the authentication</li>
                            </ol>
                        </div>
                        
                        <p style="text-align: center; margin-top: 40px;">
                            <a href="/api/angel/setup/" style="background: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin-right: 15px;">
                                Setup Instructions
                            </a>
                            <a href="/" style="background: #27ae60; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">
                                Back to Dashboard
                            </a>
                        </p>
                    </div>
                </body>
                </html>
            """)
        except Exception as e:
            return HttpResponse(f"""
                <html>
                <head><title>Ngrok Setup Error</title></head>
                <body>
                    <h1>❌ Ngrok Setup Error</h1>
                    <p>An error occurred while setting up ngrok: {str(e)}</p>
                    <p>Make sure ngrok is installed and configured properly.</p>
                    <p>To install ngrok manually: <code>pip install pyngrok</code></p>
                    <p>For best results, configure an auth token in settings.py:</p>
                    <pre>NGROK_AUTH_TOKEN = 'your_token_here'</pre>
                    <a href="/api/angel/setup/">← Back to Setup</a>
                </body>
                </html>
            """, status=500)
