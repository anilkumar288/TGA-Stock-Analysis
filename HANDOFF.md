# Project Handoff Document

## Project overview
This project is a Python-based stock analysis app for US-listed equities, focused on technical
analysis based on price action and chart indicators. It can be used in two ways:

- CLI analysis via `stock_analysis.py`
- Browser UI via `app.py`

The application downloads adjusted daily price data from Yahoo Finance, calculates common technical indicators, and produces a compact composite signal for research and educational use only. The dashboard also includes analyst-target context when available, such as mean target price, target range, and a simple analyst outlook summary.

## Project approach and delivery notes
This project was built around a genuine personal interest in stock market analysis rather than a business use case or a strict template requirement. I selected the problem of US stock technical screening and analysis based on price action and technicals, and implemented a custom solution around that workflow as a solo project.

The UI was built with a custom Python web stack rather than being forced into a Streamlit-only pattern. In this codebase, the interface uses Flask for the browser experience, while the data processing and indicator logic remain in Python. This is a valid, project-appropriate implementation and reflects the spirit of a practical data app build created through iterative, vibe-coded development.

The project also follows the broader expected development pattern for data-driven applications:

- Load a CSV or market-history dataset for analysis
- Use AI coding tools to speed up implementation and iteration
- Add charts, filters, tables, and exploratory output
- Refine the UX through iterative prompting and design feedback
- Explore additional analysis workflows such as different time ranges and signal summaries
- Add analyst-target context and broader market sentiment to complement the technical view
- Optionally add AI-powered explanations or summaries in future iterations

This documents the actual approach taken for the project rather than assuming a single prescribed stack or workflow.

## Current status
- Local Git repository is initialized.
- The app is working from the current codebase.
- No remote GitHub repository is configured yet.
- The project is intended for research/education and not as investment advice.

## Key files
- `stock_analysis.py` — core analysis logic, indicator calculations, scoring model, chart export
- `app.py` — Flask web interface for interactive use
- `templates/index.html` — web UI markup
- `static/` — CSS and JavaScript assets
- `README.md` — setup and usage instructions
- `requirements.txt` — Python dependencies

## How it works
The workflow is:

1. Fetch historical daily data for a ticker using `yfinance`.
2. Validate the returned dataset.
3. Compute indicators such as:
   - SMA 20/50/200
   - MACD
   - RSI 14
   - Bollinger Bands
   - ATR 14
   - OBV
   - volume confirmation
4. Optionally pull analyst target metadata from Yahoo Finance, including mean target price, target range, and consensus signal.
5. Build a composite score and plain-language summary for the current state.
6. Optionally display results in JSON, terminal output, or a saved PNG chart.

## App entry points
### CLI
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python stock_analysis.py AAPL
```
Optional flags:
```powershell
python stock_analysis.py MSFT --json
python stock_analysis.py NVDA --chart nvda_analysis.png
python stock_analysis.py BRK-B --period 5y
```

### Web UI
```powershell
.\.venv\Scripts\python.exe app.py
```
Then open:
```text
http://127.0.0.1:5000
```

## Dependencies
From `requirements.txt`:
- `yfinance`
- `pandas`
- `numpy`
- `matplotlib`
- `flask`

## Known project constraints
- Data comes from Yahoo Finance and may be delayed or temporarily unavailable.
- At least 50 daily observations are recommended for a meaningful technical view.
- The composite signal is a summary of indicators and not a trading recommendation.
- The app is designed as a local research tool rather than a production-grade financial system.

## Risks / watchouts
- External API failures from Yahoo Finance can break analysis requests.
- Some ticker symbols may return incomplete or sparse history.
- The website and CLI rely on the local environment and installed packages.
- The current logic uses a simplified scoring approach and should not be treated as a decision engine.

## Suggested next steps
- Add a proper `.gitignore` for local environment artifacts and output files if not already present.
- Add automated tests around indicator calculations and report generation.
- Add a remote repository and CI workflow for version control and deployment checks.
- Consider richer signal logic or user-configurable indicator thresholds.
- Harden UI error handling for invalid ticker input and market-data issues.

## Ownership and handoff notes
This project is currently in a working local state and is suitable for continued development or demo use. A future teammate should start by verifying the environment, installing dependencies, and running the CLI or app locally before making changes.

## Quick start reminder
```powershell
cd "<project-folder>"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python stock_analysis.py AAPL
```
