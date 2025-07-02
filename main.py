"""Main startup script for the Django trading platform."""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(command, description=""):
    """Run a command and return success status."""
    print(f"\n{'='*50}")
    print(f"Running: {description or command}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False

def setup_django_project():
    """Setup the Django project."""
    print("🚀 Setting up Django Trading Platform...")
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Step 1: Install dependencies from requirements.txt
    print("\n📦 Installing Python dependencies...")
    if not run_command("pip install -r requirements.txt", "Installing requirements"):
        print("⚠️  Failed to install requirements, but continuing...")
    
    # Step 2: Django migrations
    commands = [
        ("python manage.py check", "Checking Django configuration"),
        ("python manage.py makemigrations", "Creating migrations"),
        ("python manage.py migrate", "Applying migrations"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            print(f"❌ Failed: {description}")
            return False
    
    # Step 3: Create superuser
    print("\n👤 Creating superuser...")
    superuser_command = """
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trading_platform.settings')
django.setup()

from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"""
    
    with open('create_superuser.py', 'w') as f:
        f.write(superuser_command)
    
    run_command("python create_superuser.py", "Creating superuser")
    os.remove('create_superuser.py')
    
    # Step 4: Setup initial data
    print("\n📊 Setting up initial trading data...")
    initial_data_command = """
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trading_platform.settings')
django.setup()

from django.contrib.auth.models import User
from portfolio.models import Portfolio
from trading.models import TradingStrategy
from angel_api.models import NSESymbol

# Create trading user
user, created = User.objects.get_or_create(
    username='trader',
    defaults={'first_name': 'Trading', 'last_name': 'Bot', 'email': 'trader@example.com'}
)

# Create portfolio
portfolio, created = Portfolio.objects.get_or_create(
    user=user,
    defaults={'name': 'Main Portfolio', 'initial_balance': 50000, 'current_balance': 50000}
)

# Create strategy
strategy, created = TradingStrategy.objects.get_or_create(
    name='News Based Strategy',
    defaults={
        'description': 'News sentiment based trading',
        'strategy_type': 'NEWS_BASED',
        'config_parameters': {'confidence_threshold': 75}
    }
)

# Add some sample symbols
symbols = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK']
for symbol_name in symbols:
    NSESymbol.objects.get_or_create(
        symbol=symbol_name,
        exchange='NSE',
        defaults={'token': symbol_name, 'lot_size': 1}
    )

print(f'Setup complete - Portfolio: {portfolio.name}, Strategy: {strategy.name}')
"""
    
    with open('setup_data.py', 'w') as f:
        f.write(initial_data_command)
    
    run_command("python setup_data.py", "Setting up initial data")
    os.remove('setup_data.py')
    
    print("\n✅ Django Trading Platform setup complete!")
    print("\n📋 Next steps:")
    print("1. Start Django server: python manage.py runserver")
    print("2. Access admin: http://127.0.0.1:8000/admin/ (admin/admin123)")
    print("3. Run trading bot: python manage.py run_trading_bot")
    print("4. Migrate old data: python manage.py migrate_old_data")
    
    return True

def start_trading_server():
    """Start the Django development server."""
    print("\n🌐 Starting Django development server...")
    run_command("python manage.py runserver", "Starting server")

def run_trading_bot():
    """Run the trading bot."""
    print("\n🤖 Starting trading bot...")
    run_command("python manage.py run_trading_bot", "Running trading bot")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "setup":
            setup_django_project()
        elif command == "server":
            start_trading_server()
        elif command == "bot":
            run_trading_bot()
        else:
            print("Unknown command. Use: setup, server, or bot")
    else:
        print("🎯 Django Trading Platform")
        print("\nAvailable commands:")
        print("  python main.py setup   - Setup the Django project")
        print("  python main.py server  - Start the Django server") 
        print("  python main.py bot     - Run the trading bot")
        print("\nFirst time? Run: python main.py setup")
