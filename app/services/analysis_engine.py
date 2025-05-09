import pandas as pd
import pandas_ta as ta # type: ignore
from typing import List, Optional, Tuple
from app.models.pydantic_models import PricePoint

def calculate_indicators_from_history(price_history: List[PricePoint]):
    if not price_history or len(price_history) < 2: # Need at least 2 for some calcs
        return {
            "rsi": None, "macd_line": None, "macd_signal": None,
            "macd_hist": None, "sma_short": None, "sma_long": None
        }

    df = pd.DataFrame([p.model_dump() for p in price_history])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df = df.set_index('timestamp')

    if df.empty or 'price' not in df.columns or len(df['price']) < 2:
         return {
            "rsi": None, "macd_line": None, "macd_signal": None,
            "macd_hist": None, "sma_short": None, "sma_long": None
        }


    # SMA
    sma_short = df.ta.sma(length=10).iloc[-1] if len(df) >= 10 else None
    sma_long = df.ta.sma(length=30).iloc[-1] if len(df) >= 30 else None

    # RSI
    rsi = df.ta.rsi(length=14).iloc[-1] if len(df) >= 15 else None # 14 period + 1 for diff

    # MACD
    macd_data = None
    if len(df) >= 26: # Standard MACD requires enough data
        macd_df = df.ta.macd(fast=12, slow=26, signal=9)
        if macd_df is not None and not macd_df.empty:
            macd_data = {
                "macd_line": macd_df.iloc[-1, 0], # MACD_12_26_9
                "macd_hist": macd_df.iloc[-1, 1], # MACDh_12_26_9
                "macd_signal": macd_df.iloc[-1, 2] # MACDs_12_26_9
            }

    return {
        "rsi": round(rsi, 2) if rsi is not None else None,
        "macd_line": round(macd_data["macd_line"], 2) if macd_data and macd_data["macd_line"] is not None else None,
        "macd_signal": round(macd_data["macd_signal"], 2) if macd_data and macd_data["macd_signal"] is not None else None,
        "macd_hist": round(macd_data["macd_hist"], 2) if macd_data and macd_data["macd_hist"] is not None else None,
        "sma_short": round(sma_short, 2) if sma_short is not None else None,
        "sma_long": round(sma_long, 2) if sma_long is not None else None,
    }

def determine_trend(sma_short: Optional[float], sma_long: Optional[float],
                    prev_sma_short: Optional[float], prev_sma_long: Optional[float]) -> str:
    if sma_short is None or sma_long is None:
        return "Calculating..."

    # Simplified: requires previous values to detect crossover accurately.
    # For MVP, we might just indicate current state if prev values are hard to get without more state.
    # A more robust way would be to get the last two SMA values from the series.
    # This is a simplified version:
    current_short_above_long = sma_short > sma_long
    previous_short_above_long = (prev_sma_short > prev_sma_long) if prev_sma_short is not None and prev_sma_long is not None else None

    if previous_short_above_long is not None:
        if current_short_above_long and not previous_short_above_long:
            return "Bullish Crossover"
        if not current_short_above_long and previous_short_above_long:
            return "Bearish Crossover"

    if current_short_above_long:
        return "Uptrend"
    else:
        return "Downtrend"
    return "Neutral"


def generate_trade_idea(
    current_price: float,
    trend_signal: str,
    rsi_value: Optional[float],
    sentiment_label: str
):
    action = "HOLD"
    confidence = "None"
    reason_parts = []
    entry_price, stop_loss, take_profit = None, None, None

    # BUY Conditions
    if ("Uptrend" in trend_signal or "Bullish" in trend_signal) and \
       (rsi_value is not None and rsi_value < 45) and \
       (sentiment_label == "Positive" or sentiment_label == "Neutral"):
        action = "BUY"
        confidence = "Medium"
        reason_parts.append(f"Trend: {trend_signal}")
        reason_parts.append(f"RSI ({rsi_value:.2f}) suggests potential upward momentum.")
        if sentiment_label == "Positive": reason_parts.append("Positive sentiment.")

    # SELL Conditions
    elif ("Downtrend" in trend_signal or "Bearish" in trend_signal) and \
         (rsi_value is not None and rsi_value > 55) and \
         (sentiment_label == "Negative" or sentiment_label == "Neutral"):
        action = "SELL"
        confidence = "Medium"
        reason_parts.append(f"Trend: {trend_signal}")
        reason_parts.append(f"RSI ({rsi_value:.2f}) suggests potential downward momentum.")
        if sentiment_label == "Negative": reason_parts.append("Negative sentiment.")

    if action != "HOLD":
        entry_price = current_price
        if action == "BUY":
            stop_loss = round(entry_price * 0.985, 2) # 1.5% SL
            take_profit = round(entry_price * 1.03, 2)  # 3% TP (2:1 R:R)
        elif action == "SELL":
            stop_loss = round(entry_price * 1.015, 2) # 1.5% SL
            take_profit = round(entry_price * 0.97, 2)  # 3% TP

    if not reason_parts and action == "HOLD":
        reason_parts.append("No strong signal based on current rules.")
    elif not reason_parts: # Should not happen if action is not HOLD
        reason_parts.append("Conditions met for trade.")


    return {
        "asset": "BTC/USD",
        "action": action,
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "confidence": confidence,
        "reason": " ".join(reason_parts)
    }