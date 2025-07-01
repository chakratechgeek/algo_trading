"""Django management command to set up initial trading platform data."""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from portfolio.services import PortfolioService, TradingSessionService
from trading.services import TradingStrategyService, TradingBotService
from core.services import ConfigurationService


class Command(BaseCommand):
    help = 'Set up initial trading platform data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username for the admin user',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='Password for the admin user',
        )
    
    def handle(self, *args, **options):
        """Set up initial data."""
        username = options['username']
        password = options['password']
        
        self.stdout.write("Setting up initial trading platform data...")
        
        # Create admin user
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': 'Trading',
                'last_name': 'Admin',
                'email': f'{username}@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(f"✓ Created admin user: {username}")
        else:
            self.stdout.write(f"✓ Admin user already exists: {username}")
        
        # Create portfolio
        portfolio_service = PortfolioService()
        portfolio = portfolio_service.get_or_create_portfolio(user)
        self.stdout.write(f"✓ Portfolio created/verified: ₹{portfolio.current_balance}")
        
        # Create default trading strategy
        strategy_service = TradingStrategyService()
        
        try:
            strategy = strategy_service.create_news_based_strategy(
                name="Default News Strategy",
                config={
                    'sentiment_threshold': 0.7,
                    'confidence_threshold': 75,
                    'max_holding_hours': 24,
                    'stop_loss_percent': 2.0,
                    'take_profit_percent': 5.0
                }
            )
            self.stdout.write(f"✓ Created trading strategy: {strategy.name}")
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                self.stdout.write("✓ Trading strategy already exists")
            else:
                self.stdout.write(f"✗ Error creating strategy: {e}")
        
        # Create trading bot
        try:
            from trading.models import TradingStrategy
            strategy = TradingStrategy.objects.get(name="Default News Strategy")
            
            bot_service = TradingBotService()
            bot = bot_service.create_bot(
                name="Default Trading Bot",
                portfolio=portfolio,
                strategy=strategy,
                config={
                    'max_positions': 5,
                    'position_size': 10.0,
                    'is_paper_trading': True,
                    'check_interval_minutes': 10
                }
            )
            self.stdout.write(f"✓ Created trading bot: {bot.name}")
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                self.stdout.write("✓ Trading bot already exists")
            else:
                self.stdout.write(f"✗ Error creating bot: {e}")
        
        # Set up default configuration
        config_data = [
            ('CHECK_INTERVAL', '600', 'Check interval in seconds'),
            ('MAX_POSITIONS', '10', 'Maximum positions'),
            ('FIXED_QTY', '20', 'Fixed quantity per trade'),
            ('MAX_POSITION_SIZE', '0.1', 'Max position size as fraction of portfolio'),
            ('MAX_LOSS_PERCENT', '0.02', 'Maximum loss per trade'),
            ('PRICE_THRESHOLD', '200.0', 'Price threshold for stock selection'),
        ]
        
        for key, value, description in config_data:
            ConfigurationService.set_config(key, value, description)
        
        self.stdout.write("✓ Default configuration set")
        
        # Start trading session
        session_service = TradingSessionService(portfolio)
        active_session = session_service.get_active_session()
        
        if not active_session:
            session = session_service.start_session()
            self.stdout.write(f"✓ Started trading session: {session.session_date}")
        else:
            self.stdout.write("✓ Trading session already active")
        
        self.stdout.write(
            self.style.SUCCESS(
                "\n🎉 Trading platform setup complete!\n"
                f"Admin login: {username} / {password}\n"
                "You can now:\n"
                "1. Run: python manage.py runserver (start web interface)\n"
                "2. Run: python manage.py run_trading_bot (start trading)\n"
                "3. Visit: http://localhost:8000/admin (admin interface)"
            )
        )
