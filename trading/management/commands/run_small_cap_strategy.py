"""
Django management command to run the Small Cap Trading Strategy.
Usage: python manage.py run_small_cap_strategy --portfolio-id 1
"""

import time
import signal
import sys
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from trading.small_cap_strategy import SmallCapTradingService
from portfolio.models import Portfolio


class Command(BaseCommand):
    help = 'Run Small Cap Trading Strategy'
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.trading_service = SmallCapTradingService()
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--portfolio-id',
            type=int,
            required=True,
            help='Portfolio ID to use for trading',
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Run once and exit (no continuous loop)',
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=1800,  # 30 minutes
            help='Check interval in seconds (default: 1800 - 30 minutes)',
        )
        parser.add_argument(
            '--max-investment',
            type=int,
            default=5000,
            help='Maximum investment per stock (default: 5000)',
        )
    
    def handle(self, *args, **options):
        """Main command handler."""
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        portfolio_id = options['portfolio_id']
        run_once = options['once']
        interval = options['interval']
        max_investment = options['max_investment']
        
        # Validate portfolio exists
        try:
            portfolio = Portfolio.objects.get(id=portfolio_id)
            self.stdout.write(
                self.style.SUCCESS(f'Using portfolio: {portfolio.name} (ID: {portfolio_id})')
            )
        except Portfolio.DoesNotExist:
            raise CommandError(f'Portfolio with ID {portfolio_id} does not exist')
        
        self.stdout.write(
            self.style.SUCCESS('🎯 Starting Small Cap Trading Strategy with DeepSeek-V3 AI...')
        )
        self.stdout.write(f'Portfolio: {portfolio.name}')
        self.stdout.write(f'Max Investment per stock: ₹{max_investment:,}')
        self.stdout.write(f'Check interval: {interval} seconds')
        self.stdout.write('Strategy Rules:')
        self.stdout.write('  • AI Model: DeepSeek-V3 (Advanced Reasoning)')
        self.stdout.write('  • Target: Small cap stocks (₹50-100 price range)')
        self.stdout.write('  • Buy: Based on DeepSeek AI analysis + high volume')
        self.stdout.write('  • Sell: ±₹2 change from buy price OR AI suggestion')
        self.stdout.write('  • Balance check: Must have minimum ₹1000 available')
        
        if run_once:
            self._run_trading_cycle(portfolio_id, max_investment)
        else:
            self._run_continuous_trading(portfolio_id, max_investment, interval)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.stdout.write(self.style.WARNING('\\n🛑 Received shutdown signal...'))
        self.running = False
    
    def _run_trading_cycle(self, portfolio_id, max_investment):
        """Run a single trading cycle."""
        self.stdout.write(
            self.style.HTTP_INFO(f'\\n🔄 Running trading cycle at {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}')
        )
        
        try:
            # Store max_investment in service for this cycle
            self.trading_service.max_investment = max_investment
            
            results = self.trading_service.run_small_cap_trading_cycle(portfolio_id)
            
            # Display results
            self._display_results(results)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error in trading cycle: {e}')
            )
    
    def _run_continuous_trading(self, portfolio_id, max_investment, interval):
        """Run continuous trading with specified interval."""
        self.stdout.write(
            self.style.SUCCESS(f'\\n🔄 Starting continuous trading (Press Ctrl+C to stop)')
        )
        
        cycle_count = 0
        
        while self.running:
            try:
                cycle_count += 1
                self.stdout.write(
                    self.style.HTTP_INFO(f'\\n📊 Trading Cycle #{cycle_count} - {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}')
                )
                
                self._run_trading_cycle(portfolio_id, max_investment)
                
                if self.running:
                    self.stdout.write(
                        self.style.HTTP_INFO(f'😴 Waiting {interval} seconds until next cycle...\\n')
                    )
                    
                    # Sleep with interruption check
                    for _ in range(interval):
                        if not self.running:
                            break
                        time.sleep(1)
                
            except KeyboardInterrupt:
                self.running = False
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error in continuous trading: {e}')
                )
                self.stdout.write('⏰ Waiting before retry...')
                time.sleep(60)  # Wait 1 minute before retry
        
        self.stdout.write(
            self.style.SUCCESS('✅ Trading strategy stopped successfully')
        )
    
    def _display_results(self, results):
        """Display trading cycle results."""
        if 'error' in results:
            self.stdout.write(
                self.style.ERROR(f'❌ Cycle Error: {results["error"]}')
            )
            return
        
        # Display sells
        sells = results.get('sells_executed', [])
        if sells:
            self.stdout.write(self.style.SUCCESS(f'💰 SELLS EXECUTED ({len(sells)}):'))
            for sell in sells:
                if sell['result']['success']:
                    self.stdout.write(
                        f'  ✅ {sell["symbol"]}: {sell["result"]["message"]} - {sell["reason"]}'
                    )
                else:
                    self.stdout.write(
                        f'  ❌ {sell["symbol"]}: {sell["result"]["message"]}'
                    )
        
        # Display buys
        buys = results.get('buys_executed', [])
        if buys:
            self.stdout.write(self.style.SUCCESS(f'🛒 BUYS EXECUTED ({len(buys)}):'))
            for buy in buys:
                if buy['result']['success']:
                    confidence = buy['analysis']['confidence']
                    self.stdout.write(
                        f'  ✅ {buy["symbol"]}: {buy["result"]["message"]} (AI Confidence: {confidence}%)'
                    )
                else:
                    self.stdout.write(
                        f'  ❌ {buy["symbol"]}: {buy["result"]["message"]}'
                    )
        
        # Display analysis summary
        analyses = results.get('analysis_performed', [])
        if analyses:
            buy_recommendations = [a for a in analyses if a['analysis']['recommendation'] == 'BUY']
            sell_recommendations = [a for a in analyses if a['analysis']['recommendation'] == 'SELL']
            
            self.stdout.write(f'📈 ANALYSIS SUMMARY:')
            self.stdout.write(f'  • Stocks analyzed: {len(analyses)}')
            self.stdout.write(f'  • Buy recommendations: {len(buy_recommendations)}')
            self.stdout.write(f'  • Sell recommendations: {len(sell_recommendations)}')
            
            # Show top buy opportunities not executed
            high_confidence_buys = [
                a for a in buy_recommendations 
                if a['analysis']['confidence'] > 60 and a['symbol'] not in [b['symbol'] for b in buys]
            ]
            
            if high_confidence_buys:
                self.stdout.write('🔍 Top opportunities not executed:')
                for opp in high_confidence_buys[:3]:
                    reasons = ', '.join(opp['analysis']['reasons'][:2])
                    self.stdout.write(
                        f'  • {opp["symbol"]}: {opp["analysis"]["confidence"]}% confidence - {reasons}'
                    )
        
        # Display errors
        errors = results.get('errors', [])
        if errors:
            self.stdout.write(self.style.WARNING(f'⚠️ ERRORS ({len(errors)}):'))
            for error in errors:
                self.stdout.write(f'  • {error}')
        
        if not sells and not buys and not errors:
            self.stdout.write(self.style.HTTP_INFO('📊 No trading actions taken this cycle'))
