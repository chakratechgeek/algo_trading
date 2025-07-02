"""Django management command to control ngrok tunnel."""

from django.core.management.base import BaseCommand
from ngrok_auto import ngrok_manager


class Command(BaseCommand):
    help = 'Control ngrok tunnel (start/stop/status/restart)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['start', 'stop', 'restart', 'status'],
            help='Action to perform on ngrok tunnel'
        )
    
    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'start':
            self.stdout.write("🚀 Starting ngrok tunnel...")
            success = ngrok_manager.start_tunnel()
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS("✅ Ngrok tunnel started successfully!")
                )
                self.stdout.write(f"🌍 Public URL: {ngrok_manager.public_url}")
                self.stdout.write(f"🔗 Callback URL: {ngrok_manager.callback_url}")
            else:
                self.stdout.write(
                    self.style.ERROR("❌ Failed to start ngrok tunnel")
                )
        
        elif action == 'stop':
            self.stdout.write("🛑 Stopping ngrok tunnel...")
            ngrok_manager.stop_tunnel()
            self.stdout.write(
                self.style.SUCCESS("✅ Ngrok tunnel stopped")
            )
        
        elif action == 'restart':
            self.stdout.write("🔄 Restarting ngrok tunnel...")
            ngrok_manager.restart_tunnel()
            
            if ngrok_manager.is_running:
                self.stdout.write(
                    self.style.SUCCESS("✅ Ngrok tunnel restarted successfully!")
                )
                self.stdout.write(f"🌍 Public URL: {ngrok_manager.public_url}")
                self.stdout.write(f"🔗 Callback URL: {ngrok_manager.callback_url}")
            else:
                self.stdout.write(
                    self.style.ERROR("❌ Failed to restart ngrok tunnel")
                )
        
        elif action == 'status':
            if ngrok_manager.is_running:
                self.stdout.write(
                    self.style.SUCCESS("✅ Ngrok tunnel is RUNNING")
                )
                self.stdout.write(f"🌍 Public URL: {ngrok_manager.public_url}")
                self.stdout.write(f"🔗 Callback URL: {ngrok_manager.callback_url}")
            else:
                self.stdout.write(
                    self.style.WARNING("⚠️ Ngrok tunnel is NOT running")
                )
