from django.core.management.base import BaseCommand
from trading.models import Trade
from trading.scrapers import HouseScraper, SenateScraper, clean_politician_name, validate_ticker
from trading.selenium_scraper import SeleniumStockScraper
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
        
        # Primary source: Unusual Whales API (requires API key). We intentionally
        # avoid scraping official .gov sites unless explicitly enabled via env.
        
        try:
            # Option 1: Capitol Trades (example endpoint - may require API key for full access)
            # url = "https://bff.capitoltrades.com/trades"
            
            # Option 2: Use publicly available JSON endpoints or scrape
            # For demo purposes, using a placeholder that you'll replace with actual API
            
            # Fetch from configured sources (Unusual Whales -> backups -> placeholder)
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
        Fetch politician trades prioritizing licensed/hosted APIs and avoiding
        scraping of official government sites unless explicitly enabled.
        Order:
        1) Unusual Whales API (requires UW_API_KEY)
        2) JSON backups (community mirrors)
        3) Optional scraping (disabled by default via GOV_SCRAPING_ENABLED)
        4) Placeholder demo data
        """

        all_trades = []

        # Strategy 1: QuiverQuant API (popular and widely used)
        try:
            self.stdout.write('Trying QuiverQuant API...')
            qqq_trades = self._fetch_quiver_quant(limit)
            if qqq_trades:
                qqq_trades = [t for t in qqq_trades if self._validate_trade(t)]
                all_trades.extend(qqq_trades)
                self.stdout.write(self.style.SUCCESS(f'✓ Fetched {len(qqq_trades)} trades from QuiverQuant'))
                return all_trades[:limit]
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'QuiverQuant failed: {str(e)}'))

        # Strategy 2: Unusual Whales API
        try:
            self.stdout.write('Trying Unusual Whales API...')
            uw_trades = self._fetch_unusual_whales(limit)
            if uw_trades:
                uw_trades = [t for t in uw_trades if self._validate_trade(t)]
                all_trades.extend(uw_trades)
                self.stdout.write(self.style.SUCCESS(f'✓ Fetched {len(uw_trades)} trades from Unusual Whales'))
                return all_trades[:limit]
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Unusual Whales failed: {str(e)}'))

        # Strategy 3: JSON API endpoints (community mirrors)
        try:
            self.stdout.write('Trying JSON backup endpoints...')
            json_trades = self._try_json_apis(limit)
            if json_trades:
                all_trades.extend(json_trades)
                self.stdout.write(self.style.SUCCESS(f'✓ Fetched {len(json_trades)} trades from JSON backups'))
                return all_trades[:limit]
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'JSON backups failed: {str(e)}'))

        # Strategy 4 (optional): Scraping paths, gated by env flag
        if os.environ.get('GOV_SCRAPING_ENABLED', 'false').lower() in ('1', 'true', 'yes'):            
            # Selenium scrapers
            try:
                self.stdout.write('Fetching from House site (Selenium)...')
                scraper = SeleniumStockScraper(headless=True)
                house_trades = scraper.fetch_house_stock_watcher(limit=limit // 2)
                if house_trades:
                    house_trades = [t for t in house_trades if self._validate_trade(t)]
                    all_trades.extend(house_trades)
                    self.stdout.write(self.style.SUCCESS(f'✓ Fetched {len(house_trades)} trades from House (Selenium)'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'House Selenium failed: {str(e)}'))

            try:
                self.stdout.write('Fetching from Senate site (Selenium)...')
                scraper = SeleniumStockScraper(headless=True)
                senate_trades = scraper.fetch_senate_stock_watcher(limit=limit // 2)
                if senate_trades:
                    senate_trades = [t for t in senate_trades if self._validate_trade(t)]
                    all_trades.extend(senate_trades)
                    self.stdout.write(self.style.SUCCESS(f'✓ Fetched {len(senate_trades)} trades from Senate (Selenium)'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Senate Selenium failed: {str(e)}'))

            # Official scrapers
            try:
                self.stdout.write('Trying official House disclosures (requests)...')
                house_scraper = HouseScraper()
                house_trades = house_scraper.fetch_recent_transactions(max_records=limit // 2)
                if house_trades:
                    house_trades = [t for t in house_trades if self._validate_trade(t)]
                    all_trades.extend(house_trades)
                    self.stdout.write(self.style.SUCCESS(f'✓ Fetched {len(house_trades)} from House disclosures'))
                    return all_trades[:limit]
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'House disclosures failed: {str(e)}'))
        else:
            self.stdout.write(self.style.WARNING('Government site scraping disabled (set GOV_SCRAPING_ENABLED=true to enable).'))

        # Strategy 5: Try GitHub backup sources
        try:
            self.stdout.write('Trying GitHub backup sources...')
            github_trades = self._fetch_github_data(limit)
            if github_trades:
                all_trades.extend(github_trades)
                self.stdout.write(self.style.SUCCESS(f'✓ Fetched {len(github_trades)} trades from GitHub'))
                return all_trades[:limit]
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'GitHub sources failed: {str(e)}'))

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

    def _fetch_unusual_whales(self, limit):
        """Fetch trades from Unusual Whales API using env vars.
        Env:
        - UW_API_KEY or UNUSUAL_WHALES_API_KEY
        - UW_API_URL (optional override)
        """
        api_key = os.environ.get('UW_API_KEY') or os.environ.get('UNUSUAL_WHALES_API_KEY')
        if not api_key:
            self.stdout.write(self.style.WARNING('UW_API_KEY not set; skipping Unusual Whales.'))
            return []

        base_url = os.environ.get('UW_API_URL', 'https://api.unusualwhales.com/api/politics/trades')

        # Try common auth header patterns
        header_variants = [
            {'Authorization': f'Bearer {api_key}'},
            {'X-API-KEY': api_key},
            {'x-api-key': api_key},
        ]

        params = {'limit': limit}

        last_error = None
        for hv in header_variants:
            headers = {
                'Accept': 'application/json',
                'User-Agent': 'EGStudios/1.0 (+https://egmedia.org)'
            }
            headers.update(hv)
            try:
                resp = requests.get(base_url, headers=headers, params=params, timeout=30)
                if resp.status_code != 200:
                    last_error = f'status {resp.status_code}'
                    continue
                data = resp.json()
                # Some APIs wrap data under a "data" key
                if isinstance(data, dict) and 'data' in data:
                    data = data['data']
                if not isinstance(data, list):
                    # Some endpoints may return {results: [...]} or {items: [...]} formats
                    for key in ('results', 'items', 'trades'):
                        if isinstance(data, dict) and key in data:
                            data = data[key]
                            break
                if not isinstance(data, list):
                    last_error = 'unexpected JSON shape'
                    continue
                return self._parse_unusual_whales_format(data, limit)
            except Exception as e:
                last_error = str(e)
                continue

        if last_error:
            self.stdout.write(self.style.WARNING(f'Unusual Whales request failed: {last_error}'))
        return []

    def _parse_unusual_whales_format(self, data, limit):
        """Parse Unusual Whales-like JSON into our Trade dicts with best-effort mapping."""
        trades = []
        for item in data[:limit]:
            try:
                # Ticker
                ticker = (item.get('ticker') or item.get('symbol') or '').strip().upper()
                if not ticker:
                    continue

                # Action
                tx_raw = (item.get('transaction') or item.get('type') or item.get('action') or '').lower()
                if 'purchase' in tx_raw or 'buy' in tx_raw:
                    action = 'BUY'
                elif 'sale' in tx_raw or 'sell' in tx_raw or 'sold' in tx_raw:
                    action = 'SELL'
                else:
                    # Skip unknown actions
                    continue

                # Dates
                date_candidates = [
                    item.get('transaction_date'), item.get('trade_date'), item.get('date'), item.get('filed_date')
                ]
                trade_date = None
                for ds in date_candidates:
                    if not ds:
                        continue
                    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S'):
                        try:
                            trade_date = datetime.strptime(ds.split('Z')[0], fmt).date()
                            break
                        except Exception:
                            continue
                    if trade_date:
                        break
                if not trade_date:
                    continue

                disclosure_date = None
                disc_candidates = [item.get('disclosure_date'), item.get('filed_date')]
                for ds in disc_candidates:
                    if not ds:
                        continue
                    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S'):
                        try:
                            disclosure_date = datetime.strptime(ds.split('Z')[0], fmt).date()
                            break
                        except Exception:
                            continue
                    if disclosure_date:
                        break

                # Amount
                amount = None
                amt_raw = item.get('amount') or item.get('amount_usd') or item.get('amount_range') or item.get('range')
                if isinstance(amt_raw, (int, float)):
                    amount = float(amt_raw)
                elif isinstance(amt_raw, str):
                    amt_clean = amt_raw.replace('$', '').replace(',', '').strip()
                    if '-' in amt_clean:
                        parts = amt_clean.split('-')
                        try:
                            low = float(re.sub(r'[^\d.]', '', parts[0]))
                            high = float(re.sub(r'[^\d.]', '', parts[1]))
                            amount = (low + high) / 2
                        except Exception:
                            amount = None
                    else:
                        try:
                            amount = float(re.sub(r'[^\d.]', '', amt_clean))
                        except Exception:
                            amount = None

                # Politician name
                politician_name = (
                    item.get('politician') or item.get('member') or item.get('representative') or item.get('senator') or 'Unknown'
                )

                trades.append({
                    'politician_name': politician_name,
                    'ticker': ticker,
                    'action': action,
                    'trade_date': trade_date,
                    'amount': amount,
                    'disclosure_date': disclosure_date,
                    'asset_description': (item.get('asset_description') or item.get('asset') or '')[:200],
                })
            except Exception:
                continue

        return trades
    
    def _try_json_apis(self, limit):
        """Try various JSON API endpoints without Selenium."""
        urls = [
            "https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/aggregate/all_transactions.json",
            "https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json",
        ]
        
        for url in urls:
            try:
                response = requests.get(url, timeout=30, headers={
                    'User-Agent': 'Mozilla/5.0'
                })
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_stock_watcher_format(data, limit, chamber='Mixed')
            except:
                continue
        
        return []
    
    def _parse_stock_watcher_format(self, data, limit, chamber='House'):
        """Parse the stock watcher JSON format (works for both House and Senate)."""
        trades = []
        
        for item in data[:limit]:
            try:
                # Parse transaction type
                tx_type = item.get('transaction_type', item.get('type', '')).lower()
                if 'purchase' in tx_type or 'buy' in tx_type:
                    action = 'BUY'
                elif 'sale' in tx_type or 'sell' in tx_type or 'sold' in tx_type:
                    action = 'SELL'
                else:
                    continue
                
                # Get ticker
                ticker = item.get('ticker', '').strip().upper()
                if not ticker or ticker == '--' or ticker == 'N/A':
                    continue
                
                # Parse trade date
                trade_date = None
                date_str = item.get('transaction_date', item.get('disclosure_date', ''))
                if date_str:
                    try:
                        trade_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except:
                        try:
                            trade_date = datetime.strptime(date_str, '%m/%d/%Y').date()
                        except:
                            continue
                
                if not trade_date:
                    continue
                
                # Parse disclosure date
                disclosure_date = None
                disc_str = item.get('disclosure_date', item.get('filed_date', ''))
                if disc_str and disc_str != date_str:
                    try:
                        disclosure_date = datetime.strptime(disc_str, '%Y-%m-%d').date()
                    except:
                        try:
                            disclosure_date = datetime.strptime(disc_str, '%m/%d/%Y').date()
                        except:
                            pass
                
                # Parse amount
                amount = None
                amt_str = item.get('amount', item.get('size', ''))
                if amt_str:
                    try:
                        amt_clean = str(amt_str).replace('$', '').replace(',', '').strip()
                        if '-' in amt_clean:
                            parts = amt_clean.split('-')
                            low = float(re.sub(r'[^\d.]', '', parts[0]))
                            high = float(re.sub(r'[^\d.]', '', parts[1]))
                            amount = (low + high) / 2
                        else:
                            amount = float(re.sub(r'[^\d.]', '', amt_clean))
                    except:
                        pass
                
                # Get politician name
                politician_name = item.get('representative', item.get('senator', item.get('name', 'Unknown')))
                
                trades.append({
                    'politician_name': politician_name,
                    'ticker': ticker,
                    'action': action,
                    'trade_date': trade_date,
                    'amount': amount,
                    'disclosure_date': disclosure_date,
                    'asset_description': item.get('asset_description', item.get('asset', ''))[:200],
                })
            
            except Exception as e:
                continue
        
        return trades
    
    def _validate_trade(self, trade: dict) -> bool:
        """Validate trade data before saving."""
        # Must have essential fields
        if not trade.get('politician_name') or not trade.get('ticker') or not trade.get('trade_date'):
            return False
        
        # Clean politician name
        trade['politician_name'] = clean_politician_name(trade['politician_name'])
        
        # Validate ticker
        ticker = trade.get('ticker', '').strip().upper()
        if not validate_ticker(ticker):
            return False
        trade['ticker'] = ticker
        
        # Validate action
        if trade.get('action') not in ['BUY', 'SELL']:
            return False
        
        return True
    
    def _fetch_github_data(self, limit):
        """Try GitHub-hosted open data repositories."""
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
                        return trades
            except:
                continue
        
        return []
    
    def _parse_house_stock_watcher(self, data, limit):
        """Parse House Stock Watcher JSON format."""
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
