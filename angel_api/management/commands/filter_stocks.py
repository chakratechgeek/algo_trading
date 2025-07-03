"""
Django management command to filter NSE stocks by price range using real Angel One API data.
"""

from django.core.management.base import BaseCommand
from angel_api.services import AngelOneAPI
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Filter NSE stocks by price range using real Angel One API data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-price',
            type=float,
            default=75.0,
            help='Minimum price (default: 75.0)'
        )
        parser.add_argument(
            '--max-price',
            type=float,
            default=150.0,
            help='Maximum price (default: 150.0)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of symbols to process (for testing)'
        )
        parser.add_argument(
            '--load-symbols',
            action='store_true',
            help='Load symbols from OpenAPIScripMaster.json first'
        )

    def handle(self, *args, **options):
        min_price = options['min_price']
        max_price = options['max_price']
        limit = options.get('limit')
        load_symbols = options.get('load_symbols', False)

        self.stdout.write(
            self.style.SUCCESS(
                f'Starting stock filtering: ₹{min_price} - ₹{max_price}'
            )
        )

        # Initialize Angel One API
        api = AngelOneAPI()

        # Load symbols from master file if requested
        if load_symbols:
            self.stdout.write('Loading symbols from master file...')
            try:
                nse_stocks, output_file = api.load_nse_symbols_from_master()
                if nse_stocks:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Loaded {len(nse_stocks)} NSE stocks, saved to {output_file}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR('Failed to load symbols from master file')
                    )
                    return
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error loading symbols: {e}')
                )
                return

        # Filter stocks by price range
        try:
            self.stdout.write('Authenticating with Angel One API...')
            
            # Test authentication first
            success, message = api.authenticate()
            if not success:
                self.stdout.write(
                    self.style.ERROR(f'Authentication failed: {message}')
                )
                return
            
            self.stdout.write(
                self.style.SUCCESS('Authentication successful!')
            )
            
            self.stdout.write(f'Filtering stocks in price range ₹{min_price} - ₹{max_price}...')
            if limit:
                self.stdout.write(f'Processing limited to {limit} symbols for testing')
            
            filtered_stocks = api.filter_stocks_by_price_range(
                min_price=min_price,
                max_price=max_price,
                max_symbols=limit
            )
            
            if filtered_stocks:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Found {len(filtered_stocks)} stocks in price range ₹{min_price} - ₹{max_price}:'
                    )
                )
                
                # Display results
                for stock in filtered_stocks[:10]:  # Show first 10
                    self.stdout.write(
                        f"  {stock['symbol']}: Rs.{stock['price']:.2f}"
                    )
                
                if len(filtered_stocks) > 10:
                    self.stdout.write(f"  ... and {len(filtered_stocks) - 10} more")
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Results saved to filtered_stocks_{min_price}_{max_price}_*.json'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'No stocks found in price range ₹{min_price} - ₹{max_price}'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during filtering: {e}')
            )
            logger.exception("Error in filter_stocks command")
