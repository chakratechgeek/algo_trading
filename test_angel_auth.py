#!/usr/bin/env python
"""
Quick AngelOne API Test
"""

import os
import sys
import django
import requests

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trading_platform.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.conf import settings

def test_angelone_auth():
    print("🔧 Testing AngelOne API Authentication")
    print("=" * 50)
    
    config = settings.ANGEL_ONE_CONFIG
    client_id = config.get('CLIENT_ID')
    password = config.get('PASSWORD')
    
    print(f"Client ID: {client_id}")
    print(f"Password: {'✅ Set' if password else '❌ Not Set'}")
    
    if not password:
        print("❌ Password not found in environment!")
        return False
    
    # Test API authentication
    auth_url = "https://apiconnect.angelbroking.com/rest/auth/angelbroking/user/v1/loginByPassword"
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-UserType': 'USER',
        'X-SourceID': 'WEB',
        'X-ClientLocalIP': '127.0.0.1',
        'X-ClientPublicIP': '127.0.0.1',
        'X-MACAddress': 'fe80::216c:f6ff:fe71:21c6',
    }
    
    auth_data = {
        "clientcode": client_id,
        "password": password,
        "totp": "218721"  # Your current TOTP
    }
    
    print("\n🚀 Attempting authentication...")
    
    try:
        response = requests.post(auth_url, json=auth_data, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"API Response: {result}")
            
            if result.get('status'):
                print("✅ Authentication SUCCESS!")
                data = result.get('data', {})
                print(f"Session Token: {data.get('jwtToken', 'N/A')[:20]}...")
                print(f"Feed Token: {data.get('feedToken', 'N/A')[:20]}...")
                return True
            else:
                print(f"❌ Authentication FAILED: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    test_angelone_auth()
