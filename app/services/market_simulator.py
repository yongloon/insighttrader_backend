import random
import time
from typing import List
from app.models.pydantic_models import PricePoint, SentimentData

MAX_HISTORY_LENGTH = 200
CURRENT_BTC_PRICE = 65000.0  # Initial Price
SIMULATED_PRICE_HISTORY: List[PricePoint] = [
    PricePoint(timestamp=time.time() - (MAX_HISTORY_LENGTH - i) * 60, price=CURRENT_BTC_PRICE + random.uniform(-50,50) * i/10)
    for i in range(MAX_HISTORY_LENGTH)
] # Initialize with some plausible historical data

MOCK_TWEETS = [
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

def simulate_new_tick():
    global CURRENT_BTC_PRICE, SIMULATED_PRICE_HISTORY

    price_change = random.uniform(-150, 150) # Simulate some volatility
    # Add a slight random drift to make trends more visible over time
    drift_factor = random.choice([-0.0002, -0.0001, 0, 0.0001, 0.0002, 0.0003]) # Small drift
    CURRENT_BTC_PRICE = CURRENT_BTC_PRICE * (1 + drift_factor) + price_change
    CURRENT_BTC_PRICE = max(10000, CURRENT_BTC_PRICE) # Floor price

    current_timestamp = time.time()
    new_price_point = PricePoint(timestamp=current_timestamp, price=round(CURRENT_BTC_PRICE, 2))
    SIMULATED_PRICE_HISTORY.append(new_price_point)

    if len(SIMULATED_PRICE_HISTORY) > MAX_HISTORY_LENGTH:
        SIMULATED_PRICE_HISTORY.pop(0)

    return new_price_point

def get_simulated_sentiment() -> SentimentData:
    return SentimentData(**random.choice(MOCK_TWEETS))

# Initialize with a first tick
simulate_new_tick()