"""Local web interface for the stock technical-analysis tool."""

from __future__ import annotations

import math
import re
from pathlib import Path
from urllib.parse import quote, urlparse

import pandas as pd
import yfinance as yf
from flask import Flask, render_template, request

from stock_analysis import build_report, build_scenario_map, calculate_indicators


app = Flask(__name__)
YFINANCE_CACHE_DIR = Path(app.instance_path) / "yfinance-cache"
YFINANCE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
yf.set_tz_cache_location(str(YFINANCE_CACHE_DIR))

PERIODS = {"6mo": "6 months", "1y": "1 year", "2y": "2 years", "5y": "5 years"}
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9^][A-Z0-9.^=-]{0,14}$")


def _company_profile(ticker: yf.Ticker, symbol: str) -> dict[str, str | None]:
    """Return display metadata without letting a profile failure block analysis."""
    try:
        info = ticker.get_info()
    except Exception:
        info = {}

    name = next(
        (info.get(key) for key in ("longName", "shortName", "displayName") if info.get(key)),
        symbol,
    )
    logo_url = info.get("logo_url") or None
    if not logo_url and info.get("website"):
        hostname = urlparse(info["website"]).hostname
        if hostname:
            logo_url = f"https://www.google.com/s2/favicons?domain={quote(hostname)}&sz=128"

    summary = str(info.get("longBusinessSummary") or "").strip()
    employees = info.get("fullTimeEmployees")
    industry = info.get("industry")
    sector = info.get("sector")
    country = info.get("country")
    city = info.get("city")

    # Yahoo's company summary often contains a genuinely distinctive detail.
    # Prefer founding/history, then what the business uniquely makes or does.
    sentences = re.split(r"(?<=[.!?])\s+", summary)
    interesting = next(
        (sentence for keywords in (
            ("founded", "incorporated", "formerly known"),
            ("operates", "serves", "develops", "manufactures", "provides", "offers"),
        ) for sentence in sentences if any(word in sentence.lower() for word in keywords)),
        None,
    )
    if interesting:
        fact = re.sub(r"^(The company|It)\b", str(name), interesting).strip()
        if len(fact) > 240:
            fact = fact[:237].rsplit(" ", 1)[0] + "..."
    elif city and country and industry:
        fact = f"{name} is a {industry.lower()} company headquartered in {city}, {country}."
    elif industry and country:
        fact = f"{name} is a {industry.lower()} company based in {country}."
    elif industry:
        fact = f"Yahoo Finance classifies {name} in the {industry} industry."
    elif sector:
        fact = f"{name} is part of the {sector} sector."
    elif isinstance(employees, (int, float)) and employees > 0:
        fact = f"{name} has grown to approximately {int(employees):,} employees worldwide."
    else:
        fact = f"{symbol} is the market shorthand traders use for {name}."

    return {"name": str(name), "logo_url": logo_url, "fun_fact": fact}


def _chart_data(df: pd.DataFrame) -> dict:
    view = df.tail(500)

    def values(column: str) -> list[float | None]:
        return [None if pd.isna(value) or not math.isfinite(float(value)) else round(float(value), 4)
                for value in view[column]]

    return {
        "dates": [index.strftime("%Y-%m-%d") for index in view.index],
        "close": values("Close"),
        "sma20": values("SMA_20"),
        "sma50": values("SMA_50"),
        "sma200": values("SMA_200"),
        "volume": values("Volume"),
        "rsi": values("RSI_14"),
    }


def _analyst_summary(ticker: yf.Ticker, symbol: str) -> dict[str, float | str | None]:
    """Return analyst target information when Yahoo exposes it."""
    try:
        info = ticker.get_info()
    except Exception:
        info = {}

    target_mean = info.get("targetMeanPrice")
    target_high = info.get("targetHighPrice")
    target_low = info.get("targetLowPrice")
    recommendation_mean = info.get("recommendationMean")
    recommendation_key = info.get("recommendationKey")

    return {
        "symbol": symbol,
        "target_mean": float(target_mean) if isinstance(target_mean, (int, float)) and math.isfinite(float(target_mean)) else None,
        "target_high": float(target_high) if isinstance(target_high, (int, float)) and math.isfinite(float(target_high)) else None,
        "target_low": float(target_low) if isinstance(target_low, (int, float)) and math.isfinite(float(target_low)) else None,
        "recommendation_mean": float(recommendation_mean) if isinstance(recommendation_mean, (int, float)) and math.isfinite(float(recommendation_mean)) else None,
        "recommendation_key": str(recommendation_key).title() if recommendation_key else None,
    }


@app.get("/")
def index():
    symbol = request.args.get("symbol", "").strip().upper()
    period = request.args.get("period", "2y")
    if period not in PERIODS:
        period = "2y"

    report = chart = company = analyst = scenario_map = error = None
    if symbol:
        if not SYMBOL_PATTERN.fullmatch(symbol):
            error = "Enter a valid ticker, such as AAPL, MSFT, or BRK-B."
        else:
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(period=period, interval="1d", auto_adjust=True)
                if data.empty:
                    raise ValueError(f"No price history was found for {symbol}.")
                df = calculate_indicators(data)
                if len(df) < 50:
                    raise ValueError("Not enough price history was returned for a reliable analysis.")
                report = build_report(symbol, df)
                scenario_map = build_scenario_map(symbol, df)
                chart = _chart_data(df)
                company = _company_profile(ticker, symbol)
                analyst = _analyst_summary(ticker, symbol)
            except Exception as exc:
                error = str(exc) or f"Unable to analyze {symbol} right now."

    return render_template(
        "index.html", symbol=symbol, period=period, periods=PERIODS,
        report=report, chart=chart, company=company, analyst=analyst,
        scenario_map=scenario_map, error=error,
    )


if __name__ == "__main__":
    app.run(debug=True)
