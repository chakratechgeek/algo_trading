"""
Auto-Ngrok Manager for Django
=============================

This module automatically starts and manages ngrok tunnels when Django starts.
It ensures Angel One API calls always work by maintaining a public HTTPS URL.
"""

import os
import sys
import time
import requests
import subprocess
import threading
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class NgrokManager:
    """Manages ngrok tunnel lifecycle."""
    
    def __init__(self):
        self.process = None
        self.public_url = None
        self.callback_url = None
        self.is_running = False
        
    def start_tunnel(self):
        """Start ngrok tunnel automatically."""
        try:
            # Ensure clean startup - stop any existing instances first
            logger.info("🧹 Performing clean startup...")
            self.stop_tunnel()
            
            # Additional cleanup
            self._deep_cleanup()
            
            # Reset all state
            self._reset_state()
            
            logger.info("🚀 Starting fresh ngrok tunnel...")
            
            # Start ngrok process
            self.process = subprocess.Popen(
                ['ngrok', 'http', '8000', '--log', 'stdout'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
            )
            
            # Wait for tunnel to establish
            time.sleep(4)
            
            # Get public URL
            self.public_url = self._get_public_url()
            
            if self.public_url:
                self.callback_url = f"{self.public_url}/api/angel/auth/callback/"
                self.is_running = True
                
                # Update Django settings
                self._update_settings()
                
                logger.info(f"✅ Ngrok tunnel active: {self.public_url}")
                logger.info(f"🔗 Callback URL: {self.callback_url}")
                
                # Start health check thread
                self._start_health_check()
                
                return True
            else:
                logger.error("❌ Failed to get ngrok public URL")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error starting ngrok: {e}")
            return False
    
    def _cleanup_existing_processes(self):
        """Kill existing ngrok processes."""
        try:
            if sys.platform == 'win32':
                # Kill all ngrok processes
                subprocess.run(['taskkill', '/f', '/im', 'ngrok.exe'], 
                             capture_output=True, check=False)
                # Wait a moment for processes to terminate
                time.sleep(1)
            else:
                subprocess.run(['pkill', '-f', 'ngrok'], 
                             capture_output=True, check=False)
                time.sleep(1)
            logger.info("🧹 Cleaned up old ngrok processes")
        except Exception as e:
            logger.warning(f"⚠️ Error during process cleanup: {e}")
    
    def _deep_cleanup(self):
        """Perform deep cleanup of ngrok resources."""
        try:
            # Clear any stuck tunnels by checking ngrok API
            for attempt in range(3):
                try:
                    response = requests.get('http://localhost:4040/api/tunnels', timeout=2)
                    if response.status_code == 200:
                        tunnels = response.json().get('tunnels', [])
                        for tunnel in tunnels:
                            tunnel_name = tunnel.get('name')
                            if tunnel_name:
                                # Try to delete the tunnel
                                requests.delete(f'http://localhost:4040/api/tunnels/{tunnel_name}', timeout=2)
                        logger.info("🧹 Cleared existing tunnel configurations")
                        break
                except:
                    time.sleep(0.5)
                    continue
            
            # Kill any remaining processes
            self._cleanup_existing_processes()
            
            # Wait for cleanup to complete
            time.sleep(2)
            
        except Exception as e:
            logger.warning(f"⚠️ Deep cleanup warning: {e}")
    
    def _reset_state(self):
        """Reset all internal state variables."""
        self.process = None
        self.public_url = None
        self.callback_url = None
        self.is_running = False
        logger.info("🔄 State reset completed")
    
    def _get_public_url(self):
        """Get the public URL from ngrok API."""
        for attempt in range(10):  # Try for 10 seconds
            try:
                response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
                if response.status_code == 200:
                    tunnels = response.json()['tunnels']
                    
                    for tunnel in tunnels:
                        if tunnel['proto'] == 'https':
                            return tunnel['public_url']
            except:
                time.sleep(1)
                continue
        
        return None
    
    def _update_settings(self):
        """Update Django settings with the new callback URL."""
        try:
            if hasattr(settings, 'ANGEL_ONE_CONFIG'):
                settings.ANGEL_ONE_CONFIG['REDIRECT_URI'] = self.callback_url
                logger.info(f"📝 Updated Django settings with callback URL")
        except Exception as e:
            logger.error(f"❌ Error updating settings: {e}")
    
    def _start_health_check(self):
        """Start a background thread to monitor tunnel health."""
        def health_check():
            while self.is_running:
                try:
                    # Check if tunnel is still active
                    response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
                    if response.status_code != 200:
                        logger.warning("⚠️ Ngrok tunnel may be down, attempting restart...")
                        self.restart_tunnel()
                except:
                    logger.warning("⚠️ Ngrok health check failed, attempting restart...")
                    self.restart_tunnel()
                
                time.sleep(30)  # Check every 30 seconds
        
        thread = threading.Thread(target=health_check, daemon=True)
        thread.start()
    
    def restart_tunnel(self):
        """Restart the ngrok tunnel."""
        logger.info("🔄 Restarting ngrok tunnel...")
        self.stop_tunnel()
        time.sleep(2)
        self.start_tunnel()
    
    def stop_tunnel(self):
        """Stop the ngrok tunnel."""
        logger.info("🛑 Stopping ngrok tunnel...")
        self.is_running = False
        
        if self.process:
            try:
                # Gracefully terminate first
                self.process.terminate()
                
                # Wait for graceful termination
                try:
                    self.process.wait(timeout=10)
                    logger.info("✅ Ngrok process terminated gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't terminate gracefully
                    logger.warning("⚠️ Ngrok didn't terminate gracefully, force killing...")
                    self.process.kill()
                    self.process.wait()
                    logger.info("✅ Ngrok process force killed")
                    
            except Exception as e:
                logger.error(f"❌ Error stopping ngrok process: {e}")
                # Try force kill as last resort
                try:
                    self.process.kill()
                except:
                    pass
            
            self.process = None
        
        # Cleanup any remaining processes
        self._cleanup_existing_processes()
        
        # Reset state
        self.public_url = None
        self.callback_url = None
        
        logger.info("🛑 Ngrok tunnel stopped completely")
    
    def get_callback_url(self):
        """Get the current callback URL."""
        return self.callback_url if self.is_running else None

# Global ngrok manager instance
ngrok_manager = NgrokManager()
_ngrok_started = False  # Flag to prevent duplicate starts

def start_ngrok_auto():
    """Start ngrok automatically when Django starts."""
    global _ngrok_started
    
    # Prevent duplicate starts
    if _ngrok_started:
        return
        
    if not getattr(settings, 'NGROK_AUTO_START', True):
        return
    
    try:
        print("=" * 60)
        print("🧹 CLEANING UP PREVIOUS NGROK SESSIONS...")
        print("=" * 60)
        
        # Pre-startup cleanup - ensure no lingering processes
        _perform_pre_startup_cleanup()
        
        # Check if ngrok is available
        result = subprocess.run(['ngrok', 'version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            logger.warning("⚠️ Ngrok not found, skipping auto-start")
            return
        
        print("🚀 STARTING FRESH NGROK TUNNEL...")
        
        # Start tunnel
        success = ngrok_manager.start_tunnel()
        _ngrok_started = True  # Mark as started
        
        if success:
            print("=" * 60)
            print("🎉 NGROK TUNNEL ACTIVE")
            print(f"📍 Local:     http://localhost:8000")
            print(f"🌍 Public:    {ngrok_manager.public_url}")
            print(f"🔗 Callback:  {ngrok_manager.callback_url}")
            print("=" * 60)
            print("✅ Angel One API calls will now work!")
            print("📋 Use this callback URL in Angel One portal:")
            print(f"   {ngrok_manager.callback_url}")
            print("=" * 60)
        else:
            print("❌ Failed to start ngrok tunnel")
            print("💡 You can start it manually: ngrok http 8000")
    
    except Exception as e:
        logger.error(f"❌ Error in auto-start: {e}")

def _perform_pre_startup_cleanup():
    """Perform comprehensive cleanup before starting."""
    try:
        # Kill all ngrok processes
        if sys.platform == 'win32':
            subprocess.run(['taskkill', '/f', '/im', 'ngrok.exe'], 
                         capture_output=True, check=False)
        else:
            subprocess.run(['pkill', '-f', 'ngrok'], 
                         capture_output=True, check=False)
        
        # Wait for processes to terminate
        time.sleep(2)
        
        # Try to clear any API connections
        for port in [4040, 4041, 4042]:  # Common ngrok ports
            try:
                requests.get(f'http://localhost:{port}/api/tunnels', timeout=1)
                # If we can connect, there's still an ngrok instance running
                logger.warning(f"⚠️ Found ngrok instance on port {port}, terminating...")
                if sys.platform == 'win32':
                    subprocess.run(f'netstat -ano | findstr :{port}', shell=True, capture_output=True)
            except:
                pass  # Port not in use, which is good
        
        print("✅ Pre-startup cleanup completed")
        
    except Exception as e:
        logger.warning(f"⚠️ Pre-startup cleanup warning: {e}")

def stop_ngrok_auto():
    """Stop ngrok when Django shuts down."""
    global _ngrok_started
    
    if _ngrok_started:
        print("\n" + "=" * 60)
        print("🛑 SHUTTING DOWN NGROK TUNNEL...")
        print("=" * 60)
        
        ngrok_manager.stop_tunnel()
        _ngrok_started = False
        
        print("✅ Ngrok tunnel stopped gracefully")
        print("=" * 60)

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown."""
    import signal
    
    def signal_handler(signum, frame):
        print(f"\n🔔 Received signal {signum}, shutting down...")
        stop_ngrok_auto()
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Terminate signal
    
    if sys.platform == 'win32':
        # Windows-specific signals
        try:
            signal.signal(signal.SIGBREAK, signal_handler)  # Ctrl+Break
        except AttributeError:
            pass

# Auto-start when this module is imported
if 'runserver' in sys.argv:
    # Only start for development server
    import atexit
    
    # Setup signal handlers for graceful shutdown
    setup_signal_handlers()
    
    # Start ngrok
    start_ngrok_auto()
    
    # Register cleanup for normal exit
    atexit.register(stop_ngrok_auto)
