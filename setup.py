"""Setup script for the Django trading platform."""

import os
import sys
import django
from django.core.management import execute_from_command_line

def setup_django():
    """Setup Django project."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trading_platform.settings')
    django.setup()
    
    print("=== Django Trading Platform Setup ===")
    
    # Step 1: Check project
    print("1. Checking project configuration...")
    try:
        execute_from_command_line(['manage.py', 'check'])
        print("✓ Project configuration is valid")
    except Exception as e:
        print(f"✗ Project check failed: {e}")
        return False
    
    # Step 2: Create migrations
    print("2. Creating migrations...")
    try:
        execute_from_command_line(['manage.py', 'makemigrations'])
        print("✓ Migrations created")
    except Exception as e:
        print(f"✗ Migration creation failed: {e}")
        return False
    
    # Step 3: Apply migrations
    print("3. Applying migrations...")
    try:
        execute_from_command_line(['manage.py', 'migrate'])
        print("✓ Migrations applied")
    except Exception as e:
        print(f"✗ Migration application failed: {e}")
        return False
    
    # Step 4: Create superuser (optional)
    print("4. Creating superuser...")
    try:
        from django.contrib.auth.models import User
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            print("✓ Superuser 'admin' created with password 'admin123'")
        else:
            print("✓ Superuser already exists")
    except Exception as e:
        print(f"! Superuser creation failed: {e}")
    
    # Step 5: Setup initial data
    print("5. Setting up initial data...")
    try:
        setup_initial_data()
        print("✓ Initial data setup complete")
    except Exception as e:
        print(f"! Initial data setup failed: {e}")
    
    print("\n=== Setup Complete ===")
    print("You can now:")
    print("1. Run the Django server: python manage.py runserver")
    print("2. Access admin panel: http://127.0.0.1:8000/admin/")
    print("3. Run trading bot: python manage.py run_trading_bot")
    
    return True

def setup_initial_data():
    """Setup initial data for the platform."""
    from django.contrib.auth.models import User
    from portfolio.models import Portfolio
    from trading.models import TradingStrategy
    from core.models import Configuration
    
    # Create default user if not exists
    user, created = User.objects.get_or_create(
        username='trader',
        defaults={
            'first_name': 'Trading',
            'last_name': 'Bot',
            'email': 'trader@example.com'
        }
    )
    
    # Create portfolio for user
    portfolio, created = Portfolio.objects.get_or_create(
        user=user,
        defaults={
            'name': 'Main Trading Portfolio',
            'initial_balance': 50000.00,
            'current_balance': 50000.00
        }
    )
    
    # Create default trading strategy
    strategy, created = TradingStrategy.objects.get_or_create(
        name='News Based Strategy',
        defaults={
            'description': 'Trading strategy based on news sentiment analysis',
            'strategy_type': 'NEWS_BASED',
            'config_parameters': {
                'sentiment_threshold': 0.6,
                'confidence_threshold': 75,
                'max_holding_hours': 24,
                'stop_loss_percent': 2.0,
                'take_profit_percent': 5.0
            }
        }
    )
    
    # Create default configurations
    configs = [
        ('CHECK_INTERVAL', '600', 'Trading bot check interval in seconds'),
        ('MAX_POSITIONS', '10', 'Maximum number of concurrent positions'),
        ('FIXED_QTY', '20', 'Fixed quantity per trade'),
        ('PRICE_THRESHOLD', '200.0', 'Maximum price threshold for stocks'),
    ]
    
    for key, value, description in configs:
        Configuration.objects.get_or_create(
            key=key,
            defaults={'value': value, 'description': description}
        )

if __name__ == '__main__':
    setup_django()
