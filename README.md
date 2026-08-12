# US Stock Technical Analysis

A small Python CLI that downloads adjusted daily prices and calculates SMA 20/50/200,
MACD, RSI 14, Bollinger Bands, ATR 14, OBV, volume confirmation, and a simple composite
signal. The composite is a compact summary of the indicators—not a trading recommendation.

## Setup and usage

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python stock_analysis.py AAPL
```

Optional outputs:

```powershell
python stock_analysis.py MSFT --json
python stock_analysis.py NVDA --chart nvda_analysis.png
python stock_analysis.py BRK-B --period 5y
```

## Web interface

Start the local UI without activating the virtual environment:

```powershell
.\.venv\Scripts\python.exe app.py
```

Then open `http://127.0.0.1:5000` in your browser. Enter a ticker and choose a
time range to view price action, moving averages, key levels, and technical signals.

At least 50 daily observations are required. The default two-year period is needed to
make the 200-day trend and 52-week range useful. Data comes from Yahoo Finance through
`yfinance`, so it may be delayed or occasionally unavailable.

For research and education only. This has been created as part of an assignment for TGA.
