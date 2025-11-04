from django.core.management.base import BaseCommand
from trading.models import Trade
from datetime import datetime
import requests
import os
from bs4 import BeautifulSoup
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
        Fetch politician trades using multiple strategies.
        1. Try GitHub-hosted open data
        2. Try scraping Capitol Trades website
        3. Fallback to placeholder
        """
        
        # Strategy 1: Try raw GitHub data repositories
        try:
            self.stdout.write('Trying GitHub open data sources...')
            
            # Try the house-stock-watcher GitHub raw data
            urls = [
                'https://raw.githubusercontent.com/house-stock-watcher/house-stock-watcher/main/data/all_transactions.json',
                'https://raw.githubusercontent.com/house-stock-watcher/house-stock-watcher/master/data/all_transactions.json',
            ]
            
            for url in urls:
                try:
                    response = requests.get(url, timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        trades = self._parse_house_stock_watcher(data, limit)
                        if trades:
                            self.stdout.write(self.style.SUCCESS(f'✓ Fetched {len(trades)} trades from GitHub'))
                            return trades
                except:
                    continue
                    
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'GitHub sources failed: {str(e)}'))
        
        # Strategy 2: Scrape Capitol Trades website directly
        try:
            self.stdout.write('Trying Capitol Trades web scraping...')
            trades = self._scrape_capitol_trades(limit)
            if trades:
                self.stdout.write(self.style.SUCCESS(f'✓ Scraped {len(trades)} trades from Capitol Trades'))
                return trades
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Capitol Trades scraping failed: {str(e)}'))
        
        self.stdout.write(self.style.WARNING('All sources failed, using placeholder data'))
        return self._generate_placeholder_data(limit)
    
    def _parse_house_stock_watcher(self, data, limit):
        """Parse House Stock Watcher JSON format"""
        trades = []
        
        for item in data[:limit]:
            tx_type = item.get('type', '').lower()
            if 'purchase' in tx_type:
                action = 'BUY'
            elif 'sale' in tx_type:
                action = 'SELL'
            else:
                continue
            
            ticker = item.get('ticker', '').strip().upper()
            if not ticker or ticker == '--':
                continue
            
            trade_date = None
            if item.get('transaction_date'):
                try:
                    trade_date = datetime.strptime(item['transaction_date'], '%Y-%m-%d').date()
                except:
                    try:
                        trade_date = datetime.strptime(item['transaction_date'], '%m/%d/%Y').date()
                    except:
                        continue
            
            disclosure_date = None
            if item.get('disclosure_date'):
                try:
                    disclosure_date = datetime.strptime(item['disclosure_date'], '%Y-%m-%d').date()
                except:
                    try:
                        disclosure_date = datetime.strptime(item['disclosure_date'], '%m/%d/%Y').date()
                    except:
                        pass
            
            amount = None
            amt_str = item.get('amount', '')
            if amt_str:
                try:
                    amt_clean = amt_str.replace('$', '').replace(',', '').strip()
                    if '-' in amt_clean:
                        parts = amt_clean.split('-')
                        low = float(parts[0].strip())
                        high = float(parts[1].strip())
                        amount = (low + high) / 2
                    else:
                        amount = float(amt_clean)
                except:
                    pass
            
            trades.append({
                'politician_name': item.get('representative', 'Unknown'),
                'ticker': ticker,
                'action': action,
                'trade_date': trade_date,
                'amount': amount,
                'disclosure_date': disclosure_date,
                'asset_description': item.get('asset_description', ''),
            })
        
        return trades
    
    def _scrape_capitol_trades(self, limit):
        """Scrape Capitol Trades website as fallback"""
        trades = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(
                'https://www.capitoltrades.com/trades',
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Look for trade rows in the table
            # Note: This is fragile and will break if they change their HTML structure
            trade_rows = soup.select('tr.trade-row, tbody tr')[:limit]
            
            for row in trade_rows:
                try:
                    # Extract data from table cells
                    cells = row.find_all('td')
                    if len(cells) < 5:
                        continue
                    
                    # This is an example - actual selectors need to match their current HTML
                    politician_name = row.find(class_='politician-name')
                    ticker = row.find(class_='ticker')
                    tx_type = row.find(class_='transaction-type')
                    
                    if not all([politician_name, ticker, tx_type]):
                        continue
                    
                    # Parse and add to trades
                    # (Implementation depends on actual HTML structure)
                    
                except Exception:
                    continue
            
        except Exception:
            pass
        
        return trades
    
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
