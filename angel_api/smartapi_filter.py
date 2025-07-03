#!/usr/bin/env python
"""
NSE Stocks Filter ₹75-150 using Official SmartAPI
"""

import json
import pyotp
import sys
import os
import importlib.util
from datetime import datetime
from SmartApi import SmartConnect

# Add parent directory to path to import credentials
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    # Try to import from config folder first
    from config.secrets import CLIENT_CODE, MPIN, TOTP_SECRET, API_KEY
except ImportError:
    try:
        # Fallback to old credentials file
        from credentials import CLIENT_CODE, MPIN, TOTP_SECRET, API_KEY
    except ImportError:
        # If running from a different location, try to find credentials
        import importlib.util
        spec = importlib.util.spec_from_file_location("secrets", os.path.join(parent_dir, "config", "secrets.py"))
        if spec is None:
            # Try old credentials location
            spec = importlib.util.spec_from_file_location("credentials", os.path.join(parent_dir, "credentials.py"))
        
        if spec is not None:
            secrets = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(secrets)
            CLIENT_CODE = secrets.CLIENT_CODE
            MPIN = secrets.MPIN
            TOTP_SECRET = secrets.TOTP_SECRET
            API_KEY = secrets.API_KEY
        else:
            raise ImportError("Could not find credentials file. Please ensure config/secrets.py exists.")

def load_nse_stocks():
    """Load NSE stocks from the saved file."""
    try:
        # Path to data file - check multiple possible locations
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        
        # Try data directory first, then parent directory
        possible_paths = [
            os.path.join(parent_dir, 'data', 'nse_actual_stocks_20250703_214624.json'),
            os.path.join(parent_dir, 'nse_actual_stocks_20250703_214624.json'),
            '../data/nse_actual_stocks_20250703_214624.json',
            'nse_actual_stocks_20250703_214624.json'
        ]
        
        data_file = None
        for path in possible_paths:
            if os.path.exists(path):
                data_file = path
                break
        
        if not data_file:
            raise FileNotFoundError("NSE stocks data file not found in any expected location")
        
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        stocks = data.get('stocks', [])
        print(f"📥 Loaded {len(stocks)} NSE stocks from file")
        return stocks
    except Exception as e:
        print(f"❌ Error loading stocks: {e}")
        return None

def authenticate_smartapi():
    """Authenticate using official SmartAPI."""
    print("🔐 Authenticating with AngelOne SmartAPI...")
    
    try:
        # Create SmartConnect instance
        smartApi = SmartConnect(api_key=API_KEY)
        
        # Generate TOTP
        totp = pyotp.TOTP(TOTP_SECRET)
        current_totp = totp.now()
        print(f"Generated TOTP: {current_totp}")
        
        # Login with MPIN
        data = smartApi.generateSession(CLIENT_CODE, MPIN, current_totp)
        
        print(f"Auth response: {data}")
        
        if data and data.get('status'):
            print("✅ SmartAPI Authentication successful!")
            return smartApi
        else:
            print(f"❌ SmartAPI Authentication failed: {data}")
            return None
            
    except Exception as e:
        print(f"❌ SmartAPI Authentication error: {e}")
        return None

def get_real_prices_smartapi(stocks, smart_api, max_stocks=100):
    """Get real prices using SmartAPI."""
    print(f"💰 Getting REAL prices for {min(len(stocks), max_stocks)} stocks...")
    
    if not smart_api:
        print("❌ No SmartAPI connection")
        return None
    
    stocks_with_prices = []
    stocks_to_process = stocks[:max_stocks]
    
    for i, stock in enumerate(stocks_to_process):
        try:
            # Get LTP using SmartAPI
            ltp_data = smart_api.ltpData("NSE", stock['symbol'], str(stock['token']))
            
            if ltp_data and ltp_data.get('status') and ltp_data.get('data'):
                ltp = float(ltp_data['data'].get('ltp', 0))
                
                if ltp > 0:  # Valid price
                    stock_data = {
                        'symbol': stock['symbol'],
                        'token': stock['token'],
                        'name': stock['name'],
                        'price': ltp
                    }
                    stocks_with_prices.append(stock_data)
                    
                    if (i + 1) % 10 == 0:
                        print(f"  ✅ Processed {i + 1} stocks...")
                        
        except Exception as e:
            print(f"  ❌ Error getting price for {stock['symbol']}: {e}")
            continue
    
    print(f"✅ Got real prices for {len(stocks_with_prices)} stocks")
    return stocks_with_prices

def filter_by_price_range(stocks_with_prices, min_price=75, max_price=150):
    """Filter stocks by price range."""
    if not stocks_with_prices:
        return []
        
    filtered = []
    for stock in stocks_with_prices:
        if min_price <= stock['price'] <= max_price:
            filtered.append(stock)
    
    return filtered

def main():
    """Main function."""
    print("=" * 70)
    print(f"📈 REAL NSE STOCKS FILTER: ₹75-150 (SmartAPI)")
    print("=" * 70)
    
    # Load NSE stocks
    stocks = load_nse_stocks()
    if not stocks:
        return
    
    print(f"📊 Total NSE stocks available: {len(stocks)}")
    
    # Authenticate
    smart_api = authenticate_smartapi()
    if not smart_api:
        return
    
    # Get real prices
    stocks_with_prices = get_real_prices_smartapi(stocks, smart_api, max_stocks=8000)
    if not stocks_with_prices:
        return
    
    # Filter by price range
    filtered_stocks = filter_by_price_range(stocks_with_prices, 75, 150)
    
    print(f"\n🎯 Found {len(filtered_stocks)} stocks in ₹75-150 range:")
    print("-" * 70)
    print("No.  Symbol          Price    Company Name")
    print("-" * 70)
    
    # Sort by price
    filtered_stocks.sort(key=lambda x: x['price'])
    
    for i, stock in enumerate(filtered_stocks, 1):
        symbol = stock['symbol']
        price = stock['price']
        name = stock['name'][:25] if stock['name'] else 'N/A'
        print(f"{i:3d}. {symbol:15s} ₹{price:7.2f}  {name}")
    
    print("-" * 70)
    print(f"Total stocks in ₹75-150 range: {len(filtered_stocks)}")
    
    # Save results to results directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    results_dir = os.path.join(parent_dir, 'results')
    os.makedirs(results_dir, exist_ok=True)
    filename = os.path.join(results_dir, f"real_nse_75_150_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(filename, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'source': 'AngelOne SmartAPI',
            'price_range': {'min': 75, 'max': 150},
            'total_checked': len(stocks_with_prices),
            'filtered_count': len(filtered_stocks),
            'stocks': filtered_stocks
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {filename}")
    return filtered_stocks

if __name__ == '__main__':
    filtered_stocks = main()
    
    print("\n" + "=" * 70)
    print("🏁 FINAL RESULT")
    print("=" * 70)
    if filtered_stocks:
        print(f"✅ Found {len(filtered_stocks)} REAL NSE stocks between ₹75-150")
        print("✅ 100% REAL prices from AngelOne!")
    else:
        print("❌ No stocks found in price range")
    print("=" * 70)
