# src/rtd/rtd_worker.py
import pythoncom
import time
import threading
from queue import Queue
from src.rtd.client import RTDClient
from src.core.settings import SETTINGS
from config.quote_types import QuoteType

class RTDWorker:
    def __init__(self, data_queue: Queue, stop_event: threading.Event):
        self.data_queue = data_queue
        self.stop_event = stop_event
        self.client = None
        self.initialized = False
        
    def start(self, all_symbols: list):
        """Start RTD worker with all symbols at once"""
        try:
            if self.initialized:
                self.cleanup()
                #time.sleep(.2)  # 1 Wait for proper cleanup
                
            pythoncom.CoInitialize()
            time.sleep(0.1)  # Increased delay for COM initialization
            
            self.client = RTDClient(heartbeat_ms=SETTINGS['timing']['initial_heartbeat'])
            self.client.initialize()
            self.initialized = True
            
            if not all_symbols:
                return
                
            success_count = 0
            subscription_errors = []
            
            # Subscribe to all symbols at once with retry
            for symbol in all_symbols:
                retry_count = 0
                while retry_count < 3:  # Try up to 3 times
                    try:
                        if symbol.startswith('.'):
                            # Subscribe to all required option Greeks for vanna and charm calculations
                            option_quote_types = [
                                QuoteType.GAMMA,     # For existing GEX calculation
                                QuoteType.OPEN_INT,  # For existing GEX calculation  
                                QuoteType.DELTA,     # For vanna and charm calculations
                                QuoteType.VEGA,      # For vanna calculation
                                QuoteType.THETA      # For charm calculation
                            ]
                            for quote_type in option_quote_types:
                                if self.client.subscribe(quote_type, symbol):
                                    success_count += 1
                        else:
                            if self.client.subscribe(QuoteType.LAST, symbol):
                                success_count += 1
                        break  # Success, exit retry loop
                    except Exception as sub_error:
                        retry_count += 1
                        if retry_count == 3:
                            error_msg = f"Failed to subscribe to {symbol} after 3 attempts: {str(sub_error)}"
                            subscription_errors.append(error_msg)
                        time.sleep(0.1)  # Short delay between retries
            
            if subscription_errors:
                self.data_queue.put({"error": "\n".join(subscription_errors)})
                return

            time.sleep(0.3)  # Wait for subscriptions to settle
            
            message_count = 0
            last_data = {}
            
            while not self.stop_event.is_set():
                pythoncom.PumpWaitingMessages()
                
                try:
                    with self.client._value_lock:
                        if self.client._latest_values:
                            current_data = {}
                            for topic_str, quote in self.client._latest_values.items():
                                symbol, quote_type = topic_str
                                key = f"{symbol}:{quote_type}"
                                current_data[key] = quote.value
                            
                            if current_data != last_data:
                                message_count += 1
                                while not self.data_queue.empty():
                                    try:
                                        self.data_queue.get_nowait()
                                    except:
                                        break
                                
                                self.data_queue.put(current_data)
                                last_data = current_data.copy()
                                
                except Exception as e:
                    pass
                
                time.sleep(1)

        except Exception as e:
            error_msg = f"RTD Error: {str(e)}"
            self.data_queue.put({"error": error_msg})
        finally:
            self.cleanup()

    def cleanup(self):
        if self.client:
            try:
                self.client.Disconnect()
                self.client = None
            except Exception as e:
                pass
        try:
            pythoncom.CoUninitialize()
        except Exception as e:
            pass
        self.initialized = False