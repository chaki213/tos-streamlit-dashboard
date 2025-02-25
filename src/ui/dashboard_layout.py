# src/ui/dashboard_layout.py
import streamlit as st
from datetime import datetime, timedelta

class DashboardLayout:
    @staticmethod
    def setup_page(title="LLM Stock Trading Assistant"):
        """Setup basic page layout"""
        # Set page configuration
        st.set_page_config(
            page_title=title,
            page_icon="📈",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # Add custom CSS styling
        st.markdown(DashboardLayout._get_custom_css(), unsafe_allow_html=True)
        
        st.markdown(f'<h1 class="main-title">{title}</h1>', unsafe_allow_html=True)
        st.markdown('<hr class="separator">', unsafe_allow_html=True)

    @staticmethod
    def create_input_section():
        """Create the control panel section for the trading app"""
        with st.container():
            st.markdown('<div class="control-panel-header">Trading Controls</div>', unsafe_allow_html=True)
            
            # Create columns for better organization
            col1, col2 = st.columns(2)
            
            # Trading controls
            with col1:
                st.markdown("### Basic Settings")
                symbol = st.text_input(
                    "Symbol",
                    value="SPY",
                    help="Enter the ticker symbol (e.g., SPY, AAPL, MSFT)"
                ).upper()
                
                analysis_interval = st.number_input(
                    "Analysis Interval (sec)",
                    value=60,
                    min_value=30,
                    max_value=300,
                    step=30,
                    help="How often to analyze price data and make decisions"
                )
                
                auto_trade = st.checkbox(
                    "Auto-Execute Trades",
                    value=False,
                    help="Automatically execute trades based on LLM recommendations"
                )
            
            # OnDemand controls
            with col2:
                st.markdown("### OnDemand Settings")
                use_on_demand = st.checkbox(
                    "Use TOS OnDemand",
                    value=False,
                    help="Use historical data from ThinkorSwim OnDemand mode"
                )
                
                on_demand_col1, on_demand_col2 = st.columns([3, 1])
                
                with on_demand_col1:
                    start_date = st.date_input(
                        "Start Date",
                        value=datetime.now().date() - timedelta(days=7),
                        disabled=not use_on_demand,
                        help="Date to begin historical data analysis"
                    )
                    
                with on_demand_col2:
                    start_time = st.time_input(
                        "Start Time",
                        value=datetime.strptime("09:30", "%H:%M").time(),
                        disabled=not use_on_demand,
                        help="Time to begin historical data analysis"
                    )
                
                speed_factor = st.slider(
                    "Replay Speed",
                    min_value=1.0,
                    max_value=10.0,
                    value=1.0,
                    step=0.5,
                    disabled=not use_on_demand,
                    help="Speed multiplier for historical data replay"
                )
            
            # Create start/stop button
            toggle_button = st.button(
                "Pause" if hasattr(st.session_state, 'initialized') and st.session_state.initialized else "Start Trading",
                type="primary" if not hasattr(st.session_state, 'initialized') or not st.session_state.initialized else "secondary",
                use_container_width=True,
                key="start_stop_button"
            )
        
        # Combine date and time for OnDemand
        on_demand_settings = None
        if use_on_demand:
            start_datetime = datetime.combine(start_date, start_time)
            on_demand_settings = {
                'use_on_demand': use_on_demand,
                'start_time': start_datetime,
                'speed_factor': speed_factor
            }
        
        # Add a status indicator and display OnDemand info if active
        if hasattr(st.session_state, 'initialized') and st.session_state.initialized:
            if hasattr(st.session_state, 'use_on_demand') and st.session_state.use_on_demand:
                # OnDemand status
                current_time = st.session_state.simulated_time.strftime("%Y-%m-%d %H:%M:%S") if hasattr(st.session_state, 'simulated_time') else "N/A"
                st.markdown(f'<div class="status-indicator active">ONDEMAND MODE - Current Time: {current_time} (Speed: {st.session_state.speed_factor}x)</div>', unsafe_allow_html=True)
            else:
                # Live status
                st.markdown('<div class="status-indicator active">LIVE TRADING</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-indicator inactive">INACTIVE</div>', unsafe_allow_html=True)
            
        return symbol, analysis_interval, auto_trade, toggle_button, on_demand_settings

    @staticmethod
    def create_metrics_section(current_price=None, portfolio_value=None, portfolio_change=None, position=None):
        """Create a metrics section to display key statistics"""
        if current_price is None or not hasattr(st.session_state, 'initialized') or not st.session_state.initialized:
            # Default placeholder metrics when not initialized
            cols = st.columns(4)
            with cols[0]:
                st.metric("Current Price", "—", "0%")
            with cols[1]:
                st.metric("Portfolio Value", "$100,000", "0%")
            with cols[2]:
                st.metric("Current Position", "—", "")
            with cols[3]:
                st.metric("LLM Recommendation", "—", "")
            return
            
        # Format the values for display
        price_delta = "0%"
        if hasattr(st.session_state, 'price_history') and len(st.session_state.price_history) > 1:
            prev_price = st.session_state.price_history.iloc[-2]['price'] if len(st.session_state.price_history) > 1 else current_price
            price_change = ((current_price - prev_price) / prev_price) * 100
            price_delta = f"{price_change:.2f}%"
        
        # Get latest recommendation
        latest_recommendation = "HOLD"
        if hasattr(st.session_state, 'analysis_history') and st.session_state.analysis_history:
            latest_recommendation = st.session_state.analysis_history[0]['decision']
        
        # Display metrics
        cols = st.columns(4)
        with cols[0]:
            st.metric(
                "Current Price",
                f"${current_price:.2f}",
                price_delta
            )
                
        with cols[1]:
            st.metric(
                "Portfolio Value",
                f"${portfolio_value:,.2f}",
                f"{portfolio_change:.2f}%",
                delta_color="normal"
            )
                
        with cols[2]:
            st.metric(
                "Current Position",
                position,
                ""
            )
                
        with cols[3]:
            if latest_recommendation == "BUY":
                st.metric(
                    "LLM Recommendation",
                    "BUY",
                    "",
                    delta_color="normal"
                )
            elif latest_recommendation == "SELL":
                st.metric(
                    "LLM Recommendation",
                    "SELL",
                    "",
                    delta_color="inverse"
                )
            else:
                st.metric(
                    "LLM Recommendation",
                    "HOLD",
                    "",
                    delta_color="off"
                )

    @staticmethod
    def show_loading_state():
        """Display a loading indicator"""
        with st.spinner("Connecting to ThinkorSwim RTD server..."):
            st.markdown(
                """
                <div class="loading-container">
                    <div class="loading-spinner"></div>
                    <div class="loading-text">Connecting to data feed...</div>
                </div>
                """, 
                unsafe_allow_html=True
            )

    @staticmethod
    def _get_custom_css():
        """Return custom CSS styles for the dashboard"""
        return """
        <style>
            /* === Dark Theme Optimizations === */
            .main-title {
                font-size: 2rem;
                margin-bottom: 0;
                color: #60b4ff;
                font-weight: 600;
            }
            
            .separator {
                margin-top: 0;
                margin-bottom: 10px;
                border: none;
                height: 1px;
                background: linear-gradient(to right, rgba(255,255,255,0), rgba(255,255,255,0.3), rgba(255,255,255,0));
            }
            
            /* === Control Panel === */
            .control-panel-header {
                font-size: 1.2rem;
                font-weight: 600;
                margin-bottom: 10px;
                color: #60b4ff;
                padding-bottom: 5px;
                border-bottom: 1px solid rgba(255,255,255,0.2);
            }
            
            /* Status Indicator */
            .status-indicator {
                display: inline-block;
                padding: 3px 10px;
                border-radius: 15px;
                font-size: 0.8rem;
                font-weight: 600;
                margin: 10px 0;
            }
            
            .status-indicator.active {
                background-color: rgba(0, 200, 0, 0.2);
                color: #00ff00;
                border: 1px solid rgba(0, 200, 0, 0.4);
            }
            
            .status-indicator.inactive {
                background-color: rgba(200, 0, 0, 0.2);
                color: #ff6b6b;
                border: 1px solid rgba(200, 0, 0, 0.3);
            }
            
            /* === General UI Improvements === */
            [data-testid="stStatusWidget"], [data-testid="stDeployButton"], footer {
                visibility: hidden;
            }
            
            /* === Loading Animation === */
            .loading-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 30px 0;
            }
            
            .loading-spinner {
                border: 5px solid rgba(96, 180, 255, 0.1);
                border-radius: 50%;
                border-top: 5px solid #60b4ff;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin-bottom: 10px;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .loading-text {
                color: #60b4ff;
                font-size: 0.9rem;
            }
            
            /* === Metric Panels === */
            [data-testid="stMetric"] {
                background-color: rgba(61, 61, 61, 0.6);
                border-radius: 5px;
                padding: 15px 10px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.3);
            }
            
            [data-testid="stMetric"] > div:first-child {
                margin-bottom: 5px;
            }
            
            [data-testid="stMetric"] > div:first-child p {
                font-weight: 600 !important;
                color: #60b4ff !important;
            }
            
            [data-testid="stMetricLabel"] {
                color: #dddddd !important;
            }
            
            [data-testid="stMetricValue"] {
                color: white !important;
            }
            
            /* === Chart Area === */
            [data-testid="stPlotlyChart"] {
                background-color: transparent !important;
                border-radius: 5px;
                padding: 10px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                margin-top: 10px;
            }
            
            /* === Button styling === */
            div.stButton > button {
                width: 100%;
                border-radius: 4px;
                font-weight: 600;
            }
            
            /* === Expander styling for dark theme === */
            [data-testid="stExpander"] {
                background-color: rgba(61, 61, 61, 0.6);
                border-radius: 5px;
                border: 1px solid rgba(255,255,255,0.1);
                margin-bottom: 10px;
            }
            
            /* Buy/Sell/Hold specific styling */
            .decision-buy {
                color: #32CD32 !important;
                font-weight: bold;
            }
            
            .decision-sell {
                color: #FF6347 !important;
                font-weight: bold;
            }
            
            .decision-hold {
                color: #FFA500 !important;
                font-weight: bold;
            }
            
            /* Styling for analysis history */
            .analysis-timestamp {
                color: #888888;
                font-size: 0.8rem;
            }
            
            .analysis-price {
                color: #60b4ff;
                font-weight: bold;
            }
            
            /* Override plotly background colors */
            .js-plotly-plot .plotly .main-svg {
                background-color: transparent !important;
            }
            
            .js-plotly-plot .plotly .bg {
                fill: rgba(30, 30, 30, 0.8) !important;
            }
            
            /* OnDemand mode styling */
            .ondemand-active {
                background-color: rgba(100, 149, 237, 0.2);
                color: #60b4ff;
                border: 1px solid rgba(100, 149, 237, 0.4);
                padding: 5px 10px;
                border-radius: 5px;
                margin: 10px 0;
            }
            
            /* Section headers */
            h3 {
                color: #60b4ff !important;
                font-size: 1.1rem !important;
                margin-bottom: 15px !important;
            }
        </style>
        """