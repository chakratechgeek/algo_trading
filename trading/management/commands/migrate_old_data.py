"""Django management command to migrate old database to Django models."""

import sqlite3
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from portfolio.models import Portfolio, Trade
from portfolio.services import PortfolioService
from angel_api.models import NSESymbol


class Command(BaseCommand):
    help = 'Migrate data from old SQLite database to Django models'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--db-path',
            type=str,
            default='../trading.db',
            help='Path to the old SQLite database',
        )
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username for the portfolio owner',
        )
    
    def handle(self, *args, **options):
        """Migrate data from old database."""
        db_path = options['db_path']
        username = options['username']
        
        self.stdout.write(f"Migrating data from {db_path}")
        
        try:
            # Get or create user
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': 'Trading',
                    'last_name': 'Bot',
                    'email': f'{username}@example.com'
                }
            )
            
            if created:
                self.stdout.write(f"Created user: {username}")
            
            # Get or create portfolio
            portfolio_service = PortfolioService()
            portfolio = portfolio_service.get_or_create_portfolio(user)
            
            # Connect to old database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Migrate balance
            cursor.execute('SELECT balance FROM amount WHERE id=1')
            balance_row = cursor.fetchone()
            if balance_row:
                portfolio.current_balance = balance_row[0]
                portfolio.save()
                self.stdout.write(f"Migrated balance: ₹{balance_row[0]}")
            
            # Migrate trades
            cursor.execute('''
                SELECT symbol, price, qty, timestamp, action, buy_amount, 
                       brokerage_fee, profit, order_type, exchange, status, 
                       remarks, pnl_percent, holding_days, ref_trade_id
                FROM trade_metadata 
                ORDER BY timestamp
            ''')
            
            trades_migrated = 0
            for row in cursor.fetchall():
                try:
                    symbol_name = row[0]
                    price = row[1]
                    quantity = row[2]
                    timestamp_str = row[3]
                    action = row[4]
                    buy_amount = row[5]
                    brokerage_fee = row[6] or 0
                    profit = row[7]
                    order_type = row[8] or 'MARKET'
                    exchange = row[9] or 'NSE'
                    status = row[10] or 'EXECUTED'
                    remarks = row[11] or ''
                    pnl_percent = row[12]
                    holding_days = row[13]
                    ref_trade_id = row[14]
                    
                    # Parse timestamp
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    except:
                        timestamp = datetime.now()
                    
                    # Get or create symbol
                    symbol, created = NSESymbol.objects.get_or_create(
                        symbol=symbol_name,
                        exchange=exchange,
                        defaults={'token': symbol_name, 'lot_size': 1}
                    )
                    
                    # Create trade
                    trade = Trade.objects.create(
                        portfolio=portfolio,
                        symbol=symbol,
                        price=price,
                        quantity=quantity,
                        action=action,
                        buy_amount=buy_amount,
                        brokerage_fee=brokerage_fee,
                        profit=profit,
                        order_type=order_type,
                        exchange=exchange,
                        status=status,
                        remarks=remarks,
                        pnl_percent=pnl_percent,
                        holding_days=holding_days
                    )
                    
                    # Set the created_at timestamp
                    trade.created_at = timestamp
                    trade.save()
                    
                    trades_migrated += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error migrating trade: {e}")
                    )
            
            conn.close()
            
            self.stdout.write(
                self.style.SUCCESS(f"Migration completed: {trades_migrated} trades migrated")
            )
            
            # Update portfolio positions based on trades
            self._update_positions(portfolio_service)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Migration failed: {e}")
            )
    
    def _update_positions(self, portfolio_service):
        """Update portfolio positions based on migrated trades."""
        # This would typically be handled by the portfolio service
        # For now, just log that positions should be calculated
        self.stdout.write("Note: Position calculations should be run separately")
