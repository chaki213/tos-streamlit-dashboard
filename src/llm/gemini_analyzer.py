# src/llm/gemini_analyzer.py
import os
import google.generativeai as genai
from datetime import datetime, timedelta
import pandas as pd

class GeminiAnalyzer:
    def __init__(self, api_key=None):
        """Initialize Gemini API connection"""
        # Try to get API key from environment variable if not provided
        self.api_key = api_key or os.environ.get('GEMINI_API_KEY')
        
        if not self.api_key:
            print("Warning: No Gemini API key found. Please set GEMINI_API_KEY environment variable.")
            self.client = None
        else:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
    
    def analyze(self, symbol, price_history, position=None):
        """
        Analyze price data and make a trading decision
        
        Args:
            symbol: Stock symbol
            price_history: DataFrame with timestamp and price columns
            position: Current position information (optional)
            
        Returns:
            Dictionary with decision and reasoning
        """
        if not self.api_key:
            return {
                'decision': 'HOLD',
                'reasoning': "No Gemini API key provided. Please set the GEMINI_API_KEY environment variable."
            }
            
        # If we have less than 3 data points, not enough to analyze
        if len(price_history) < 3:
            return {
                'decision': 'HOLD',
                'reasoning': "Not enough price data collected yet. Waiting for more data points."
            }
            
        # Format the price data for the prompt
        price_data = self._format_price_data(price_history)
        
        # Format position information
        position_info = self._format_position_info(position)
        
        # Create the prompt
        prompt = f"""
You are a financial analyst and trading assistant. Analyze the recent price data for {symbol} and make a trading decision (BUY, SELL, or HOLD).

Recent price data (timestamps are in descending order - newest first):
{price_data}

Current position information:
{position_info}

Based ONLY on the price pattern in this data, determine if there appears to be a trend that suggests buying, selling, or holding.
Consider:
1. Recent price movements
2. Volatility
3. Current position
4. Simple momentum in short time frames

Respond with your analysis in the following format:
DECISION: [BUY/SELL/HOLD]
REASONING: [Your detailed analysis explaining your decision]
        """
        
        try:
            # Get response from Gemini
            response = self.model.generate_content(prompt)
            text = response.text
            
            # Parse the response
            decision, reasoning = self._parse_response(text)
            
            return {
                'decision': decision,
                'reasoning': reasoning
            }
        except Exception as e:
            print(f"Error calling Gemini API: {str(e)}")
            return {
                'decision': 'HOLD',
                'reasoning': f"Error analyzing data: {str(e)}"
            }
    
    def _format_price_data(self, price_history):
        """Format price data for the prompt"""
        # Sort by timestamp descending
        df = price_history.sort_values('timestamp', ascending=False).reset_index(drop=True)
        
        # Keep only the most recent 10 data points to avoid overwhelming the LLM
        df = df.head(10)
        
        # Calculate minute-to-minute percentage changes
        if len(df) > 1:
            df['change'] = df['price'].shift(-1).pct_change(-1) * 100
        
        # Format as string
        formatted_data = ""
        for i, row in df.iterrows():
            time_str = row['timestamp'].strftime('%H:%M:%S')
            price_str = f"${row['price']:.2f}"
            
            if i < len(df) - 1:
                change = row['change']
                change_str = f"{change:.2f}%" if not pd.isna(change) else "N/A"
                formatted_data += f"{time_str}: {price_str} (Change: {change_str})\n"
            else:
                formatted_data += f"{time_str}: {price_str}\n"
        
        return formatted_data
    
    def _format_position_info(self, position):
        """Format position information for the prompt"""
        if position is None or position['shares'] == 0:
            return "No current position."
            
        return f"""
Shares owned: {position['shares']}
Average cost basis: ${position['cost_basis']:.2f}
Total investment: ${position['shares'] * position['cost_basis']:.2f}
Profit/Loss: ${position['profit_loss']:.2f} ({position['profit_loss_pct']:.2f}%)
        """
    
    def _parse_response(self, response_text):
        """Parse the LLM response to extract decision and reasoning"""
        # Default values
        decision = "HOLD"
        reasoning = response_text
        
        # Try to extract decision
        if "DECISION:" in response_text:
            decision_parts = response_text.split("DECISION:")
            if len(decision_parts) > 1:
                decision_line = decision_parts[1].strip().split("\n")[0]
                
                # Clean up and normalize
                decision = decision_line.strip().upper()
                
                # Standardize
                if "BUY" in decision:
                    decision = "BUY"
                elif "SELL" in decision:
                    decision = "SELL"
                else:
                    decision = "HOLD"
        
        # Try to extract reasoning
        if "REASONING:" in response_text:
            reason_parts = response_text.split("REASONING:")
            if len(reason_parts) > 1:
                reasoning = reason_parts[1].strip()
        
        return decision, reasoning