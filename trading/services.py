"""Trading strategy and execution services."""

import logging
import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from together import Together
from .models import (
    TradingStrategy, TradingBot, TradingSignal, TradingExecution, 
    MarketAnalysis, NewsAnalysis
)
from angel_api.models import NSESymbol
from angel_api.services import AngelOneAPI
from portfolio.services import PortfolioService
from core.services import MarketService, RiskManager


class TradingStrategyService:
    """Service for managing trading strategies."""
    
    def __init__(self):
        self.logger = logging.getLogger('trading')
        self.angel_api = AngelOneAPI()
        self.market_service = MarketService()
        self.llm_client = Together(api_key=settings.LLM_CONFIG['API_KEY'])
    
    def create_news_based_strategy(self, name, config=None):
        """Create a news-based trading strategy."""
        default_config = {
            'news_sources': ['economic_times', 'moneycontrol', 'business_standard'],
            'sentiment_threshold': 0.6,
            'confidence_threshold': 75,
            'max_holding_hours': 24,
            'stop_loss_percent': 2.0,
            'take_profit_percent': 5.0,
            'keywords': list(settings.TRADING_CONFIG.get('NEWS_KEYWORDS', [])),
        }
        
        if config:
            default_config.update(config)
        
        strategy = TradingStrategy.objects.create(
            name=name,
            description="News-based trading strategy using sentiment analysis",
            strategy_type='NEWS_BASED',
            config_parameters=default_config,
            is_active=True
        )
        
        self.logger.info(f"Created news-based strategy: {name}")
        return strategy
    
    def analyze_news_for_symbol(self, symbol_name, headlines, limit=5):
        """Analyze news headlines for trading signals."""
        try:
            # Select relevant headlines
            selected_headlines = headlines[:limit]
            
            if not selected_headlines:
                return {
                    'sentiment': 'NEUTRAL',
                    'confidence': 0,
                    'signals': [],
                    'analysis': 'No headlines available'
                }
            
            # Prepare prompt for LLM analysis
            prompt = f"""
Analyze the following news headlines for {symbol_name} and provide trading insights:

Headlines:
{chr(10).join([f"- {headline}" for headline in selected_headlines])}

Please provide:
1. Overall sentiment (POSITIVE/NEGATIVE/NEUTRAL)
2. Confidence score (0-100)
3. Trading recommendation (BUY/SELL/HOLD)
4. Key factors driving the sentiment
5. Risk assessment

Format the response as JSON with keys: sentiment, confidence, recommendation, factors, risk_level
"""
            
            # Call LLM for analysis
            response = self.llm_client.chat.completions.create(
                model=settings.LLM_CONFIG['MODEL'],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            
            # Parse response
            analysis_text = response.choices[0].message.content
            
            try:
                analysis = json.loads(analysis_text)
            except json.JSONDecodeError:
                # Fallback parsing
                analysis = {
                    'sentiment': 'NEUTRAL',
                    'confidence': 50,
                    'recommendation': 'HOLD',
                    'factors': ['Analysis parsing failed'],
                    'risk_level': 'MEDIUM'
                }
            
            self.logger.info(f"News analysis for {symbol_name}: {analysis.get('sentiment')} ({analysis.get('confidence')}%)")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing news for {symbol_name}: {e}")
            return {
                'sentiment': 'NEUTRAL',
                'confidence': 0,
                'recommendation': 'HOLD',
                'factors': [f'Analysis error: {str(e)}'],
                'risk_level': 'HIGH'
            }
    
    def generate_trading_signals(self, strategy_id, symbols=None):
        """Generate trading signals based on strategy."""
        try:
            strategy = TradingStrategy.objects.get(id=strategy_id, is_active=True)
            
            if strategy.strategy_type == 'NEWS_BASED':
                return self._generate_news_based_signals(strategy, symbols)
            else:
                self.logger.warning(f"Strategy type {strategy.strategy_type} not implemented")
                return []
                
        except TradingStrategy.DoesNotExist:
            self.logger.error(f"Strategy {strategy_id} not found")
            return []
    
    def _generate_news_based_signals(self, strategy, symbols=None):
        """Generate signals based on news analysis."""
        signals = []
        config = strategy.config_parameters
        
        if not symbols:
            # Get symbols from discovery or watchlist
            symbols = self.angel_api.discover_symbols()
        
        for symbol_name in symbols[:10]:  # Limit to avoid API overuse
            try:
                # Get symbol object
                symbol, created = NSESymbol.objects.get_or_create(
                    symbol=symbol_name,
                    exchange='NSE',
                    defaults={'token': symbol_name, 'lot_size': 1}
                )
                
                # Fetch headlines (placeholder implementation)
                headlines = [f"Sample headline for {symbol_name}"]
                
                # Analyze news
                analysis = self.analyze_news_for_symbol(symbol_name, headlines)
                
                # Generate signal if conditions are met
                if (analysis['confidence'] >= config.get('confidence_threshold', 75) and
                    analysis['sentiment'] in ['POSITIVE', 'NEGATIVE']):
                    
                    current_price = self.angel_api.get_ltp(symbol_name)
                    
                    signal_type = 'BUY' if analysis['sentiment'] == 'POSITIVE' else 'SELL'
                    
                    # Calculate target and stop loss
                    if signal_type == 'BUY':
                        target_price = current_price * (1 + config.get('take_profit_percent', 5) / 100)
                        stop_loss_price = current_price * (1 - config.get('stop_loss_percent', 2) / 100)
                    else:
                        target_price = current_price * (1 - config.get('take_profit_percent', 5) / 100)
                        stop_loss_price = current_price * (1 + config.get('stop_loss_percent', 2) / 100)
                    
                    # Create signal
                    signal = TradingSignal.objects.create(
                        strategy=strategy,
                        symbol=symbol,
                        signal_type=signal_type,
                        confidence=analysis['confidence'],
                        entry_price=current_price,
                        target_price=target_price,
                        stop_loss_price=stop_loss_price,
                        signal_strength='STRONG' if analysis['confidence'] > 85 else 'MODERATE',
                        analysis_data=analysis,
                        news_sentiment=analysis['sentiment'],
                        expires_at=timezone.now() + timedelta(hours=config.get('max_holding_hours', 24))
                    )
                    
                    signals.append(signal)
                    self.logger.info(f"Generated {signal_type} signal for {symbol_name} (confidence: {analysis['confidence']}%)")
                
            except Exception as e:
                self.logger.error(f"Error generating signal for {symbol_name}: {e}")
        
        self.logger.info(f"Generated {len(signals)} trading signals")
        return signals


class TradingBotService:
    """Service for managing trading bots."""
    
    def __init__(self, bot_id=None):
        self.bot_id = bot_id
        self.bot = None
        self.logger = logging.getLogger('trading')
        self.angel_api = AngelOneAPI()
        self.market_service = MarketService()
        self.risk_manager = RiskManager()
        
        if bot_id:
            try:
                self.bot = TradingBot.objects.get(id=bot_id)
            except TradingBot.DoesNotExist:
                self.logger.error(f"Trading bot {bot_id} not found")
    
    def create_bot(self, name, portfolio, strategy, config=None):
        """Create a new trading bot."""
        default_config = {
            'max_positions': 5,
            'position_size': 10.0,
            'stop_loss_percent': 2.0,
            'take_profit_percent': 5.0,
            'check_interval_minutes': 5,
            'is_paper_trading': True
        }
        
        if config:
            default_config.update(config)
        
        bot = TradingBot.objects.create(
            name=name,
            portfolio=portfolio,
            strategy=strategy,
            **default_config
        )
        
        self.logger.info(f"Created trading bot: {name}")
        return bot
    
    def run_bot_cycle(self):
        """Run a single bot trading cycle."""
        if not self.bot or not self.bot.is_active:
            return
        
        try:
            # Update bot run statistics
            self.bot.last_run_at = timezone.now()
            self.bot.total_runs += 1
            self.bot.save()
            
            # Check if market is open (if required)
            if self.bot.trading_hours_only and not self.market_service.is_market_open():
                self.logger.info(f"Bot {self.bot.name}: Market closed, skipping cycle")
                return
            
            # Get portfolio service
            portfolio_service = PortfolioService(self.bot.portfolio)
            
            # Check risk limits
            if not self._check_risk_limits(portfolio_service):
                self.logger.warning(f"Bot {self.bot.name}: Risk limits exceeded, stopping")
                self.bot.is_active = False
                self.bot.save()
                return
            
            # Process pending signals
            self._process_pending_signals(portfolio_service)
            
            # Generate new signals if positions allow
            if self._can_open_new_positions(portfolio_service):
                self._generate_and_process_signals()
            
            # Monitor existing positions
            self._monitor_positions(portfolio_service)
            
            self.logger.info(f"Bot {self.bot.name}: Cycle completed successfully")
            
        except Exception as e:
            self.bot.error_count += 1
            self.bot.last_error = str(e)
            self.bot.save()
            self.logger.error(f"Bot {self.bot.name}: Error in cycle: {e}")
    
    def _check_risk_limits(self, portfolio_service):
        """Check if bot can continue trading based on risk limits."""
        if self.bot.daily_loss_limit:
            # Calculate today's P&L
            today_trades = portfolio_service.get_trades().filter(
                created_at__date=timezone.now().date()
            )
            daily_pnl = sum(trade.profit or 0 for trade in today_trades)
            
            if daily_pnl < -self.bot.daily_loss_limit:
                self.logger.warning(f"Daily loss limit exceeded: ₹{daily_pnl}")
                return False
        
        return True
    
    def _process_pending_signals(self, portfolio_service):
        """Process pending trading signals."""
        pending_signals = TradingSignal.objects.filter(
            strategy=self.bot.strategy,
            is_active=True,
            is_executed=False
        ).exclude(expires_at__lt=timezone.now())
        
        for signal in pending_signals:
            try:
                self._execute_signal(signal, portfolio_service)
            except Exception as e:
                self.logger.error(f"Error executing signal {signal.id}: {e}")
    
    def _execute_signal(self, signal, portfolio_service):
        """Execute a trading signal."""
        # Check if we already have a position in this symbol
        existing_position = portfolio_service.get_open_positions().filter(
            symbol=signal.symbol
        ).first()
        
        if signal.signal_type == 'SELL' and not existing_position:
            self.logger.info(f"No position to sell for {signal.symbol.symbol}")
            signal.is_active = False
            signal.save()
            return
        
        if signal.signal_type == 'BUY' and existing_position:
            self.logger.info(f"Already have position in {signal.symbol.symbol}")
            signal.is_active = False
            signal.save()
            return
        
        # Calculate position size
        if signal.signal_type == 'BUY':
            portfolio_value = portfolio_service.get_balance()
            position_value = portfolio_value * (self.bot.position_size / 100)
            quantity = int(position_value / signal.entry_price)
            
            if quantity == 0:
                self.logger.warning(f"Insufficient funds for {signal.symbol.symbol}")
                return
        else:
            quantity = existing_position.total_quantity
        
        # Create execution record
        execution = TradingExecution.objects.create(
            bot=self.bot,
            signal=signal,
            execution_type='SIGNAL_ENTRY',
            quantity=quantity,
            requested_price=signal.entry_price,
            status='PENDING'
        )
        
        try:
            # Place order
            if not self.bot.is_paper_trading:
                success, order_id = self.angel_api.place_order(
                    symbol=signal.symbol.symbol,
                    quantity=quantity,
                    price=signal.entry_price,
                    order_type='LIMIT',
                    transaction_type=signal.signal_type
                )
                
                if success:
                    execution.order_id = order_id
                    execution.status = 'EXECUTED'
                    execution.executed_price = signal.entry_price
                else:
                    execution.status = 'FAILED'
                    execution.error_message = order_id  # Error message
            else:
                # Paper trading - simulate execution
                execution.status = 'EXECUTED'
                execution.executed_price = signal.entry_price
            
            execution.save()
            
            # Update signal
            if execution.status == 'EXECUTED':
                signal.is_executed = True
                signal.executed_at = timezone.now()
                signal.execution_price = execution.executed_price
                signal.save()
                
                # Update portfolio (for paper trading)
                if self.bot.is_paper_trading:
                    portfolio_service.execute_trade(
                        symbol_name=signal.symbol.symbol,
                        price=execution.executed_price,
                        quantity=quantity,
                        action=signal.signal_type,
                        remarks=f"Bot execution - Signal {signal.id}"
                    )
                
                self.logger.info(f"Signal executed: {signal.signal_type} {quantity} {signal.symbol.symbol}")
            
        except Exception as e:
            execution.status = 'FAILED'
            execution.error_message = str(e)
            execution.save()
            self.logger.error(f"Signal execution failed: {e}")
    
    def _can_open_new_positions(self, portfolio_service):
        """Check if bot can open new positions."""
        open_positions = portfolio_service.get_open_positions().count()
        return open_positions < self.bot.max_positions
    
    def _generate_and_process_signals(self):
        """Generate new signals and process them."""
        strategy_service = TradingStrategyService()
        
        # Get symbols to analyze (from discovery or watchlist)
        symbols = self.angel_api.discover_symbols()[:10]  # Limit for performance
        
        # Generate signals
        signals = strategy_service.generate_trading_signals(
            strategy_id=self.bot.strategy.id,
            symbols=symbols
        )
        
        self.logger.info(f"Bot {self.bot.name}: Generated {len(signals)} new signals")
    
    def _monitor_positions(self, portfolio_service):
        """Monitor existing positions for exit conditions."""
        open_positions = portfolio_service.get_open_positions()
        
        for position in open_positions:
            try:
                # Update current price
                current_price = self.angel_api.get_ltp(position.symbol.symbol)
                position.update_current_price(current_price)
                
                # Check stop loss and take profit
                if self._should_exit_position(position):
                    self._create_exit_signal(position)
                    
            except Exception as e:
                self.logger.error(f"Error monitoring position {position.symbol.symbol}: {e}")
    
    def _should_exit_position(self, position):
        """Check if position should be exited."""
        if not position.current_price:
            return False
        
        # Calculate P&L percentage
        pnl_percent = ((position.current_price - position.average_price) / position.average_price) * 100
        
        # Check stop loss
        if pnl_percent <= -self.bot.stop_loss_percent:
            self.logger.info(f"Stop loss triggered for {position.symbol.symbol}: {pnl_percent:.2f}%")
            return True
        
        # Check take profit
        if pnl_percent >= self.bot.take_profit_percent:
            self.logger.info(f"Take profit triggered for {position.symbol.symbol}: {pnl_percent:.2f}%")
            return True
        
        return False
    
    def _create_exit_signal(self, position):
        """Create exit signal for position."""
        # Create sell signal
        signal = TradingSignal.objects.create(
            strategy=self.bot.strategy,
            symbol=position.symbol,
            signal_type='SELL',
            confidence=100,  # Exit signals are always high confidence
            entry_price=position.current_price,
            signal_strength='STRONG',
            analysis_data={'reason': 'risk_management', 'position_id': position.id},
            expires_at=timezone.now() + timedelta(hours=1)
        )
        
        self.logger.info(f"Created exit signal for {position.symbol.symbol}")
        return signal
    
    def stop_bot(self):
        """Stop the trading bot."""
        if self.bot:
            self.bot.is_active = False
            self.bot.save()
            self.logger.info(f"Bot {self.bot.name} stopped")
    
    def get_bot_performance(self):
        """Get bot performance metrics."""
        if not self.bot:
            return {}
        
        # Get all executions
        executions = TradingExecution.objects.filter(bot=self.bot)
        
        total_executions = executions.count()
        successful_executions = executions.filter(status='EXECUTED').count()
        
        # Calculate success rate
        success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
        
        return {
            'bot_name': self.bot.name,
            'is_active': self.bot.is_active,
            'total_runs': self.bot.total_runs,
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'success_rate': success_rate,
            'error_count': self.bot.error_count,
            'last_run': self.bot.last_run_at,
            'last_error': self.bot.last_error
        }
