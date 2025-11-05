from django.core.management.base import BaseCommand
from trading.models import Trade
from datetime import datetime
import requests
import os
import json
import re


class Command(BaseCommand):
    help = 'Fetch politician stock trades from Capitol Trades API and populate database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Number of trades to fetch (default: 100)',
        )

    def handle(self, *args, **options):
        limit = options['limit']
        
        self.stdout.write(self.style.WARNING(f'Fetching up to {limit} recent politician trades...'))
        
    # Primary source: QuiverQuant API via QUIVER_API_KEY. No scraping is performed.
        
        try:
            # Option 1: Capitol Trades (example endpoint - may require API key for full access)
            # url = "https://bff.capitoltrades.com/trades"
            
            # Option 2: Use publicly available JSON endpoints or scrape
            # For demo purposes, using a placeholder that you'll replace with actual API
            
            # Fetch from configured sources (QuiverQuant -> placeholder)
            trades_data = self._fetch_from_api(limit)
            
            created_count = 0
            updated_count = 0
            
            for trade_data in trades_data:
                # Check if trade already exists (avoid duplicates)
                # Using politician + ticker + trade_date as unique combination
                existing = Trade.objects.filter(
                    politician_name=trade_data['politician_name'],
                    ticker=trade_data['ticker'],
                    trade_date=trade_data['trade_date']
                ).first()
                
                if existing:
                    # Update existing trade
                    for key, value in trade_data.items():
                        setattr(existing, key, value)
                    existing.save()
                    updated_count += 1
                else:
                    # Create new trade
                    Trade.objects.create(**trade_data)
                    created_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Sync complete: {created_count} new trades, {updated_count} updated'
                )
            )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error fetching trades: {str(e)}'))
            raise
    
    def _fetch_from_api(self, limit):
        """
        Fetch politician trades from QuiverQuant. If that fails, fall back to
        generating a small placeholder dataset so the UI stays functional.
        """

        # Strategy 1: QuiverQuant API (primary)
        try:
            self.stdout.write('Trying QuiverQuant API...')
            qqq_trades = self._fetch_quiver_quant(limit)
            if qqq_trades:
                qqq_trades = [t for t in qqq_trades if self._validate_trade(t)]
                self.stdout.write(self.style.SUCCESS(f'✓ Fetched {len(qqq_trades)} trades from QuiverQuant'))
                return qqq_trades[:limit]
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'QuiverQuant failed: {str(e)}'))

        # Fallback: Use placeholder data
        self.stdout.write(self.style.WARNING('All sources failed, using placeholder data for demo'))
        return self._generate_placeholder_data(limit)

    def _fetch_quiver_quant(self, limit):
        """Fetch trades from QuiverQuant API using env vars.
        Env:
        - QUIVER_API_KEY (required)
        - QUIVER_API_URL (optional override; defaults to live congresstrading)
        Notes: Quiver commonly uses 'Authorization: Token <key>'
        """
        api_key = os.environ.get('QUIVER_API_KEY')
        if not api_key:
            self.stdout.write(self.style.WARNING('QUIVER_API_KEY not set; skipping QuiverQuant.'))
            return []

        base_url = os.environ.get('QUIVER_API_URL', 'https://api.quiverquant.com/beta/live/congresstrading')

        headers_base = {
            'Accept': 'application/json',
            'User-Agent': 'EGStudios/1.0 (+https://egmedia.org)'
        }
        header_variants = [
            {**headers_base, 'Authorization': f'Token {api_key}'},
            {**headers_base, 'Authorization': f'Bearer {api_key}'},
            {**headers_base, 'X-API-KEY': api_key},
        ]

        last_error = None
        for headers in header_variants:
            try:
                resp = requests.get(base_url, headers=headers, timeout=30)
                if resp.status_code != 200:
                    last_error = f'status {resp.status_code}'
                    continue
                data = resp.json()
                if isinstance(data, dict) and 'data' in data:
                    data = data['data']
                if not isinstance(data, list):
                    for key in ('results', 'items', 'trades'):
                        if isinstance(data, dict) and key in data:
                            data = data[key]
                            break
                if not isinstance(data, list):
                    last_error = 'unexpected JSON shape'
                    continue
                return self._parse_quiver_quant_format(data, limit)
            except Exception as e:
                last_error = str(e)
                continue

        if last_error:
            self.stdout.write(self.style.WARNING(f'QuiverQuant request failed: {last_error}'))
        return []

    def _parse_quiver_quant_format(self, data, limit):
        """Parse QuiverQuant-like JSON into our Trade dicts."""
        trades = []
        for item in data[:limit]:
            try:
                ticker = (item.get('Ticker') or item.get('ticker') or '').strip().upper()
                if not ticker:
                    continue

                action_raw = (item.get('Transaction') or item.get('transaction') or '').lower()
                if 'purchase' in action_raw or 'buy' in action_raw:
                    action = 'BUY'
                elif 'sale' in action_raw or 'sell' in action_raw or 'sold' in action_raw:
                    action = 'SELL'
                else:
                    continue

                date_candidates = [item.get('TransactionDate'), item.get('transaction_date'), item.get('Date')]
                trade_date = None
                for ds in date_candidates:
                    if not ds:
                        continue
                    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%dT%H:%M:%SZ'):
                        try:
                            trade_date = datetime.strptime(ds.split('T')[0], fmt).date()
                            break
                        except Exception:
                            continue
                    if trade_date:
                        break
                if not trade_date:
                    continue

                amount = None
                amt = item.get('Range') or item.get('Amount') or item.get('amount')
                if isinstance(amt, str):
                    clean = amt.replace('$', '').replace(',', '').strip()
                    if '-' in clean:
                        parts = clean.split('-')
                        try:
                            low = float(re.sub(r'[^\d.]', '', parts[0]))
                            high = float(re.sub(r'[^\d.]', '', parts[1]))
                            amount = (low + high) / 2
                        except Exception:
                            amount = None
                    else:
                        try:
                            amount = float(re.sub(r'[^\d.]', '', clean))
                        except Exception:
                            amount = None
                elif isinstance(amt, (int, float)):
                    amount = float(amt)

                politician_name = (
                    item.get('Representative') or item.get('Senator') or item.get('Name') or item.get('politician') or 'Unknown'
                )

                trades.append({
                    'politician_name': politician_name,
                    'ticker': ticker,
                    'action': action,
                    'trade_date': trade_date,
                    'amount': amount,
                    'disclosure_date': None,
                    'asset_description': (item.get('AssetDescription') or item.get('Asset') or '')[:200],
                })
            except Exception:
                continue
        return trades
    
    def _validate_trade(self, trade: dict) -> bool:
        """Validate trade data before saving."""
        # Must have essential fields
        if not trade.get('politician_name') or not trade.get('ticker') or not trade.get('trade_date'):
            return False
        
        # Clean politician name
        trade['politician_name'] = self._clean_politician_name(trade['politician_name'])
        
        # Validate ticker
        ticker = trade.get('ticker', '').strip().upper()
        if not self._validate_ticker(ticker):
            return False
        trade['ticker'] = ticker
        
        # Validate action
        if trade.get('action') not in ['BUY', 'SELL']:
            return False
        
        return True

    # Minimal local copies of the name/ticker validators (removed scraper deps)
    def _clean_politician_name(self, name: str) -> str:
        name = name.strip()
        name = re.sub(r'\b(Rep\.|Sen\.|Representative|Senator|Hon\.)\s*', '', name, flags=re.IGNORECASE)
        return ' '.join(name.split())

    def _validate_ticker(self, ticker: str) -> bool:
        if not ticker:
            return False
        ticker = ticker.strip().upper()
        return bool(re.match(r'^[A-Z]{1,5}$', ticker))
    
    
    def _generate_placeholder_data(self, limit):
        
        # PLACEHOLDER: Return sample data for testing
        # Remove this once you integrate a real API
        from datetime import date, timedelta
        import random
        
        politicians = [
            'Nancy Pelosi', 'Paul Pelosi', 'Dan Crenshaw', 'Josh Gottheimer',
            'Marjorie Taylor Greene', 'Tommy Tuberville', 'Pat Fallon'
        ]
        tickers = ['NVDA', 'TSLA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'AMD']
        
        trades = []
        for i in range(min(limit, 20)):  # Generate up to 20 sample trades
            trades.append({
                'politician_name': random.choice(politicians),
                'ticker': random.choice(tickers),
                'action': random.choice(['BUY', 'SELL']),
                'trade_date': date.today() - timedelta(days=random.randint(1, 90)),
                'amount': random.randint(10000, 1000000),
                'disclosure_date': date.today() - timedelta(days=random.randint(0, 30)),
                'asset_description': f'Stock trade transaction',
            })
        
        return trades
