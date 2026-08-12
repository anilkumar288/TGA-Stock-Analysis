# US Stock Technical Analysis

A small Python CLI that downloads adjusted daily prices and calculates SMA 20/50/200,
MACD, RSI 14, Bollinger Bands, ATR 14, OBV, volume confirmation, and a simple composite
signal. The composite is a compact summary of the indicators—not a trading recommendation.

## Project approach and scope

This project was designed around a custom use case rather than following a fixed template or
single framework requirement. I selected a practical stock-analysis workflow that fits
research and education needs: load market data, inspect technical indicators, and present the
results in a usable interface.

The application was built with a custom web stack for this project, rather than requiring a
specific Streamlit setup. In this implementation, the UI is delivered with Flask and a browser-based
interface, while the analysis logic remains in Python. The workflow still reflects the same
core principles expected in a data-product build, but it was created as a solo, vibe-coded project:

- Load a dataset or market history for a symbol
- Use AI-assisted coding to accelerate development and iteration
- Add charts, filters, and tabular/summary views
- Improve the UX through iterative prompting and refinement
- Experiment with additional analysis workflows and display formats
- Optionally extend with AI-generated insights or narrative summaries

This project therefore represents a tailored solution for stock technical analysis, rather than a
generic demo or one-size-fits-all template.

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
