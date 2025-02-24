# LLM-Powered Stock Trading Assistant

A real-time stock trading assistant that uses LLM (Gemini) to analyze market data and make trading decisions.

## Features

- Real-time stock price monitoring via ThinkorSwim (TOS) data feed
- Automated analysis through Google's Gemini LLM
- Portfolio tracking and performance visualization
- Trading history and decision logs
- Optional auto-execution of trades based on LLM recommendations

## Demo Screenshot

[Screenshot coming soon]

## Prerequisites

- Windows OS (required for ThinkorSwim RTD)
- Python 3.11+
- ThinkorSwim desktop application installed and running
- Gemini API key (get one at https://ai.google.dev/)

## Installation

1. Clone the repository
```bash
git clone https://github.com/2187Nick/llm-trading-assistant
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your Gemini API key:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

## Usage

1. Start ThinkorSwim desktop application and log in
2. Run the dashboard:
```bash
streamlit run app.py
```
3. Open the browser and navigate to `http://localhost:8501`

## Interface Controls

- **Symbol**: Ticker symbol to trade (e.g., "SPY")
- **Analysis Interval**: How often to analyze data and make decisions (in seconds)
- **Auto-Execute Trades**: Toggle automatic trade execution
- **Start/Stop Trading**: Begin/pause the trading assistant

## How It Works

1. The app connects to ThinkorSwim's Real-Time Data (RTD) service
2. Price data is collected at regular intervals
3. When analysis is triggered, the price data is sent to Gemini API
4. Gemini analyzes the data and makes a BUY/SELL/HOLD recommendation
5. If auto-trading is enabled, trades are executed based on recommendations
6. The portfolio is tracked and visualized in real-time

## Notes

- This is for educational purposes only. Use at your own risk.
- The LLM analysis is based only on recent price movements and does not incorporate fundamental analysis, news, or other market factors.
- Auto-trading uses simple rules (buys with 25% of available cash, sells 50% of position)

## Build On This

Some ideas for extending this project:
- Add support for multiple symbols simultaneously
- Incorporate news sentiment analysis
- Implement more sophisticated trading strategies
- Add backtesting capabilities
- Connect to a real brokerage API

## Build
- This repo is a basic example. We hope you will build upon it and make it your own.
- If you build something, share it and we can keep a directory of projects.

## Credits
This project was built upon the TOS-Streamlit-Dashboard by [@2187Nick](https://x.com/2187Nick)

Backend:

[@FollowerOfFlow](https://x.com/FollowerOfFlow) worked some magic to get TOS RTD working directly with Python.

Check it out here: [pyrtdc](https://github.com/tifoji/pyrtdc/)


## Support
[@2187Nick](https://x.com/2187Nick)

[Discord](https://discord.com/invite/vxKepZ6XNC)

<br />
<div align="center">
  <p>Finding value in my work?</p>
  <a href="https://www.buymeacoffee.com/2187Nick" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>
</div>