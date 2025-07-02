#!/usr/bin/env python
"""
Clean Startup Script for Algo Trading Platform
============================================

This script provides a clean way to start the trading platform.
"""

import os
import sys
import subprocess
import time

def main():
    """Main startup function."""
    print("🚀 Algo Trading Platform - Clean Startup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('manage.py'):
        print("❌ Error: Please run this script from the project root directory")
        sys.exit(1)
    
    # Show available options
    print("\nAvailable startup options:")
    print("1. Start Django Server Only")
    print("2. Run Small-Cap Strategy")
    print("3. Start Automated Scheduler (10-min intervals)")
    print("4. Start Server + Open Admin")
    print("5. Setup Admin User & Portfolio")
    
    choice = input("\nSelect option (1-5): ").strip()
    
    if choice == '1':
        start_server()
    elif choice == '2':
        test_strategy()
    elif choice == '3':
        start_scheduler()
    elif choice == '4':
        start_server_and_admin()
    elif choice == '5':
        create_test_data()
    else:
        print("Invalid choice. Starting server...")
        start_server()

def start_server():
    """Start Django development server."""
    print("\n🌐 Starting Django server...")
    print("Admin URL: http://127.0.0.1:8000/admin/")
    print("Login: admin / admin123")
    print("Press Ctrl+C to stop")
    
    subprocess.run([sys.executable, 'manage.py', 'runserver'])

def test_strategy():
    """Run the small-cap strategy."""
    print("\n🧪 Running Small-Cap Strategy...")
    
    # Run the actual strategy
    print("Starting small-cap trading strategy...")
    subprocess.run([
        sys.executable, 'manage.py', 'run_small_cap_strategy'
    ])
    
    print("\n✅ Strategy execution completed! Check the output above.")
    input("Press Enter to continue...")

def start_scheduler():
    """Start the automated scheduler."""
    print("\n🤖 Starting Automated Trading Scheduler...")
    print("Interval: Every 10 minutes")
    print("Active: Market hours only (9:15 AM - 3:30 PM IST)")
    print("Days: Weekdays only")
    print("Press Ctrl+C to stop")
    
    subprocess.run([
        sys.executable, 'manage.py', 'start_scheduler',
        '--interval', '10', '--market-hours-only', '--weekdays-only'
    ])

def start_server_and_admin():
    """Start server and open admin in browser."""
    print("\n🌐 Starting server and opening admin...")
    
    import webbrowser
    import threading
    
    def open_browser():
        time.sleep(2)  # Wait for server to start
        webbrowser.open('http://127.0.0.1:8000/admin/')
    
    # Start browser opener in background
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Start server
    subprocess.run([sys.executable, 'manage.py', 'runserver'])

def create_test_data():
    """Create admin user and basic setup."""
    print("\n📊 Setting up admin user and basic data...")
    
    # Create superuser if needed
    print("Creating admin user (if not exists)...")
    subprocess.run([
        sys.executable, 'manage.py', 'shell', '-c',
        """
from django.contrib.auth.models import User
from portfolio.models import Portfolio
if not User.objects.filter(username='admin').exists():
    user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    # Create a basic portfolio
    Portfolio.objects.get_or_create(
        user=user,
        defaults={
            'name': 'Default Portfolio',
            'current_balance': 50000.00
        }
    )
    print('Admin user and portfolio created: admin/admin123')
else:
    print('Admin user already exists')
"""
    ])
    
    print("\n✅ Setup completed!")
    print("Login to admin with: admin / admin123")
    input("Press Enter to continue...")

if __name__ == '__main__':
    main()
