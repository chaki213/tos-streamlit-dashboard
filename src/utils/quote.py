import time
from typing import Any, Dict, Union

from config import QuoteType


class Quote:
    def __init__(self, quote_type: Union[str, QuoteType], symbol: str, value: Any, timestamp: float = None):
        self.quote_type = self._parse_quote_type(quote_type)
        self.symbol = symbol
        self.value = self._process_value(value)
        self.timestamp = timestamp or time.time()

    @staticmethod
    def _parse_quote_type(quote_type: Union[str, QuoteType]) -> QuoteType:
        if isinstance(quote_type, QuoteType):
            return quote_type
        if isinstance(quote_type, str):
            try:
                return QuoteType[quote_type.upper()]
            except KeyError:
                raise ValueError(f"Invalid quote type: {quote_type}")
        raise ValueError(f"Invalid quote type: {quote_type}")

    def _process_value(self, value: Any) -> Any:
        if value is None or value in ['N/A', '!N/A']:
            return None

        if self.quote_type in [QuoteType.LAST, QuoteType.BID, QuoteType.ASK, QuoteType.HIGH, QuoteType.LOW, QuoteType.OPEN, QuoteType.CLOSE, QuoteType.MARK, QuoteType.DELTA, QuoteType.GAMMA]:
            return self._to_float(value)
        elif self.quote_type in [QuoteType.VOLUME, QuoteType.ASK_SIZE, QuoteType.BID_SIZE, QuoteType.LAST_SIZE, QuoteType.OPEN_INT]:
            return self._to_int(value)
        elif self.quote_type == QuoteType.IMPL_VOL:
            float_value = self._to_float(value, percentage=True)
            return round(float_value, 4) if float_value is not None else None
        return value

    """ @staticmethod
    def _to_float(value: Any, percentage: bool = False) -> Union[float, None]:
        try:
            if isinstance(value, str):
                value = value.rstrip('%')
            result = float(value)
            #return result / 100 if percentage else result
            return result
        except (ValueError, TypeError):
            return None """
        
    @staticmethod
    def _to_float(value: Any, percentage: bool = False) -> Union[float, None]:
        """
        Convert value to float, handling special Treasury futures format.
        
        Args:
            value: Value to convert
            percentage: Whether value is a percentage
            
        Returns:
            float: Converted value
            None: If conversion fails
            
        Examples:
            "109'080" -> 109.25 (109 + 8/32)  # 8 ticks = 8/32 = 0.25
            "123'165" -> 123.515625 (123 + 16.5/32)
        """
        try:
            #print(f"Processing value: {value} of type {type(value)}")
            if isinstance(value, str):
                # Handle Treasury futures format like "109'080"
                if "'" in value:
                    #print(f"Processing Treasury format: {value}")
                    whole, ticks = value.split("'")
                    #print(f"Split into whole: {whole}, ticks: {ticks}")
                    whole_num = float(whole)
                    # Convert ticks directly to 32nds (first 2 digits are the number of 32nds)
                    ticks_num = float(ticks[:2])  # Take first two digits for 32nds
                    # If there's a third digit, it represents 1/2 of a 32nd
                    if len(ticks) > 2 and ticks[2] == '5':
                        ticks_num += 0.5
                    result = whole_num + (ticks_num / 32)
                    #print(f"Calculated result: {result}")
                    return result
                
                value = value.rstrip('%')
            result = float(value)
            #print(f"Final result: {result}")
            return result
        except (ValueError, TypeError) as e:
            print(f"Error converting value: {e}")
            return None

    @staticmethod
    def _to_int(value: Any) -> Union[int, None]:
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None

    def __str__(self):
        if self.value is None:
            return "N/A"
        if isinstance(self.value, float):
            if self.quote_type == QuoteType.IMPL_VOL:
                return f"{self.value:.2%}"
            elif self.quote_type in [QuoteType.DELTA, QuoteType.GAMMA]:
                return f"{self.value:.4f}"
            return f"${self.value:.2f}"
        if isinstance(self.value, int):
            return f"{self._format_int(self.value)}"
        return str(self.value)

    def __repr__(self):
        return f"Quote(type={self.quote_type!r}, symbol='{self.symbol}', value={self.value!r}, timestamp={self.timestamp})"

    @staticmethod
    def _format_int(value: int) -> str:
        return f"{value:,}"

    @classmethod
    def create(cls, quote_type: Union[str, QuoteType], symbol: str, value: Any, timestamp: float = None) -> 'Quote':
        return cls(quote_type, symbol, value, timestamp)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'quote_type': self.quote_type.value,
            'symbol': self.symbol,
            'value': self.value,
            'timestamp': self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Quote':
        return cls(
            quote_type=data['quote_type'],
            symbol=data['symbol'],
            value=data['value'],
            timestamp=data['timestamp']
        )
