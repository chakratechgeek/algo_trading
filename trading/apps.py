from django.apps import AppConfig


class TradingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'trading'
    
    def ready(self):
        """Import admin when app is ready."""
        import trading.admin
