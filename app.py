# app.py
import time
import threading
from queue import Queue
import streamlit as st
from src.rtd.rtd_worker import RTDWorker
from src.utils.option_symbol_builder import OptionSymbolBuilder
from src.ui.gamma_chart import GammaChartBuilder
from src.ui.volatility_surface import VolatilitySurfaceBuilder
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
    st.session_state.expiration_dates = []

# Setup UI
DashboardLayout.setup_page()
symbol, view_type, expiry_date, strike_range, strike_spacing, refresh_rate, start_stop_button = DashboardLayout.create_input_section()

# Create placeholder for chart
chart_container = st.empty()

# Initialize charts if needed
if 'gamma_chart' not in st.session_state:
    st.session_state.gamma_chart = GammaChartBuilder(symbol)
if 'vol_surface' not in st.session_state:
    st.session_state.vol_surface = VolatilitySurfaceBuilder(symbol)

# Show appropriate chart
if view_type == "Gamma Exposure":
    if st.session_state.last_figure:
        chart_container.plotly_chart(st.session_state.last_figure, use_container_width=True, key="main_chart")
else:
    # Volatility Surface view
    if st.session_state.last_figure:
        chart_container.plotly_chart(st.session_state.last_figure, use_container_width=True, key="surface_chart")

# Handle start/stop button clicks
if start_stop_button:
    if not st.session_state.initialized:
        # Clean stop any existing thread
        if st.session_state.active_thread:
            st.session_state.stop_event.set()
            st.session_state.active_thread.join(timeout=2.0)
        
        # Reset state
        st.session_state.stop_event = threading.Event()
        st.session_state.data_queue = Queue()
        st.session_state.rtd_worker = RTDWorker(st.session_state.data_queue, st.session_state.stop_event)
        st.session_state.option_symbols = []
        st.session_state.expiration_dates = []
        
        # Only reset chart if symbol changed
        if 'last_symbol' not in st.session_state or st.session_state.last_symbol != symbol:
            st.session_state.gamma_chart = GammaChartBuilder(symbol)
            st.session_state.vol_surface = VolatilitySurfaceBuilder(symbol)
            st.session_state.last_figure = (st.session_state.gamma_chart.create_empty_chart() 
                                          if view_type == "Gamma Exposure" 
                                          else st.session_state.vol_surface.create_empty_chart())
            chart_container.plotly_chart(st.session_state.last_figure, use_container_width=True, key="reset_chart")
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
            time.sleep(0.5)
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
        st.session_state.option_symbols = []
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
                
                if price:
                    # If we just got the price and don't have option symbols yet,
                    # restart with all symbols
                    if not st.session_state.option_symbols:
                        if view_type == "Gamma Exposure":
                            option_symbols = OptionSymbolBuilder.build_symbols(
                                symbol, expiry_date, price, strike_range, strike_spacing
                            )
                            st.session_state.option_symbols = option_symbols
                            all_symbols = [symbol] + option_symbols
                        else:
                            # Get symbols for volatility surface
                            option_symbols, strikes, expiration_dates = OptionSymbolBuilder.build_surface_symbols(
                                symbol, price, strike_range, strike_spacing
                            )
                            st.session_state.option_symbols = option_symbols
                            st.session_state.strikes = strikes
                            st.session_state.expiration_dates = expiration_dates
                            print(f"expiration_dates: {expiration_dates}")
                            all_symbols = [symbol] + option_symbols
                        
                        # Stop current thread
                        st.session_state.stop_event.set()
                        if st.session_state.active_thread:
                            st.session_state.active_thread.join(timeout=1.0)
                        
                        # Start new thread with all symbols
                        st.session_state.stop_event = threading.Event()
                        
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
                
                # Update chart based on view type
                if st.session_state.option_symbols:
                    if view_type == "Gamma Exposure":
                        strikes = []
                        for sym in st.session_state.option_symbols:
                            if 'C' in sym:
                                strike_str = sym.split('C')[-1]
                                if '.5' in strike_str:
                                    strikes.append(float(strike_str))
                                else:
                                    strikes.append(int(strike_str))
                        strikes.sort()
                        
                        fig = st.session_state.gamma_chart.create_chart(
                            data, strikes, st.session_state.option_symbols
                        )
                    else:
                        # Create volatility surface
                        fig = st.session_state.vol_surface.create_chart(
                            data, 
                            st.session_state.strikes,
                            st.session_state.expiration_dates,
                            st.session_state.option_symbols
                        )
                    
                    st.session_state.last_figure = fig
                    chart_container.plotly_chart(fig, use_container_width=True, key="update_chart")

                    if not st.session_state.loading_complete:
                        st.session_state.loading_complete = True
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