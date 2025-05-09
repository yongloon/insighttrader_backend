from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any # Added Any
import time
import asyncio
import logging # Added logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.models.pydantic_models import (
    MarketDataResponse, TradeIdea, IndicatorValues,
    Alert, AlertCreate # AlertBase is not directly used in endpoints
)
from app.services import market_simulator, analysis_engine

app = FastAPI(title="InsightTrader AI MVP")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], # Frontend URL, add both
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- In-memory storage for MVP ---
ACTIVE_ALERTS: Dict[str, Alert] = {}


async def background_price_simulator_task(interval_seconds: int = 5):
    """Periodically simulate a new price tick."""
    logger.info("Background price simulator task started.")
    while True:
        try:
            new_tick = market_simulator.simulate_new_tick()
            # logger.debug(f"New tick: {new_tick.price:.2f} at {time.strftime('%H:%M:%S', time.localtime(new_tick.timestamp))}")
        except Exception as e:
            logger.error(f"Error in background_price_simulator_task: {e}", exc_info=True)
            # Optionally, add a longer sleep here if there's a persistent error to avoid spamming logs
        await asyncio.sleep(interval_seconds)

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup event triggered.")
    # Start the background task for price simulation
    # Wrap the task creation in a try-except if task creation itself could fail (unlikely here)
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(background_price_simulator_task(5)) # Use event loop's create_task
        logger.info("Background price simulator task scheduled.")
    except Exception as e:
        logger.error(f"Failed to schedule background task: {e}", exc_info=True)


@app.get("/api/market-data", response_model=MarketDataResponse)
async def get_market_data_endpoint():
    try:
        price_history = market_simulator.get_price_history()
        current_price = market_simulator.get_current_btc_price()
        
        if not price_history: # Should be initialized by market_simulator module load
            logger.warning("Price history is empty in get_market_data_endpoint.")
            # Fallback or error response might be needed here depending on requirements
            # For now, proceed, calculate_indicators should handle empty history
            
        indicator_calcs_current = analysis_engine.calculate_indicators_from_history(price_history)
        
        prev_sma_short, prev_sma_long = None, None
        # Ensure there's enough history to get a "previous" set of indicators
        if len(price_history) > 1 : # At least 2 points to have a "previous" state for indicators
            indicator_calcs_previous = analysis_engine.calculate_indicators_from_history(price_history[:-1])
            prev_sma_short = indicator_calcs_previous.get('sma_short')
            prev_sma_long = indicator_calcs_previous.get('sma_long')

        trend = analysis_engine.determine_trend(
            indicator_calcs_current.get('sma_short'),
            indicator_calcs_current.get('sma_long'),
            prev_sma_short,
            prev_sma_long
        )
        
        sentiment = market_simulator.get_simulated_sentiment()

        return MarketDataResponse(
            asset="BTC/USD",
            current_price=round(current_price, 2),
            price_history=price_history,
            trend=trend,
            indicators=IndicatorValues(**indicator_calcs_current),
            sentiment=sentiment
        )
    except Exception as e:
        logger.error(f"Error in /api/market-data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error fetching market data.")


@app.get("/api/trade-idea", response_model=TradeIdea)
async def get_trade_idea_endpoint():
    try:
        # Fetch fresh market data to base the idea on
        market_data = await get_market_data_endpoint() 
        
        # Ensure that indicator values are not None before passing if your function expects numbers
        # The generate_trade_idea function was updated to handle Optional[float] for rsi_value
        idea_dict = analysis_engine.generate_trade_idea(
            current_price=market_data.current_price,
            trend_signal=market_data.trend,
            rsi_value=market_data.indicators.rsi, # This can be None
            sentiment_label=market_data.sentiment.sentiment_label
        )
        return TradeIdea(**idea_dict)
    except Exception as e:
        logger.error(f"Error in /api/trade-idea: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error generating trade idea.")


@app.post("/api/alerts", response_model=Alert, status_code=201)
async def create_alert(alert_in: AlertCreate):
    try:
        # id and created_at are auto-generated by Pydantic model default_factory
        new_alert = Alert(**alert_in.model_dump()) 
        # No, AlertCreate doesn't have id. We need to construct Alert fully
        # new_alert = Alert(id=str(uuid.uuid4()), asset="BTC/USD", triggered=False, created_at=time.time(), **alert_in.model_dump())

        # The Alert model itself handles id generation
        # If we want to ensure it's not a duplicate ID (highly unlikely with UUID4)
        # while new_alert.id in ACTIVE_ALERTS:
        #     new_alert.id = str(uuid.uuid4()) # Regenerate if somehow a clash

        ACTIVE_ALERTS[new_alert.id] = new_alert
        logger.info(f"Alert created: {new_alert.id} for price {new_alert.price_level} {new_alert.direction}")
        return new_alert
    except Exception as e:
        logger.error(f"Error creating alert: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error creating alert.")

@app.get("/api/check-alerts", response_model=List[Alert])
async def check_alerts_endpoint():
    try:
        triggered_alerts_to_return: List[Alert] = []
        current_price = market_simulator.get_current_btc_price()
        alerts_to_remove_ids: List[str] = []

        # Iterate over a copy of items for safe removal if needed, or just IDs
        for alert_id, alert_obj in list(ACTIVE_ALERTS.items()): 
            if not alert_obj.triggered: # Only check non-triggered alerts
                trigger = False
                if alert_obj.direction == "above" and current_price > alert_obj.price_level:
                    trigger = True
                elif alert_obj.direction == "below" and current_price < alert_obj.price_level:
                    trigger = True
                
                if trigger:
                    alert_obj.triggered = True # Mark as triggered
                    triggered_alerts_to_return.append(alert_obj)
                    alerts_to_remove_ids.append(alert_id) 
                    logger.info(f"Alert triggered and to be removed: {alert_id}")
            
        # Remove triggered alerts from active list
        for alert_id_to_remove in alerts_to_remove_ids:
            if alert_id_to_remove in ACTIVE_ALERTS:
                del ACTIVE_ALERTS[alert_id_to_remove]
                
        return triggered_alerts_to_return
    except Exception as e:
        logger.error(f"Error checking alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error checking alerts.")


@app.delete("/api/alerts/{alert_id}", status_code=204)
async def delete_alert(alert_id: str):
    if alert_id not in ACTIVE_ALERTS:
        logger.warning(f"Attempt to delete non-existent alert: {alert_id}")
        raise HTTPException(status_code=404, detail="Alert not found")
    try:
        del ACTIVE_ALERTS[alert_id]
        logger.info(f"Alert deleted: {alert_id}")
    except Exception as e: # Should not happen if check is done
        logger.error(f"Error deleting alert {alert_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error deleting alert.")
    return None # No content response for 204

# To run: uvicorn app.main:app --reload --port 8000
# Example for root endpoint if needed:
# @app.get("/")
# async def read_root():
#    logger.info("Root endpoint accessed.")
#    return {"message": "InsightTrader AI Backend is running!"}

logger.info("FastAPI application object created. Uvicorn will now complete startup.")