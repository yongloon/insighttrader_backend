import random
import time
from typing import List, Dict, Any
from app.models.pydantic_models import PricePoint, SentimentData

MAX_HISTORY_LENGTH = 200
INITIAL_BTC_PRICE = 65000.0
SIMULATED_PRICE_HISTORY: List[PricePoint] = []
CURRENT_BTC_PRICE = INITIAL_BTC_PRICE # Will be updated by first call to simulate_new_tick


# Initialize with some plausible historical data
def _initialize_history():
    global CURRENT_BTC_PRICE, SIMULATED_PRICE_HISTORY
    # Ensure this runs only once or is idempotent if module is reloaded
    if SIMULATED_PRICE_HISTORY:
        return

    price_val = INITIAL_BTC_PRICE
    current_ts = time.time()
    for i in range(MAX_HISTORY_LENGTH):
        # Simulate prices going backwards in time from 'now'
        timestamp = current_ts - (MAX_HISTORY_LENGTH - 1 - i) * 60 # 1 minute intervals
        price_val += random.uniform(-50, 50) * ((i / MAX_HISTORY_LENGTH) * 0.5 + 0.5) # Smaller fluctuations for older data
        price_val = max(10000, price_val) # Floor price
        SIMULATED_PRICE_HISTORY.append(PricePoint(timestamp=timestamp, price=round(price_val, 2)))
    
    if SIMULATED_PRICE_HISTORY:
        CURRENT_BTC_PRICE = SIMULATED_PRICE_HISTORY[-1].price
    else: # Should not happen if MAX_HISTORY_LENGTH > 0
        CURRENT_BTC_PRICE = INITIAL_BTC_PRICE
        SIMULATED_PRICE_HISTORY.append(PricePoint(timestamp=current_ts, price=round(CURRENT_BTC_PRICE, 2)))


MOCK_TWEETS: List[Dict[str, Any]] = [
    {"text": "BTC soaring! To the moon we go! 🚀 #Bitcoin", "sentiment_score": 0.9, "sentiment_label": "Positive"},
    {"text": "Looks like BTC is consolidating around its current price. Neutral for now.", "sentiment_score": 0.1, "sentiment_label": "Neutral"},
    {"text": "Big drop in BTC, a bit worried. Holding off for now. #CryptoCrash", "sentiment_score": -0.8, "sentiment_label": "Negative"},
    {"text": "Analyst predicts BTC will hit 70k soon. Very bullish!", "sentiment_score": 0.75, "sentiment_label": "Positive"},
    {"text": "Not sure about BTC at these levels, might see a correction.", "sentiment_score": -0.4, "sentiment_label": "Negative"},
]

def get_current_btc_price() -> float:
    return CURRENT_BTC_PRICE

def get_price_history() -> List[PricePoint]:
    return SIMULATED_PRICE_HISTORY

def simulate_new_tick() -> PricePoint:
    global CURRENT_BTC_PRICE, SIMULATED_PRICE_HISTORY

    if not SIMULATED_PRICE_HISTORY: # Ensure history is initialized
        _initialize_history()
        # If still empty (e.g., MAX_HISTORY_LENGTH was 0), seed it
        if not SIMULATED_PRICE_HISTORY:
            SIMULATED_PRICE_HISTORY.append(PricePoint(price=INITIAL_BTC_PRICE))


    price_change = random.uniform(-150, 150) 
    drift_factor = random.choice([-0.0002, -0.0001, 0, 0.0001, 0.0002, 0.0003])
    
    # Update current price based on the last known price or initial if history is somehow still empty
    last_price = SIMULATED_PRICE_HISTORY[-1].price if SIMULATED_PRICE_HISTORY else INITIAL_BTC_PRICE
    CURRENT_BTC_PRICE = last_price * (1 + drift_factor) + price_change
    CURRENT_BTC_PRICE = max(10000, CURRENT_BTC_PRICE) 

    current_timestamp = time.time()
    new_price_point = PricePoint(timestamp=current_timestamp, price=round(CURRENT_BTC_PRICE, 2))
    SIMULATED_PRICE_HISTORY.append(new_price_point)

    if len(SIMULATED_PRICE_HISTORY) > MAX_HISTORY_LENGTH:
        SIMULATED_PRICE_HISTORY.pop(0)
    
    return new_price_point

def get_simulated_sentiment() -> SentimentData:
    return SentimentData(**random.choice(MOCK_TWEETS))

# Call initialization when module is loaded
_initialize_history()
# And simulate one tick to ensure CURRENT_BTC_PRICE is set from a dynamic point
if MAX_HISTORY_LENGTH > 0 : # Only simulate if history was meant to be populated
    simulate_new_tick()