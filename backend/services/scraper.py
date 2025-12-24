"""
OpenInsider.com scraper service for fetching insider trading data.
"""
import re
import time
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

import requests
from bs4 import BeautifulSoup

from models import db, InsiderTrade

logger = logging.getLogger(__name__)


class OpenInsiderScraper:
    """Scrape insider trading data from OpenInsider.com"""
    
    BASE_URL = "http://openinsider.com/screener"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    def __init__(self, delay: float = 1.0):
        """
        Initialize scraper.
        
        Args:
            delay: Delay between requests in seconds to be polite
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def scrape_trades(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_value: int = 25000,
        trade_type: Optional[str] = None,  # 'P' for purchases, 'S' for sales
        max_pages: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Scrape insider trades within date range.
        
        Args:
            start_date: Start of date range (default: 5 years ago)
            end_date: End of date range (default: today)
            min_value: Minimum trade value in dollars
            trade_type: Filter by trade type ('P' or 'S')
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of trade dictionaries
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=5*365)
        if end_date is None:
            end_date = datetime.now()
        
        trades = []
        page = 1
        
        while page <= max_pages:
            logger.info(f"Scraping page {page}...")
            
            params = {
                'fd': '730',  # Filing date window (days)
                'fdr': f"{start_date.strftime('%m/%d/%Y')}+-+{end_date.strftime('%m/%d/%Y')}",
                'td': '0',  # Trade date window
                'tdr': '',
                'fdlyl': '',
                'fdlyh': '',
                'dtefrom': '',
                'dteto': '',
                'xp': '1',  # Exclude derivatives
                'vl': str(min_value),  # Minimum value
                'vh': '',
                'ocl': '',
                'och': '',
                'session': '',
                'iession': '',
                'cnt': '100',  # Results per page
                'page': str(page)
            }
            
            if trade_type:
                params['xs'] = '1' if trade_type == 'P' else '0'  # Exclude sales for purchases
                params['xb'] = '0' if trade_type == 'P' else '1'  # Exclude buys for sales
            
            try:
                response = self.session.get(self.BASE_URL, params=params, timeout=30)
                response.raise_for_status()
                
                page_trades = self._parse_trades_page(response.text)
                
                if not page_trades:
                    logger.info(f"No more trades found on page {page}")
                    break
                
                trades.extend(page_trades)
                logger.info(f"Found {len(page_trades)} trades on page {page}")
                
                page += 1
                time.sleep(self.delay)
                
            except requests.RequestException as e:
                logger.error(f"Error scraping page {page}: {e}")
                break
        
        return trades
    
    def _parse_trades_page(self, html: str) -> List[Dict[str, Any]]:
        """Parse trades from HTML page."""
        soup = BeautifulSoup(html, 'lxml')
        trades = []
        
        # Find the trades table
        table = soup.find('table', class_='tinytable')
        if not table:
            return trades
        
        rows = table.find_all('tr')[1:]  # Skip header row
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 12:
                continue
            
            try:
                trade = self._parse_trade_row(cells)
                if trade:
                    trades.append(trade)
            except Exception as e:
                logger.warning(f"Error parsing row: {e}")
                continue
        
        return trades
    
    def _parse_trade_row(self, cells) -> Optional[Dict[str, Any]]:
        """Parse a single trade row."""
        try:
            # Extract SEC filing link
            sec_link_elem = cells[1].find('a')
            sec_filing_url = sec_link_elem['href'] if sec_link_elem else None
            
            # Filing date
            filing_date_str = cells[1].get_text(strip=True)
            filing_date = self._parse_date(filing_date_str)
            
            # Trade date
            trade_date_str = cells[2].get_text(strip=True)
            trade_date = self._parse_date(trade_date_str)
            
            # Ticker
            ticker_elem = cells[3].find('a')
            ticker = ticker_elem.get_text(strip=True) if ticker_elem else cells[3].get_text(strip=True)
            
            # Company name
            company_elem = cells[4].find('a')
            company_name = company_elem.get_text(strip=True) if company_elem else cells[4].get_text(strip=True)
            
            # Insider name
            insider_elem = cells[5].find('a')
            insider_name = insider_elem.get_text(strip=True) if insider_elem else cells[5].get_text(strip=True)
            
            # Insider title
            insider_title = cells[6].get_text(strip=True)
            
            # Trade type
            trade_type = cells[7].get_text(strip=True)
            
            # Price
            price_str = cells[8].get_text(strip=True).replace('$', '').replace(',', '')
            price = float(price_str) if price_str else None
            
            # Quantity
            qty_str = cells[9].get_text(strip=True).replace(',', '').replace('+', '').replace('-', '')
            quantity = int(qty_str) if qty_str else None
            
            # Value
            value_str = cells[11].get_text(strip=True).replace('$', '').replace(',', '').replace('+', '').replace('-', '')
            value = float(value_str) if value_str else None
            
            # Delta owned
            delta_str = cells[12].get_text(strip=True).replace('%', '').replace('+', '') if len(cells) > 12 else None
            delta_owned = float(delta_str) if delta_str and delta_str != 'New' else None
            
            return {
                'filing_date': filing_date,
                'trade_date': trade_date,
                'ticker': ticker,
                'company_name': company_name,
                'insider_name': insider_name,
                'insider_title': insider_title,
                'trade_type': trade_type,
                'price': price,
                'quantity': quantity,
                'value': value,
                'delta_owned': delta_owned,
                'sec_filing_url': sec_filing_url
            }
        except Exception as e:
            logger.warning(f"Error parsing trade row: {e}")
            return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None
        
        # Clean up the string
        date_str = date_str.strip()
        
        # Try different formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%m/%d/%Y %H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def save_trades_to_db(self, trades: List[Dict[str, Any]]) -> int:
        """
        Save scraped trades to database.
        
        Args:
            trades: List of trade dictionaries
            
        Returns:
            Number of new trades saved
        """
        saved_count = 0
        
        for trade_data in trades:
            # Check if trade already exists
            existing = InsiderTrade.query.filter_by(
                ticker=trade_data['ticker'],
                filing_date=trade_data['filing_date'],
                insider_name=trade_data['insider_name']
            ).first()
            
            if existing:
                continue
            
            trade = InsiderTrade(
                filing_date=trade_data['filing_date'],
                trade_date=trade_data['trade_date'],
                ticker=trade_data['ticker'],
                company_name=trade_data['company_name'],
                insider_name=trade_data['insider_name'],
                insider_title=trade_data['insider_title'],
                trade_type=trade_data['trade_type'],
                price=trade_data['price'],
                quantity=trade_data['quantity'],
                value=trade_data['value'],
                delta_owned=trade_data['delta_owned'],
                sec_filing_url=trade_data['sec_filing_url']
            )
            
            db.session.add(trade)
            saved_count += 1
        
        db.session.commit()
        logger.info(f"Saved {saved_count} new trades to database")
        
        return saved_count
    
    def get_cluster_buys(self, days: int = 30, min_insiders: int = 2) -> List[Dict[str, Any]]:
        """
        Find cluster buys - multiple insiders buying the same stock.
        
        Args:
            days: Look back period in days
            min_insiders: Minimum number of distinct insiders
            
        Returns:
            List of cluster buy opportunities
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get recent purchases
        purchases = InsiderTrade.query.filter(
            InsiderTrade.trade_type.like('%P%'),
            InsiderTrade.trade_date >= cutoff_date
        ).all()
        
        # Group by ticker
        ticker_insiders = {}
        for trade in purchases:
            if trade.ticker not in ticker_insiders:
                ticker_insiders[trade.ticker] = {
                    'ticker': trade.ticker,
                    'company_name': trade.company_name,
                    'insiders': set(),
                    'total_value': 0,
                    'trades': []
                }
            ticker_insiders[trade.ticker]['insiders'].add(trade.insider_name)
            ticker_insiders[trade.ticker]['total_value'] += trade.value or 0
            ticker_insiders[trade.ticker]['trades'].append(trade.to_dict())
        
        # Filter for clusters
        clusters = [
            {
                **data,
                'insiders': list(data['insiders']),
                'num_insiders': len(data['insiders'])
            }
            for data in ticker_insiders.values()
            if len(data['insiders']) >= min_insiders
        ]
        
        # Sort by number of insiders
        clusters.sort(key=lambda x: x['num_insiders'], reverse=True)
        
        return clusters
