from django.core.management.base import BaseCommand
from trading.models import Trade
from datetime import datetime
import requests
import os


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
        
        # Using Capitol Trades public API (no auth required for basic data)
        # Alternative: https://api.quiverquant.com/beta/live/congresstrading (requires key)
        # For now, using a mock/fallback approach - you can plug in real API
        
        try:
            # Option 1: Capitol Trades (example endpoint - may require API key for full access)
            # url = "https://bff.capitoltrades.com/trades"
            
            # Option 2: Use publicly available JSON endpoints or scrape
            # For demo purposes, using a placeholder that you'll replace with actual API
            
            # TEMPORARY: Mock data generator (replace with real API call)
            self.stdout.write(self.style.WARNING('Using placeholder data. Replace with real API in production.'))
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
        Fetch politician trades from free public sources.
        Uses Capitol Trades unofficial API (free, no key required).
        """
        
        try:
            # Capitol Trades has a publicly accessible endpoint
            self.stdout.write('Fetching from Capitol Trades...')
            
            # Their public feed endpoint (may change - monitor for updates)
            response = requests.get(
                'https://bff.capitoltrades.com/trades',
                params={'pageSize': limit, 'page': 1},
                headers={'User-Agent': 'Mozilla/5.0'},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            trades = []
            trade_list = data.get('data', []) if isinstance(data, dict) else data
            
            for item in trade_list[:limit]:
                # Parse politician info
                politician = item.get('politician', {})
                politician_name = f"{politician.get('firstName', '')} {politician.get('lastName', '')}".strip()
                if not politician_name:
                    politician_name = item.get('politicianName', 'Unknown')
                
                # Parse asset/ticker
                asset = item.get('asset', {})
                ticker = asset.get('ticker', '') or asset.get('assetTicker', '') or ''
                ticker = ticker.strip().upper()
                
                # Parse transaction type
                tx_type = item.get('txType', '').lower() or item.get('transactionType', '').lower()
                if 'purchase' in tx_type or 'buy' in tx_type:
                    action = 'BUY'
                elif 'sale' in tx_type or 'sell' in tx_type:
                    action = 'SELL'
                else:
                    continue  # Skip unclear transactions
                
                # Parse dates
                trade_date = None
                tx_date = item.get('txDate') or item.get('transactionDate')
                if tx_date:
                    try:
                        trade_date = datetime.strptime(tx_date[:10], '%Y-%m-%d').date()
                    except:
                        pass
                
                disclosure_date = None
                pub_date = item.get('pubDate') or item.get('disclosureDate')
                if pub_date:
                    try:
                        disclosure_date = datetime.strptime(pub_date[:10], '%Y-%m-%d').date()
                    except:
                        pass
                
                # Parse amount
                amount = None
                amt = item.get('size') or item.get('amount')
                if amt:
                    try:
                        # Handle ranges like "$15,001 - $50,000"
                        amt_str = str(amt).replace('$', '').replace(',', '')
                        if '-' in amt_str:
                            # Take the midpoint of range
                            parts = amt_str.split('-')
                            low = float(parts[0].strip())
                            high = float(parts[1].strip())
                            amount = (low + high) / 2
                        else:
                            amount = float(amt_str)
                    except:
                        pass
                
                if not ticker or not trade_date:
                    continue  # Skip incomplete data
                
                trades.append({
                    'politician_name': politician_name,
                    'ticker': ticker,
                    'action': action,
                    'trade_date': trade_date,
                    'amount': amount,
                    'disclosure_date': disclosure_date,
                    'asset_description': asset.get('assetDescription', '') or item.get('assetDescription', ''),
                })
            
            self.stdout.write(self.style.SUCCESS(f'✓ Fetched {len(trades)} trades from Capitol Trades'))
            return trades
            
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Capitol Trades request failed: {str(e)}'))
            self.stdout.write(self.style.WARNING('Falling back to placeholder data'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error parsing Capitol Trades data: {str(e)}'))
            self.stdout.write(self.style.WARNING('Falling back to placeholder data'))
        
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
