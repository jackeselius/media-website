"""
Scraper utilities for fetching politician financial disclosures
from official government sources (House and Senate).
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
import time


class HouseScraper:
    """
    Scrape House of Representatives financial disclosures.
    Source: https://disclosures-clerk.house.gov/FinancialDisclosure
    """
    
    BASE_URL = "https://disclosures-clerk.house.gov"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def fetch_recent_transactions(self, days_back=90, max_records=200) -> List[Dict]:
        """
        Fetch recent periodic transaction reports (PTRs) from House.
        """
        trades = []
        
        try:
            # The House publishes a search page with recent filings
            search_url = f"{self.BASE_URL}/PublicDisclosure/FinancialDisclosure"
            
            # Search for PTR (Periodic Transaction Report) filings
            params = {
                'FilingYear': datetime.now().year,
                'ReportType': 'PTR'  # Periodic Transaction Reports
            }
            
            response = self.session.get(search_url, params=params, timeout=30)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Look for filing links in the results table
            filing_links = soup.select('a[href*="Ptr"]')[:50]  # Get up to 50 recent filings
            
            for link in filing_links:
                try:
                    filing_url = link.get('href')
                    if not filing_url.startswith('http'):
                        filing_url = f"{self.BASE_URL}{filing_url}"
                    
                    # Parse individual filing
                    filing_trades = self._parse_filing(filing_url)
                    trades.extend(filing_trades)
                    
                    if len(trades) >= max_records:
                        break
                    
                    time.sleep(0.5)  # Be polite to the server
                    
                except Exception as e:
                    continue
            
        except Exception as e:
            print(f"House scraper error: {str(e)}")
        
        return trades[:max_records]
    
    def _parse_filing(self, filing_url: str) -> List[Dict]:
        """Parse an individual PTR filing."""
        trades = []
        
        try:
            response = self.session.get(filing_url, timeout=30)
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Extract politician name
            politician_name = self._extract_politician_name(soup)
            
            # Find transaction table(s)
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')[1:]  # Skip header
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) < 5:
                        continue
                    
                    try:
                        trade = self._parse_transaction_row(cells, politician_name)
                        if trade:
                            trades.append(trade)
                    except:
                        continue
        
        except Exception:
            pass
        
        return trades
    
    def _extract_politician_name(self, soup) -> str:
        """Extract politician name from filing page."""
        # Try common patterns
        name_elem = soup.find('span', class_='filing-person')
        if name_elem:
            return name_elem.get_text(strip=True)
        
        # Fallback: look for name in title or headers
        title = soup.find('title')
        if title:
            match = re.search(r'Representative\s+([\w\s\.]+)', title.get_text())
            if match:
                return match.group(1).strip()
        
        return "Unknown"
    
    def _parse_transaction_row(self, cells, politician_name: str) -> Optional[Dict]:
        """Parse a single transaction row from the table."""
        try:
            # Common field order: Date, Asset, Type, Amount, etc.
            # This varies by filing format - adjust as needed
            
            date_text = cells[0].get_text(strip=True) if len(cells) > 0 else ""
            asset_text = cells[1].get_text(strip=True) if len(cells) > 1 else ""
            tx_type = cells[2].get_text(strip=True) if len(cells) > 2 else ""
            amount_text = cells[3].get_text(strip=True) if len(cells) > 3 else ""
            
            # Parse transaction type
            if 'purchase' in tx_type.lower() or 'buy' in tx_type.lower():
                action = 'BUY'
            elif 'sale' in tx_type.lower() or 'sell' in tx_type.lower():
                action = 'SELL'
            else:
                return None
            
            # Extract ticker from asset description
            ticker = self._extract_ticker(asset_text)
            if not ticker:
                return None
            
            # Parse date
            trade_date = self._parse_date(date_text)
            if not trade_date:
                return None
            
            # Parse amount
            amount = self._parse_amount(amount_text)
            
            return {
                'politician_name': politician_name,
                'ticker': ticker,
                'action': action,
                'trade_date': trade_date,
                'amount': amount,
                'disclosure_date': datetime.now().date(),
                'asset_description': asset_text[:200],  # Truncate if too long
            }
        
        except Exception:
            return None
    
    def _extract_ticker(self, asset_text: str) -> Optional[str]:
        """Extract stock ticker from asset description."""
        # Common patterns: "Apple Inc. (AAPL)", "AAPL", "Ticker: AAPL"
        
        # Pattern 1: Text in parentheses
        match = re.search(r'\(([A-Z]{1,5})\)', asset_text)
        if match:
            return match.group(1)
        
        # Pattern 2: Standalone uppercase 1-5 letter word
        match = re.search(r'\b([A-Z]{1,5})\b', asset_text)
        if match:
            ticker = match.group(1)
            # Filter out common words that aren't tickers
            if ticker not in ['LLC', 'INC', 'CORP', 'LP', 'LTD', 'THE', 'AND', 'FOR']:
                return ticker
        
        return None
    
    def _parse_date(self, date_text: str) -> Optional[object]:
        """Parse date from various formats."""
        date_text = date_text.strip()
        
        formats = [
            '%m/%d/%Y',
            '%Y-%m-%d',
            '%m-%d-%Y',
            '%B %d, %Y',
            '%b %d, %Y',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_text, fmt).date()
            except:
                continue
        
        return None
    
    def _parse_amount(self, amount_text: str) -> Optional[float]:
        """Parse amount from text (handles ranges)."""
        try:
            # Remove dollar signs, commas
            amount_clean = amount_text.replace('$', '').replace(',', '').strip()
            
            # Handle ranges: "$15,001 - $50,000"
            if '-' in amount_clean or 'to' in amount_clean.lower():
                parts = re.split(r'[-–to]+', amount_clean)
                if len(parts) == 2:
                    low = float(re.sub(r'[^\d.]', '', parts[0]))
                    high = float(re.sub(r'[^\d.]', '', parts[1]))
                    return (low + high) / 2
            
            # Single value
            amount_num = re.sub(r'[^\d.]', '', amount_clean)
            if amount_num:
                return float(amount_num)
        
        except:
            pass
        
        return None


class SenateScraper:
    """
    Scrape Senate financial disclosures.
    Source: https://efdsearch.senate.gov/
    """
    
    BASE_URL = "https://efdsearch.senate.gov"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_recent_transactions(self, max_records=200) -> List[Dict]:
        """
        Fetch recent periodic transaction reports from Senate.
        """
        trades = []
        
        try:
            # Senate has a search API endpoint
            search_url = f"{self.BASE_URL}/search/report/data/"
            
            # Search for PTR reports (Periodic Transaction Reports)
            payload = {
                'report_types': '[11]',  # PTR report type
                'start': 0,
                'length': 100,
                'order': [{'column': 0, 'dir': 'desc'}]  # Most recent first
            }
            
            response = self.session.post(search_url, json=payload, timeout=30)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            reports = data.get('data', [])
            
            for report in reports[:50]:  # Process up to 50 recent reports
                try:
                    report_trades = self._parse_senate_report(report)
                    trades.extend(report_trades)
                    
                    if len(trades) >= max_records:
                        break
                    
                    time.sleep(0.5)
                    
                except Exception:
                    continue
        
        except Exception as e:
            print(f"Senate scraper error: {str(e)}")
        
        return trades[:max_records]
    
    def _parse_senate_report(self, report: Dict) -> List[Dict]:
        """Parse a Senate PTR report."""
        trades = []
        
        try:
            # Extract basic info
            senator_name = report.get('first_name', '') + ' ' + report.get('last_name', '')
            senator_name = senator_name.strip()
            
            # Get transactions from report details
            # Senate reports often have a detailed view URL
            # This is simplified - actual implementation would fetch and parse the report
            
            # For now, return empty - full implementation would download and parse PDF/XML
            pass
        
        except Exception:
            pass
        
        return trades


def clean_politician_name(name: str) -> str:
    """Normalize politician names."""
    name = name.strip()
    # Remove titles
    name = re.sub(r'\b(Rep\.|Sen\.|Representative|Senator|Hon\.)\s*', '', name, flags=re.IGNORECASE)
    # Remove extra whitespace
    name = ' '.join(name.split())
    return name


def validate_ticker(ticker: str) -> bool:
    """Basic ticker validation."""
    if not ticker:
        return False
    ticker = ticker.strip().upper()
    # Basic rules: 1-5 uppercase letters
    return bool(re.match(r'^[A-Z]{1,5}$', ticker))
