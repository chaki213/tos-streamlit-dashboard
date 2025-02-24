# app.py
import time
import threading
from queue import Queue
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from src.rtd.rtd_worker import RTDWorker
from src.llm.gemini_analyzer import GeminiAnalyzer
from src.trading.portfolio import Portfolio
from src.ui.dashboard_layout import DashboardLayout

def create_price_chart(data, symbol):
    """Create a price chart with Plotly"""
    if len(data) < 2:
        # Create an empty chart if not enough data
        fig = go.Figure()
        fig.update_layout(
            title=f"{symbol} Price",
            xaxis_title="Time",
            yaxis_title="Price ($)",
            height=400
        )
        return fig
    
    # Create the price chart
    fig = go.Figure()
    
    # Add the price line
    fig.add_trace(go.Scatter(
        x=data['timestamp'],
        y=data['price'],
        mode='lines',
        name='Price',
        line=dict(color='#00BFFF', width=2)
    ))
    
    # Add buy/sell markers if we have analysis history
    if st.session_state.analysis_history:
        buys = [a for a in st.session_state.analysis_history if a['decision'] == 'BUY']
        sells = [a for a in st.session_state.analysis_history if a['decision'] == 'SELL']
        
        if buys:
            buy_times = [b['timestamp'] for b in buys]
            buy_prices = [b['price'] for b in buys]
            fig.add_trace(go.Scatter(
                x=buy_times,
                y=buy_prices,
                mode='markers',
                name='Buy Signal',
                marker=dict(color='green', size=10, symbol='triangle-up')
            ))
            
        if sells:
            sell_times = [s['timestamp'] for s in sells]
            sell_prices = [s['price'] for s in sells]
            fig.add_trace(go.Scatter(
                x=sell_times,
                y=sell_prices,
                mode='markers',
                name='Sell Signal',
                marker=dict(color='red', size=10, symbol='triangle-down')
            ))
    
    # Layout improvements
    fig.update_layout(
        title=f"{symbol} Price",
        xaxis_title="Time",
        yaxis_title="Price ($)",
        height=400,
        template="plotly_dark",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def create_portfolio_chart(portfolio):
    """Create a portfolio value chart with Plotly"""
    history = portfolio.history
    
    if not history:
        # Create an empty chart if no history
        fig = go.Figure()
        fig.update_layout(
            title="Portfolio Value",
            xaxis_title="Time",
            yaxis_title="Value ($)",
            height=300
        )
        return fig
    
    # Convert history to DataFrame
    df = pd.DataFrame(history)
    
    # Create the portfolio chart
    fig = go.Figure()
    
    # Add the portfolio value line
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['total_value'],
        mode='lines',
        name='Portfolio Value',
        line=dict(color='#32CD32', width=2)
    ))
    
    # Add starting value reference line
    fig.add_shape(
        type="line",
        x0=df['timestamp'].min(),
        y0=100000,
        x1=df['timestamp'].max(),
        y1=100000,
        line=dict(color="gray", width=1, dash="dash"),
    )
    
    # Layout improvements
    fig.update_layout(
        title="Portfolio Value",
        xaxis_title="Time",
        yaxis_title="Value ($)",
        height=300,
        template="plotly_dark"
    )
    
    return fig

# Initialize session state
if 'initialized' not in st.session_state:
    print("Initializing")
    st.session_state.initialized = False
    st.session_state.data_queue = Queue()
    st.session_state.stop_event = threading.Event()
    st.session_state.active_thread = None
    st.session_state.price_history = pd.DataFrame(columns=['timestamp', 'price'])
    st.session_state.last_analysis_time = None
    st.session_state.analysis_interval = 60  # in seconds
    st.session_state.portfolio = Portfolio(initial_balance=100000)
    st.session_state.analysis_history = []
    st.session_state.last_price = None
    st.session_state.auto_trade = False

# Setup UI
DashboardLayout.setup_page("LLM Stock Trading Assistant")

# Create control section
symbol, analysis_interval, auto_trade, start_stop_button = DashboardLayout.create_input_section()

# Initialize LLM analyzer
if 'llm_analyzer' not in st.session_state:
    st.session_state.llm_analyzer = GeminiAnalyzer()

# Create metrics section
if st.session_state.initialized:
    current_price = st.session_state.last_price if st.session_state.last_price else 0
    portfolio = st.session_state.portfolio
    DashboardLayout.create_metrics_section(
        current_price=current_price,
        portfolio_value=portfolio.get_total_value(),
        portfolio_change=portfolio.get_percent_change(),
        position=portfolio.get_position_summary(symbol)
    )
else:
    DashboardLayout.create_metrics_section()

# Create placeholder for charts
price_chart_container = st.container()
with price_chart_container:
    price_chart = st.empty()

portfolio_chart_container = st.container()
with portfolio_chart_container:
    portfolio_chart = st.empty()

# Analysis history section
st.subheader("Analysis History")
analysis_container = st.container()

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
        st.session_state.last_analysis_time = None
        st.session_state.analysis_interval = analysis_interval
        st.session_state.auto_trade = auto_trade
        
        # Start with stock symbol to get price
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
        # Stop tracking
        st.session_state.stop_event.set()
        if st.session_state.active_thread:
            st.session_state.active_thread.join(timeout=1.0)
        st.session_state.active_thread = None
        st.session_state.initialized = False
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
                current_price = data.get(price_key, 0)
                
                if current_price and current_price > 0:
                    # Update price history
                    now = datetime.now()
                    new_row = pd.DataFrame([{
                        'timestamp': now, 
                        'price': float(current_price)
                    }])
                    
                    st.session_state.price_history = pd.concat([st.session_state.price_history, new_row], ignore_index=True)
                    st.session_state.last_price = float(current_price)
                    
                    # Update price chart
                    fig = create_price_chart(st.session_state.price_history, symbol)
                    price_chart.plotly_chart(fig, use_container_width=True)
                    
                    # Check if it's time for a new analysis
                    if (st.session_state.last_analysis_time is None or 
                        (now - st.session_state.last_analysis_time).total_seconds() >= st.session_state.analysis_interval):
                        
                        # Run LLM analysis
                        analysis_result = st.session_state.llm_analyzer.analyze(
                            symbol, 
                            st.session_state.price_history.copy(),
                            st.session_state.portfolio.get_position(symbol)
                        )
                        
                        # Record the analysis
                        analysis_record = {
                            'timestamp': now,
                            'price': float(current_price),
                            'decision': analysis_result['decision'],
                            'reasoning': analysis_result['reasoning']
                        }
                        st.session_state.analysis_history.insert(0, analysis_record)
                        
                        # Auto-execute trades if enabled
                        if st.session_state.auto_trade:
                            if analysis_result['decision'] == 'BUY':
                                # Buy with 25% of available cash
                                cash_to_use = st.session_state.portfolio.cash * 0.25
                                shares_to_buy = int(cash_to_use / current_price)
                                if shares_to_buy > 0:
                                    st.session_state.portfolio.buy(symbol, shares_to_buy, current_price)
                            elif analysis_result['decision'] == 'SELL':
                                # Sell 50% of current position
                                position = st.session_state.portfolio.get_position(symbol)
                                if position['shares'] > 0:
                                    shares_to_sell = int(position['shares'] * 0.5)
                                    if shares_to_sell > 0:
                                        st.session_state.portfolio.sell(symbol, shares_to_sell, current_price)
                        
                        # Update the last analysis time
                        st.session_state.last_analysis_time = now
                    
                    # Update portfolio chart
                    portfolio_fig = create_portfolio_chart(st.session_state.portfolio)
                    portfolio_chart.plotly_chart(portfolio_fig, use_container_width=True)
                    
                    # Update analysis history
                    with analysis_container:
                        for i, analysis in enumerate(st.session_state.analysis_history[:10]):  # Show last 10
                            with st.expander(
                                f"{analysis['timestamp'].strftime('%H:%M:%S')} - ${analysis['price']:.2f} - {analysis['decision']}",
                                expanded=(i == 0)
                            ):
                                st.write(analysis['reasoning'])
        
        # Rerun to keep updating
        time.sleep(2)  # Short delay to prevent excessive reruns
        if st.session_state.initialized:
            st.rerun()
            
    except Exception as e:
        st.error(f"Display Error: {str(e)}")
        print(f"Error details: {e}")