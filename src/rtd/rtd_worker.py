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

    def subscribe_additional_symbols(self, symbols: list) -> int:
        """Add new symbol subscriptions to existing RTD client."""
        success_count = 0
        for symbol in symbols:
            try:
                if symbol.startswith('.'):
                    if self.client.subscribe(QuoteType.GAMMA, symbol):
                        success_count += 1
                    if self.client.subscribe(QuoteType.OPEN_INT, symbol):
                        success_count += 1
                else:
                    print(f"Subscribing to LAST for {symbol}")
                    if self.client.subscribe(QuoteType.LAST, symbol):
                        success_count += 1
            except Exception as sub_error:
                print(f"Error subscribing to {symbol}: {str(sub_error)}")
        
        print(f"Successfully subscribed to {success_count} additional topics")
        return success_count

    def start(self, symbols: list):
        try:
            # We need this because RTDWorker runs in its own thread
            pythoncom.CoInitialize()
            
            # Increase initialization delay
            #print("RTD Worker: Sleeping for .1 seconds...")
            time.sleep(.2) # .1 seconds does work but lets go with .2 for now
            
            #print("RTD Worker: Creating RTDClient...")
            self.client = RTDClient(heartbeat_ms=SETTINGS['timing']['initial_heartbeat'])
            self.client.initialize()
            
            if not symbols:
                print("No symbols provided!")
                return
                
            #print(f"RTD Worker About to subscribe to symbols: {symbols}")
            success_count = 0
            # Subscribe to all symbols
            for symbol in symbols:
                try:
                    if symbol.startswith('.'):
                        #print(f"Subscribing to GAMMA and OPEN_INT for {symbol}")
                        if self.client.subscribe(QuoteType.GAMMA, symbol):
                            success_count += 1
                        if self.client.subscribe(QuoteType.OPEN_INT, symbol):
                            success_count += 1
                    else:
                        print(f"Subscribing to LAST for {symbol}")
                        if self.client.subscribe(QuoteType.LAST, symbol):
                            success_count += 1
                    #print(f"Successfully subscribed to {symbol}")
                except Exception as sub_error:
                    print(f"Error subscribing to {symbol}: {str(sub_error)}")
            
            print(f"Successfully subscribed to {success_count} topics")
            
            # Add delay after subscriptions
            #print("RTD Worker after subscribing.  Sleeping for .1 seconds...") # maybe less is ok?
            time.sleep(.1)
            
            #print("RTD Worker Starting main message listening loop")
            message_count = 0
            last_data = {}  # Track last known values
            
            while not self.stop_event.is_set():
                # Process COM messages
                pythoncom.PumpWaitingMessages()
                
                try:
                    with self.client._value_lock:
                        if self.client._latest_values:
                            current_data = {}
                            for topic_str, quote in self.client._latest_values.items():
                                symbol, quote_type = topic_str
                                key = f"{symbol}:{quote_type}"
                                current_data[key] = quote.value
                            
                            # Only update queue if values changed
                            if current_data != last_data:
                                message_count += 1
                                #print(f"Message #{message_count} - Data changed, updating queue")
                                
                                # Clear queue if it has old data
                                while not self.data_queue.empty():
                                    try:
                                        self.data_queue.get_nowait()
                                    except:
                                        break
                                
                                self.data_queue.put(current_data)
                                last_data = current_data.copy()
                                
                except Exception as e:
                    print(f"Data processing error: {str(e)}")
                
                # Sleep a reasonable amount between checks
                time.sleep(0.5)  # Check twice per second

        except Exception as e:
            error_msg = f"RTD Error: {str(e)}"
            print(error_msg)
            self.data_queue.put({"error": error_msg})
        finally:
            self.cleanup()
            print("RTDWorker cleanup complete")

    def cleanup(self):
        if self.client:
            try:
                print("Disconnecting RTDClient...")
                self.client.Disconnect()
            except Exception as e:
                print(f"Error during disconnect: {str(e)}")
        pythoncom.CoUninitialize()
