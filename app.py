#  app.py
import time
import threading
from queue import Queue
import streamlit as st
from src.rtd.rtd_worker import RTDWorker
from src.utils.option_symbol_builder import OptionSymbolBuilder
from src.ui.gamma_chart import GammaChartBuilder
from src.ui.dashboard_layout import DashboardLayout

# Initialize session state
if 'initialized' not in st.session_state:
    print("Initializing")
    st.session_state.initialized = False
    st.session_state.data_queue = Queue()
    st.session_state.stop_event = threading.Event()
    st.session_state.current_price = None
    st.session_state.option_symbols = []
    st.session_state.active_thread = None
    st.session_state.last_figure = None
    st.session_state.loading_complete = False
    st.session_state.debug_mode = False

# Setup UI
DashboardLayout.setup_page()

# Create control section
symbol, expiry_date, strike_range, strike_spacing, refresh_rate, start_stop_button = DashboardLayout.create_input_section()

# Only show metrics section at the top of the page
if st.session_state.initialized:
    try:
        last_data = st.session_state.get('last_data', None)
        if last_data:
            DashboardLayout.create_metrics_section(last_data)
        else:
            DashboardLayout.create_metrics_section()
    except Exception as e:
        DashboardLayout.create_metrics_section()
else:
    DashboardLayout.create_metrics_section()

# Create placeholder for chart
gamma_chart = st.empty()

# Initialize chart if needed
if 'chart_builder' not in st.session_state:
    st.session_state.chart_builder = GammaChartBuilder(symbol)
    st.session_state.last_figure = st.session_state.chart_builder.create_empty_chart()

if st.session_state.last_figure:
    chart_height = st.session_state.get('chart_height', 600)
    gamma_chart.plotly_chart(st.session_state.last_figure, use_container_width=True, height=chart_height, key="main_chart")

# Add insights panel at the bottom
DashboardLayout.create_insights_panel()

# Handle start/stop button clicks
if start_stop_button:
    if not st.session_state.initialized:
        # Show loading state
        DashboardLayout.show_loading_state()
        
        # Clean stop any existing thread
        if st.session_state.active_thread:
            st.session_state.stop_event.set()
            st.session_state.active_thread.join(timeout=2.0)
        
        # Reset state
        st.session_state.stop_event = threading.Event()
        st.session_state.data_queue = Queue()
        st.session_state.rtd_worker = RTDWorker(st.session_state.data_queue, st.session_state.stop_event)
        st.session_state.option_symbols = []  # Reset option symbols
        
        # Only reset chart if symbol changed
        if 'last_symbol' not in st.session_state or st.session_state.last_symbol != symbol:
            st.session_state.chart_builder = GammaChartBuilder(symbol)
            st.session_state.last_figure = st.session_state.chart_builder.create_empty_chart()
            chart_height = st.session_state.get('chart_height', 600)
            gamma_chart.plotly_chart(st.session_state.last_figure, use_container_width=True, height=chart_height, key="reset_chart")
            st.session_state.last_symbol = symbol
        
        # Start with stock symbol only to get price first
        try:
            thread = threading.Thread(
                target=st.session_state.rtd_worker.start,
                args=([symbol],),
                daemon=True
            )
            thread.start()
            st.session_state.active_thread = thread
            st.session_state.initialized = True
            time.sleep(0.5)  # Give time for initial connection
            st.rerun()
        except Exception as e:
            st.error(f"Failed to start RTD worker: {str(e)}")
            st.session_state.initialized = False
    else:
        # Stop tracking but keep the chart
        st.session_state.stop_event.set()
        if st.session_state.active_thread:
            st.session_state.active_thread.join(timeout=1.0)
        st.session_state.active_thread = None
        st.session_state.initialized = False
        st.session_state.loading_complete = False
        st.session_state.option_symbols = []  # Reset option symbols
        st.rerun()

# Display updates
if st.session_state.initialized:
    try:
        if not st.session_state.data_queue.empty():
            data = st.session_state.data_queue.get()
            
            if "error" in data:
                st.error(data["error"])
            elif "status" not in data:
                price_key = f"{symbol}:LAST"
                price = data.get(price_key)
                
                # Save the data for metrics display
                st.session_state.last_data = data
                
                if price:
                    # If we just got the price and don't have option symbols yet,
                    # restart with all symbols
                    if not st.session_state.option_symbols:
                        option_symbols = OptionSymbolBuilder.build_symbols(
                            symbol, expiry_date, price, strike_range, strike_spacing
                        )
                        
                        # Stop current thread
                        st.session_state.stop_event.set()
                        if st.session_state.active_thread:
                            st.session_state.active_thread.join(timeout=1.0)
                        
                        # Start new thread with all symbols
                        st.session_state.stop_event = threading.Event()
                        st.session_state.option_symbols = option_symbols
                        all_symbols = [symbol] + option_symbols
                        
                        # Create new RTD worker and thread
                        st.session_state.rtd_worker = RTDWorker(st.session_state.data_queue, st.session_state.stop_event)
                        thread = threading.Thread(
                            target=st.session_state.rtd_worker.start,
                            args=(all_symbols,),
                            daemon=True
                        )
                        thread.start()
                        st.session_state.active_thread = thread
                        time.sleep(0.2)
                
                # Update chart
                if st.session_state.option_symbols:
                    strikes = []
                    for sym in st.session_state.option_symbols:
                        if 'C' in sym:
                            strike_str = sym.split('C')[-1]
                            if '.5' in strike_str:
                                strikes.append(float(strike_str))
                            else:
                                strikes.append(int(strike_str))
                    strikes.sort()
                    
                    # Create and display updated chart
                    chart_height = st.session_state.get('chart_height', 600)
                    fig = st.session_state.chart_builder.create_chart(data, strikes, st.session_state.option_symbols)
                    st.session_state.last_figure = fig
                    gamma_chart.plotly_chart(fig, use_container_width=True, height=chart_height, key="update_chart")
                    
                    # Update only the metrics section at the top, not duplicating below chart
                    if not st.session_state.loading_complete:
                        st.session_state.loading_complete = True
                        st.rerun()  # Force a full rerun to update metrics
                    else:
                        time.sleep(refresh_rate)

                    if st.session_state.initialized:
                        st.rerun()
        else:
            if st.session_state.initialized:
                time.sleep(.5)
                st.rerun()
                
    except Exception as e:
        st.error(f"Display Error: {str(e)}")
        print(f"Error details: {e}")