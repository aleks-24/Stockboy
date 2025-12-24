"""
Test script for OpenInsider scraper.
Run this standalone to test the scraping functionality.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.scraper import OpenInsiderScraper
from datetime import datetime, timedelta

def test_scraper():
    """Test the OpenInsider scraper."""
    print("=" * 60)
    print("Testing OpenInsider Scraper")
    print("=" * 60)
    
    scraper = OpenInsiderScraper(delay=2.0)  # Be polite with 2s delay
    
    # Test 1: Scrape recent trades (last 30 days, max 1 page)
    print("\n[TEST 1] Scraping recent trades (last 30 days, 1 page)...")
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    
    try:
        trades = scraper.scrape_trades(
            start_date=start_date,
            end_date=end_date,
            min_value=25000,
            max_pages=1
        )
        
        print(f"✓ Successfully scraped {len(trades)} trades")
        
        if trades:
            print("\nSample trade:")
            sample = trades[0]
            for key, value in sample.items():
                print(f"  {key}: {value}")
        else:
            print("⚠ Warning: No trades found. This might be normal if there are no recent trades.")
            
    except Exception as e:
        print(f"✗ Error scraping trades: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Parse date function
    print("\n[TEST 2] Testing date parsing...")
    test_dates = [
        "2024-12-24",
        "2024-12-24 10:30:00",
        "12/24/2024",
        "12/24/2024 10:30:00"
    ]
    
    for date_str in test_dates:
        parsed = scraper._parse_date(date_str)
        if parsed:
            print(f"✓ '{date_str}' -> {parsed}")
        else:
            print(f"✗ Failed to parse: '{date_str}'")
    
    print("\n" + "=" * 60)
    print("Scraper test completed!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    success = test_scraper()
    sys.exit(0 if success else 1)
