"""Angel One API service."""

import requests
import json
import time
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from .models import AngelOneSession, NSESymbol, MarketData, APILog, Order


class AngelOneAPI:
    """Service class for Angel One API integration."""
    
    def __init__(self):
        self.config = settings.ANGEL_ONE_CONFIG
        self.base_url = "https://apiconnect.angelbroking.com"
        self.logger = logging.getLogger('angel_api')
        self.session = None
        
    def _log_api_call(self, endpoint, method, request_data, status_code, response_data, response_time_ms, error_message=''):
        """Log API call details."""
        try:
            APILog.objects.create(
                endpoint=endpoint,
                method=method,
                request_data=request_data,
                status_code=status_code,
                response_data=response_data,
                response_time_ms=response_time_ms,
                error_message=error_message
            )
        except Exception as e:
            self.logger.error(f"Failed to log API call: {e}")
    
    def _make_request(self, endpoint, method='GET', data=None, headers=None):
        """Make HTTP request to Angel One API."""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        default_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-UserType': 'USER',
            'X-SourceID': 'WEB',
            'X-ClientLocalIP': '127.0.0.1',
            'X-ClientPublicIP': '127.0.0.1',
            'X-MACAddress': 'fe80::216c:f6ff:fe71:21c6',
        }
        
        if headers:
            default_headers.update(headers)
            
        try:
            if method.upper() == 'POST':
                response = requests.post(url, json=data, headers=default_headers, timeout=30)
            else:
                response = requests.get(url, params=data, headers=default_headers, timeout=30)
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            try:
                response_data = response.json()
            except:
                response_data = {'raw_response': response.text}
            
            self._log_api_call(
                endpoint=endpoint,
                method=method,
                request_data=data,
                status_code=response.status_code,
                response_data=response_data,
                response_time_ms=response_time_ms
            )
            
            return response, response_data
            
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            error_message = str(e)
            
            self._log_api_call(
                endpoint=endpoint,
                method=method,
                request_data=data,
                status_code=0,
                response_data=None,
                response_time_ms=response_time_ms,
                error_message=error_message
            )
            
            self.logger.error(f"API request failed: {e}")
            raise
    
    def authenticate(self, client_id, password, totp):
        """Authenticate with Angel One API."""
        endpoint = "/rest/auth/angelbroking/user/v1/loginByPassword"
        
        data = {
            "clientcode": client_id,
            "password": password,
            "totp": totp
        }
        
        try:
            response, response_data = self._make_request(endpoint, 'POST', data)
            
            if response.status_code == 200 and response_data.get('status'):
                session_data = response_data.get('data', {})
                
                # Store session information
                session = AngelOneSession.objects.create(
                    client_id=client_id,
                    auth_token=session_data.get('jwtToken', ''),
                    feed_token=session_data.get('feedToken', ''),
                    refresh_token=session_data.get('refreshToken', ''),
                    session_expiry=timezone.now() + timedelta(hours=8),  # Typical session duration
                    is_active=True
                )
                
                self.session = session
                self.logger.info(f"Authentication successful for client: {client_id}")
                return True, session_data
            else:
                error_msg = response_data.get('message', 'Authentication failed')
                self.logger.error(f"Authentication failed: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return False, str(e)
    
    def get_active_session(self):
        """Get active session if available."""
        try:
            session = AngelOneSession.objects.filter(
                is_active=True,
                session_expiry__gt=timezone.now()
            ).first()
            return session
        except Exception as e:
            self.logger.error(f"Error getting active session: {e}")
            return None
    
    def discover_symbols(self, keywords=None):
        """Discover NSE symbols (placeholder for now)."""
        # For now, return a basic list. This should be implemented with actual Angel One API
        # or load from a master symbol file
        self.logger.info("Symbol discovery - using placeholder implementation")
        
        symbols = [
            "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR",
            "ICICIBANK", "KOTAKBANK", "ITC", "LT", "SBIN"
        ]
        
        # Create or update symbol records
        for symbol in symbols:
            NSESymbol.objects.get_or_create(
                symbol=symbol,
                exchange='NSE',
                defaults={
                    'token': symbol,  # Placeholder
                    'lot_size': 1,
                    'instrument_type': 'EQ'
                }
            )
        
        return symbols
    
    def get_ltp(self, symbol):
        """Get Last Traded Price for a symbol."""
        # Placeholder implementation - should use Angel One API
        self.logger.info(f"Getting LTP for {symbol} - using placeholder")
        
        # For now, return a random price between 100-1000
        import random
        price = random.uniform(100, 1000)
        
        # Store market data
        try:
            nse_symbol = NSESymbol.objects.get(symbol=symbol, exchange='NSE')
            MarketData.objects.create(
                symbol=nse_symbol,
                ltp=price,
                data_timestamp=timezone.now()
            )
        except NSESymbol.DoesNotExist:
            pass
        
        return price
    
    def place_order(self, symbol, quantity, price=None, order_type='MARKET', transaction_type='BUY'):
        """Place an order."""
        self.logger.info(f"Placing {transaction_type} order for {quantity} {symbol} at {price or 'market price'}")
        
        # Placeholder implementation
        try:
            nse_symbol = NSESymbol.objects.get(symbol=symbol, exchange='NSE')
            
            order = Order.objects.create(
                order_id=f"ORD_{int(time.time())}",
                symbol=nse_symbol,
                order_type=order_type,
                transaction_type=transaction_type,
                quantity=quantity,
                price=price,
                status='PENDING'
            )
            
            # Simulate order execution (for testing)
            order.status = 'COMPLETE'
            order.filled_quantity = quantity
            order.average_price = price or self.get_ltp(symbol)
            order.save()
            
            self.logger.info(f"Order placed successfully: {order.order_id}")
            return True, order.order_id
            
        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            return False, str(e)
    
    def get_portfolio(self):
        """Get portfolio holdings."""
        # Placeholder implementation
        self.logger.info("Getting portfolio - using placeholder")
        return []
    
    def get_balance(self):
        """Get account balance."""
        # Placeholder implementation
        self.logger.info("Getting balance - using placeholder")
        return {"available_balance": 50000.0}
    
    def get_orders(self):
        """Get order history."""
        try:
            orders = Order.objects.all().order_by('-created_at')[:50]
            return [
                {
                    'order_id': order.order_id,
                    'symbol': order.symbol.symbol,
                    'order_type': order.order_type,
                    'transaction_type': order.transaction_type,
                    'quantity': order.quantity,
                    'price': order.price,
                    'status': order.status,
                    'created_at': order.created_at
                }
                for order in orders
            ]
        except Exception as e:
            self.logger.error(f"Error getting orders: {e}")
            return []
    
    def cancel_order(self, order_id):
        """Cancel an order."""
        try:
            order = Order.objects.get(order_id=order_id)
            if order.status in ['PENDING', 'OPEN']:
                order.status = 'CANCELLED'
                order.save()
                self.logger.info(f"Order {order_id} cancelled successfully")
                return True, "Order cancelled"
            else:
                return False, "Order cannot be cancelled"
        except Order.DoesNotExist:
            return False, "Order not found"
        except Exception as e:
            self.logger.error(f"Error cancelling order: {e}")
            return False, str(e)
    
    def get_market_data(self, symbols):
        """Get market data for multiple symbols."""
        market_data = {}
        for symbol in symbols:
            try:
                price = self.get_ltp(symbol)
                market_data[symbol] = {
                    'ltp': price,
                    'timestamp': timezone.now().isoformat()
                }
            except Exception as e:
                self.logger.error(f"Error getting market data for {symbol}: {e}")
                market_data[symbol] = None
        
        return market_data
