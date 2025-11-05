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
        Scrape House Financial Disclosures (official government site).
        Target: https://disclosurespreview.house.gov/
        """
        try:
            self._init_driver()
            
            url = "https://disclosurespreview.house.gov/ld/ldsearch"
            print(f"Loading {url}...")
            
            self.driver.get(url)
            self._human_delay(3, 5)  # Wait for page load
            
            # Wait for page to fully load
            wait = WebDriverWait(self.driver, 15)
            self._human_delay(5, 8)  # Extra wait for JavaScript to execute and load content
            
            # Try to wait for any interactive elements
            try:
                wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
                print("Page readyState is complete")
            except:
                pass
            
            # Execute JavaScript to check if page has loaded dynamic content
            js_check = self.driver.execute_script("""
                return {
                    'links': document.getElementsByTagName('a').length,
                    'tables': document.getElementsByTagName('table').length,
                    'forms': document.getElementsByTagName('form').length,
                    'buttons': document.getElementsByTagName('button').length,
                    'body_text_length': document.body.innerText.length
                };
            """)
            print(f"JavaScript elements check: {js_check}")
            
            # Debug: Print page title and source snippet
            print(f"Page title: {self.driver.title}")
            print(f"Page URL: {self.driver.current_url}")
            print(f"Body text preview: {self.driver.find_element(By.TAG_NAME, 'body').text[:200]}")
            
            # Save screenshot for debugging
            try:
                self.driver.save_screenshot('/tmp/house_disclosure_debug.png')
                print("Screenshot saved to /tmp/house_disclosure_debug.png")
            except:
                pass
            
            # Try to find PTR (Periodic Transaction Report) links
            try:
                # Look for any links first to see what's available
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                print(f"Found {len(all_links)} total links on page")
                
                # Print first 10 link texts for debugging
                for i, link in enumerate(all_links[:10]):
                    print(f"Link {i}: {link.text[:50]} -> {link.get_attribute('href')[:80] if link.get_attribute('href') else 'no href'}")
                
                # Look for recent PTR filings
                ptr_links = self.driver.find_elements(
                    By.XPATH, "//a[contains(@href, 'ptr') or contains(@href, 'PTR') or contains(text(), 'PTR') or contains(text(), 'Transaction')]"
                )[:limit]
                
                print(f"Found {len(ptr_links)} PTR-related links")
                
                trades = []
                
                for idx, link in enumerate(ptr_links):
                    try:
                        # Click to view the PTR filing
                        filing_url = link.get_attribute('href')
                        if filing_url:
                            self.driver.get(filing_url)
                            self._human_delay(2, 4)
                            
                            # Parse the filing page for transaction details
                            # Look for transaction tables
                            try:
                                rows = self.driver.find_elements(By.CSS_SELECTOR, "table tr")
                                
                                for row in rows:
                                    cells = row.find_elements(By.TAG_NAME, "td")
                                    if len(cells) < 4:
                                        continue
                                    
                                    # Extract transaction data (adjust indices based on actual table structure)
                                    asset_text = cells[0].text.strip()
                                    transaction_type = cells[1].text.strip().lower() if len(cells) > 1 else ''
                                    trade_date_str = cells[2].text.strip() if len(cells) > 2 else ''
                                    amount_str = cells[3].text.strip() if len(cells) > 3 else ''
                                    
                                    # Extract ticker from asset description
                                    ticker = self._extract_ticker_from_text(asset_text)
                                    if not ticker:
                                        continue
                                    
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
                                    
                                    trades.append({
                                        'politician_name': 'House Member',  # Extract from filing header
                                        'ticker': ticker,
                                        'action': action,
                                        'trade_date': trade_date,
                                        'amount': amount,
                                        'disclosure_date': None,
                                        'asset_description': asset_text[:200]
                                    })
                            except:
                                pass
                            
                            # Go back to listing
                            self.driver.back()
                            self._human_delay(1, 2)
                        
                        if idx % 5 == 0 and idx > 0:
                            self._human_delay(2, 4)
                    
                    except Exception as e:
                        print(f"Error parsing filing: {e}")
                        continue
                
                return trades[:limit]
            
            except Exception as e:
                print(f"Could not find PTR filings: {e}")
                return []
        
        except Exception as e:
            print(f"Error scraping House Stock Watcher: {e}")
            return []
        
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def fetch_senate_stock_watcher(self, limit=50):
        """
        Scrape Senate Financial Disclosures (official government site).
        Target: https://efdsearch.senate.gov/search/
        """
        try:
            self._init_driver()
            
            url = "https://efdsearch.senate.gov/search/home/"
            print(f"Loading {url}...")
            
            self.driver.get(url)
            self._human_delay(3, 5)
            
            # Wait for page to load
            wait = WebDriverWait(self.driver, 15)
            self._human_delay(5, 8)  # Extra wait for JavaScript
            
            # Wait for page readyState
            try:
                wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
                print("Senate page readyState is complete")
            except:
                pass
            
            # Check what elements loaded
            js_check = self.driver.execute_script("""
                return {
                    'links': document.getElementsByTagName('a').length,
                    'tables': document.getElementsByTagName('table').length,
                    'forms': document.getElementsByTagName('form').length,
                    'buttons': document.getElementsByTagName('button').length,
                    'inputs': document.getElementsByTagName('input').length,
                    'body_text_length': document.body.innerText.length
                };
            """)
            print(f"Senate JavaScript elements check: {js_check}")
            
            # Debug output
            print(f"Page title: {self.driver.title}")
            print(f"Page URL: {self.driver.current_url}")
            print(f"Body text preview (pre-accept): {self.driver.find_element(By.TAG_NAME, 'body').text[:200]}")
            
            # Save screenshot
            try:
                self.driver.save_screenshot('/tmp/senate_disclosure_debug.png')
                print("Screenshot saved to /tmp/senate_disclosure_debug.png")
            except:
                pass
            
            trades = []
            
            try:
                # Attempt to accept the disclosure terms to unlock search
                try:
                    # Check the agreement checkbox
                    checkbox = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='checkbox']")))
                    self.driver.execute_script("arguments[0].click();", checkbox)
                    self._human_delay(0.5, 1.0)
                    print("Checked the Senate disclosure agreement checkbox")
                except Exception as e:
                    print(f"No checkbox interacted: {e}")
                
                # Click the Get Access button (or any button present)
                try:
                    # Prefer a button containing the text 'Get Access'
                    buttons = self.driver.find_elements(By.XPATH, "//button[contains(., 'Get Access') or contains(., 'Access') or contains(., 'Search')]")
                    if buttons:
                        self.driver.execute_script("arguments[0].click();", buttons[0])
                        print("Clicked Get Access/Search button")
                    else:
                        # Try any enabled button
                        any_buttons = self.driver.find_elements(By.TAG_NAME, 'button')
                        if any_buttons:
                            self.driver.execute_script("arguments[0].click();", any_buttons[0])
                            print("Clicked a generic button on Senate page")
                    self._human_delay(2, 3)
                except Exception as e:
                    print(f"No button clicked: {e}")
                
                # After acceptance, re-check the DOM and links
                js_check_after = self.driver.execute_script("""
                    return {
                        'links': document.getElementsByTagName('a').length,
                        'tables': document.getElementsByTagName('table').length,
                        'forms': document.getElementsByTagName('form').length,
                        'buttons': document.getElementsByTagName('button').length,
                        'inputs': document.getElementsByTagName('input').length,
                        'body_text_length': document.body.innerText.length
                    };
                """)
                print(f"Senate elements after accept: {js_check_after}")
                print(f"Body text preview (post-accept): {self.driver.find_element(By.TAG_NAME, 'body').text[:200]}")
                
                # Look for all links to understand page structure
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                print(f"Found {len(all_links)} total links on Senate page (post-accept)")
                for i, link in enumerate(all_links[:15]):
                    href = link.get_attribute('href')
                    print(f"Link {i}: {link.text[:60]} -> {href[:100] if href else 'no href'}")
                
                # Try to navigate to any search page discovered
                try:
                    search_links = [l for l in all_links if (l.get_attribute('href') or '').find('/search/') != -1]
                    if search_links:
                        self.driver.execute_script("arguments[0].click();", search_links[0])
                        self._human_delay(2, 3)
                        print("Navigated to a search-related link")
                except Exception as e:
                    print(f"Could not navigate to search link: {e}")
                
                # Look for any report-related links
                filing_links = self.driver.find_elements(
                    By.XPATH, "//a[contains(@href, 'report') or contains(@href, 'filing') or contains(text(), 'Report') or contains(text(), 'Disclosure')]"
                )[:limit]
                print(f"Found {len(filing_links)} report-related links")
                
                for idx, link in enumerate(filing_links):
                    try:
                        filing_url = link.get_attribute('href')
                        if filing_url:
                            self.driver.get(filing_url)
                            self._human_delay(2, 4)
                            
                            # Parse filing for transactions
                            # (Senate uses PDF format - would need PDF parsing in production)
                            # For now, look for any HTML transaction tables
                            try:
                                rows = self.driver.find_elements(By.CSS_SELECTOR, "table tr")
                                
                                for row in rows:
                                    cells = row.find_elements(By.TAG_NAME, "td")
                                    if len(cells) < 4:
                                        continue
                                    
                                    asset_text = cells[0].text.strip()
                                    transaction_type = cells[1].text.strip().lower() if len(cells) > 1 else ''
                                    trade_date_str = cells[2].text.strip() if len(cells) > 2 else ''
                                    amount_str = cells[3].text.strip() if len(cells) > 3 else ''
                                    
                                    ticker = self._extract_ticker_from_text(asset_text)
                                    if not ticker:
                                        continue
                                    
                                    if 'purchase' in transaction_type or 'buy' in transaction_type:
                                        action = 'BUY'
                                    elif 'sale' in transaction_type or 'sell' in transaction_type:
                                        action = 'SELL'
                                    else:
                                        continue
                                    
                                    trade_date = self._parse_date(trade_date_str)
                                    if not trade_date:
                                        continue
                                    
                                    amount = self._parse_amount(amount_str)
                                    
                                    trades.append({
                                        'politician_name': 'Senate Member',
                                        'ticker': ticker,
                                        'action': action,
                                        'trade_date': trade_date,
                                        'amount': amount,
                                        'disclosure_date': None,
                                        'asset_description': asset_text[:200]
                                    })
                            except:
                                pass
                            
                            self.driver.back()
                            self._human_delay(1, 2)
                        
                        if idx % 5 == 0 and idx > 0:
                            self._human_delay(2, 4)
                    
                    except Exception as e:
                        print(f"Error parsing Senate filing: {e}")
                        continue
                
                return trades[:limit]
            
            except Exception as e:
                print(f"Could not access Senate filings: {e}")
                return []
        
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
    
    def _extract_ticker_from_text(self, text):
        """Extract ticker symbol from asset description text."""
        if not text:
            return None
        
        # Look for ticker in parentheses: "Apple Inc. (AAPL)"
        match = re.search(r'\(([A-Z]{1,5})\)', text)
        if match:
            return match.group(1)
        
        # Look for standalone ticker at start: "AAPL - Apple Inc."
        match = re.search(r'^([A-Z]{1,5})\s*[-:]', text)
        if match:
            return match.group(1)
        
        # Look for any 1-5 uppercase letters surrounded by word boundaries
        match = re.search(r'\b([A-Z]{1,5})\b', text)
        if match:
            ticker = match.group(1)
            # Exclude common words that aren't tickers
            excluded = {'INC', 'LLC', 'CORP', 'LTD', 'CO', 'LP', 'USA', 'US', 'THE', 'AND', 'OR'}
            if ticker not in excluded:
                return ticker
        
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
