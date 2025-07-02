"""Utility functions for Angel API."""

import socket
import requests
import json
from django.conf import settings
from django.urls import reverse


def get_public_ip():
    """Get the public IP address of the server."""
    try:
        # Use a service that returns your public IP
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        return response.json()['ip']
    except Exception:
        # Fallback to another service
        try:
            response = requests.get('https://ifconfig.me/ip', timeout=5)
            return response.text.strip()
        except Exception:
            # Final fallback
            return None


def get_local_ips():
    """Get local IP addresses."""
    hostname = socket.gethostname()
    local_ips = []
    
    try:
        # Get all local IP addresses
        for ip in socket.getaddrinfo(hostname, None):
            # Filter for IPv4 addresses
            if ip[0] == socket.AF_INET:
                local_ips.append(ip[4][0])
    except Exception:
        pass
        
    return local_ips


def get_callback_urls(request=None):
    """
    Generate a list of possible callback URLs for Angel One API.
    
    Returns a dict with:
    - recommended: The recommended URL to use
    - alternatives: List of alternative URLs
    - localhost: Standard localhost URL
    """
    result = {
        'recommended': None,
        'alternatives': [],
        'localhost': f"http://localhost:8000{reverse('angel_callback')}"
    }
    
    # 1. Try to get the public IP
    public_ip = get_public_ip()
    if public_ip:
        result['alternatives'].append(f"http://{public_ip}:8000{reverse('angel_callback')}")
        result['alternatives'].append(f"https://{public_ip}:8000{reverse('angel_callback')}")
    
    # 2. Get local IP addresses
    local_ips = get_local_ips()
    for ip in local_ips:
        if ip != '127.0.0.1':  # Skip localhost
            result['alternatives'].append(f"http://{ip}:8000{reverse('angel_callback')}")
    
    # 3. If request is provided, use the host from the request
    if request:
        host = request.get_host()
        scheme = 'https' if request.is_secure() else 'http'
        url = f"{scheme}://{host}{reverse('angel_callback')}"
        result['recommended'] = url
    else:
        # Default to localhost if no request
        result['recommended'] = result['localhost']
    
    return result


def update_angel_one_redirect_uri(new_uri):
    """Update the Angel One redirect URI in settings."""
    if hasattr(settings, 'ANGEL_ONE_CONFIG'):
        settings.ANGEL_ONE_CONFIG['REDIRECT_URI'] = new_uri
        return True
    return False