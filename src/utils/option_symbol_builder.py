from datetime import date, timedelta
import numpy as np

class OptionSymbolBuilder:
    @staticmethod
    def _round_to_nearest_strike(price: float, spacing: float) -> float:
        """Round price to nearest valid strike price based on strike spacing"""
        return round(price / spacing) * spacing

    @staticmethod
    def _is_third_friday(d: date) -> bool:
        """Check if date is the third Friday of its month"""
        # Find first day of the month
        first = date(d.year, d.month, 1)
        # Find first Friday
        friday = first + timedelta(days=((4 - first.weekday()) % 7))
        # Find third Friday
        third_friday = friday + timedelta(days=14)  # Fixed: removed parentheses around 14
        #print(f"Third Friday: {third_friday}")
        return d == third_friday

    @staticmethod
    def _get_next_n_fridays(start_date: date, n: int) -> list:
        """Get the next n Fridays from a start date"""
        fridays = []
        current = start_date
        while len(fridays) < n:
            days_ahead = 4 - current.weekday()  # 4 is Friday
            if days_ahead <= 0:
                days_ahead += 7
            next_friday = current + timedelta(days=days_ahead)
            fridays.append(next_friday)
            current = next_friday + timedelta(days=1)
        return fridays

    @staticmethod
    def build_surface_symbols(base_symbol: str, current_price: float, strike_range: int, strike_spacing: float, num_expirations: int = 4) -> tuple:
        """
        Builds option symbols across multiple expirations for volatility surface
        Returns: Tuple of (option_symbols, strikes, expiration_dates)
        """
        # Get next n Fridays
        fridays = OptionSymbolBuilder._get_next_n_fridays(date.today(), num_expirations)
        
        symbols = []
        # Use same strike range for all expirations
        rounded_price = OptionSymbolBuilder._round_to_nearest_strike(current_price, strike_spacing)
        
        # Generate strike prices
        num_strikes = int(2 * strike_range / strike_spacing) + 1
        strikes = np.linspace(
            rounded_price - strike_range,
            rounded_price + strike_range,
            num_strikes
        )
        
        # Format strikes to match build_symbols behavior
        formatted_strikes = []
        for strike in strikes:
            if strike_spacing in [0.5, 2.5] and abs(strike % 1 - 0.5) < 0.001:
                formatted_strikes.append(float(f"{strike:.1f}"))
            else:
                formatted_strikes.append(int(strike))
        
        # Format expiration dates
        expiration_dates = []
        
        for expiry in fridays:
            # Handle index symbol conversion
            symbol = base_symbol
            if not OptionSymbolBuilder._is_third_friday(expiry):
                if base_symbol == "SPX":
                    symbol = "SPXW"
                elif base_symbol == "NDX":
                    symbol = "NDXP"
                elif base_symbol == "RUT":
                    symbol = "RUTW"
            
            date_str = expiry.strftime("%y%m%d")
            expiration_dates.append(date_str)
            
            for strike in strikes:
                if strike_spacing in [0.5, 2.5] and abs(strike % 1 - 0.5) < 0.001:
                    strike_str = f"{strike:.1f}"
                else:
                    strike_str = f"{int(strike)}"
                    
                call_symbol = f".{symbol}{date_str}C{strike_str}"
                put_symbol = f".{symbol}{date_str}P{strike_str}"
                symbols.extend([call_symbol, put_symbol])
        
        return symbols, formatted_strikes, expiration_dates

    @staticmethod
    def build_symbols(base_symbol: str, expiry: date, current_price: float, strike_range: int, strike_spacing: float) -> list:
        """
        Builds a list of option symbols for both calls and puts
        Returns: List of option symbols in ThinkorSwim format
        Example: .SPY250129C601
        """

        # Only convert symbols if it's NOT the third Friday of the month
        # I need to figure out how to display SPX afternoon expiry contract on 3rd friday
        if not OptionSymbolBuilder._is_third_friday(expiry):
            if base_symbol == "SPX":
                base_symbol = "SPXW"
            elif base_symbol == "NDX":
                base_symbol = "NDXP"
            elif base_symbol == "RUT":
                base_symbol = "RUTW"
  
        # Round current price to nearest valid strike
        rounded_price = OptionSymbolBuilder._round_to_nearest_strike(current_price, strike_spacing)
        
        # Generate strike prices using numpy arange
        num_strikes = int(2 * strike_range / strike_spacing) + 1
        #print(f"Num Strikes: {num_strikes}")
        strikes = np.linspace(
            rounded_price - strike_range,
            rounded_price + strike_range,
            num_strikes
        )
        
        symbols = []
        date_str = expiry.strftime("%y%m%d")
        
        for strike in strikes:
            # Format strike string: only show decimal for .5 strikes
            if (strike_spacing in [0.5, 2.5] and 
                abs(strike % 1 - 0.5) < 0.001):  # Handle floating point comparison
                strike_str = f"{strike:.1f}"
            else:
                strike_str = f"{int(strike)}"
                
            call_symbol = f".{base_symbol}{date_str}C{strike_str}"
            put_symbol = f".{base_symbol}{date_str}P{strike_str}"
            symbols.extend([call_symbol, put_symbol])
        
        return symbols
