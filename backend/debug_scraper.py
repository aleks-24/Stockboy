"""
Debug script to test scraper and print sample HTML structure.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.scraper import OpenInsiderScraper
from bs4 import BeautifulSoup

def debug_scraper():
    """Debug the scraper by printing HTML structure."""
    print("=" * 60)
    print("Scraper Debug - Analyzing HTML Structure")
    print("=" * 60)
    
    scraper = OpenInsiderScraper(delay=0.5)
    
    # Fetch one page
    response = scraper.session.get(scraper.BASE_URL, params={'cnt': '10', 'page': '1'}, timeout=30)
    
    soup = BeautifulSoup(response.text, 'lxml')
    table = soup.find('table', class_='tinytable')
    
    if not table:
        print("❌ No table found!")
        return
    
    print("✓ Table found")
    
    rows = table.find_all('tr')
    print(f"✓ Found {len(rows)} rows")
    
    # Print header row
    if rows:
        header = rows[0]
        headers = [th.get_text(strip=True) for th in header.find_all('th')]
        print(f"\nTable headers ({len(headers)} columns):")
        for i, h in enumerate(headers):
            print(f"  [{i}] {h}")
    
    # Print first data row details
    if len(rows) > 1:
        print("\nFirst data row cell contents:")
        cells = rows[1].find_all('td')
        for i, cell in enumerate(cells):
            text = cell.get_text(strip=True)
            print(f"  [{i}] '{text}' (len={len(cells)})")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    debug_scraper()
