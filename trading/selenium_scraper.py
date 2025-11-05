"""
Selenium-based scraper for politician stock trades.
Uses headless Chrome to bypass bot detection.
"""

import time
import random
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import os
import shutil


class SeleniumStockScraper:
    """Scraper using headless Chrome to appear more human-like."""
    
    def __init__(self, headless=True):
        """Initialize the Selenium scraper with Chrome options."""
        self.headless = headless
        self.driver = None
    
    def _init_driver(self):
        """Initialize Chrome driver with robust server-safe options."""
        if self.driver:
            return
        
        chrome_options = Options()
        
        # Prefer the new headless, fall back to legacy headless if needed
        if self.headless:
            chrome_options.add_argument('--headless=new')
        
        # Stealth options to avoid bot detection
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--remote-debugging-port=9222')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-software-rasterizer')
        
        # Realistic user agent
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Detect Chrome/Chromium binary
        chrome_binary = os.getenv('CHROME_BINARY')
        if not chrome_binary:
            for candidate in [
                shutil.which('google-chrome'),
                shutil.which('google-chrome-stable'),
                shutil.which('chromium-browser'),
                shutil.which('chromium'),
                '/usr/bin/google-chrome',
                '/usr/bin/google-chrome-stable',
                '/usr/bin/chromium-browser',
                '/usr/bin/chromium',
                '/snap/bin/chromium',
            ]:
                if candidate and os.path.exists(candidate):
                    chrome_binary = candidate
                    break
        if chrome_binary:
            chrome_options.binary_location = chrome_binary

        # Prefer system chromedriver if available, else use webdriver-manager
        chromedriver_path = os.getenv('CHROMEDRIVER_PATH')
        if not chromedriver_path:
            for candidate in [
                shutil.which('chromedriver'),
                '/usr/bin/chromedriver',
                '/snap/bin/chromium.chromedriver',
            ]:
                if candidate and os.path.exists(candidate):
                    chromedriver_path = candidate
                    break

        try:
            if chromedriver_path:
                service = Service(executable_path=chromedriver_path)
            else:
                # Use webdriver-manager to auto-install matching chromedriver
                service = Service(ChromeDriverManager().install())

            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # Remove webdriver flag
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            # Retry once with legacy headless flag in case server Chrome doesn't support new headless
            if self.headless:
                try:
                    # Rebuild chrome_options with legacy headless instead of modifying arguments
                    chrome_options_legacy = Options()
                    chrome_options_legacy.add_argument('--headless')  # Legacy headless
                    chrome_options_legacy.add_argument('--no-sandbox')
                    chrome_options_legacy.add_argument('--disable-dev-shm-usage')
                    chrome_options_legacy.add_argument('--disable-blink-features=AutomationControlled')
                    chrome_options_legacy.add_experimental_option("excludeSwitches", ["enable-automation"])
                    chrome_options_legacy.add_experimental_option('useAutomationExtension', False)
                    chrome_options_legacy.add_argument('--disable-gpu')
                    chrome_options_legacy.add_argument('--remote-debugging-port=9222')
                    chrome_options_legacy.add_argument('--window-size=1920,1080')
                    chrome_options_legacy.add_argument('--disable-software-rasterizer')
                    chrome_options_legacy.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                    
                    if chrome_binary:
                        chrome_options_legacy.binary_location = chrome_binary
                    
                    if chromedriver_path:
                        service = Service(executable_path=chromedriver_path)
                    else:
                        service = Service(ChromeDriverManager().install())
                    
                    self.driver = webdriver.Chrome(service=service, options=chrome_options_legacy)
                    self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                except Exception as e2:
                    raise RuntimeError(f"Failed to launch headless Chrome: {e2}") from e
            else:
                raise
    
    def _human_delay(self, min_seconds=1, max_seconds=3):
        """Add random delay to mimic human behavior."""
        time.sleep(random.uniform(min_seconds, max_seconds))
    
    def fetch_house_stock_watcher(self, limit=50):
        """
        Scrape House Stock Watcher website.
        Target: https://housestockwatcher.com/summary_by_ticker
        """
        try:
            self._init_driver()
            
            url = "https://housestockwatcher.com/summary_by_ticker"
            print(f"Loading {url}...")
            
            self.driver.get(url)
            self._human_delay(2, 4)  # Wait for page load
            
            # Wait for table to load
            wait = WebDriverWait(self.driver, 10)
            table = wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            
            trades = []
            
            # Find all rows in the table
            rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            
            for idx, row in enumerate(rows[:limit]):
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    
                    if len(cells) < 6:
                        continue
                    
                    # Extract data from cells
                    # Typical format: Ticker | Representative | Transaction | Date | Amount | Filed
                    ticker = cells[0].text.strip().upper()
                    politician_name = cells[1].text.strip()
                    transaction_type = cells[2].text.strip().lower()
                    trade_date_str = cells[3].text.strip()
                    amount_str = cells[4].text.strip()
                    filed_date_str = cells[5].text.strip() if len(cells) > 5 else None
                    
                    # Parse transaction type
                    if 'purchase' in transaction_type or 'buy' in transaction_type:
                        action = 'BUY'
                    elif 'sale' in transaction_type or 'sell' in transaction_type:
                        action = 'SELL'
                    else:
                        continue
                    
                    # Parse dates
                    trade_date = self._parse_date(trade_date_str)
                    if not trade_date:
                        continue
                    
                    disclosure_date = self._parse_date(filed_date_str) if filed_date_str else None
                    
                    # Parse amount
                    amount = self._parse_amount(amount_str)
                    
                    # Validate ticker
                    if not self._validate_ticker(ticker):
                        continue
                    
                    trades.append({
                        'politician_name': politician_name,
                        'ticker': ticker,
                        'action': action,
                        'trade_date': trade_date,
                        'amount': amount,
                        'disclosure_date': disclosure_date,
                        'asset_description': f"{ticker} - {transaction_type}"
                    })
                    
                    # Random delay between processing rows
                    if idx % 10 == 0:
                        self._human_delay(0.5, 1.5)
                
                except Exception as e:
                    print(f"Error parsing row: {e}")
                    continue
            
            return trades
        
        except Exception as e:
            print(f"Error scraping House Stock Watcher: {e}")
            return []
        
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def fetch_senate_stock_watcher(self, limit=50):
        """
        Scrape Senate Stock Watcher website.
        Target: https://senatestockwatcher.com/
        """
        try:
            self._init_driver()
            
            url = "https://senatestockwatcher.com/"
            print(f"Loading {url}...")
            
            self.driver.get(url)
            self._human_delay(2, 4)
            
            # Wait for table to load
            wait = WebDriverWait(self.driver, 10)
            table = wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            
            trades = []
            
            # Find all rows
            rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            
            for idx, row in enumerate(rows[:limit]):
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    
                    if len(cells) < 5:
                        continue
                    
                    # Extract data (adjust column indices based on actual site structure)
                    politician_name = cells[0].text.strip()
                    ticker = cells[1].text.strip().upper()
                    transaction_type = cells[2].text.strip().lower()
                    trade_date_str = cells[3].text.strip()
                    amount_str = cells[4].text.strip()
                    
                    # Parse transaction type
                    if 'purchase' in transaction_type or 'buy' in transaction_type:
                        action = 'BUY'
                    elif 'sale' in transaction_type or 'sell' in transaction_type:
                        action = 'SELL'
                    else:
                        continue
                    
                    # Parse date
                    trade_date = self._parse_date(trade_date_str)
                    if not trade_date:
                        continue
                    
                    # Parse amount
                    amount = self._parse_amount(amount_str)
                    
                    # Validate ticker
                    if not self._validate_ticker(ticker):
                        continue
                    
                    trades.append({
                        'politician_name': politician_name,
                        'ticker': ticker,
                        'action': action,
                        'trade_date': trade_date,
                        'amount': amount,
                        'disclosure_date': None,
                        'asset_description': f"{ticker} - {transaction_type}"
                    })
                    
                    if idx % 10 == 0:
                        self._human_delay(0.5, 1.5)
                
                except Exception as e:
                    print(f"Error parsing row: {e}")
                    continue
            
            return trades
        
        except Exception as e:
            print(f"Error scraping Senate Stock Watcher: {e}")
            return []
        
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def _parse_date(self, date_str):
        """Parse date string into date object."""
        if not date_str:
            return None
        
        date_formats = [
            '%m/%d/%Y',
            '%Y-%m-%d',
            '%B %d, %Y',
            '%b %d, %Y',
            '%m-%d-%Y',
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except:
                continue
        
        return None
    
    def _parse_amount(self, amount_str):
        """Parse amount string (handles ranges like '$15,001 - $50,000')."""
        if not amount_str:
            return None
        
        try:
            # Remove $ and commas
            clean = amount_str.replace('$', '').replace(',', '').strip()
            
            # Handle ranges
            if '-' in clean:
                parts = clean.split('-')
                low = float(re.sub(r'[^\d.]', '', parts[0]))
                high = float(re.sub(r'[^\d.]', '', parts[1]))
                return (low + high) / 2
            else:
                return float(re.sub(r'[^\d.]', '', clean))
        except:
            return None
    
    def _validate_ticker(self, ticker):
        """Validate ticker symbol (1-5 uppercase letters)."""
        if not ticker:
            return False
        return bool(re.match(r'^[A-Z]{1,5}$', ticker))
    
    def close(self):
        """Clean up driver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
