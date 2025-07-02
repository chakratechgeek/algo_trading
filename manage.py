#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trading_platform.settings')
    
    # Auto-configure ngrok for runserver
    if len(sys.argv) >= 2 and sys.argv[1] == 'runserver':
        # Set default environment variables if not set
        if 'NGROK_AUTO_START' not in os.environ:
            os.environ['NGROK_AUTO_START'] = 'True'
        
        if 'NGROK_AUTH_TOKEN' not in os.environ:
            os.environ['NGROK_AUTH_TOKEN'] = '2zIambSj5KfyMpM6mcBWmkvDWtq_69e8qH2wuA4jGu7A5o6RL'
        
        if 'ANGEL_CLIENT_ID' not in os.environ:
            os.environ['ANGEL_CLIENT_ID'] = 'xhMChjlS'
        
        if 'ANGEL_CLIENT_SECRET' not in os.environ:
            os.environ['ANGEL_CLIENT_SECRET'] = '78e4798a-f35b-481f-9804-ff78557f99ed'
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
