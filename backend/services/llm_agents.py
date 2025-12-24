"""
LLM agent framework for trading decisions.
"""
import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseTradingAgent(ABC):
    """Base class for LLM trading agents."""
    
    def __init__(
        self,
        name: str,
        temperature: float = 0.7,
        risk_tolerance: str = 'moderate',
        max_position_size: float = 0.1,
        stop_loss_pct: float = 0.1,
        take_profit_pct: float = 0.2,
        system_prompt: Optional[str] = None
    ):
        self.name = name
        self.temperature = temperature
        self.risk_tolerance = risk_tolerance
        self.max_position_size = max_position_size
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.system_prompt = system_prompt or self._default_system_prompt()
    
    def _default_system_prompt(self) -> str:
        return f"""You are an expert stock trading analyst evaluating insider trading signals.
        
Your risk tolerance is: {self.risk_tolerance}
Maximum position size: {self.max_position_size * 100}% of portfolio
Stop loss target: {self.stop_loss_pct * 100}%
Take profit target: {self.take_profit_pct * 100}%

When analyzing an insider trade, consider:
1. The insider's position and track record
2. The size and significance of the trade
3. Technical indicators and price action
4. Sector trends and market conditions
5. Company fundamentals

Respond with a JSON object containing:
{{
    "decision": "BUY" | "SELL" | "HOLD",
    "confidence": 0.0 to 1.0,
    "position_size": 0.0 to {self.max_position_size},
    "reasoning": "explanation of your decision",
    "key_factors": ["list", "of", "key", "factors"],
    "risk_assessment": "low" | "medium" | "high",
    "price_target": float or null,
    "stop_loss": float or null
}}
"""
    
    def build_analysis_prompt(
        self,
        insider_trade: Dict[str, Any],
        stock_context: Dict[str, Any]
    ) -> str:
        """Build the analysis prompt for the LLM."""
        return f"""
Analyze this insider trading signal and provide a trading recommendation:

## Insider Trade Details
- Ticker: {insider_trade.get('ticker')}
- Company: {insider_trade.get('company_name')}
- Trade Type: {insider_trade.get('trade_type')} ({'Purchase' if 'P' in str(insider_trade.get('trade_type', '')) else 'Sale'})
- Insider: {insider_trade.get('insider_name')}
- Title: {insider_trade.get('insider_title')}
- Trade Date: {insider_trade.get('trade_date')}
- Price: ${insider_trade.get('price')}
- Value: ${insider_trade.get('value'):,.0f}
- Ownership Change: {insider_trade.get('delta_owned')}%

## Stock Context
- Sector: {stock_context.get('sector')}
- Industry: {stock_context.get('industry')}
- Market Cap: ${stock_context.get('market_cap'):,.0f if stock_context.get('market_cap') else 'N/A'}

## Fundamentals
- P/E Ratio: {stock_context.get('fundamentals', {}).get('pe_ratio')}
- Forward P/E: {stock_context.get('fundamentals', {}).get('forward_pe')}
- Dividend Yield: {stock_context.get('fundamentals', {}).get('dividend_yield')}
- Beta: {stock_context.get('fundamentals', {}).get('beta')}

## Technical Indicators
- RSI (14): {stock_context.get('technicals', {}).get('rsi')}
- MACD: {stock_context.get('technicals', {}).get('macd')}
- MACD Signal: {stock_context.get('technicals', {}).get('macd_signal')}
- SMA 20: {stock_context.get('technicals', {}).get('sma_20')}
- SMA 50: {stock_context.get('technicals', {}).get('sma_50')}
- SMA 200: {stock_context.get('technicals', {}).get('sma_200')}
- ATR: {stock_context.get('technicals', {}).get('atr')}
- ADX: {stock_context.get('technicals', {}).get('adx')}
- 20-day Volatility: {stock_context.get('technicals', {}).get('volatility')}

## Technical Signals
{json.dumps(stock_context.get('signals', {}), indent=2)}

Based on this information, provide your trading recommendation as a JSON object.
"""
    
    @abstractmethod
    def analyze_trade(
        self,
        insider_trade: Dict[str, Any],
        stock_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze an insider trade and return a trading decision."""
        pass
    
    def parse_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response to extract the trading decision."""
        try:
            # Try to extract JSON from the response
            # Handle cases where response includes markdown code blocks
            if '```json' in response:
                json_str = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                json_str = response.split('```')[1].split('```')[0]
            else:
                # Try to find JSON object in response
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end > start:
                    json_str = response[start:end]
                else:
                    json_str = response
            
            result = json.loads(json_str)
            
            # Validate required fields
            required_fields = ['decision', 'confidence', 'reasoning']
            for field in required_fields:
                if field not in result:
                    result[field] = 'HOLD' if field == 'decision' else 0.5 if field == 'confidence' else 'Unable to parse response'
            
            return result
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            return {
                'decision': 'HOLD',
                'confidence': 0.0,
                'reasoning': f'Failed to parse response: {response[:200]}',
                'error': str(e)
            }


class OpenAIAgent(BaseTradingAgent):
    """Trading agent using OpenAI GPT models."""
    
    def __init__(self, model: str = 'gpt-4', **kwargs):
        super().__init__(**kwargs)
        self.model = model
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        return self._client
    
    def analyze_trade(
        self,
        insider_trade: Dict[str, Any],
        stock_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze trade using OpenAI."""
        try:
            prompt = self.build_analysis_prompt(insider_trade, stock_context)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            return self.parse_response(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return {
                'decision': 'HOLD',
                'confidence': 0.0,
                'reasoning': f'API error: {str(e)}',
                'error': str(e)
            }


class AnthropicAgent(BaseTradingAgent):
    """Trading agent using Anthropic Claude models."""
    
    def __init__(self, model: str = 'claude-3-sonnet-20240229', **kwargs):
        super().__init__(**kwargs)
        self.model = model
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            from anthropic import Anthropic
            self._client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        return self._client
    
    def analyze_trade(
        self,
        insider_trade: Dict[str, Any],
        stock_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze trade using Anthropic Claude."""
        try:
            prompt = self.build_analysis_prompt(insider_trade, stock_context)
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return self.parse_response(response.content[0].text)
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return {
                'decision': 'HOLD',
                'confidence': 0.0,
                'reasoning': f'API error: {str(e)}',
                'error': str(e)
            }


class GoogleAgent(BaseTradingAgent):
    """Trading agent using Google Gemini models."""
    
    def __init__(self, model: str = 'gemini-pro', **kwargs):
        super().__init__(**kwargs)
        self.model = model
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            import google.generativeai as genai
            genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
            self._client = genai.GenerativeModel(self.model)
        return self._client
    
    def analyze_trade(
        self,
        insider_trade: Dict[str, Any],
        stock_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze trade using Google Gemini."""
        try:
            prompt = f"{self.system_prompt}\n\n{self.build_analysis_prompt(insider_trade, stock_context)}"
            
            response = self.client.generate_content(prompt)
            
            return self.parse_response(response.text)
            
        except Exception as e:
            logger.error(f"Google API error: {e}")
            return {
                'decision': 'HOLD',
                'confidence': 0.0,
                'reasoning': f'API error: {str(e)}',
                'error': str(e)
            }


class MockAgent(BaseTradingAgent):
    """Mock agent for testing without API calls."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def analyze_trade(
        self,
        insider_trade: Dict[str, Any],
        stock_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Return mock analysis based on simple rules."""
        trade_type = insider_trade.get('trade_type', '')
        is_purchase = 'P' in str(trade_type)
        value = insider_trade.get('value', 0) or 0
        
        # Simple rule-based mock
        if is_purchase and value > 100000:
            decision = 'BUY'
            confidence = min(0.5 + (value / 1000000) * 0.3, 0.9)
        elif not is_purchase and value > 500000:
            decision = 'SELL'
            confidence = min(0.4 + (value / 2000000) * 0.3, 0.8)
        else:
            decision = 'HOLD'
            confidence = 0.3
        
        return {
            'decision': decision,
            'confidence': round(confidence, 2),
            'position_size': self.max_position_size * confidence if decision == 'BUY' else 0,
            'reasoning': f"Mock analysis: {'Purchase' if is_purchase else 'Sale'} of ${value:,.0f} by {insider_trade.get('insider_name')}",
            'key_factors': ['insider_type', 'trade_value', 'trade_type'],
            'risk_assessment': 'medium',
            'price_target': None,
            'stop_loss': None
        }


def create_agent(
    provider: str,
    model: str,
    **kwargs
) -> BaseTradingAgent:
    """
    Factory function to create trading agents.
    
    Args:
        provider: LLM provider (openai, anthropic, google, mock)
        model: Model name
        **kwargs: Additional agent parameters
        
    Returns:
        Trading agent instance
    """
    agents = {
        'openai': OpenAIAgent,
        'anthropic': AnthropicAgent,
        'google': GoogleAgent,
        'mock': MockAgent
    }
    
    agent_class = agents.get(provider.lower())
    if agent_class is None:
        raise ValueError(f"Unknown provider: {provider}. Available: {list(agents.keys())}")
    
    if provider.lower() != 'mock':
        return agent_class(model=model, **kwargs)
    else:
        return agent_class(**kwargs)
