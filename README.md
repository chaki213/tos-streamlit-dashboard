# TOS Streamlit Dashboard

A real-time dashboard using ThinkorSwim's RTD (Real-Time Data) and Streamlit with Gamma Exposure, Vanna, and Charm analysis.

## Demo
https://github.com/user-attachments/assets/1d6446e0-5c49-4208-872f-f63a55da36a5

## Features

- **Real-time Gamma Exposure**: Live gamma exposure calculations and visualization
- **Vanna Analysis**: Real-time vanna exposure charts (volatility risk)
- **Charm Analysis**: Real-time charm exposure charts (time decay risk)
- **Black-Scholes Greeks**: Automatic calculation when RTD data unavailable
- **Dynamic Charts**: Switch between Gamma, Vanna, and Charm histograms
- **Live Data**: Direct integration with ThinkorSwim RTD feed

## Prerequisites

- Windows OS (required for ThinkorSwim RTD)
- Python 3.8+
- ThinkorSwim desktop application installed and running

## Installation

1. Clone the repository
```bash
git clone https://github.com/2187Nick/tos-streamlit-dashboard
cd tos-streamlit-dashboard
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. **Start ThinkorSwim** desktop application and log in

2. **Run the dashboard**:
```bash
# Using virtual environment (recommended)
.\.venv\Scripts\streamlit.exe run app.py

# Alternative if streamlit is globally installed
streamlit run app.py
```

3. **Open browser** and navigate to `http://localhost:8501`

## Interface Controls

### Basic Settings
- **Symbol**: Ticker symbol (e.g., "SPY")
- **Expiry Date**: Contract expiration date (Defaults to the nearest Friday)
- **Strike Range**: Range of strikes to monitor (Defaults to ±$20)
- **Strike Spacing**: Spacing between strikes (0.5, 1.0, 2.5, 5.0, 10.0, 25.0)
- **Refresh Rate**: Data refresh rate in seconds (1-300)
- **Start/Pause**: Toggle data streaming

### Chart Types
- **Default**: Gamma Exposure (green/red histogram)
- **Vanna**: Vanna exposure chart (purple histogram) - volatility risk
- **Charm**: Charm exposure chart (orange histogram) - time decay risk

*Note: Only one chart type can be selected at a time*

## Chart Features

- **Color-coded totals** in chart title
- **Real-time calculations** using Black-Scholes when needed
- **Strike annotations** showing max exposure levels
- **Current price line** indicator
- **Automatic scaling** in millions of dollars

## Notes

- Works with ThinkorSwim OnDemand for historical data analysis
- Exposure values displayed in millions of dollars
- Greeks calculated per 1% move in underlying asset (Gamma), 1% volatility move (Vanna), or per day (Charm)
- Real-time Black-Scholes calculation when RTD Greek data unavailable

## Troubleshooting

### "streamlit not recognized" error:
Use the virtual environment executable:
```bash
.\.venv\Scripts\streamlit.exe run app.py
```

### No data appearing:
1. Ensure ThinkorSwim is running and logged in
2. Check that the symbol and expiry date are valid
3. Verify market hours or use OnDemand mode

## Build
- This repo is a basic example. We hope you will build upon it and make it your own.
- If you build something, share it and we can keep a directory of projects.

## Credit
Backend:

[@FollowerOfFlow](https://x.com/FollowerOfFlow) worked some magic to get TOS RTD working directly with Python.

Check it out here: [pyrtdc](https://github.com/tifoji/pyrtdc/)

Gamma Exposure Calculations: [perfiliev](https://perfiliev.com/blog/how-to-calculate-gamma-exposure-and-zero-gamma-level/)

Black-Scholes Greeks Implementation: Built-in mathematical calculations for accurate option analytics

## Support
[@2187Nick](https://x.com/2187Nick)

[Discord](https://discord.com/invite/vxKepZ6XNC)

<br />
<div align="center">
  <p>Finding value in my work?</p>
  <a href="https://www.buymeacoffee.com/2187Nick" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>
</div>