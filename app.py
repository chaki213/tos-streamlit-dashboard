import time
import threading
from queue import Queue
import streamlit as st
from src.rtd.rtd_worker import RTDWorker
from src.utils.option_symbol_builder import OptionSymbolBuilder
from src.ui.gamma_chart import GammaChartBuilder
from src.ui.dashboard_layout import DashboardLayout

# Initialize session state before anything else
if 'initialized' not in st.session_state:
    print("Initializing")
    st.session_state.initialized = False
    st.session_state.data_queue = Queue()
    st.session_state.stop_event = threading.Event()
    st.session_state.current_price = None
    st.session_state.option_symbols = []
    st.session_state.active_thread = None
    st.session_state.last_figure = None  # Add storage for last figure
    st.session_state.loading_complete = False  # Add new state variable

# Setup UI
DashboardLayout.setup_page()
symbol, expiry_date, strike_range, strike_spacing, refresh_rate, start_stop_button = DashboardLayout.create_input_section()

# Create placeholder for chart
gamma_chart = st.empty()

# Remove the redundant chart initialization - we only need this once
if 'chart_builder' not in st.session_state:
    st.session_state.chart_builder = GammaChartBuilder(symbol)
    st.session_state.last_figure = st.session_state.chart_builder.create_empty_chart()

# Always show last chart - this is all we need for chart display
if st.session_state.last_figure:
    gamma_chart.plotly_chart(st.session_state.last_figure, use_container_width=True, key="main_chart")

# Handle start/stop button clicks
if start_stop_button:
    if not st.session_state.initialized:
        # Clean stop any existing thread
        if st.session_state.active_thread:
            st.session_state.stop_event.set()
            st.session_state.active_thread.join(timeout=1.0)
        
        # Reset state
        st.session_state.stop_event = threading.Event()
        st.session_state.data_queue = Queue()
        st.session_state.option_symbols = []
        st.session_state.phase = "stock_only"
        st.session_state.rtd_worker = RTDWorker(st.session_state.data_queue, st.session_state.stop_event)
        
        # Only reset chart if symbol changed
        if 'last_symbol' not in st.session_state or st.session_state.last_symbol != symbol:
            st.session_state.chart_builder = GammaChartBuilder(symbol)
            st.session_state.last_figure = st.session_state.chart_builder.create_empty_chart()
            gamma_chart.plotly_chart(st.session_state.last_figure, use_container_width=True, key="reset_chart")
            st.session_state.last_symbol = symbol
        
        # Start with just the stock symbol
        thread = threading.Thread(
            target=st.session_state.rtd_worker.start,
            args=([symbol],),
            daemon=True
        )
        thread.start()
        st.session_state.active_thread = thread
        st.session_state.initialized = True
        st.rerun()  # Update button state
    else:
        # Stop tracking but keep the chart
        st.session_state.stop_event.set()
        if st.session_state.active_thread:
            st.session_state.active_thread.join(timeout=1.0)
        st.session_state.active_thread = None
        st.session_state.initialized = False
        st.session_state.phase = None
        st.session_state.loading_complete = False
        st.rerun() 

# Display updates
if st.session_state.initialized:
    try:
        # Initially we are waiting on data. Once we get the stock price, we can subscribe to options
        # and fill in the chart with data etc.
        if not st.session_state.data_queue.empty():
            #print("Update chart loop: Data queue not empty")
            data = st.session_state.data_queue.get()
            
            if "error" in data:
                st.error(data["error"])
            elif "status" not in data:
                price_key = f"{symbol}:LAST"
                price = data.get(price_key)
                
                # Transition from stock-only to all symbols
                if price and st.session_state.phase == "stock_only":
                    #print("Update chart loop: Adding option symbol subscriptions to existing RTD worker")
                    option_symbols = OptionSymbolBuilder.build_symbols(
                        symbol, expiry_date, price, strike_range, strike_spacing,
                    )
                    st.session_state.option_symbols = option_symbols
                    st.session_state.rtd_worker.subscribe_additional_symbols(option_symbols)
                    st.session_state.phase = "all_symbols"
                    #print(f"Subscribed to {len(option_symbols)} option symbols")
                    #print("Update chart loop: Sleeping for 0.1 seconds. We finally got options data!!...")
                    time.sleep(0.1)
                
                # Update chart
                if st.session_state.option_symbols:
                    # Improved strike price parsing
                    strikes = []
                    for sym in st.session_state.option_symbols:
                        if 'C' in sym:
                            strike_str = sym.split('C')[-1]
                            # Handle .5 strikes specially
                            if '.5' in strike_str:
                                strikes.append(float(strike_str))
                            else:
                                strikes.append(int(strike_str))
                    strikes.sort()
                    
                    fig = st.session_state.chart_builder.create_chart(data, strikes, st.session_state.option_symbols)
                    st.session_state.last_figure = fig  # Store figure before displaying
                    gamma_chart.plotly_chart(fig, use_container_width=True, key="update_chart")

                    # Use shorter sleep during initial loading
                    if not st.session_state.loading_complete:
                        #time.sleep(0.5)
                        st.session_state.loading_complete = True
                    else:
                        time.sleep(refresh_rate)

                    if st.session_state.initialized:
                        st.rerun()  # Only rerun if still running
        else:
            if st.session_state.initialized:
                #print("Update chart loop: Data queue empty. Sleeping for 1 second...\n\n")
                time.sleep(.5)
                st.rerun() 
                
    except Exception as e:
        st.error(f"Display Error: {str(e)}")
        print(f"Error details: {e}")



