import pandas as pd
import pandas_ta as ta # type: ignore # Assuming pandas_ta is installed and working
from typing import List, Optional, Dict, Any
from app.models.pydantic_models import PricePoint # Assuming PricePoint is correctly defined

def calculate_indicators_from_history(price_history: List[PricePoint]) -> Dict[str, Optional[float]]:
    # Default all to None
    results: Dict[str, Optional[float]] = {
        "rsi": None, "macd_line": None, "macd_signal": None,
        "macd_hist": None, "sma_short": None, "sma_long": None
    }

    if not price_history or len(price_history) < 2: # Need at least 2 for most calcs
        return results

    try:
        # Convert list of Pydantic models to DataFrame
        df = pd.DataFrame([p.model_dump() for p in price_history])
        if 'timestamp' in df.columns:
             df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
             df = df.set_index('timestamp')
        
        if df.empty or 'price' not in df.columns or df['price'].isnull().all():
            return results
        
        # Drop NaNs from price if any, as TA-Lib/pandas-ta might not handle them well for all indicators
        df_price = df['price'].dropna()
        if len(df_price) < 2:
            return results

        # SMA
        if len(df_price) >= 10: results["sma_short"] = round(ta.sma(df_price, length=10).iloc[-1], 2)
        if len(df_price) >= 30: results["sma_long"] = round(ta.sma(df_price, length=30).iloc[-1], 2)

        # RSI
        if len(df_price) >= 15: # 14 period + 1 for diff
            rsi_series = ta.rsi(df_price, length=14)
            if rsi_series is not None and not rsi_series.empty:
                 results["rsi"] = round(rsi_series.iloc[-1], 2)

        # MACD
        if len(df_price) >= 26: # Standard MACD requires enough data
            macd_df = ta.macd(df_price, fast=12, slow=26, signal=9)
            if macd_df is not None and not macd_df.empty:
                # Column names can vary slightly with pandas_ta versions for MACD
                # Common names: MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
                # Or: MACD_12_26_9, MACD_12_26_9_histogram, MACD_12_26_9_signal
                macd_col_name = next((col for col in macd_df.columns if 'MACD' in col and 'h' not in col and 's' not in col), None)
                hist_col_name = next((col for col in macd_df.columns if 'h' in col), None) # Histogram
                signal_col_name = next((col for col in macd_df.columns if 's' in col), None) # Signal

                if macd_col_name: results["macd_line"] = round(macd_df[macd_col_name].iloc[-1], 2)
                if hist_col_name: results["macd_hist"] = round(macd_df[hist_col_name].iloc[-1], 2)
                if signal_col_name: results["macd_signal"] = round(macd_df[signal_col_name].iloc[-1], 2)
    except Exception as e:
        print(f"Error calculating indicators: {e}") # Log error
        # Return defaults if any error occurs
        return {key: None for key in results}
        
    return results


def determine_trend(
    sma_short_current: Optional[float], sma_long_current: Optional[float],
    sma_short_previous: Optional[float], sma_long_previous: Optional[float]
) -> str:
    if sma_short_current is None or sma_long_current is None:
        return "Calculating..."

    current_short_above_long = sma_short_current > sma_long_current

    if sma_short_previous is not None and sma_long_previous is not None:
        previous_short_above_long = sma_short_previous > sma_long_previous
        if current_short_above_long and not previous_short_above_long:
            return "Bullish Crossover"
        if not current_short_above_long and previous_short_above_long:
            return "Bearish Crossover"
    
    if current_short_above_long:
        return "Uptrend"
    else:
        return "Downtrend"
    # Fallback, though one of the above should ideally be met
    # return "Neutral" # Or remove if Uptrend/Downtrend covers all non-crossover states


def generate_trade_idea(
    current_price: float,
    trend_signal: str,
    rsi_value: Optional[float],
    sentiment_label: str
) -> Dict[str, Any]:
    action = "HOLD"
    confidence = "None"
    reason_parts = []
    entry_price, stop_loss, take_profit = None, None, None

    rsi_val_safe = rsi_value if rsi_value is not None else 50 # Neutral RSI if unknown

    # BUY Conditions
    if ("Uptrend" in trend_signal or "Bullish" in trend_signal) and \
       (rsi_val_safe < 45) and \
       (sentiment_label == "Positive" or sentiment_label == "Neutral"):
        action = "BUY"
        confidence = "Medium" # Simplified confidence
        reason_parts.append(f"Trend: {trend_signal}.")
        reason_parts.append(f"RSI ({rsi_val_safe:.2f}) suggests room for upward movement.")
        if sentiment_label == "Positive": reason_parts.append("Positive sentiment.")

    # SELL Conditions
    elif ("Downtrend" in trend_signal or "Bearish" in trend_signal) and \
         (rsi_val_safe > 55) and \
         (sentiment_label == "Negative" or sentiment_label == "Neutral"):
        action = "SELL"
        confidence = "Medium" # Simplified confidence
        reason_parts.append(f"Trend: {trend_signal}.")
        reason_parts.append(f"RSI ({rsi_val_safe:.2f}) suggests room for downward movement.")
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
        reason_parts.append("Market conditions are neutral or signals are conflicting.")
    elif not reason_parts and action != "HOLD":
         reason_parts.append("Signal conditions met based on TA rules and sentiment.")


    return {
        "asset": "BTC/USD",
        "action": action,
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "confidence": confidence,
        "reason": " ".join(reason_parts) if reason_parts else "No clear signal."
    }