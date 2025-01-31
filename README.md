# TOS Streamlit Dashboard

A real-time dashboard using ThinkorSwim's RTD (Real-Time Data) and Streamlit.

## Demo
https://github.com/user-attachments/assets/1d6446e0-5c49-4208-872f-f63a55da36a5


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
3. Open the browser and navigate to `http://localhost:8501`

## Interface Controls

- **Symbol**: Enter the ticker symbol (e.g., "SPY")
- **Expiry Date**: Select option expiration date (Defaults to the nearest Friday)
- **Strike Range**: Set the range of strikes to monitor (Defaults to +- $10)
- **Strike Spacing**: Set the spacing between strikes (Defaults to 1)
- **Refresh Rate**: Set the data refresh rate (Defaults to 15 seconds)
- **Start/Stop**: Toggle data streaming

## Notes

- This does work with Ondemand. Can use this on weekends to review historical data.
- Gamma values are displayed in millions of dollars per 1% move in underlying asset

## Credit
Backend:

https://x.com/FollowerOfFlow worked some magic to get RTD working directly with Python.

Check it out here: [pyrtdc](https://github.com/tifoji/pyrtdc/)
