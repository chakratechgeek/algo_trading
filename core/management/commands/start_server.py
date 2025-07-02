"""Django management command to start server with optional ngrok integration."""

import os
import sys
import subprocess
import time
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from ngrok_auto import ngrok_manager


class Command(BaseCommand):
    help = 'Start Django development server with optional ngrok tunnel'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--port',
            type=int,
            default=8000,
            help='Port to run the server on (default: 8000)'
        )
        parser.add_argument(
            '--host',
            type=str,
            default='127.0.0.1',
            help='Host to bind the server to (default: 127.0.0.1)'
        )
        parser.add_argument(
            '--no-ngrok',
            action='store_true',
            help='Disable ngrok tunnel (ngrok is enabled by default)'
        )
        parser.add_argument(
            '--ngrok-only',
            action='store_true',
            help='Only start ngrok tunnel, do not start Django server'
        )
        parser.add_argument(
            '--production',
            action='store_true',
            help='Use production settings (disable debug, etc.)'
        )
    
    def handle(self, *args, **options):
        port = options['port']
        host = options['host']
        no_ngrok = options['no_ngrok']
        ngrok_only = options['ngrok_only']
        production = options['production']
        
        # Display startup banner
        self._display_banner()
        
        # Configure production settings if requested
        if production:
            self._configure_production_mode()
        
        # Start ngrok if not disabled
        if not no_ngrok:
            self._start_ngrok(port)
        
        # Start Django server unless ngrok-only mode
        if not ngrok_only:
            self._start_django_server(host, port)
        else:
            self.stdout.write(
                self.style.SUCCESS("🎯 Ngrok-only mode: Django server not started")
            )
            self.stdout.write("💡 Start Django manually: python manage.py runserver")
    
    def _display_banner(self):
        """Display startup banner."""
        banner = """
════════════════════════════════════════════════════════════════
🎯 DJANGO TRADING PLATFORM SERVER
════════════════════════════════════════════════════════════════
🚀 Starting trading platform with auto-ngrok integration...
📊 Features: Angel One API, AI Trading Bot, Portfolio Management
════════════════════════════════════════════════════════════════
        """
        self.stdout.write(self.style.SUCCESS(banner))
    
    def _configure_production_mode(self):
        """Configure production settings."""
        self.stdout.write("⚙️  Configuring production mode...")
        
        # Temporarily override settings for production
        if hasattr(settings, 'DEBUG'):
            settings.DEBUG = False
        
        self.stdout.write("✅ Production mode enabled")
    
    def _start_ngrok(self, port):
        """Start ngrok tunnel."""
        self.stdout.write("🌐 Starting ngrok tunnel...")
        
        try:
            # Update port if different from default
            if port != 8000:
                self.stdout.write(f"📝 Configuring ngrok for port {port}")
            
            success = ngrok_manager.start_tunnel(port)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS("✅ Ngrok tunnel started successfully!")
                )
                self.stdout.write(f"🌍 Public URL: {ngrok_manager.public_url}")
                self.stdout.write(f"🔗 Callback URL: {ngrok_manager.callback_url}")
                
                # Update Angel One settings with new callback
                self._update_angel_one_config()
                
            else:
                self.stdout.write(
                    self.style.WARNING("⚠️  Failed to start ngrok tunnel")
                )
                self.stdout.write("💡 Server will start without public access")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Ngrok error: {e}")
            )
    
    def _update_angel_one_config(self):
        """Update Angel One configuration with new callback URL."""
        if hasattr(settings, 'ANGEL_ONE_CONFIG') and ngrok_manager.callback_url:
            settings.ANGEL_ONE_CONFIG['REDIRECT_URI'] = ngrok_manager.callback_url
            self.stdout.write("📝 Updated Angel One callback URL")
    
    def _start_django_server(self, host, port):
        """Start Django development server."""
        self.stdout.write(f"🚀 Starting Django server on {host}:{port}...")
        
        try:
            # Run migrations if needed
            self._run_migrations()
            
            # Display access information
            self._display_access_info(host, port)
            
            # Start the Django server
            call_command('runserver', f'{host}:{port}', verbosity=1)
            
        except KeyboardInterrupt:
            self.stdout.write("\n🛑 Server stopped by user")
            self._cleanup()
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Server error: {e}")
            )
            self._cleanup()
    
    def _run_migrations(self):
        """Run database migrations if needed."""
        self.stdout.write("🔄 Checking for pending migrations...")
        
        try:
            # Check if migrations are needed (simplified check)
            call_command('migrate', '--check', verbosity=0)
            self.stdout.write("✅ Database is up to date")
        except:
            self.stdout.write("📝 Running database migrations...")
            call_command('migrate', verbosity=0)
            self.stdout.write("✅ Migrations completed")
    
    def _display_access_info(self, host, port):
        """Display server access information."""
        info = f"""
════════════════════════════════════════════════════════════════
🌐 SERVER ACCESS INFORMATION
════════════════════════════════════════════════════════════════
📍 Local Server:    http://{host}:{port}/
🔧 Admin Panel:     http://{host}:{port}/admin/
📊 Trading API:     http://{host}:{port}/api/trading/
💼 Portfolio API:   http://{host}:{port}/api/portfolio/
🔌 Angel One API:   http://{host}:{port}/api/angel/
"""
        
        if ngrok_manager.is_running and ngrok_manager.public_url:
            info += f"""
🌍 Public URL:      {ngrok_manager.public_url}/
🔗 Angel Callback:  {ngrok_manager.callback_url}
"""
        
        info += """════════════════════════════════════════════════════════════════
💡 Quick Commands:
   - Create superuser:     python manage.py createsuperuser
   - Run trading bot:      python manage.py run_trading_bot
   - Control ngrok:        python manage.py ngrok_control status
   - Setup platform:       python manage.py setup_platform
════════════════════════════════════════════════════════════════
"""
        
        self.stdout.write(self.style.SUCCESS(info))
    
    def _cleanup(self):
        """Cleanup on server shutdown."""
        self.stdout.write("🧹 Cleaning up...")
        
        # Stop ngrok if running
        if ngrok_manager.is_running:
            self.stdout.write("🛑 Stopping ngrok tunnel...")
            ngrok_manager.stop_tunnel()
            self.stdout.write("✅ Ngrok tunnel stopped")
        
        self.stdout.write("👋 Goodbye!")
