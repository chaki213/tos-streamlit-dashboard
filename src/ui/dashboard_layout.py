import streamlit as st
from datetime import date, timedelta

class DashboardLayout:
    @staticmethod
    def _get_nearest_friday(from_date=None):
        """Get the nearest Friday from a given date"""
        if from_date is None:
            from_date = date.today()
        
        # If today is Friday (weekday 4), return today's date
        if from_date.weekday() == 4:
            return from_date
            
        # Get days until next Friday
        days_ahead = 4 - from_date.weekday()
        if days_ahead <= 0:  # If weekend
            days_ahead += 7
        return from_date + timedelta(days_ahead)

    @staticmethod
    def setup_page():
        """Setup basic page layout"""
        # Set page configuration
        st.set_page_config(
            page_title="TOS GEX Dashboard",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # Add custom CSS styling
        st.markdown(DashboardLayout._get_custom_css(), unsafe_allow_html=True)
        

        st.markdown('<h1 class="main-title">Live Gamma Exposure Dashboard</h1>', unsafe_allow_html=True)
        
        st.markdown('<hr class="separator">', unsafe_allow_html=True)

    @staticmethod
    def create_input_section():
        """Create the control panel section with improved layout"""
        # Create a container with styled box
        with st.container():
            st.markdown('<div class="control-panel-header">Dashboard Controls</div>', unsafe_allow_html=True)
            
            # Create two rows of controls for better organization
            row1_cols = st.columns([2, 2, 2, 2])
            row2_cols = st.columns([2, 2, 2, 2])
            
            # First row controls
            with row1_cols[0]:
                symbol = st.text_input(
                    "Symbol",
                    value="SPY",
                    help="Enter the ticker symbol (e.g., SPY, QQQ, AAPL)"
                ).upper()
                
            with row1_cols[1]:
                expiry_date = st.date_input(
                    "Expiry Date",
                    value=DashboardLayout._get_nearest_friday(),
                    format="MM/DD/YYYY",
                    help="Select the option expiration date"
                )
                
            with row1_cols[2]:
                strike_range = st.number_input(
                    "Strike Range $(±)",
                    value=10,
                    min_value=1,
                    max_value=500,
                    help="Range of strikes around current price to display"
                )
                
            with row1_cols[3]:
                strike_spacing = st.selectbox(
                    "Strike Spacing",
                    options=[0.5, 1.0, 2.5, 5.0, 10.0, 25.0],
                    index=1,  # Default to 1.0
                    help="The interval between adjacent strike prices"
                )
            
            # Second row controls
            with row2_cols[0]:
                refresh_rate = st.number_input(
                    "Refresh Rate (seconds)",
                    value=15,
                    min_value=1,
                    max_value=300,
                    help="How frequently to update the data from ThinkorSwim"
                )
                
            with row2_cols[1]:
                chart_height = st.slider(
                    "Chart Height",
                    min_value=400,
                    max_value=800,
                    value=600,
                    step=50,
                    help="Adjust the height of the chart"
                )
                
            with row2_cols[2]:
                chart_type = st.selectbox(
                    "Chart Type",
                    options=["Horizontal Bars", "Vertical Bars", "Area"],
                    index=0,
                    help="Select visualization style for gamma exposure"
                )
                
            with row2_cols[3]:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown('<div style="padding-top: 28px;">', unsafe_allow_html=True)
                    # Improved button with icon
                    toggle_button = st.button(
                        "Pause" if st.session_state.initialized else "Start",
                        type="primary" if not st.session_state.initialized else "secondary",
                        use_container_width=True,
                        key="start_stop_button"
                    )
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<div style="padding-top: 28px;">', unsafe_allow_html=True)
                    # Add a refresh button
                    refresh_button = st.button(
                        "↻",
                        help="Force refresh data",
                        use_container_width=True
                    )
                    st.markdown('</div>', unsafe_allow_html=True)
        
        # Add a status indicator
        if st.session_state.initialized:
            st.markdown('<div class="status-indicator active">LIVE DATA</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-indicator inactive">INACTIVE</div>', unsafe_allow_html=True)
            
        # Store additional settings in session state for use in other components
        if 'chart_height' not in st.session_state:
            st.session_state.chart_height = chart_height
        else:
            st.session_state.chart_height = chart_height
            
        if 'chart_type' not in st.session_state:
            st.session_state.chart_type = chart_type
        else:
            st.session_state.chart_type = chart_type
            
        return symbol, expiry_date, strike_range, strike_spacing, round(refresh_rate/2), toggle_button

    @staticmethod
    def create_metrics_section(data=None):
        """Create a metrics section to display key statistics"""
        if not data or not st.session_state.initialized:
            # Default placeholder metrics when not initialized
            cols = st.columns(4)
            with cols[0]:
                st.metric("Current Price", "—", "0%")
            with cols[1]:
                st.metric("Net GEX", "—", "0")
            with cols[2]:
                st.metric("Max Positive GEX", "—", "Strike: —")
            with cols[3]:
                st.metric("Max Negative GEX", "—", "Strike: —")
            return
            
        # Calculate metrics from data
        try:
            symbol = st.session_state.get('last_symbol', 'Unknown')
            current_price = float(data.get(f"{symbol}:LAST", 0))
            
            # Extract GEX data from session state
            pos_gex_sum = st.session_state.get('total_pos_gex', 0)
            neg_gex_sum = st.session_state.get('total_neg_gex', 0)
            total_gex = pos_gex_sum + neg_gex_sum
            
            # Format the values for display
            price_delta = st.session_state.get('price_change_pct', "0%")
            max_pos_gex = st.session_state.get('max_pos_gex', 0)
            max_pos_strike = st.session_state.get('max_pos_strike', 0)
            max_neg_gex = st.session_state.get('max_neg_gex', 0)
            max_neg_strike = st.session_state.get('max_neg_strike', 0)
            
            # Display metrics
            cols = st.columns(4)
            with cols[0]:
                st.metric(
                    "Current Price",
                    f"${current_price:.2f}",
                    price_delta,
                    delta_color="normal"
                )
                
            with cols[1]:
                st.metric(
                    "Net GEX",
                    f"${total_gex:.2f}M",
                    f"Positive: ${pos_gex_sum:.2f}M | Negative: ${abs(neg_gex_sum):.2f}M",
                    delta_color="off"
                )
                
            with cols[2]:
                st.metric(
                    "Max Positive GEX",
                    f"+${max_pos_gex:.2f}M",
                    f"Strike: ${max_pos_strike}",
                    delta_color="off"
                )
                
            with cols[3]:
                st.metric(
                    "Max Negative GEX", 
                    f"-${abs(max_neg_gex):.2f}M",
                    f"Strike: ${max_neg_strike}",
                    delta_color="off"
                )
                
        except Exception as e:
            st.error(f"Error calculating metrics: {str(e)}")
            st.error("Check if data is being received properly from ThinkorSwim.")

    @staticmethod
    def create_insights_panel():
        """Create a collapsible panel for insights and additional information"""
        with st.expander("📊 Market Insights & Information", expanded=False):
            tabs = st.tabs(["About GEX", "How to Use", "Interpretation", "Data Source"])
            
            with tabs[0]:
                st.markdown("""
                ## Gamma Exposure (GEX)
                
                **Gamma Exposure** represents the amount of shares that market makers need to buy or sell in response to 
                price movements in the underlying asset. This dashboard visualizes GEX in terms of millions of dollars 
                per 1% move in the underlying asset.

                * **Positive GEX (green)**: Market makers need to buy as price falls, providing support.
                * **Negative GEX (red)**: Market makers need to sell as price falls, potentially accelerating downside.
                """)
                
            with tabs[1]:
                st.markdown("""
                ## How to Use This Dashboard

                1. **Enter a symbol** - Type the ticker symbol for any equity or index (e.g., SPY, QQQ, AAPL)
                2. **Select expiry date** - Choose the option expiration date you want to analyze
                3. **Adjust strike range** - Set how far above and below current price to display
                4. **Click Start** - Begin streaming real-time data from ThinkorSwim

                **Note**: You must have the ThinkorSwim desktop application running for data connectivity.
                """)
                
            with tabs[2]:
                st.markdown("""
                ## Interpreting GEX Data

                ### Key Patterns to Watch:
                
                * **Large positive GEX at a price level**: Acts as support (harder for price to move below)
                * **Large negative GEX at a price level**: Acts as resistance or potential volatility accelerator 
                * **Zero GEX level**: Price may gravitate toward areas where GEX crosses from positive to negative
                * **Overall GEX profile**: Net positive GEX typically indicates lower volatility, net negative suggests higher volatility

                Remember that GEX is just one factor among many that affect market behavior.
                """)
                
            with tabs[3]:
                st.markdown("""
                ## Data Source Information

                * **Data Provider**: ThinkorSwim (TD Ameritrade) Real-Time Data (RTD)
                * **Calculation Method**: GEX = ((call_oi * call_gamma) - (put_oi * put_gamma)) * 100 * (price² * 0.01)
                * **Units**: Millions of dollars per 1% move in underlying price
                
                For more information on RTD integration, check out [pyrtdc](https://github.com/tifoji/pyrtdc/)
                """)

    @staticmethod
    def show_loading_state():
        """Display a loading indicator"""
        with st.spinner("Connecting to ThinkorSwim RTD server..."):
            st.markdown(
                """
                <div class="loading-container">
                    <div class="loading-spinner"></div>
                    <div class="loading-text">Fetching data from ThinkorSwim...</div>
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
            
            .logo-container {
                font-size: 2.5rem;
                text-align: center;
                margin-top: 10px;
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
            
            [data-testid="stMetricDelta"] {
                color: #aaaaaa !important;
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
            }
            
            /* Override plotly background colors */
            .js-plotly-plot .plotly .main-svg {
                background-color: transparent !important;
            }
            
            .js-plotly-plot .plotly .bg {
                fill: rgba(30, 30, 30, 0.8) !important;
            }
            
            /* Tabs in dark theme */
            .stTabs [data-baseweb="tab-list"] {
                background-color: rgba(30, 30, 30, 0.3);
                border-radius: 4px;
            }
            
            .stTabs [data-baseweb="tab"] {
                color: #dddddd;
            }
            
            .stTabs [aria-selected="true"] {
                color: #60b4ff;
                background-color: rgba(96, 180, 255, 0.1);
            }
            
            /* Fix for plotly overlays */
            .plotly.html-inner-div {
                background: transparent !important;
            }
            
            .plot-container.plotly {
                opacity: 1 !important;
            }
            
            .main-svg {
                opacity: 1 !important;
            }
        </style>
        """