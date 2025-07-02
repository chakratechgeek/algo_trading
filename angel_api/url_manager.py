"""URL manager for Angel API."""

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.http import HttpResponse
from django.conf import settings
from .utils import get_callback_urls, update_angel_one_redirect_uri

class URLConfigManagerView(APIView):
    """View to manage the redirect URL configuration."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Display possible redirect URLs and allow selection."""
        callback_urls = get_callback_urls(request)
        current_redirect_uri = settings.ANGEL_ONE_CONFIG.get('REDIRECT_URI', '')
        
        # Create a unique list of all URLs for display
        all_urls = [callback_urls['recommended']]
        all_urls.extend([url for url in callback_urls['alternatives'] if url not in all_urls])
        if callback_urls['localhost'] not in all_urls:
            all_urls.append(callback_urls['localhost'])
        
        # Generate URL list HTML
        url_options_html = ""
        for i, url in enumerate(all_urls):
            selected = ' checked' if url == current_redirect_uri else ''
            url_options_html += f"""
                <div style="margin: 10px 0;">
                    <input type="radio" name="redirect_uri" id="url_{i}" value="{url}"{selected}>
                    <label for="url_{i}">
                        <code style="padding: 5px; background: #f5f5f5;">{url}</code>
                        {' (Current)' if url == current_redirect_uri else ''}
                        {' (Recommended)' if url == callback_urls['recommended'] else ''}
                    </label>
                </div>
            """
            
        html_content = """
            <html>
            <head>
                <title>Angel One API URL Configuration</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                    .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    .code { background: #f8f9fa; padding: 10px; border-radius: 5px; font-family: monospace; margin: 10px 0; overflow-wrap: break-word; }
                    .step { margin: 20px 0; padding: 15px; border-left: 4px solid #3498db; background: #f8f9fa; }
                    .important { background: #fff3cd; border-color: #ffc107; padding: 15px; border-radius: 5px; margin: 20px 0; }
                    .success { color: #27ae60; }
                    .error { color: #e74c3c; }
                    .tips { background: #e8f4f8; padding: 15px; border-radius: 5px; margin: 20px 0; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🔗 Angel One API URL Configuration</h1>
                    
                    <div class="important">
                        <strong>⚠️ Important:</strong> Select a redirect URL that will work with Angel One API.<br>
                        - Most OAuth providers require public HTTPS URLs.<br>
                        - Localhost URLs often don't work with OAuth providers.
                    </div>
                    
                    <form method="post" action="" onsubmit="return confirm('Update the redirect URI to the selected URL?');">
                        <div class="step">
                            <h3>Available Redirect URLs:</h3>
                            URL_OPTIONS_PLACEHOLDER
                        </div>
                        
                        <div class="tips">
                            <h3>Troubleshooting Tips:</h3>
                            <ul>
                                <li>If none of these URLs work, try using <a href="/api/angel/ngrok-setup/">ngrok</a> to create a public HTTPS URL.</li>
                                <li>For localhost testing, you might need to add the domain to your hosts file.</li>
                                <li>Make sure port 8000 is accessible if using a non-localhost URL.</li>
                                <li>Some OAuth providers only accept HTTPS URLs (not HTTP).</li>
                            </ul>
                        </div>
                        
                        <p style="text-align: center; margin-top: 30px;">
                            <button type="submit" style="background: #3498db; color: white; padding: 12px 30px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px;">
                                Update Redirect URL
                            </button>
                        </p>
                    </form>
                    
                    <hr style="margin: 30px 0;">
                    
                    <p style="text-align: center;">
                        <a href="/api/angel/setup/" style="background: #27ae60; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">
                            Angel API Setup Guide
                        </a>
                        <a href="/api/angel/ngrok-setup/" style="background: #9b59b6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">
                            Configure with ngrok
                        </a>
                        <a href="/" style="color: #3498db; text-decoration: none; margin-left: 10px;">
                            Back to Dashboard
                        </a>
                    </p>
                </div>
                
                <script>
                    // Auto-update form when radio button changes
                    document.addEventListener('DOMContentLoaded', function() {
                        var radioButtons = document.querySelectorAll('input[name="redirect_uri"]');
                        radioButtons.forEach(function(btn) {
                            btn.addEventListener('change', function() {
                                if (this.checked) {
                                    if (confirm('Update the redirect URI to ' + this.value + '?')) {
                                        document.querySelector('form').submit();
                                    }
                                }
                            });
                        });
                    });
                </script>
            </body>
            </html>
        """
        
        # Replace placeholder with generated URL options
        html_content = html_content.replace("URL_OPTIONS_PLACEHOLDER", url_options_html)
        
        return HttpResponse(html_content)
        
    def post(self, request):
        """Update the redirect URI configuration."""
        new_uri = request.POST.get('redirect_uri')
        
        if not new_uri:
            return HttpResponse("""
                <html><head><title>Error</title></head><body>
                    <h1 class="error">❌ Missing Redirect URI</h1>
                    <p>No redirect URI was provided.</p>
                    <a href="/api/angel/url-config/">← Back</a>
                </body></html>
            """, status=400)
            
        success = update_angel_one_redirect_uri(new_uri)
        
        if success:
            html_content = f"""
                <html><head>
                    <title>Success</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                        .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        .success {{ color: #27ae60; }}
                        .code {{ background: #f8f9fa; padding: 10px; border-radius: 5px; font-family: monospace; margin: 10px 0; }}
                    </style>
                </head><body>
                    <div class="container">
                        <h1 class="success">✅ Redirect URI Updated</h1>
                        <p>The Angel One API redirect URI has been updated to:</p>
                        <div class="code">{new_uri}</div>
                        <p>Update this URL in your Angel One developer portal as well.</p>
                        <p style="margin-top: 30px; text-align: center;">
                            <a href="/api/angel/setup/" style="background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                                ← Back to Setup
                            </a>
                        </p>
                    </div>
                </body></html>
            """
            return HttpResponse(html_content)
        else:
            return HttpResponse("""
                <html><head><title>Error</title></head><body>
                    <h1 class="error">❌ Update Failed</h1>
                    <p>Failed to update the redirect URI. Check your settings.</p>
                    <a href="/api/angel/url-config/">← Back</a>
                </body></html>
            """, status=500)
