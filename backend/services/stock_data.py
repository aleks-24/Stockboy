"""
Stock data service for fetching price history and technical indicators.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

import pandas as pd
import numpy as np
import yfinance as yf
import ta

logger = logging.getLogger(__name__)


class StockDataService:
    """Service for fetching stock price data and calculating indicators."""
    
    def __init__(self):
        """Initialize the stock data service."""
        self._cache = {}
    
    def get_stock_data(
        self,
        ticker: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_indicators: bool = True
    ) -> Dict[str, Any]:
        """
        Get stock price data with optional technical indicators.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date for data (default: 1 year ago)
            end_date: End date for data (default: today)
            include_indicators: Whether to calculate technical indicators
            
        Returns:
            Dictionary with stock data and indicators
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=365)
        if end_date is None:
            end_date = datetime.now()
        
        try:
            # Fetch data from yfinance
            stock = yf.Ticker(ticker)
            df = stock.history(start=start_date, end=end_date)
            
            if df.empty:
                return {'error': f'No data found for {ticker}'}
            
            # Get stock info
            info = stock.info
            
            result = {
                'ticker': ticker,
                'company_name': info.get('longName', ticker),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'dividend_yield': info.get('dividendYield'),
                'beta': info.get('beta'),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
                'price_history': self._df_to_price_history(df),
            }
            
            if include_indicators:
                indicators = self.calculate_indicators(df)
                result['indicators'] = indicators
                result['latest_indicators'] = self._get_latest_indicators(indicators)
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            return {'error': str(e)}
    
    def _df_to_price_history(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Convert dataframe to list of price records."""
        records = []
        for date, row in df.iterrows():
            records.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': round(row['Open'], 2),
                'high': round(row['High'], 2),
                'low': round(row['Low'], 2),
                'close': round(row['Close'], 2),
                'volume': int(row['Volume'])
            })
        return records
    
    def calculate_indicators(self, df: pd.DataFrame) -> Dict[str, List[Dict[str, Any]]]:
        """
        Calculate technical indicators for stock data.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Dictionary of indicator time series
        """
        indicators = {}
        
        # Ensure we have enough data
        if len(df) < 50:
            return indicators
        
        try:
            # Moving Averages
            df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
            df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
            df['SMA_200'] = ta.trend.sma_indicator(df['Close'], window=200)
            df['EMA_12'] = ta.trend.ema_indicator(df['Close'], window=12)
            df['EMA_26'] = ta.trend.ema_indicator(df['Close'], window=26)
            
            # RSI
            df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
            
            # MACD
            macd = ta.trend.MACD(df['Close'])
            df['MACD'] = macd.macd()
            df['MACD_Signal'] = macd.macd_signal()
            df['MACD_Histogram'] = macd.macd_diff()
            
            # Bollinger Bands
            bollinger = ta.volatility.BollingerBands(df['Close'])
            df['BB_Upper'] = bollinger.bollinger_hband()
            df['BB_Middle'] = bollinger.bollinger_mavg()
            df['BB_Lower'] = bollinger.bollinger_lband()
            
            # ATR (Average True Range) - volatility
            df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'])
            
            # Volume indicators
            df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
            
            # Stochastic Oscillator
            stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'])
            df['Stoch_K'] = stoch.stoch()
            df['Stoch_D'] = stoch.stoch_signal()
            
            # ADX (Trend Strength)
            df['ADX'] = ta.trend.adx(df['High'], df['Low'], df['Close'])
            
            # Calculate daily returns
            df['Daily_Return'] = df['Close'].pct_change()
            df['Volatility_20'] = df['Daily_Return'].rolling(window=20).std() * np.sqrt(252)
            
            # Convert to serializable format
            indicator_cols = [
                'SMA_20', 'SMA_50', 'SMA_200', 'EMA_12', 'EMA_26',
                'RSI', 'MACD', 'MACD_Signal', 'MACD_Histogram',
                'BB_Upper', 'BB_Middle', 'BB_Lower', 'ATR',
                'Volume_SMA', 'Volume_Ratio', 'Stoch_K', 'Stoch_D',
                'ADX', 'Volatility_20'
            ]
            
            for col in indicator_cols:
                if col in df.columns:
                    indicators[col] = [
                        {
                            'date': date.strftime('%Y-%m-%d'),
                            'value': round(val, 4) if pd.notna(val) else None
                        }
                        for date, val in df[col].items()
                    ]
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
        
        return indicators
    
    def _get_latest_indicators(self, indicators: Dict[str, List]) -> Dict[str, float]:
        """Get the most recent value for each indicator."""
        latest = {}
        for name, series in indicators.items():
            if series:
                # Get the last non-null value
                for item in reversed(series):
                    if item['value'] is not None:
                        latest[name] = item['value']
                        break
        return latest
    
    def get_price_at_date(self, ticker: str, date: datetime) -> Optional[float]:
        """Get the closing price for a stock on a specific date."""
        try:
            stock = yf.Ticker(ticker)
            # Get data for a few days around the target date
            start = date - timedelta(days=5)
            end = date + timedelta(days=5)
            df = stock.history(start=start, end=end)
            
            if df.empty:
                return None
            
            # Find the closest date
            target_date = pd.Timestamp(date)
            closest_idx = df.index.get_indexer([target_date], method='nearest')[0]
            
            return float(df.iloc[closest_idx]['Close'])
            
        except Exception as e:
            logger.error(f"Error getting price for {ticker} on {date}: {e}")
            return None
    
    def get_sp500_data(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """Get S&P 500 index data for benchmarking."""
        try:
            spy = yf.Ticker('SPY')
            df = spy.history(start=start_date, end=end_date)
            return df
        except Exception as e:
            logger.error(f"Error fetching S&P 500 data: {e}")
            return None
    
    def get_analysis_context(self, ticker: str, trade_date: datetime) -> Dict[str, Any]:
        """
        Get comprehensive analysis context for LLM decision making.
        
        Args:
            ticker: Stock ticker
            trade_date: Date of the insider trade
            
        Returns:
            Context dictionary with all relevant data
        """
        # Get 6 months of data before the trade
        start_date = trade_date - timedelta(days=180)
        stock_data = self.get_stock_data(ticker, start_date, trade_date)
        
        if 'error' in stock_data:
            return stock_data
        
        latest = stock_data.get('latest_indicators', {})
        
        # Generate analysis summary
        analysis = {
            'ticker': ticker,
            'company_name': stock_data.get('company_name'),
            'sector': stock_data.get('sector'),
            'industry': stock_data.get('industry'),
            'market_cap': stock_data.get('market_cap'),
            'fundamentals': {
                'pe_ratio': stock_data.get('pe_ratio'),
                'forward_pe': stock_data.get('forward_pe'),
                'dividend_yield': stock_data.get('dividend_yield'),
                'beta': stock_data.get('beta'),
            },
            'technicals': {
                'rsi': latest.get('RSI'),
                'macd': latest.get('MACD'),
                'macd_signal': latest.get('MACD_Signal'),
                'sma_20': latest.get('SMA_20'),
                'sma_50': latest.get('SMA_50'),
                'sma_200': latest.get('SMA_200'),
                'atr': latest.get('ATR'),
                'adx': latest.get('ADX'),
                'volatility': latest.get('Volatility_20'),
            },
            'signals': self._generate_signals(latest, stock_data),
        }
        
        return analysis
    
    def _generate_signals(self, indicators: Dict, stock_data: Dict) -> Dict[str, str]:
        """Generate trading signals from indicators."""
        signals = {}
        
        # RSI signals
        rsi = indicators.get('RSI')
        if rsi:
            if rsi < 30:
                signals['rsi'] = 'oversold'
            elif rsi > 70:
                signals['rsi'] = 'overbought'
            else:
                signals['rsi'] = 'neutral'
        
        # MACD signals
        macd = indicators.get('MACD')
        macd_signal = indicators.get('MACD_Signal')
        if macd and macd_signal:
            if macd > macd_signal:
                signals['macd'] = 'bullish'
            else:
                signals['macd'] = 'bearish'
        
        # Moving average signals
        sma_20 = indicators.get('SMA_20')
        sma_50 = indicators.get('SMA_50')
        sma_200 = indicators.get('SMA_200')
        
        if sma_20 and sma_50:
            if sma_20 > sma_50:
                signals['ma_short'] = 'bullish'
            else:
                signals['ma_short'] = 'bearish'
        
        if sma_50 and sma_200:
            if sma_50 > sma_200:
                signals['ma_long'] = 'bullish (golden cross potential)'
            else:
                signals['ma_long'] = 'bearish (death cross potential)'
        
        # Trend strength
        adx = indicators.get('ADX')
        if adx:
            if adx > 25:
                signals['trend_strength'] = 'strong trend'
            else:
                signals['trend_strength'] = 'weak/no trend'
        
        return signals
