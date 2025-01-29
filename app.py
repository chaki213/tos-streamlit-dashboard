import pythoncom
import time
import threading
import plotly.graph_objects as go
from datetime import date
from queue import Queue
from config.quote_types import QuoteType
from src.rtd.client import RTDClient
from src.core.settings import SETTINGS
import streamlit as st

# start button centered horizontally
# Add user setting to control the update frequency. Seconds
# Can we get the strike spacing or find all the strikes in range?
# handle spx and ndx and futures
# remove deploy button

# Must be the first Streamlit command
st.set_page_config(
    page_title="Live Dashboard",
    page_icon="🧊",
    menu_items={
        'Get Help': 'https://github.com/2187Nick/tos-streamlit-dashboard',
        'About': 'Gamma Exposure Dashboard',
    },
    layout="centered",
)

# Updated CSS to match button height with inputs
hide_streamlit_style = """
<style>
    [data-testid="stStatusWidget"] {visibility: hidden;}
    .stButton > button {
        width: 100%;
        height: 42px;  /* Match Streamlit input height */
        padding: 0;     /* Remove padding to prevent size issues */
        line-height: 42px;  /* Center text vertically */
        font-size: 14px;    /* Match input text size */
        margin-top: 0;      /* Remove top margin */
    }
    .stDeployButton {
        visibility: hidden;
    }
</style>
"""

st.markdown(hide_streamlit_style, unsafe_allow_html=True)

def rtd_worker(data_queue: Queue, stop_event: threading.Event, symbols: list):
    """RTD worker thread for price, gamma, and open interest"""
    client = None
    try:
        # Initialize COM
        pythoncom.CoInitialize()
        time.sleep(0.5)
        
        client = RTDClient(heartbeat_ms=SETTINGS['timing']['initial_heartbeat'])
        client.initialize()
        
        # Subscribe to all symbols
        for symbol in symbols:
            if symbol.startswith('.'):
                client.subscribe(QuoteType.GAMMA, symbol)
                client.subscribe(QuoteType.OPEN_INT, symbol)
            else:
                client.subscribe(QuoteType.ASK, symbol)
        
        while not stop_event.is_set():
            pythoncom.PumpWaitingMessages()
            
            try:
                with client._value_lock:
                    if client._latest_values:
                        data = {}
                        for topic_str, quote in client._latest_values.items():
                            symbol, quote_type = topic_str
                            key = f"{symbol}:{quote_type}"
                            data[key] = quote.value
                        if data:
                            data_queue.put(data)
            except Exception as e:
                print(f"Data processing error: {str(e)}")
            
            time.sleep(3) # 0.1

    except Exception as e:
        error_msg = f"RTD Error: {str(e)}"
        print(error_msg)
        data_queue.put({"error": error_msg})
    finally:
        if client:
            try:
                client.Disconnect()
            except:
                pass
        pythoncom.CoUninitialize()

# Initialize Streamlit app
st.title("Live Dashboard")

# Initialize session state first - before any UI elements
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
    st.session_state.data_queue = Queue()
    st.session_state.stop_event = threading.Event()
    st.session_state.current_price = None
    st.session_state.option_symbols = []
    st.session_state.options_initialized = False
    st.session_state.active_thread = None

# Modified layout section - adjust column widths and button placement
col1, col2, col3, button_col = st.columns([2, 2, 2, 1])
with col1:
    symbol = st.text_input("Enter Symbol:", value="SPY").upper()
with col2:
    expiry_date = st.date_input(
        "Expiry Date:",
        value=date.today(),
        format="MM/DD/YYYY"
    )
with col3:
    strike_range = st.number_input("Strike Range (±)", value=10, min_value=1, max_value=50)
with button_col:
    # Add container for better button positioning
    with st.container():
        start_stop_button = st.button(
            "Start" if not st.session_state.initialized else "Stop",
            use_container_width=True  # Makes button fill container
        )

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
        
        # Start with just the stock symbol
        thread = threading.Thread(
            target=rtd_worker,
            args=(st.session_state.data_queue, st.session_state.stop_event, [symbol]),
            daemon=True
        )
        thread.start()
        st.session_state.active_thread = thread
        st.session_state.initialized = True
    else:
        # Stop tracking
        st.session_state.stop_event.set()
        if st.session_state.active_thread:
            st.session_state.active_thread.join(timeout=1.0)
        st.session_state.active_thread = None
        st.session_state.initialized = False
        st.rerun()

# Display area
price_display = st.empty()

# Create a placeholder for the gamma exposure chart
gamma_chart = st.empty()

# Function to build option symbols
def build_option_symbols(base_symbol: str, expiry: date, current_price: float, strike_range: int):
    """
    Builds a list of option symbols for both calls and puts
    Returns: List of option symbols in ThinkorSwim format
    Example: .SPY250129C601
    """
    symbols = []
    base_strikes = range(
        int(current_price - strike_range), 
        int(current_price + strike_range + 1)
    )
    print(f"Base Strikes: {base_strikes}")
    
    for strike in base_strikes:
        # Format: .SYMBOL_YYMMDD{C/P}Strike
        date_str = expiry.strftime("%y%m%d")  # Changed to YYMMDD format
        #print(f"Date Str: {date_str}")
        strike_str = f"{strike}"  # Pad strike with zeros if needed
        call_symbol = f".{base_symbol}{date_str}C{strike_str}"
        #print(f"Call Symbol: {call_symbol}")
        put_symbol = f".{base_symbol}{date_str}P{strike_str}"
        symbols.extend([call_symbol, put_symbol])
    
    return symbols


# Then, update the update_gamma_chart function
def update_gamma_chart(data, strikes, option_symbols):
    """Update the plotly chart with real gamma data"""
    fig = go.Figure()
    
    pos_gex_values = []
    neg_gex_values = []
    
    # Get the underlying price first
    underlying_price = float(data.get(f"{symbol}:ASK", 0))
    if underlying_price == 0:
        return  # Don't update chart if we don't have a valid price
    
    for strike in strikes:
        # Look for both call and put gamma at this strike
        call_symbol = next(sym for sym in option_symbols if f'C{strike}' in sym)
        put_symbol = next(sym for sym in option_symbols if f'P{strike}' in sym)
        
        # Get raw gamma values
        call_gamma = float(data.get(f"{call_symbol}:GAMMA", 0))
        put_gamma = float(data.get(f"{put_symbol}:GAMMA", 0))
        call_oi = float(data.get(f"{call_symbol}:OPEN_INT", 0))
        put_oi = float(data.get(f"{put_symbol}:OPEN_INT", 0))
        
        # Calculate GEX using underlying price instead of strike
        gex = ((call_oi*call_gamma) - (put_oi*put_gamma)) * 100 * underlying_price
        
        if gex > 0:
            pos_gex_values.append(gex)
            neg_gex_values.append(0)
        else:
            pos_gex_values.append(0)
            neg_gex_values.append(gex)
    
    # Modified traces with explicit rounding of values
    pos_values = [round(x/1000000, 0) for x in pos_gex_values]
    neg_values = [round(x/1000000, 0) for x in neg_gex_values]
    
    # Find max values and their strikes
    max_pos_idx = pos_values.index(max(pos_values)) if any(pos_values) else -1
    max_neg_idx = neg_values.index(min(neg_values)) if any(neg_values) else -1
    
    max_pos_strike = strikes[max_pos_idx] if max_pos_idx >= 0 else None
    max_neg_strike = strikes[max_neg_idx] if max_neg_idx >= 0 else None
    
    # Add bar traces with names for legend
    fig.add_trace(go.Bar(
        x=pos_values,
        y=strikes,
        orientation='h',
        name='Positive GEX',  # Added name
        marker_color='green'
    ))
    
    fig.add_trace(go.Bar(
        x=neg_values,
        y=strikes,
        orientation='h',
        name='Negative GEX',  # Added name
        marker_color='red'
    ))
        
    # Fixed max value calculation with safety checks
    max_pos = max(pos_values) if pos_values else 0
    min_neg = min(neg_values) if neg_values else 0
    max_abs_value = max(abs(min_neg), abs(max_pos))
    
    # Ensure we have a non-zero range
    if max_abs_value == 0:
        max_abs_value = 1
        
    # Add padding to the range (30% on each side)
    padding = max_abs_value * 0.3
    chart_range = max_abs_value + padding
    
    # Adjust annotation positions based on padding
    annotation_offset = padding * 0.7  # 70% of padding for annotation offset
    
    # Add annotations for max values with adjusted positions
    if max_pos_idx >= 0 and max_pos > 0:
        fig.add_annotation(
            x=max_pos,
            y=max_pos_strike,
            text=f"+${max_pos}M @ {max_pos_strike}",
            showarrow=True,
            arrowhead=2,
            ax=min(40, annotation_offset * 30),  # Scale based on padding
            ay=0
        )
    
    if max_neg_idx >= 0 and min_neg < 0:
        fig.add_annotation(
            x=min_neg,
            y=max_neg_strike,
            text=f"-${abs(min_neg)}M @ {max_neg_strike}",
            showarrow=True,
            arrowhead=2,
            ax=max(-40, -annotation_offset * 30),  # Scale based on padding
            ay=0
        )
    
    fig.update_layout(
        title=f'{symbol} Gamma Exposure ($ per 1% move)',
        xaxis_title='Gamma Exposure ($M)',  # Added M to indicate millions
        yaxis_title='Strike Price',
        barmode='overlay',
        showlegend=True,  # Enable legend
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        height=600,
        xaxis=dict(
            range=[-chart_range, chart_range],  # Use padded range
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='black',
        )
    )
    
    gamma_chart.plotly_chart(fig)

# Display updates
if st.session_state.initialized:
    try:
        while True:
            if st.session_state.data_queue.empty():
                break
                
            data = st.session_state.data_queue.get()
            
            # Only show errors, not status messages
            if "error" in data:
                st.error(data["error"])
                continue
            # Remove status message handling
            if "status" in data:
                continue
            
            price_key = f"{symbol}:ASK"
            price = data.get(price_key)
            
            if price:
                st.session_state.current_price = price
                price_display.write(f"${price:.2f}")
                
                if not st.session_state.option_symbols:
                    option_symbols = build_option_symbols(
                        symbol, expiry_date, price, strike_range
                    )
                    st.session_state.option_symbols = option_symbols
                    
                    # Restart thread with all symbols
                    st.session_state.stop_event.set()
                    if st.session_state.active_thread:
                        st.session_state.active_thread.join(timeout=1.0)
                    
                    st.session_state.stop_event = threading.Event()
                    all_symbols = [symbol] + option_symbols
                    new_thread = threading.Thread(
                        target=rtd_worker,
                        args=(st.session_state.data_queue, st.session_state.stop_event, all_symbols),
                        daemon=True
                    )
                    new_thread.start()
                    st.session_state.active_thread = new_thread
            
            if st.session_state.option_symbols:
                strikes = sorted([
                    int(sym.split('C')[-1]) 
                    for sym in st.session_state.option_symbols 
                    if 'C' in sym
                ])
                update_gamma_chart(data, strikes, st.session_state.option_symbols)
            
            break

        time.sleep(3) # .1 second delay
        st.rerun()
        
    except Exception as e:
        st.error(f"Display Error: {str(e)}")
        print(f"Error details: {e}")


