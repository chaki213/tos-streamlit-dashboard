from datetime import date, timedelta
import numpy as np

class OptionSymbolBuilder:
    # Dictionary mapping futures to their exchanges
    FUTURES_EXCHANGES = {
        "/ZN": "XCBT",  # 10-Year T-Note
        "/ZB": "XCBT",  # 30-Year T-Bond
        "/ES": "XCME",  # E-mini S&P 500
        "/NQ": "XCME",  # E-mini NASDAQ
        "/RTY": "XCME", # E-mini Russell 2000
        "/YM": "XCBT",  # E-mini Dow
        "/CL": "XNYM",  # Crude Oil
        "/GC": "XCEC",  # Gold
        "/SI": "XCEC",  # Silver
        "/ZC": "XCBT",  # Corn
        "/ZS": "XCBT",  # Soybeans
        "/ZW": "XCBT",  # Wheat
    }

    # Dictionary mapping futures to their contract months
    FUTURES_MONTHS = {
        'F': '01',  # January
        'G': '02',  # February
        'H': '03',  # March
        'J': '04',  # April
        'K': '05',  # May
        'M': '06',  # June
        'N': '07',  # July
        'Q': '08',  # August
        'U': '09',  # September
        'V': '10',  # October
        'X': '11',  # November
        'Z': '12'   # December
    }

    # Dictionary mapping /ES maturities to their product codes
    ES_PRODUCT_CODES = {
        7: "EW1",    # Weekly 1
        10: "E2A",   # Weekly 2
        11: "E2B"    # Weekly 3
    }

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
        third_friday = friday + timedelta(days=14)
        return d == third_friday

    @staticmethod
    def _get_futures_month_code(expiry: date) -> str:
        """Convert a date to a futures month code"""
        for code, month in OptionSymbolBuilder.FUTURES_MONTHS.items():
            if int(month) == expiry.month:
                return code
        return ''

    @staticmethod
    def _get_es_product_code(expiry: date) -> str:
        """Get the product code for /ES contracts based on expiry day"""
        if expiry.day in OptionSymbolBuilder.ES_PRODUCT_CODES:
            return OptionSymbolBuilder.ES_PRODUCT_CODES[expiry.day]
        return "ES"  # Default to regular ES

    @staticmethod
    def _format_strike(strike: float, is_futures: bool = False) -> str:
        """Format strike price string, ensuring no decimals if it's a whole number"""
        if abs(round(strike) - strike) < 0.0001:  # More precise check for whole numbers
            return str(int(round(strike)))
        # Only keep decimal if it's not a whole number
        return str(int(round(strike * 10) / 10))

    @staticmethod
    def build_symbols(base_symbol: str, expiry: date, current_price: float, strike_range: int, strike_spacing: float) -> list:
        """
        Builds a list of option symbols for both calls and puts
        """
        if not current_price or current_price <= 0:
            print("Invalid current price")
            return []
            
        if not strike_range or strike_range <= 0:
            print("Invalid strike range")
            return []
            
        if not strike_spacing or strike_spacing <= 0:
            print("Invalid strike spacing")
            return []
            
        # Check if this is a futures symbol
        is_futures = base_symbol.startswith('/')
        
        if is_futures:
            # Get exchange suffix
            exchange = OptionSymbolBuilder.FUTURES_EXCHANGES.get(base_symbol, "XCBT")
            # Get futures month code
            month_code = OptionSymbolBuilder._get_futures_month_code(expiry)
            
            # Special handling for /ES weekly contracts
            if base_symbol == "/ES":
                product_code = OptionSymbolBuilder._get_es_product_code(expiry)
                futures_base = f"{product_code}{month_code}{str(expiry.year)[-2:]}"
                print(f"ES Weekly base: {futures_base}")  # Debug log
            else:
                futures_base = f"{base_symbol}1{month_code}{str(expiry.year)[-2:]}"
                print(f"Regular futures base: {futures_base}")  # Debug log
                
            # For any futures contract, strip the forward slash for the option symbol
            if futures_base.startswith('/'):
                futures_base = futures_base[1:]
        else:
            # Handle regular equity/index symbols
            if not OptionSymbolBuilder._is_third_friday(expiry):
                if base_symbol == "SPX":
                    base_symbol = "SPXW"
                elif base_symbol == "NDX":
                    base_symbol = "NDXP"
                elif base_symbol == "RUT":
                    base_symbol = "RUTW"
  
        # Round current price to nearest valid strike
        rounded_price = OptionSymbolBuilder._round_to_nearest_strike(current_price, strike_spacing)
        print(f"Rounded price: {rounded_price}, Range: ±{strike_range}, Spacing: {strike_spacing}")  # Debug log
        
        # Generate strike prices using numpy arange
        num_strikes = int(2 * strike_range / strike_spacing) + 1
        strikes = np.linspace(
            rounded_price - strike_range,
            rounded_price + strike_range,
            num_strikes
        )
        
        if len(strikes) == 0:
            print("No strikes generated")
            return []
            
        print(f"Generated {len(strikes)} strikes from {strikes[0]} to {strikes[-1]}")  # Debug log
        
        symbols = []
        
        if is_futures:
            for strike in strikes:
                strike_str = OptionSymbolBuilder._format_strike(strike, is_futures=True)
                call_symbol = f"./{futures_base}C{strike_str}:{exchange}"
                put_symbol = f"./{futures_base}P{strike_str}:{exchange}"
                symbols.extend([call_symbol, put_symbol])
        else:
            date_str = expiry.strftime("%y%m%d")
            for strike in strikes:
                strike_str = OptionSymbolBuilder._format_strike(strike)
                call_symbol = f".{base_symbol}{date_str}C{strike_str}"
                put_symbol = f".{base_symbol}{date_str}P{strike_str}"
                symbols.extend([call_symbol, put_symbol])
        
        if not symbols:
            print("No symbols generated")
            return []
            
        print(f"Generated {len(symbols)} total symbols. First few: {symbols[:4]}")  # Debug log
        return symbols
