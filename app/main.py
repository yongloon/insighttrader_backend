from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import time
import asyncio

from app.models.pydantic_models import (
    MarketDataResponse, TradeIdea, IndicatorValues,
    Alert, AlertCreate, AlertBase
)
from app.services import market_simulator, analysis_engine

app = FastAPI(title="InsightTrader AI MVP")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- In-memory storage for MVP ---
ACTIVE_ALERTS: Dict[str, Alert] = {}


async def background_price_simulator(interval_seconds: int = 5):
    """Periodically simulate a new price tick."""
    while True:
        market_simulator.simulate_new_tick()
        # print(f"New tick: {market_simulator.CURRENT_BTC_PRICE:.2f} at {time.strftime('%H:%M:%S')}")
        await asyncio.sleep(interval_seconds)

@app.on_event("startup")
async def startup_event():
    # Start the background task for price simulation
    asyncio.create_task(background_price_simulator(5)) # Simulate a new tick every 5 seconds


@app.get("/api/market-data", response_model=MarketDataResponse)
async def get_market_data_endpoint():
    price_history = market_simulator.get_price_history()
    current_price = market_simulator.get_current_btc_price()
    
    # For trend, we need previous SMAs. Let's get them from the history directly if possible
    # This is a simplification. For better accuracy, indicator calculation should handle this.
    indicator_calcs = analysis_engine.calculate_indicators_from_history(price_history)
    
    prev_sma_short, prev_sma_long = None, None
    if len(price_history) > 31: # Need enough data points for previous calculation
        prev_indicator_calcs = analysis_engine.calculate_indicators_from_history(price_history[:-1])
        prev_sma_short = prev_indicator_calcs.get('sma_short')
        prev_sma_long = prev_indicator_calcs.get('sma_long')

    trend = analysis_engine.determine_trend(
        indicator_calcs.get('sma_short'),
        indicator_calcs.get('sma_long'),
        prev_sma_short,
        prev_sma_long
    )
    
    sentiment = market_simulator.get_simulated_sentiment()

    return MarketDataResponse(
        asset="BTC/USD",
        current_price=round(current_price, 2),
        price_history=price_history,
        trend=trend,
        indicators=IndicatorValues(**indicator_calcs),
        sentiment=sentiment
    )

@app.get("/api/trade-idea", response_model=TradeIdea)
async def get_trade_idea_endpoint():
    market_data = await get_market_data_endpoint() # Reuse to get fresh data
    idea = analysis_engine.generate_trade_idea(
        current_price=market_data.current_price,
        trend_signal=market_data.trend,
        rsi_value=market_data.indicators.rsi,
        sentiment_label=market_data.sentiment.sentiment_label
    )
    return TradeIdea(**idea)

@app.post("/api/alerts", response_model=Alert, status_code=201)
async def create_alert(alert_in: AlertCreate):
    new_alert = Alert(**alert_in.model_dump())
    if new_alert.id in ACTIVE_ALERTS:
        raise HTTPException(status_code=400, detail="Alert with this ID already exists")
    ACTIVE_ALERTS[new_alert.id] = new_alert
    return new_alert

@app.get("/api/check-alerts", response_model=List[Alert])
async def check_alerts_endpoint():
    triggered_alerts_to_return: List[Alert] = []
    current_price = market_simulator.get_current_btc_price()
    alerts_to_remove_ids: List[str] = []

    for alert_id, alert_obj in list(ACTIVE_ALERTS.items()): # Iterate over a copy for safe removal
        if not alert_obj.triggered:
            trigger = False
            if alert_obj.direction == "above" and current_price > alert_obj.price_level:
                trigger = True
            elif alert_obj.direction == "below" and current_price < alert_obj.price_level:
                trigger = True
            
            if trigger:
                alert_obj.triggered = True
                triggered_alerts_to_return.append(alert_obj)
                alerts_to_remove_ids.append(alert_id) # Mark for removal after triggering

    for alert_id in alerts_to_remove_ids:
        if alert_id in ACTIVE_ALERTS:
            del ACTIVE_ALERTS[alert_id]
            
    return triggered_alerts_to_return

@app.delete("/api/alerts/{alert_id}", status_code=204)
async def delete_alert(alert_id: str):
    if alert_id not in ACTIVE_ALERTS:
        raise HTTPException(status_code=404, detail="Alert not found")
    del ACTIVE_ALERTS[alert_id]
    return None # No content response

# To run: uvicorn app.main:app --reload