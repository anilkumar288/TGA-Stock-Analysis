#!/usr/bin/env python3
"""Command-line technical analysis for a US-listed stock."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


def calculate_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """Return OHLCV data enriched with common technical indicators."""
    required = {"Close", "High", "Low", "Volume"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Price data is missing required columns: {', '.join(sorted(missing))}")
    if data.empty:
        raise ValueError("Price data is empty")

    df = data.copy()
    for column in required:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df = df.dropna(subset=["Close", "High", "Low", "Volume"])
    if df.empty:
        raise ValueError("Price data contains no valid numeric rows")
    close = df["Close"]
    for window in (20, 50, 200):
        df[f"SMA_{window}"] = close.rolling(window).mean()

    df["EMA_12"] = close.ewm(span=12, adjust=False).mean()
    df["EMA_26"] = close.ewm(span=26, adjust=False).mean()
    df["MACD"] = df["EMA_12"] - df["EMA_26"]
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_hist"] = df["MACD"] - df["MACD_signal"]

    change = close.diff()
    gain = change.clip(lower=0).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    loss = -change.clip(upper=0).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - 100 / (1 + rs)
    rsi = rsi.where(loss.ne(0), 100.0)
    # A period with neither gains nor losses is neutral, not overbought.
    df["RSI_14"] = rsi.where(gain.ne(0) | loss.ne(0), 50.0)

    middle = close.rolling(20).mean()
    std = close.rolling(20).std()
    df["BB_middle"] = middle
    df["BB_upper"] = middle + 2 * std
    df["BB_lower"] = middle - 2 * std

    previous_close = close.shift(1)
    true_range = pd.concat(
        [(df["High"] - df["Low"]), (df["High"] - previous_close).abs(),
         (df["Low"] - previous_close).abs()], axis=1
    ).max(axis=1)
    df["ATR_14"] = true_range.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    direction = np.sign(close.diff()).fillna(0)
    df["OBV"] = (direction * df["Volume"]).cumsum()
    df["Volume_SMA_20"] = df["Volume"].rolling(20).mean()
    return df


def _number(value: float) -> float | None:
    return None if pd.isna(value) or not math.isfinite(float(value)) else round(float(value), 4)


def _price_action_outlook(latest: pd.Series, previous: pd.Series, score: int) -> dict[str, str]:
    """Turn the indicator stack into a cautious, plain-language scenario."""
    price = float(latest["Close"])
    sma20 = float(latest["SMA_20"])
    sma50 = float(latest["SMA_50"])
    rsi = float(latest["RSI_14"])
    macd_hist = float(latest["MACD_hist"])
    prior_hist = float(previous["MACD_hist"])
    lower = float(latest["BB_lower"])
    upper = float(latest["BB_upper"])
    atr = float(latest["ATR_14"])

    if price > sma20 > sma50:
        trend = "Price is in a constructive short-term uptrend above the 20- and 50-day averages."
    elif price < sma20 < sma50:
        trend = "Price is in a weak short-term downtrend below the 20- and 50-day averages."
    else:
        trend = "Price is trading in a mixed structure around its short- and medium-term averages."

    if rsi >= 70:
        momentum = "Momentum is stretched, so a pause or pullback would be normal."
    elif rsi <= 30:
        momentum = "Momentum is washed out, which raises the chance of a relief bounce."
    elif macd_hist > prior_hist:
        momentum = "Momentum is improving, though confirmation still depends on follow-through."
    else:
        momentum = "Momentum is fading, so near-term follow-through may be limited."

    support = max(lower, min(sma20, sma50))
    resistance = upper
    if score >= 2:
        scenario = (f"The near-term bias is higher while price holds roughly ${support:.2f}; "
                    f"a sustained move above ${resistance:.2f} would strengthen the bullish case.")
        bias = "Bullish bias"
    elif score <= -2:
        scenario = (f"The near-term bias is lower unless price reclaims roughly ${sma20:.2f}; "
                    f"watch ${lower:.2f} as the next downside area.")
        bias = "Bearish bias"
    else:
        scenario = (f"Expect choppy or range-bound trade between roughly ${lower:.2f} and ${upper:.2f} "
                    "until price breaks that range with confirmation.")
        bias = "Mixed bias"

    return {
        "bias": bias,
        "comment": f"{trend} {momentum} {scenario}",
        "risk": f"Typical daily movement is about ${atr:.2f} based on 14-day ATR.",
    }


def build_report(symbol: str, df: pd.DataFrame) -> dict:
    if len(df) < 2:
        raise ValueError("At least two observations are required to build a report")

    latest = df.iloc[-1]
    previous = df.iloc[-2]
    score, signals = 0, []

    def signal(name: str, bullish: bool, bearish: bool, detail: str) -> None:
        nonlocal score
        label = "bullish" if bullish else "bearish" if bearish else "neutral"
        score += 1 if bullish else -1 if bearish else 0
        signals.append({"indicator": name, "signal": label, "detail": detail})

    price = float(latest["Close"])
    sma50, sma200 = latest["SMA_50"], latest["SMA_200"]
    signal("Price vs SMA 50", price > sma50, price < sma50,
           f"Close {price:.2f}; SMA 50 {sma50:.2f}")
    if pd.notna(sma200):
        signal("Long-term trend", price > sma200 and sma50 > sma200,
               price < sma200 and sma50 < sma200,
               f"SMA 50 {sma50:.2f}; SMA 200 {sma200:.2f}")
    macd, macd_signal = float(latest["MACD"]), float(latest["MACD_signal"])
    signal("MACD", macd > macd_signal and latest["MACD_hist"] > previous["MACD_hist"],
           macd < macd_signal and latest["MACD_hist"] < previous["MACD_hist"],
           f"MACD {macd:.2f}; signal {macd_signal:.2f}")
    rsi = float(latest["RSI_14"])
    signal("RSI (14)", 50 <= rsi < 70, rsi < 40 or rsi >= 70,
           f"RSI {rsi:.1f}" + (" (overbought)" if rsi >= 70 else " (oversold)" if rsi <= 30 else ""))
    signal("Volume", latest["Volume"] > 1.25 * latest["Volume_SMA_20"] and price > previous["Close"],
           latest["Volume"] > 1.25 * latest["Volume_SMA_20"] and price < previous["Close"],
           f"{latest['Volume'] / latest['Volume_SMA_20']:.2f}x 20-day average")

    rating = "Strong bullish" if score >= 4 else "Bullish" if score >= 2 else \
        "Strong bearish" if score <= -4 else "Bearish" if score <= -2 else "Neutral/mixed"
    return {
        "symbol": symbol,
        "as_of": df.index[-1].strftime("%Y-%m-%d"),
        "rating": rating,
        "score": score,
        "score_range": [-len(signals), len(signals)],
        "metrics": {
            "close": _number(price), "daily_change_pct": _number((price / previous["Close"] - 1) * 100),
            "sma_20": _number(latest["SMA_20"]), "sma_50": _number(sma50),
            "sma_200": _number(sma200), "ema_12": _number(latest["EMA_12"]),
            "ema_26": _number(latest["EMA_26"]), "rsi_14": _number(rsi), "macd": _number(macd),
            "macd_signal": _number(macd_signal), "atr_14": _number(latest["ATR_14"]),
            "bollinger_lower": _number(latest["BB_lower"]),
            "bollinger_upper": _number(latest["BB_upper"]),
            "52_week_low": _number(df["Low"].tail(252).min()),
            "52_week_high": _number(df["High"].tail(252).max()),
        },
        "signals": signals,
        "price_action": _price_action_outlook(latest, previous, score),
    }


def build_scenario_map(symbol: str, df: pd.DataFrame) -> dict:
    """Stress-test the composite signal across plausible next-session closes."""
    latest = df.iloc[-1]
    close = float(latest["Close"])
    atr = float(latest["ATR_14"])
    if not math.isfinite(atr) or atr <= 0:
        raise ValueError("A valid ATR is required to build the scenario map")

    scenarios = []
    for atr_move in (-2, -1, 0, 1, 2):
        hypothetical_close = max(0.01, close + atr_move * atr)
        next_index = df.index[-1] + pd.tseries.offsets.BDay(1)
        next_row = pd.DataFrame({
            "Close": [hypothetical_close],
            "High": [max(close, hypothetical_close)],
            "Low": [min(close, hypothetical_close)],
            "Volume": [float(latest["Volume_SMA_20"])],
        }, index=[next_index])
        source = pd.concat([df[["Close", "High", "Low", "Volume"]], next_row])
        scenario_report = build_report(symbol, calculate_indicators(source))
        scenarios.append({
            "atr_move": atr_move,
            "price": _number(hypothetical_close),
            "change_pct": _number((hypothetical_close / close - 1) * 100),
            "score": scenario_report["score"],
            "rating": scenario_report["rating"],
        })

    current = build_report(symbol, df)
    return {
        "atr": _number(atr), "current_score": current["score"],
        "current_rating": current["rating"], "scenarios": scenarios,
        "assumption": "Next-session close only; volume is held at its 20-day average.",
    }


def print_report(report: dict) -> None:
    m = report["metrics"]
    print(f"\n{report['symbol']} technical analysis - {report['as_of']}")
    print("=" * 52)
    print(f"Close: ${m['close']:.2f}  Daily change: {m['daily_change_pct']:+.2f}%")
    print(f"52-week range: ${m['52_week_low']:.2f} - ${m['52_week_high']:.2f}")
    print(f"SMA 20/50/200: {m['sma_20']:.2f} / {m['sma_50']:.2f} / " +
          (f"{m['sma_200']:.2f}" if m['sma_200'] is not None else "N/A"))
    print(f"EMA 12/26: {m['ema_12']:.2f} / {m['ema_26']:.2f}")
    print(f"RSI 14: {m['rsi_14']:.1f}  MACD/signal: {m['macd']:.2f}/{m['macd_signal']:.2f}")
    print(f"ATR 14: ${m['atr_14']:.2f}  Bollinger band: ${m['bollinger_lower']:.2f} - ${m['bollinger_upper']:.2f}")
    print(f"\nComposite: {report['rating']} ({report['score']:+d})")
    for item in report["signals"]:
        print(f"  {item['signal'].upper():7} {item['indicator']}: {item['detail']}")
    print("\nFor research/education only; this is not investment advice.")


def save_chart(symbol: str, df: pd.DataFrame, path: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("Charting requires matplotlib: pip install matplotlib") from exc
    view = df.tail(252)
    fig, (price_ax, rsi_ax) = plt.subplots(2, 1, figsize=(12, 8), sharex=True,
                                                   gridspec_kw={"height_ratios": [3, 1]})
    price_ax.plot(view.index, view["Close"], label="Close", linewidth=1.5)
    for n in (20, 50, 200):
        price_ax.plot(view.index, view[f"SMA_{n}"], label=f"SMA {n}", linewidth=1)
    price_ax.fill_between(view.index, view["BB_lower"], view["BB_upper"], alpha=.1, label="Bollinger bands")
    price_ax.set_title(f"{symbol} - Technical Analysis"); price_ax.set_ylabel("Price ($)")
    price_ax.grid(alpha=.25); price_ax.legend(ncol=3)
    rsi_ax.plot(view.index, view["RSI_14"], color="purple", label="RSI 14")
    rsi_ax.axhline(70, color="red", linestyle="--", linewidth=.8)
    rsi_ax.axhline(30, color="green", linestyle="--", linewidth=.8)
    rsi_ax.set_ylim(0, 100); rsi_ax.set_ylabel("RSI"); rsi_ax.grid(alpha=.25)
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description="Technical analysis for a US stock symbol")
    parser.add_argument("symbol", help="US ticker, e.g. AAPL, MSFT, or BRK-B")
    parser.add_argument("--period", default="2y", help="History period accepted by yfinance (default: 2y)")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument("--chart", type=Path, metavar="FILE", help="Save a PNG chart")
    args = parser.parse_args()
    symbol = args.symbol.strip().upper()
    try:
        data = yf.Ticker(symbol).history(period=args.period, interval="1d", auto_adjust=True)
        if data.empty:
            raise ValueError(f"No price history found for {symbol}; check the symbol")
        df = calculate_indicators(data)
        if len(df) < 50:
            raise ValueError(f"Only {len(df)} valid observations returned; use a period of at least 3mo")
        report = build_report(symbol, df)
        print(json.dumps(report, indent=2) if args.json else "", end="" if args.json else "")
        if not args.json:
            print_report(report)
        if args.chart:
            args.chart.parent.mkdir(parents=True, exist_ok=True)
            save_chart(symbol, df, args.chart)
            if not args.json:
                print(f"Chart saved to {args.chart}")
        return 0
    except (ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Unable to retrieve/analyze {symbol}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
