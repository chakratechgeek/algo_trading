"""Django management command - alias for start_server with ngrok."""

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Start Django server with ngrok (alias for start_server)'
    
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
    
    def handle(self, *args, **options):
        """Forward to start_server command."""
        self.stdout.write("🔄 Forwarding to start_server command...")
        call_command('start_server', 
                    port=options['port'], 
                    host=options['host'])
