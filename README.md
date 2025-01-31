# TOS Streamlit Dashboard

A real-time options gamma exposure dashboard using ThinkorSwim's RTD (Real-Time Data) and Streamlit.

## Dashboard Preview
![Dashboard Preview](view.png)

## Features

- Real-time price updates
- Live visualizations
- Interactive Plotly charts

## Prerequisites

- Windows OS (required for ThinkorSwim RTD)
- Python 3.8+
- ThinkorSwim desktop application installed and running

## Installation

1. Clone the repository
```bash
git clone https://github.com/2187Nick/tos-streamlit-dashboard
```
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start ThinkorSwim desktop application and log in
2. Run the dashboard:
```bash
streamlit run app.py
```
3. Enter a symbol (e.g., "SPY")
4. Select expiry date
5. Set strike range
6. Click "Start" to begin real-time monitoring

## Interface Controls

- **Symbol**: Enter the ticker symbol
- **Expiry Date**: Select option expiration date
- **Strike Range**: Set the range of strikes to monitor (±)
- **Start/Stop**: Toggle data streaming

## Notes

- Updates every 3 seconds
- Gamma values are displayed in millions of dollars per 1% move

## Credit
https://x.com/FollowerOfFlow for his [pyrtdc](https://github.com/tifoji/pyrtdc/) project.
