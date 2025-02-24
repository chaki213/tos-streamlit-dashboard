# src/trading/portfolio.py
from datetime import datetime
import pandas as pd

class Portfolio:
    def __init__(self, initial_balance=100000):
        """Initialize portfolio with starting cash balance"""
        self.initial_balance = initial_balance
        self.cash = initial_balance
        self.positions = {}  # symbol -> {'shares': n, 'cost_basis': x}
        self.history = []  # List of portfolio value snapshots
        self.transactions = []  # List of all trades
        
        # Record initial state
        self._record_portfolio_value()
    
    def buy(self, symbol, shares, price):
        """Buy shares of a stock"""
        cost = shares * price
        if cost > self.cash:
            # Can't afford, buy as many as possible
            shares = int(self.cash / price)
            cost = shares * price
            
        if shares <= 0:
            return False
            
        # Execute the purchase
        self.cash -= cost
        
        # Update position
        if symbol in self.positions:
            # Calculate new cost basis
            current = self.positions[symbol]
            total_shares = current['shares'] + shares
            total_cost = (current['shares'] * current['cost_basis']) + cost
            new_cost_basis = total_cost / total_shares
            
            self.positions[symbol] = {
                'shares': total_shares,
                'cost_basis': new_cost_basis
            }
        else:
            self.positions[symbol] = {
                'shares': shares,
                'cost_basis': price
            }
            
        # Record the transaction
        transaction = {
            'timestamp': datetime.now(),
            'type': 'BUY',
            'symbol': symbol,
            'shares': shares,
            'price': price,
            'total': cost
        }
        self.transactions.append(transaction)
        
        # Update portfolio value
        self._record_portfolio_value()
        
        return True
    
    def sell(self, symbol, shares, price):
        """Sell shares of a stock"""
        if symbol not in self.positions or self.positions[symbol]['shares'] < shares:
            return False
            
        proceeds = shares * price
        self.cash += proceeds
        
        # Update position
        current_shares = self.positions[symbol]['shares']
        new_shares = current_shares - shares
        
        if new_shares == 0:
            # Sold entire position
            del self.positions[symbol]
        else:
            # Keep same cost basis
            self.positions[symbol]['shares'] = new_shares
            
        # Record the transaction
        transaction = {
            'timestamp': datetime.now(),
            'type': 'SELL',
            'symbol': symbol,
            'shares': shares,
            'price': price,
            'total': proceeds
        }
        self.transactions.append(transaction)
        
        # Update portfolio value
        self._record_portfolio_value()
        
        return True
    
    def get_position(self, symbol):
        """Get current position for a symbol"""
        if symbol not in self.positions:
            return {'shares': 0, 'cost_basis': 0, 'market_value': 0, 'profit_loss': 0, 'profit_loss_pct': 0}
            
        position = self.positions[symbol].copy()
        
        # If we have a last price, calculate market value and P&L
        if hasattr(self, 'last_prices') and symbol in self.last_prices:
            current_price = self.last_prices[symbol]
            position['market_value'] = position['shares'] * current_price
            position['profit_loss'] = position['market_value'] - (position['shares'] * position['cost_basis'])
            if position['shares'] * position['cost_basis'] > 0:
                position['profit_loss_pct'] = (position['profit_loss'] / (position['shares'] * position['cost_basis'])) * 100
            else:
                position['profit_loss_pct'] = 0
        else:
            position['market_value'] = position['shares'] * position['cost_basis']
            position['profit_loss'] = 0
            position['profit_loss_pct'] = 0
            
        return position
    
    def get_position_summary(self, symbol):
        """Get a summary string for a position"""
        position = self.get_position(symbol)
        
        if position['shares'] == 0:
            return "No position"
            
        return f"{position['shares']} shares @ ${position['cost_basis']:.2f}"
    
    def update_prices(self, prices_dict):
        """Update last known prices for all positions"""
        self.last_prices = prices_dict
        self._record_portfolio_value()
    
    def get_total_value(self):
        """Calculate total portfolio value"""
        total = self.cash
        
        for symbol, position in self.positions.items():
            # Use last known price if available, otherwise use cost basis
            if hasattr(self, 'last_prices') and symbol in self.last_prices:
                price = self.last_prices[symbol]
            else:
                price = position['cost_basis']
                
            total += position['shares'] * price
            
        return total
    
    def get_percent_change(self):
        """Calculate percent change from initial balance"""
        current_value = self.get_total_value()
        change = ((current_value - self.initial_balance) / self.initial_balance) * 100
        return change
    
    def _record_portfolio_value(self):
        """Record current portfolio value for historical tracking"""
        snapshot = {
            'timestamp': datetime.now(),
            'cash': self.cash,
            'investments': self.get_total_value() - self.cash,
            'total_value': self.get_total_value()
        }
        self.history.append(snapshot)
    
    def get_transaction_history(self, as_dataframe=False):
        """Get transaction history"""
        if not as_dataframe:
            return self.transactions
            
        return pd.DataFrame(self.transactions)
    
    def get_portfolio_history(self, as_dataframe=False):
        """Get portfolio value history"""
        if not as_dataframe:
            return self.history
            
        return pd.DataFrame(self.history)