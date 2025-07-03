"""Angel One API service."""

import requests
import json
import time
import logging
import pyotp
import os
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from SmartApi import SmartConnect
from .models import AngelOneSession, NSESymbol, MarketData, APILog, Order


class AngelOneAPI:
    """Service class for Angel One API integration using SmartAPI."""
    
    def __init__(self):
        # Load credentials from config folder (not in git)
        try:
            from config.secrets import CLIENT_CODE, MPIN, TOTP_SECRET, API_KEY
            self.client_code = CLIENT_CODE
            self.mpin = MPIN
            self.totp_secret = TOTP_SECRET
            self.api_key = API_KEY
        except ImportError:
            try:
                # Fallback to old credentials file
                from credentials import CLIENT_CODE, MPIN, TOTP_SECRET, API_KEY
                self.client_code = CLIENT_CODE
                self.mpin = MPIN
                self.totp_secret = TOTP_SECRET
                self.api_key = API_KEY
            except ImportError:
                # Fallback to settings if credentials file not available
                self.config = settings.ANGEL_ONE_CONFIG
                self.client_code = self.config.get('CLIENT_ID')
                self.mpin = self.config.get('MPIN')
                self.totp_secret = self.config.get('TOTP_SECRET')
                self.api_key = self.config.get('API_KEY')
            
        self.base_url = "https://apiconnect.angelone.in"
        self.logger = logging.getLogger('angel_api')
        self.session_token = None
        self.feed_token = None
        self.user_info = None
        self.smart_api = None
        
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
    
    def _generate_totp(self):
        """Generate TOTP using the secret."""
        try:
            totp = pyotp.TOTP(self.totp_secret)
            return totp.now()
        except Exception as e:
            self.logger.error(f"Failed to generate TOTP: {e}")
            return None
    
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
    
    def authenticate(self):
        """Authenticate with Angel One API using SmartAPI and MPIN."""
        self.logger.info("Authenticating with AngelOne SmartAPI...")
        
        try:
            # Create SmartConnect instance
            self.smart_api = SmartConnect(api_key=self.api_key)
            
            # Generate TOTP
            totp = self._generate_totp()
            if not totp:
                return False, "Failed to generate TOTP"
            
            # Login with MPIN using SmartAPI
            data = self.smart_api.generateSession(self.client_code, self.mpin, totp)
            
            self.logger.info(f"SmartAPI auth response: {data}")
            
            if data and data.get('status'):
                session_data = data.get('data', {})
                
                # Store session tokens
                self.session_token = session_data.get('jwtToken', '')
                self.feed_token = session_data.get('feedToken', '')
                self.user_info = session_data
                
                # Store session information in database
                session = AngelOneSession.objects.create(
                    client_id=self.client_code,
                    auth_token=self.session_token,
                    feed_token=self.feed_token,
                    refresh_token=session_data.get('refreshToken', ''),
                    session_expiry=timezone.now() + timedelta(hours=8),  # Typical session duration
                    is_active=True
                )
                
                self.session = session
                self.logger.info(f"SmartAPI authentication successful for client: {self.client_code}")
                return True, session_data
            else:
                error_msg = data.get('message', 'SmartAPI authentication failed') if data else 'No response from SmartAPI'
                self.logger.error(f"SmartAPI authentication failed: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            self.logger.error(f"SmartAPI authentication error: {e}")
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
    
    def load_nse_stocks_from_file(self, file_path=None):
        """Load NSE stocks from the saved symbol master file."""
        if not file_path:
            # Look for the most recent NSE stocks file in data directory
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(current_dir, 'data')
            file_pattern = 'nse_actual_stocks_*.json'
            
            import glob
            files = glob.glob(os.path.join(data_dir, file_pattern))
            if files:
                file_path = max(files, key=os.path.getctime)  # Most recent file
            else:
                self.logger.error("No NSE stocks file found in data directory")
                return []
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            stocks = data.get('stocks', [])
            self.logger.info(f"Loaded {len(stocks)} NSE stocks from {file_path}")
            return stocks
        except Exception as e:
            self.logger.error(f"Error loading NSE stocks from {file_path}: {e}")
            return []

    def discover_symbols(self, keywords=None):
        """Load real NSE symbols from the symbol master file."""
        self.logger.info("Loading real NSE symbols from symbol master file")
        
        stocks = self.load_nse_stocks_from_file()
        if not stocks:
            # Fallback to basic symbols if file not found
            self.logger.warning("Using fallback symbol list")
            stocks = [
                {"symbol": "RELIANCE", "token": "2885", "name": "Reliance Industries Ltd"},
                {"symbol": "TCS", "token": "11536", "name": "Tata Consultancy Services Ltd"},
                {"symbol": "HDFCBANK", "token": "1333", "name": "HDFC Bank Ltd"},
                {"symbol": "INFY", "token": "1594", "name": "Infosys Ltd"},
                {"symbol": "HINDUNILVR", "token": "356", "name": "Hindustan Unilever Ltd"},
            ]
        
        # Create or update symbol records in database
        symbols = []
        for stock in stocks:
            symbol_obj, created = NSESymbol.objects.get_or_create(
                symbol=stock['symbol'],
                exchange='NSE',
                defaults={
                    'token': stock.get('token', ''),
                    'lot_size': 1,
                    'instrument_type': 'EQ',
                    'name': stock.get('name', '')
                }
            )
            symbols.append(stock['symbol'])
        
        self.logger.info(f"Loaded {len(symbols)} NSE symbols into database")
        return stocks
    
    def get_ltp(self, exchange, trading_symbol, symbol_token):
        """Get Last Traded Price for a symbol using SmartAPI."""
        if not self.smart_api:
            self.logger.error("No active SmartAPI connection")
            return None
            
        try:
            # Get LTP using SmartAPI
            ltp_data = self.smart_api.ltpData(exchange, trading_symbol, str(symbol_token))
            
            if ltp_data and ltp_data.get('status') and ltp_data.get('data'):
                ltp = float(ltp_data['data'].get('ltp', 0))
                
                if ltp > 0:  # Valid price
                    # Store market data
                    try:
                        nse_symbol, created = NSESymbol.objects.get_or_create(
                            symbol=trading_symbol,
                            exchange=exchange,
                            defaults={
                                'token': symbol_token,
                                'lot_size': 1,
                                'instrument_type': 'EQ'
                            }
                        )
                        MarketData.objects.create(
                            symbol=nse_symbol,
                            ltp=ltp,
                            data_timestamp=timezone.now()
                        )
                    except Exception as e:
                        self.logger.error(f"Error storing market data for {trading_symbol}: {e}")
                    
                    return ltp
                else:
                    self.logger.warning(f"Invalid LTP (0) for {trading_symbol}")
                    return None
            else:
                error_msg = ltp_data.get('message', 'Failed to get LTP') if ltp_data else 'No response from SmartAPI'
                self.logger.error(f"LTP fetch failed for {trading_symbol}: {error_msg}")
                return None
                
        except Exception as e:
            self.logger.error(f"SmartAPI LTP fetch error for {trading_symbol}: {e}")
            return None
    
    def get_ltp_batch(self, symbols_data, max_symbols=None):
        """Get LTP for multiple symbols using SmartAPI. symbols_data should be a list of dicts with exchange, tradingsymbol, symboltoken."""
        if not self.smart_api:
            self.logger.error("No active SmartAPI connection")
            return {}
            
        if max_symbols:
            symbols_data = symbols_data[:max_symbols]
            
        results = {}
        total_symbols = len(symbols_data)
        
        self.logger.info(f"Fetching LTP for {total_symbols} symbols...")
        
        for i, symbol_data in enumerate(symbols_data):
            exchange = symbol_data.get('exchange', 'NSE')
            trading_symbol = symbol_data.get('symbol') or symbol_data.get('tradingsymbol')
            symbol_token = symbol_data.get('token') or symbol_data.get('symboltoken')
            
            if trading_symbol and symbol_token:
                try:
                    ltp = self.get_ltp(exchange, trading_symbol, symbol_token)
                    if ltp is not None:
                        results[trading_symbol] = {
                            'symbol': trading_symbol,
                            'price': ltp,
                            'token': symbol_token,
                            'name': symbol_data.get('name', '')
                        }
                        
                    # Progress logging
                    if (i + 1) % 50 == 0 or (i + 1) == total_symbols:
                        self.logger.info(f"Processed {i + 1}/{total_symbols} symbols...")
                        
                    # Small delay to avoid rate limiting
                    time.sleep(0.05)
                    
                except Exception as e:
                    self.logger.error(f"Error processing {trading_symbol}: {e}")
                    continue
            else:
                self.logger.warning(f"Invalid symbol data: {symbol_data}")
        
        self.logger.info(f"Successfully fetched LTP for {len(results)} out of {total_symbols} symbols")
        return results
    
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
    
    def filter_stocks_by_price_range(self, min_price=75, max_price=150, max_symbols=None):
        """Filter NSE stocks by price range using real SmartAPI data."""
        self.logger.info(f"Filtering NSE stocks in price range Rs.{min_price}-Rs.{max_price}")
        
        # Authenticate if not already done
        if not self.smart_api:
            success, message = self.authenticate()
            if not success:
                self.logger.error(f"Authentication failed: {message}")
                return []
        
        # Load NSE symbols
        stocks = self.load_nse_stocks_from_file()
        if not stocks:
            self.logger.error("No NSE symbols available")
            return []
        
        # Limit symbols if specified
        if max_symbols:
            stocks = stocks[:max_symbols]
            
        self.logger.info(f"Processing {len(stocks)} symbols for price filtering...")
        
        # Get real-time prices for all symbols
        stocks_with_prices = self.get_ltp_batch(stocks, max_symbols)
        
        # Filter by price range
        filtered_stocks = []
        for symbol, stock_data in stocks_with_prices.items():
            price = stock_data['price']
            if min_price <= price <= max_price:
                filtered_stocks.append({
                    'symbol': symbol,
                    'price': price,
                    'token': stock_data['token'],
                    'name': stock_data['name']
                })
        
        # Sort by price
        filtered_stocks.sort(key=lambda x: x['price'])
        
        self.logger.info(f"Found {len(filtered_stocks)} stocks in Rs.{min_price}-Rs.{max_price} range")
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"filtered_stocks_{min_price}_{max_price}_{timestamp}.json"
        
        try:
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            file_path = os.path.join(current_dir, output_file)
            
            with open(file_path, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'source': 'AngelOne SmartAPI',
                    'price_range': {'min': min_price, 'max': max_price},
                    'total_checked': len(stocks_with_prices),
                    'filtered_count': len(filtered_stocks),
                    'stocks': filtered_stocks
                }, f, indent=2)
            
            self.logger.info(f"Results saved to: {file_path}")
        except Exception as e:
            self.logger.error(f"Error saving results: {e}")
        
        return filtered_stocks

    def get_stocks_in_price_range(self, min_price=75, max_price=150, max_symbols=1000):
        """Public method to get stocks in a specific price range."""
        return self.filter_stocks_by_price_range(min_price, max_price, max_symbols)

    def get_market_data(self, symbols):
        """Get market data for multiple symbols using SmartAPI."""
        if not self.smart_api:
            self.logger.error("No active SmartAPI connection")
            return {}
            
        market_data = {}
        for symbol in symbols:
            try:
                # For NSE symbols, we need to get the token
                try:
                    nse_symbol = NSESymbol.objects.get(symbol=symbol, exchange='NSE')
                    token = nse_symbol.token
                except NSESymbol.DoesNotExist:
                    self.logger.warning(f"Token not found for {symbol}, skipping")
                    continue
                
                ltp = self.get_ltp('NSE', symbol, token)
                if ltp is not None:
                    market_data[symbol] = {
                        'ltp': ltp,
                        'timestamp': timezone.now().isoformat()
                    }
                else:
                    market_data[symbol] = None
            except Exception as e:
                self.logger.error(f"Error getting market data for {symbol}: {e}")
                market_data[symbol] = None
        
        return market_data

    # ...existing code...
