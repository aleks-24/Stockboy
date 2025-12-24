"""
Test script for Stock Data Service.
Run this standalone to test stock data fetching and technical indicators.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.stock_data import StockDataService
from datetime import datetime, timedelta

def test_stock_data():
    """Test the stock data service."""
    print("=" * 60)
    print("Testing Stock Data Service")
    print("=" * 60)
    
    service = StockDataService()
    
    # Test 1: Fetch stock data with indicators
    print("\n[TEST 1] Fetching AAPL data with indicators...")
    try:
        data = service.get_stock_data('AAPL', 
                                      start=datetime.now() - timedelta(days=180),
                                      end=datetime.now())
        
        if 'error' in data:
            print(f"✗ Error: {data['error']}")
            return False
        
        print(f"✓ Successfully fetched data")
        print(f"  Ticker: {data.get('ticker')}")
        print(f"  Data points: {len(data.get('prices', []))}")
        print(f"  Has indicators: {bool(data.get('indicators'))}")
        
        if data.get('indicators'):
            print("\n  Technical Indicators:")
            for key, value in list(data['indicators'].items())[:5]:
                print(f"    {key}: {value}")
                
    except Exception as e:
        print(f"✗ Error fetching stock data: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Get analysis context
    print("\n[TEST 2] Getting analysis context for AAPL...")
    try:
        context = service.get_analysis_context('AAPL', datetime.now())
        
        if 'error' in context:
            print(f"✗ Error: {context['error']}")
        else:
            print(f"✓ Successfully got analysis context")
            print(f"  Has fundamentals: {bool(context.get('fundamentals'))}")
            print(f"  Has technicals: {bool(context.get('technicals'))}")
            print(f"  Has signals: {bool(context.get('signals'))}")
            
    except Exception as e:
        print(f"✗ Error getting analysis context: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("Stock data test completed!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    success = test_stock_data()
    sys.exit(0 if success else 1)
